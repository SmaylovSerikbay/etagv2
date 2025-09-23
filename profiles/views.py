from django.shortcuts import render, get_object_or_404, redirect
import uuid
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .models import Profile, NfcCard, ProfileWidget
from django.utils import timezone
from .forms import SignUpForm, ProfileForm, CustomAuthenticationForm, ProfileWidgetForm
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

def welcome(request):
    if request.user.is_authenticated:
        try:
            return redirect('profiles:profile_detail', hash=request.user.profile.hash)
        except Profile.DoesNotExist:
            return redirect('profiles:edit_profile')
    return render(request, 'profiles/welcome.html')

def signup(request):
    next_url = request.GET.get('next') or request.POST.get('next')
    if request.user.is_authenticated:
        if next_url:
            return redirect(next_url)
        return redirect('profiles:profile_detail', hash=request.user.profile.hash)
        
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Создаем пользователя
                    user = form.save()

                    # Создаем профиль с именем из full_name (если указано)
                    full_name = form.cleaned_data.get('full_name') or user.username
                    profile = Profile.objects.create(
                        user=user,
                        name=full_name.upper(),
                        email=user.email
                    )

                    # Установим текущий сайт перед сохранением
                    current_site = get_current_site(request)
                    protocol = 'https' if request.is_secure() else 'http'
                    profile.set_current_site(f"{protocol}://{current_site.domain}")
                    # Сохраним профиль (генерация hash/QR)
                    profile.save()

                # Входим в систему после фиксации транзакции
                login(request, user)
                messages.success(request, 'Регистрация успешна!')
                if next_url:
                    return redirect(next_url)
                return redirect('profiles:profile_detail', hash=profile.hash)
            except Exception as e:
                # Если произошла ошибка, удаляем пользователя, если он был создан
                try:
                    if user:
                        user.delete()
                except Exception:
                    pass
                messages.error(request, f'Ошибка при регистрации: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = SignUpForm()
    
    return render(request, 'profiles/signup.html', {'form': form, 'next': next_url})

@login_required
def profile_list(request):
    profiles = Profile.objects.all()
    return render(request, 'profiles/profile_list.html', {
        'profiles': profiles
    })

def profile_detail(request, hash):
    # Support both dashed UUIDs and 32-char hex hashes (case-insensitive)
    normalized_hash = hash.replace('-', '').lower()

    # Try to find profile by hash first
    profile = Profile.objects.filter(hash=normalized_hash).first()

    # If not found, try to help the authenticated user recover/create their profile
    if not profile:
        if request.user.is_authenticated:
            # Ensure the current user has a profile
            try:
                profile = request.user.profile
            except Profile.DoesNotExist:
                # Create a minimal profile for the user and persist it with proper site for QR
                profile = Profile(
                    user=request.user,
                    name=request.user.username.upper(),
                    email=request.user.email,
                )
                current_site = get_current_site(request)
                protocol = 'https' if request.is_secure() else 'http'
                profile.set_current_site(f"{protocol}://{current_site.domain}")
                profile.save()

            # Redirect the user to their own canonical profile URL
            return redirect('profiles:profile_detail', hash=profile.hash)

        # Anonymous user requested a non-existent profile: return 404 instead of redirecting
        from django.http import Http404
        raise Http404("Profile not found")

    # Redirect to canonical URL (always dashed UUID form)
    try:
        dashed_hash = str(uuid.UUID(profile.hash))
    except Exception:
        dashed_hash = profile.hash
    if hash != dashed_hash:
        return redirect('profiles:profile_detail', hash=dashed_hash)

    # Разрешаем просмотр профиля без авторизации; владелец определяется только для авторизованных
    is_owner = request.user.is_authenticated and profile.user == request.user
    return render(request, 'profiles/profile_detail.html', {
        'profile': profile,
        'is_owner': is_owner
    })

def nfc_entry(request, uid):
    # Normalize uid to uppercase without spaces
    normalized_uid = (uid or '').strip().upper()
    if not normalized_uid:
        from django.http import Http404
        raise Http404("NFC UID is required")

    # Get or create NFC card record
    card, _ = NfcCard.objects.get_or_create(uid=normalized_uid)
    card.mark_tap()

    # Case 1: Card is already assigned to a profile → всем показываем привязанный профиль
    if card.profile:
        card.save(update_fields=['last_seen_at', 'tap_count'])
        try:
            dashed_hash = str(uuid.UUID(card.profile.hash))
        except Exception:
            dashed_hash = card.profile.hash
        return redirect('profiles:profile_detail', hash=dashed_hash)

    # Card is not assigned yet
    if not request.user.is_authenticated:
        # For anonymous users, require signup and return here after, using absolute URL
        absolute_signup = f"{request.scheme}://{request.get_host()}{reverse('signup')}"
        card.save(update_fields=['first_seen_at', 'last_seen_at', 'tap_count'])
        return redirect(f"{absolute_signup}?next={request.get_full_path()}")

    # Authenticated user tapped an unassigned card → assign it to their profile on second tap
    # Ensure the user has a profile
    try:
        user_profile = request.user.profile
    except Profile.DoesNotExist:
        # Create minimal profile if missing
        user_profile = Profile(
            user=request.user,
            name=request.user.username.upper(),
            email=request.user.email,
        )
        current_site = get_current_site(request)
        protocol = 'https' if request.is_secure() else 'http'
        user_profile.set_current_site(f"{protocol}://{current_site.domain}")
        user_profile.save()

    # Assign and persist
    card.profile = user_profile
    card.assigned_at = timezone.now()
    card.save(update_fields=['profile', 'assigned_at', 'last_seen_at', 'tap_count', 'first_seen_at'])

    try:
        dashed_hash = str(uuid.UUID(user_profile.hash))
    except Exception:
        dashed_hash = user_profile.hash
    return redirect('profiles:profile_detail', hash=dashed_hash)

@login_required
def edit_profile(request):
    profile = get_object_or_404(Profile, user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.name = profile.name.upper()
            profile.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profiles:profile_detail', hash=profile.hash)
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'profiles/edit_profile.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('welcome')

class SmartLoginView(LoginView):
    template_name = 'profiles/login.html'
    redirect_authenticated_user = True
    form_class = CustomAuthenticationForm

    def get_success_url(self):
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url:
            return next_url
        user = self.request.user
        # Если есть профиль — в профиль, иначе на создание профиля
        try:
            profile = user.profile
            return reverse('profiles:profile_detail', kwargs={'hash': profile.hash})
        except Profile.DoesNotExist:
            return reverse('profiles:edit_profile')


# Виджет-лист больше не используется


@login_required
def widget_create(request):
    """Создание нового виджета"""
    profile = get_object_or_404(Profile, user=request.user)
    
    if request.method == 'POST':
        form = ProfileWidgetForm(request.POST)
        if form.is_valid():
            widget = form.save(commit=False)
            widget.profile = profile
            widget.save()
            messages.success(request, 'Виджет успешно создан!')
            return redirect('profiles:profile_detail', hash=profile.hash)
    else:
        form = ProfileWidgetForm()
    
    return render(request, 'profiles/widget_form.html', {
        'form': form,
        'profile': profile,
        'title': 'Добавить кнопку'
    })


@login_required
def widget_edit(request, widget_id):
    """Редактирование виджета — оформление и UX как при создании из шаблона."""
    profile = get_object_or_404(Profile, user=request.user)
    widget = get_object_or_404(ProfileWidget, id=widget_id, profile=profile)

    if request.method == 'POST':
        title = request.POST.get('title', widget.title)
        content = request.POST.get('content', widget.content)
        color = request.POST.get('color', widget.color)
        icon = request.POST.get('icon', widget.icon)

        widget.title = title
        widget.content = content
        widget.color = color
        widget.icon = icon
        widget.save()
        messages.success(request, 'Виджет успешно обновлен!')
        return redirect('profiles:profile_detail', hash=profile.hash)

    return render(request, 'profiles/widget_edit_form.html', {
        'profile': profile,
        'widget': widget
    })


@login_required
def widget_delete(request, widget_id):
    """Удаление виджета"""
    profile = get_object_or_404(Profile, user=request.user)
    widget = get_object_or_404(ProfileWidget, id=widget_id, profile=profile)
    
    if request.method == 'POST':
        widget.delete()
        messages.success(request, 'Виджет успешно удален!')
        return redirect('profiles:profile_detail', hash=profile.hash)
    
    return render(request, 'profiles/widget_confirm_delete.html', {
        'widget': widget,
        'profile': profile
    })


@login_required
@require_http_methods(["POST"])
def widget_hide_api(request, widget_id):
    profile = get_object_or_404(Profile, user=request.user)
    widget = get_object_or_404(ProfileWidget, id=widget_id, profile=profile)
    widget.is_active = False
    widget.save(update_fields=["is_active"])
    return JsonResponse({"success": True})


@login_required
@require_http_methods(["POST"])
def widget_show_api(request, widget_id):
    profile = get_object_or_404(Profile, user=request.user)
    widget = get_object_or_404(ProfileWidget, id=widget_id, profile=profile)
    widget.is_active = True
    widget.save(update_fields=["is_active"])
    return JsonResponse({"success": True})


@login_required
@require_http_methods(["POST"])
def widget_delete_api(request, widget_id):
    profile = get_object_or_404(Profile, user=request.user)
    widget = get_object_or_404(ProfileWidget, id=widget_id, profile=profile)
    widget.delete()
    return JsonResponse({"success": True})


@login_required
@require_http_methods(["POST"])
def widget_duplicate_api(request, widget_id):
    profile = get_object_or_404(Profile, user=request.user)
    widget = get_object_or_404(ProfileWidget, id=widget_id, profile=profile)
    # Create a shallow copy
    original_title = widget.title
    widget.pk = None
    widget.id = None
    widget.order = profile.widgets.count()
    widget.title = original_title
    widget.save()
    return JsonResponse({"success": True, "id": widget.id})


def _get_button_and_widget_templates():
    """Вспомогательная функция возвращает предустановленные шаблоны кнопок и виджетов."""
    button_templates = [
        {
            'id': 'phone',
            'title': 'Номер телефона',
            'icon': 'fas fa-phone',
            'color': '#111111',
            'widget_type': 'contact',
            'content_placeholder': 'Введите номер телефона',
            'description': 'Кнопка для быстрого звонка'
        },
        {
            'id': 'sms',
            'title': 'SMS',
            'icon': 'fas fa-sms',
            'color': '#25D366',
            'widget_type': 'button',
            'content_placeholder': 'Введите номер для SMS',
            'description': 'Отправить SMS сообщение'
        },
        {
            'id': 'email',
            'title': 'Электронная Почта',
            'icon': 'fas fa-envelope',
            'color': '#444444',
            'widget_type': 'contact',
            'content_placeholder': 'Введите email адрес',
            'description': 'Отправить электронное письмо'
        },
        {
            'id': 'website',
            'title': 'Мой Сайт',
            'icon': 'fas fa-globe',
            'color': '#6B6B6B',
            'widget_type': 'link',
            'content_placeholder': 'Введите URL сайта',
            'description': 'Перейти на веб-сайт'
        },
        {
            'id': 'whatsapp',
            'title': 'WhatsApp',
            'icon': 'fab fa-whatsapp',
            'color': '#25D366',
            'widget_type': 'social',
            'content_placeholder': 'Введите номер WhatsApp',
            'description': 'Написать в WhatsApp'
        },
        {
            'id': 'whatsapp_group',
            'title': 'WhatsApp группа',
            'icon': 'fab fa-whatsapp',
            'color': '#25D366',
            'widget_type': 'social',
            'content_placeholder': 'Введите ссылку на группу',
            'description': 'Присоединиться к группе WhatsApp'
        },
        {
            'id': 'telegram',
            'title': 'Telegram',
            'icon': 'fab fa-telegram-plane',
            'color': '#0088cc',
            'widget_type': 'social',
            'content_placeholder': 'Введите username или ссылку',
            'description': 'Написать в Telegram'
        },
        {
            'id': 'instagram',
            'title': 'Instagram',
            'icon': 'fab fa-instagram',
            'color': '#E4405F',
            'widget_type': 'social',
            'content_placeholder': 'Введите username',
            'description': 'Подписаться в Instagram'
        },
        {
            'id': 'facebook',
            'title': 'Facebook',
            'icon': 'fab fa-facebook-f',
            'color': '#1877F2',
            'widget_type': 'social',
            'content_placeholder': 'Введите ссылку на профиль',
            'description': 'Перейти в Facebook'
        },
        {
            'id': 'linkedin',
            'title': 'LinkedIn',
            'icon': 'fab fa-linkedin-in',
            'color': '#0A66C2',
            'widget_type': 'social',
            'content_placeholder': 'Введите ссылку на профиль',
            'description': 'Перейти в LinkedIn'
        },
        {
            'id': 'youtube',
            'title': 'YouTube',
            'icon': 'fab fa-youtube',
            'color': '#FF0000',
            'widget_type': 'social',
            'content_placeholder': 'Введите ссылку на канал',
            'description': 'Подписаться на YouTube'
        },
        {
            'id': 'tiktok',
            'title': 'TikTok',
            'icon': 'fab fa-tiktok',
            'color': '#000000',
            'widget_type': 'social',
            'content_placeholder': 'Введите username',
            'description': 'Подписаться в TikTok'
        }
    ]

    # Дополнительные кнопки, которые нужно добавить, если их нет
    additional_button_templates = [
        {
            'id': 'telegram_group',
            'title': 'Telegram группа',
            'icon': 'fab fa-telegram-plane',
            'color': '#0088cc',
            'widget_type': 'social',
            'content_placeholder': 'Введите ссылку на группу',
            'description': 'Присоединиться к группе Telegram'
        },
        {
            'id': 'vk',
            'title': 'VK',
            'icon': 'fab fa-vk',
            'color': '#4C75A3',
            'widget_type': 'social',
            'content_placeholder': 'Введите ссылку на профиль',
            'description': 'Перейти в VK'
        },
        {
            'id': 'yandex_maps',
            'title': 'Яндекс Карты',
            'icon': 'fas fa-map-marker-alt',
            'color': '#FFCC00',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на Яндекс Карты',
            'description': 'Открыть в Яндекс Картах'
        },
        {
            'id': 'google_maps',
            'title': 'Google Карты',
            'icon': 'fas fa-map-marker-alt',
            'color': '#34A853',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на Google Карты',
            'description': 'Открыть в Google Картах'
        },
        {
            'id': 'two_gis',
            'title': '2ГИС',
            'icon': 'fas fa-map-marker-alt',
            'color': '#00B341',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на 2ГИС',
            'description': 'Открыть в 2ГИС'
        },
        {
            'id': 'ok',
            'title': 'OK',
            'icon': 'fab fa-odnoklassniki',
            'color': '#EE8208',
            'widget_type': 'social',
            'content_placeholder': 'Введите ссылку на профиль',
            'description': 'Перейти в Одноклассники'
        },
        {
            'id': 'skype',
            'title': 'Skype',
            'icon': 'fab fa-skype',
            'color': '#00AFF0',
            'widget_type': 'social',
            'content_placeholder': 'Введите username',
            'description': 'Позвонить в Skype'
        },
        {
            'id': 'x_twitter',
            'title': 'X (Twitter)',
            'icon': 'fab fa-twitter',
            'color': '#1DA1F2',
            'widget_type': 'social',
            'content_placeholder': 'Введите ссылку или username',
            'description': 'Перейти в X (Twitter)'
        },
        {
            'id': 'snapchat',
            'title': 'Snapchat',
            'icon': 'fab fa-snapchat-ghost',
            'color': '#FFFC00',
            'widget_type': 'social',
            'content_placeholder': 'Введите username',
            'description': 'Подписаться в Snapchat'
        },
        {
            'id': 'viber',
            'title': 'Viber',
            'icon': 'fas fa-phone',
            'color': '#7360F2',
            'widget_type': 'social',
            'content_placeholder': 'Введите номер телефона Viber',
            'description': 'Написать в Viber'
        },
        {
            'id': 'viber_group',
            'title': 'Viber группа',
            'icon': 'fas fa-users',
            'color': '#7360F2',
            'widget_type': 'social',
            'content_placeholder': 'Введите ссылку на группу',
            'description': 'Присоединиться к группе Viber'
        },
        {
            'id': 'yandex_zen',
            'title': 'Яндекс Дзен',
            'icon': 'fas fa-rss',
            'color': '#FF0000',
            'widget_type': 'social',
            'content_placeholder': 'Введите ссылку на канал',
            'description': 'Читать Яндекс Дзен'
        },
        {
            'id': 'kwai',
            'title': 'Kwaii',
            'icon': 'fas fa-video',
            'color': '#FF6B00',
            'widget_type': 'social',
            'content_placeholder': 'Введите username',
            'description': 'Подписаться в Kwaii'
        },
        {
            'id': 'wechat',
            'title': 'WeChat',
            'icon': 'fab fa-weixin',
            'color': '#09B83E',
            'widget_type': 'social',
            'content_placeholder': 'Введите ID или ссылку',
            'description': 'Написать в WeChat'
        },
        {
            'id': 'likee',
            'title': 'Likee',
            'icon': 'fas fa-heart',
            'color': '#FF3D68',
            'widget_type': 'social',
            'content_placeholder': 'Введите username',
            'description': 'Подписаться в Likee'
        },
        {
            'id': 'yclients',
            'title': 'YCLIENTS',
            'icon': 'fas fa-calendar-check',
            'color': '#3B82F6',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на запись',
            'description': 'Записаться через YCLIENTS'
        },
        {
            'id': 'sber',
            'title': 'Сбер',
            'icon': 'fas fa-credit-card',
            'color': '#21A038',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку или номер',
            'description': 'Оплатить через Сбер'
        },
        {
            'id': 'yumoney',
            'title': 'ЮMoney',
            'icon': 'fas fa-wallet',
            'color': '#7F3DF2',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на оплату',
            'description': 'Оплатить через ЮMoney'
        },
        {
            'id': 'qiwi',
            'title': 'Киви',
            'icon': 'fas fa-wallet',
            'color': '#FF8C00',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку или номер кошелька',
            'description': 'Оплатить через QIWI'
        },
        {
            'id': 'sber_tips',
            'title': 'Сбер Чаевые',
            'icon': 'fas fa-coins',
            'color': '#21A038',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на чаевые',
            'description': 'Оставить чаевые через Сбер'
        },
        {
            'id': 'yandex_tips',
            'title': 'Яндекс Чаевые',
            'icon': 'fas fa-coins',
            'color': '#FFCC00',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на чаевые',
            'description': 'Оставить чаевые через Яндекс'
        },
        {
            'id': 'two_tip',
            'title': '2TIP',
            'icon': 'fas fa-coins',
            'color': '#0EA5E9',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на чаевые',
            'description': 'Оставить чаевые через 2TIP'
        },
        {
            'id': 'tinkoff',
            'title': 'Тинькофф',
            'icon': 'fas fa-credit-card',
            'color': '#FFDD2D',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на оплату',
            'description': 'Оплатить через Тинькофф'
        },
        {
            'id': 'behance',
            'title': 'Behance',
            'icon': 'fab fa-behance',
            'color': '#1769FF',
            'widget_type': 'social',
            'content_placeholder': 'Введите ссылку на профиль',
            'description': 'Посмотреть портфолио на Behance'
        },
        {
            'id': 'fivehundredpx',
            'title': '500px',
            'icon': 'fab fa-500px',
            'color': '#0099E5',
            'widget_type': 'social',
            'content_placeholder': 'Введите ссылку на профиль',
            'description': 'Посмотреть фото на 500px'
        },
        {
            'id': 'pinterest',
            'title': 'Pinterest',
            'icon': 'fab fa-pinterest',
            'color': '#E60023',
            'widget_type': 'social',
            'content_placeholder': 'Введите ссылку на профиль',
            'description': 'Посмотреть Pinterest'
        },
        {
            'id': 'twitch',
            'title': 'Twitch',
            'icon': 'fab fa-twitch',
            'color': '#9146FF',
            'widget_type': 'social',
            'content_placeholder': 'Введите ссылку на канал',
            'description': 'Смотреть стрим на Twitch'
        },
        {
            'id': 'donationalerts',
            'title': 'DonationAlerts',
            'icon': 'fas fa-donate',
            'color': '#22C55E',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на DonationAlerts',
            'description': 'Поддержать донатом'
        },
        {
            'id': 'onlyfans',
            'title': 'OnlyFans',
            'icon': 'fas fa-star',
            'color': '#00AFF0',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на профиль',
            'description': 'Подписаться на OnlyFans'
        },
        {
            'id': 'boosty',
            'title': 'Boosty',
            'icon': 'fas fa-bolt',
            'color': '#FF6B00',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на профиль',
            'description': 'Поддержать на Boosty'
        },
        {
            'id': 'patreon',
            'title': 'Patreon',
            'icon': 'fab fa-patreon',
            'color': '#FF424D',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на профиль',
            'description': 'Поддержать на Patreon'
        },
        {
            'id': 'apple_music',
            'title': 'Apple Музыка',
            'icon': 'fab fa-apple',
            'color': '#000000',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на плейлист',
            'description': 'Слушать в Apple Music'
        },
        {
            'id': 'spotify',
            'title': 'Spotify',
            'icon': 'fab fa-spotify',
            'color': '#1DB954',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на плейлист',
            'description': 'Слушать в Spotify'
        },
        {
            'id': 'youtube_music',
            'title': 'YouTube Музыка',
            'icon': 'fab fa-youtube',
            'color': '#FF0000',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на плейлист',
            'description': 'Слушать в YouTube Music'
        },
        {
            'id': 'sber_sound',
            'title': 'Сбер Звук',
            'icon': 'fas fa-music',
            'color': '#21A038',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на плейлист',
            'description': 'Слушать в Сбер Звук'
        },
        {
            'id': 'yandex_music',
            'title': 'Яндекс Музыка',
            'icon': 'fas fa-music',
            'color': '#FFCC00',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на плейлист',
            'description': 'Слушать в Яндекс Музыке'
        },
        {
            'id': 'vk_music',
            'title': 'VK Музыка',
            'icon': 'fas fa-music',
            'color': '#4C75A3',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на плейлист',
            'description': 'Слушать в VK Музыке'
        },
        {
            'id': 'soundcloud',
            'title': 'SoundCloud',
            'icon': 'fab fa-soundcloud',
            'color': '#FF5500',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на трек или плейлист',
            'description': 'Слушать в SoundCloud'
        },
        {
            'id': 'boom',
            'title': 'Boom',
            'icon': 'fas fa-music',
            'color': '#000000',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на плейлист',
            'description': 'Слушать в Boom'
        },
        {
            'id': 'steam',
            'title': 'Steam',
            'icon': 'fab fa-steam',
            'color': '#1B2838',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на профиль',
            'description': 'Перейти в Steam'
        },
        {
            'id': 'teamspeak',
            'title': 'TeamSpeak',
            'icon': 'fas fa-headset',
            'color': '#004E9A',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на сервер',
            'description': 'Подключиться к TeamSpeak'
        },
        {
            'id': 'discord',
            'title': 'Discord',
            'icon': 'fab fa-discord',
            'color': '#5865F2',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на сервер',
            'description': 'Присоединиться к серверу Discord'
        },
        {
            'id': 'app_store',
            'title': 'App Store',
            'icon': 'fab fa-apple',
            'color': '#000000',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на приложение',
            'description': 'Открыть в App Store'
        },
        {
            'id': 'play_market',
            'title': 'Play Market',
            'icon': 'fab fa-android',
            'color': '#3DDC84',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на приложение',
            'description': 'Открыть в Google Play'
        },
        {
            'id': 'avito',
            'title': 'Avito',
            'icon': 'fas fa-shopping-bag',
            'color': '#19B5FE',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на магазин или объявление',
            'description': 'Открыть на Avito'
        },
        {
            'id': 'olx',
            'title': 'OLX',
            'icon': 'fas fa-shopping-bag',
            'color': '#3A77FF',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на магазин или объявление',
            'description': 'Открыть на OLX'
        },
        {
            'id': 'google_docs',
            'title': 'Google Docs',
            'icon': 'fab fa-google',
            'color': '#4285F4',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на документ',
            'description': 'Открыть Google Документ'
        },
        {
            'id': 'google_sheets',
            'title': 'Google Sheets',
            'icon': 'fab fa-google',
            'color': '#34A853',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на таблицу',
            'description': 'Открыть Google Таблицу'
        },
        {
            'id': 'google_slides',
            'title': 'Google Presentation',
            'icon': 'fab fa-google',
            'color': '#FBBC05',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на презентацию',
            'description': 'Открыть Google Презентацию'
        },
        {
            'id': 'google_forms',
            'title': 'Google Forms',
            'icon': 'fab fa-google',
            'color': '#673AB7',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на форму',
            'description': 'Открыть Google Форму'
        },
        {
            'id': 'yandex_disk',
            'title': 'Яндекс Диск',
            'icon': 'fas fa-hdd',
            'color': '#FFCC00',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на файл/папку',
            'description': 'Открыть Яндекс Диск'
        },
        {
            'id': 'kaspi',
            'title': 'KASPI',
            'icon': 'fas fa-credit-card',
            'color': '#ED1B24',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на оплату или магазин',
            'description': 'Открыть Kaspi'
        }
    ]

    existing_ids = {t['id'] for t in button_templates}
    for t in additional_button_templates:
        if t['id'] not in existing_ids:
            button_templates.append(t)
            existing_ids.add(t['id'])

    widget_templates = [
        {
            'id': 'text_info',
            'title': 'Информационный текст',
            'icon': 'fas fa-info-circle',
            'color': '#3B82F6',
            'widget_type': 'text',
            'content_placeholder': 'Введите текст для отображения',
            'description': 'Отобразить информационный текст'
        },
        {
            'id': 'contact_card',
            'title': 'Визитная карточка',
            'icon': 'fas fa-address-card',
            'color': '#10B981',
            'widget_type': 'contact',
            'content_placeholder': 'Введите контактную информацию',
            'description': 'Показать контактные данные'
        },
        {
            'id': 'location',
            'title': 'Карта',
            'icon': 'fas fa-map-marker-alt',
            'color': '#EF4444',
            'widget_type': 'link',
            'content_placeholder': 'Введите ссылку на карту',
            'description': 'Открыть местоположение на карте'
        },
        {
            'id': 'calendar',
            'title': 'Календарь',
            'icon': 'fas fa-calendar',
            'color': '#8B5CF6',
            'widget_type': 'button',
            'content_placeholder': 'Введите ссылку на календарь',
            'description': 'Записаться на встречу'
        },
        {
            'id': 'download',
            'title': 'Скачать файл',
            'icon': 'fas fa-download',
            'color': '#F59E0B',
            'widget_type': 'button',
            'content_placeholder': 'Введите ссылку на файл',
            'description': 'Скачать документ или файл'
        }
    ]

    # Исключаем ненужные шаблоны виджетов
    excluded_widget_ids = {"text_info", "contact_card", "calendar", "download"}
    widget_templates = [t for t in widget_templates if t.get('id') not in excluded_widget_ids]

    return button_templates, widget_templates


@login_required
def widget_templates(request):
    """Страница выбора готовых шаблонов кнопок и виджетов"""
    profile = get_object_or_404(Profile, user=request.user)
    button_templates, widget_templates = _get_button_and_widget_templates()
    templates = button_templates + widget_templates

    return render(request, 'profiles/widget_templates.html', {
        'profile': profile,
        'templates': templates
    })


@login_required
def widget_template_new(request, template_id: str):
    """Полноэкранная страница создания виджета из выбранного шаблона (вместо модального окна)."""
    profile = get_object_or_404(Profile, user=request.user)
    button_templates, widget_templates = _get_button_and_widget_templates()

    # Ищем шаблон по id среди обоих списков
    combined = {t['id']: t for t in (button_templates + widget_templates)}
    template = combined.get(template_id)
    if not template:
        messages.error(request, 'Шаблон не найден')
        return redirect('profiles:widget_templates')

    # Эта страница только отображает форму; отправка пойдёт POST-ом в widget_create_from_template
    return render(request, 'profiles/widget_template_form.html', {
        'profile': profile,
        'template': template,
        'post_url': reverse('profiles:widget_create_from_template', kwargs={'template_id': template_id})
    })


@login_required
def widget_create_from_template(request, template_id):
    """Создание виджета из шаблона"""
    profile = get_object_or_404(Profile, user=request.user)
    
    # Получаем данные шаблона из POST запроса
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        icon = request.POST.get('icon')
        color = request.POST.get('color')
        widget_type = request.POST.get('widget_type')
        
        if title and content:
            # Обрабатываем содержимое в зависимости от типа виджета
            if widget_type == 'social':
                if 'whatsapp' in template_id and not content.startswith('https://'):
                    content = f"https://wa.me/{content.replace('+', '').replace(' ', '')}"
                elif 'telegram' in template_id and not content.startswith('https://'):
                    content = f"https://t.me/{content.replace('@', '')}"
                elif 'instagram' in template_id and not content.startswith('https://'):
                    content = f"https://instagram.com/{content.replace('@', '')}"
                elif 'youtube' in template_id and not content.startswith('https://'):
                    content = f"https://youtube.com/@{content.replace('@', '')}"
                elif 'tiktok' in template_id and not content.startswith('https://'):
                    content = f"https://tiktok.com/@{content.replace('@', '')}"
            elif widget_type == 'contact':
                if 'phone' in template_id and not content.startswith('tel:'):
                    content = f"tel:{content.replace('+', '').replace(' ', '')}"
            elif widget_type == 'button':
                if 'sms' in template_id and not content.startswith('sms:'):
                    content = f"sms:{content.replace('+', '').replace(' ', '')}"
                elif 'location' in template_id and not content.startswith('https://'):
                    content = f"https://maps.google.com/?q={content}"
            
            # Создаем виджет
            widget = ProfileWidget.objects.create(
                profile=profile,
                title=title,
                content=content,
                icon=icon,
                color=color,
                widget_type=widget_type,
                order=profile.widgets.count()
            )
            
            messages.success(request, f'Виджет "{title}" успешно добавлен!')
            return redirect('profiles:profile_detail', hash=profile.hash)
        else:
            messages.error(request, 'Пожалуйста, заполните все обязательные поля')
    
    # Если это GET запрос, перенаправляем на страницу шаблонов
    return redirect('profiles:widget_templates')


@login_required
@require_http_methods(["POST"])
def update_contact_order(request):
    """Обновление порядка контактов и виджетов"""
    try:
        data = json.loads(request.body)
        order_data = data.get('order', [])
        
        profile = get_object_or_404(Profile, user=request.user)
        
        # Обновляем порядок виджетов
        for item in order_data:
            if item.get('type') == 'widget' and item.get('id'):
                try:
                    widget = ProfileWidget.objects.get(
                        id=item['id'], 
                        profile=profile
                    )
                    widget.order = item['order']
                    widget.save()
                except ProfileWidget.DoesNotExist:
                    continue
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=400)
