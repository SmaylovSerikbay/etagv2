from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from .models import Profile
from .forms import SignUpForm, ProfileForm, CustomAuthenticationForm
from django.contrib.sites.shortcuts import get_current_site

def welcome(request):
    if request.user.is_authenticated:
        return redirect('profiles:profile_detail', hash=request.user.profile.hash)
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
    profile = get_object_or_404(Profile, hash=hash)
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
