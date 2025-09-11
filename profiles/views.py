from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .models import Profile
from .forms import SignUpForm, ProfileForm, CustomAuthenticationForm
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse

def welcome(request):
    if request.user.is_authenticated:
        try:
            return redirect('profiles:profile_detail', hash=request.user.profile.hash)
        except Profile.DoesNotExist:
            return redirect('profiles:edit_profile')
    return render(request, 'profiles/welcome.html')

def signup(request):
    if request.user.is_authenticated:
        return redirect('profiles:profile_detail', hash=request.user.profile.hash)
        
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
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
                # Сразу сохраним, чтобы сгенерировались hash/QR с корректным доменом
                profile.save()
                
                # Входим в систему
                login(request, user)
                
                messages.success(request, 'Регистрация успешна! Теперь заполните свой профиль.')
                return redirect('profiles:profile_detail', hash=profile.hash)
            except Exception as e:
                # Если произошла ошибка, удаляем пользователя
                if user:
                    user.delete()
                messages.error(request, f'Ошибка при регистрации: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = SignUpForm()
    
    return render(request, 'profiles/signup.html', {'form': form})

@login_required
def profile_list(request):
    profiles = Profile.objects.all()
    return render(request, 'profiles/profile_list.html', {
        'profiles': profiles
    })

def profile_detail(request, hash):
    # Support both dashed UUIDs and 32-char hex hashes
    normalized_hash = hash.replace('-', '')

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

        # Anonymous user requested a non-existent profile: send to welcome instead of 404
        return redirect('welcome')

    # Redirect to canonical URL if incoming hash was dashed or otherwise different
    if hash != normalized_hash:
        return redirect('profiles:profile_detail', hash=profile.hash)

    is_owner = request.user.is_authenticated and profile.user == request.user
    return render(request, 'profiles/profile_detail.html', {
        'profile': profile,
        'is_owner': is_owner
    })

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
        user = self.request.user
        # Если есть профиль — в профиль, иначе на создание профиля
        try:
            profile = user.profile
            return reverse('profiles:profile_detail', kwargs={'hash': profile.hash})
        except Profile.DoesNotExist:
            return reverse('profiles:edit_profile')
