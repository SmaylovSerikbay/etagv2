from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('', views.profile_list, name='profile_list'),  # Список всех профилей
    path('edit/', views.edit_profile, name='edit_profile'),  # Редактирование профиля
    path('nfc/<str:uid>/', views.nfc_entry, name='nfc_entry'),  # Вход через NFC UID
    path('<str:hash>/', views.profile_detail, name='profile_detail'),  # Детали профиля
]