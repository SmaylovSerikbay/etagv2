from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('', views.profile_list, name='profile_list'),  # Список всех профилей
    path('edit/', views.edit_profile, name='edit_profile'),  # Редактирование профиля
    path('widgets/create/', views.widget_create, name='widget_create'),  # Создание виджета
    path('widgets/templates/', views.widget_templates, name='widget_templates'),  # Шаблоны виджетов
    path('widgets/templates/<str:template_id>/new/', views.widget_template_new, name='widget_template_new'),  # Полностраничное создание из шаблона
    path('widgets/templates/<str:template_id>/', views.widget_create_from_template, name='widget_create_from_template'),  # Создание из шаблона
    path('widgets/<int:widget_id>/edit/', views.widget_edit, name='widget_edit'),  # Редактирование виджета
    path('widgets/<int:widget_id>/delete/', views.widget_delete, name='widget_delete'),  # Удаление виджета
    # API-действия с виджетом
    path('widgets/<int:widget_id>/hide/', views.widget_hide_api, name='widget_hide_api'),
    path('widgets/<int:widget_id>/show/', views.widget_show_api, name='widget_show_api'),
    path('widgets/<int:widget_id>/duplicate/', views.widget_duplicate_api, name='widget_duplicate_api'),
    path('widgets/<int:widget_id>/delete-json/', views.widget_delete_api, name='widget_delete_api'),
    path('update-contact-order/', views.update_contact_order, name='update_contact_order'),  # Обновление порядка контактов
    path('nfc/<str:uid>/', views.nfc_entry, name='nfc_entry'),  # Вход через NFC UID
    path('<str:hash>/', views.profile_detail, name='profile_detail'),  # Детали профиля
]