"""
URL configuration for etag_profile project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from profiles.forms import CustomAuthenticationForm
from profiles import views
from django.shortcuts import redirect

class CustomLoginView(auth_views.LoginView):
    def get_success_url(self):
        return f'/profiles/{self.request.user.profile.hash}/'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.welcome, name='welcome'),
    path('nfc/<str:uid>/', views.nfc_entry, name='nfc_entry_root'),
    path('profiles/', include('profiles.urls')),
    path('login/', CustomLoginView.as_view(
        template_name='registration/login.html',
        authentication_form=CustomAuthenticationForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        next_page='welcome'
    ), name='logout'),
    path('signup/', views.signup, name='signup'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
