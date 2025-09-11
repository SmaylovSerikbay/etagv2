from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from profiles import views
from profiles.views import SmartLoginView
from django.contrib.auth import views as auth_views
from django.http import HttpResponse

def health_check(request):
    return HttpResponse("healthy")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.welcome, name='welcome'),  # Корневой URL
    path('profiles/', include('profiles.urls')),  # URL для profiles
    
    # Аутентификация
    path('login/', SmartLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='welcome'), name='logout'),
    path('signup/', views.signup, name='signup'),
    
    # Health check
    path('health/', health_check, name='health_check'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 