from django.shortcuts import render, get_object_or_404, redirect
import uuid
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .models import Profile, NfcCard
from django.utils import timezone
from .forms import SignUpForm, ProfileForm, CustomAuthenticationForm
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.db import transaction

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

                    # Создаем профиль
                    profile = Profile.objects.create(
                        user=user,
                        name=user.username.upper(),
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
        # Do not force registration for anonymous users; send them to welcome page
        card.save(update_fields=['first_seen_at', 'last_seen_at', 'tap_count'])
        return redirect('welcome')

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
