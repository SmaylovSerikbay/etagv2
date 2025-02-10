from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('list/', views.profile_list, name='profile_list'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('<str:hash>/', views.profile_detail, name='profile_detail'),
]