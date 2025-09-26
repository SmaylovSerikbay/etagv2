from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image, ImageDraw, ImageOps
from django.utils import timezone
import os

def optimize_image(image_field, max_size=(800, 600), quality=85, max_size_mb=5):
    """
    Быстро оптимизирует изображение до указанного размера в MB
    """
    if not image_field:
        return image_field
    
    try:
        # Открываем изображение
        img = Image.open(image_field)
        
        # Конвертируем в RGB если нужно
        if img.mode in ('RGBA', 'LA', 'P'):
            # Создаем белый фон для прозрачных изображений
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Агрессивно уменьшаем размер для быстрой обработки
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Быстрое сжатие с более агрессивными настройками
        max_size_bytes = max_size_mb * 1024 * 1024
        
        # Начинаем с более низкого качества для быстрого результата
        current_quality = min(quality, 0.7)  # Максимум 70% качества
        
        # Пробуем только 3 уровня качества для скорости
        quality_levels = [current_quality, 0.5, 0.3]
        
        for q in quality_levels:
            output = BytesIO()
            img.save(output, format='JPEG', quality=int(q * 100), optimize=True)
            # Measure actual bytes of the buffer, not the current cursor
            size_bytes = output.getbuffer().nbytes
            output.seek(0)
            if size_bytes <= max_size_bytes:
                break
        
        # Создаем новый файл с оптимизированным содержимым
        # Во избежание вложенных путей типа avatars/avatars/... используем только базовое имя
        # и синхронизируем расширение с форматом JPEG
        original_name = os.path.basename(getattr(image_field, 'name', 'upload'))
        base_name, _ = os.path.splitext(original_name)
        safe_name = f"{base_name}.jpg"
        optimized_file = File(output, name=safe_name)
        return optimized_file
        
    except Exception as e:
        # Если оптимизация не удалась, возвращаем оригинальный файл
        print(f"Ошибка оптимизации изображения: {e}")
        return image_field

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField('ИМЯ', max_length=100)
    info = models.TextField('МОЯ ЭЛЕКТРОННАЯ ВИЗИТКА', blank=True)
    avatar = models.ImageField('ФОТО', upload_to='avatars/', help_text='Рекомендуемый размер 100x100', null=True, blank=True)
    background = models.ImageField('ФОН', upload_to='backgrounds/', null=True, blank=True, help_text='Рекомендуемый размер 530x200')
    company = models.CharField('КОМПАНИЯ', max_length=100, blank=True)
    position = models.CharField('ДОЛЖНОСТЬ', max_length=100, blank=True)
    phone = models.CharField('ТЕЛЕФОН', max_length=255, blank=True)
    email = models.CharField('EMAIL', max_length=512, blank=True)
    website = models.CharField('САЙТ', max_length=1024, blank=True)
    instagram = models.CharField('INSTAGRAM', max_length=512, blank=True)
    facebook = models.CharField('FACEBOOK', max_length=512, blank=True)
    twitter = models.CharField('TWITTER', max_length=512, blank=True)
    linkedin = models.CharField('LINKEDIN', max_length=512, blank=True)
    telegram = models.CharField('TELEGRAM', max_length=512, blank=True)
    whatsapp = models.CharField('WHATSAPP', max_length=512, blank=True)
    birthday = models.DateField('ДЕНЬ РОЖДЕНИЯ', null=True, blank=True)
    display_birthday = models.BooleanField('ПОКАЗЫВАТЬ ДЕНЬ РОЖДЕНИЯ', default=False)
    hash = models.CharField(max_length=32, unique=True, editable=False)
    is_trial = models.BooleanField('ПРОБНЫЙ ПЕРИОД', default=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.hash:
            self.hash = uuid.uuid4().hex
        if not self.name:
            self.name = self.user.username.upper()
        
        # Оптимизируем изображения перед сохранением (сжимаем до 5MB)
        if self.avatar:
            optimized = optimize_image(self.avatar, max_size=(300, 300), quality=70, max_size_mb=5)
            if optimized:
                # Сохраняем через FieldFile.save, чтобы корректно применился upload_to ('avatars/')
                original_name = os.path.basename(getattr(self.avatar, 'name', 'upload'))
                base_name, _ = os.path.splitext(original_name)
                safe_name = f"{base_name}.jpg"
                self.avatar.save(safe_name, optimized, save=False)
        if self.background:
            optimized_bg = optimize_image(self.background, max_size=(600, 300), quality=65, max_size_mb=5)
            if optimized_bg:
                original_bg_name = os.path.basename(getattr(self.background, 'name', 'upload'))
                base_bg_name, _ = os.path.splitext(original_bg_name)
                safe_bg_name = f"{base_bg_name}.jpg"
                self.background.save(safe_bg_name, optimized_bg, save=False)
            
        # Генерация QR кода
        if not self.qr_code:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=2,
            )
            
            # Получаем абсолютный URL для профиля
            if hasattr(self, '_current_site'):
                # Используем сохраненный current_site если он есть
                current_site = self._current_site
            else:
                # Для локальной разработки используем настройки из settings
                protocol = 'http' if settings.DEBUG else 'https'
                domain = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'
                current_site = f"{protocol}://{domain}"

            # Генерируем URL с UUID в формате с дефисами
            try:
                dashed_hash = str(uuid.UUID(self.hash))
            except Exception:
                dashed_hash = self.hash
            profile_url = f"{current_site}{reverse('profiles:profile_detail', kwargs={'hash': dashed_hash})}"
            qr.add_data(profile_url)
            qr.make(fit=True)

            # Создаем QR код с логотипом
            qr_image = qr.make_image(fill_color="#007AFF", back_color="white").convert('RGB')
            
            # Сохраняем QR код
            buffer = BytesIO()
            qr_image.save(buffer, format='PNG')
            self.qr_code.save(f'qr_{self.hash}.png', File(buffer), save=False)
            
        super().save(*args, **kwargs)
    
    def set_current_site(self, current_site):
        """Метод для установки текущего сайта перед сохранением"""
        self._current_site = current_site
    
    def get_absolute_url(self):
        # Возвращаем URL с UUID в формате с дефисами
        try:
            dashed_hash = str(uuid.UUID(self.hash))
        except Exception:
            dashed_hash = self.hash
        return reverse('profiles:profile_detail', kwargs={'hash': dashed_hash})
    
    def __str__(self):
        return self.name.upper()
    
    class Meta:
        verbose_name = 'ПРОФИЛЬ'
        verbose_name_plural = 'ПРОФИЛИ'

    # Удобные свойства для работы с несколькими значениями соцсетей (через запятую)
    @property
    def telegram_list(self):
        return [item.strip() for item in (self.telegram or '').split(',') if item.strip()]

    @property
    def whatsapp_list(self):
        return [item.strip() for item in (self.whatsapp or '').split(',') if item.strip()]

    @property
    def instagram_list(self):
        return [item.strip() for item in (self.instagram or '').split(',') if item.strip()]

    @property
    def facebook_list(self):
        return [item.strip() for item in (self.facebook or '').split(',') if item.strip()]

    @property
    def linkedin_list(self):
        return [item.strip() for item in (self.linkedin or '').split(',') if item.strip()]

    @property
    def phone_list(self):
        return [item.strip() for item in (self.phone or '').split(',') if item.strip()]

    @property
    def email_list(self):
        return [item.strip() for item in (self.email or '').split(',') if item.strip()]

    @property
    def website_list(self):
        return [item.strip() for item in (self.website or '').split(',') if item.strip()]


class NfcCard(models.Model):
    uid = models.CharField(max_length=128, unique=True)
    profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='nfc_cards')
    first_seen_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    tap_count = models.PositiveIntegerField(default=0)

    def mark_tap(self):
        now = timezone.now()
        if not self.first_seen_at:
            self.first_seen_at = now
        self.last_seen_at = now
        self.tap_count = (self.tap_count or 0) + 1

    def __str__(self):
        return f"NFC {self.uid} -> {self.profile.name if self.profile else 'unassigned'}"

    class Meta:
        verbose_name = 'NFC карта'
        verbose_name_plural = 'NFC карты'


class ProfileWidget(models.Model):
    WIDGET_TYPES = [
        ('button', 'Кнопка'),
        ('link', 'Ссылка'),
        ('text', 'Текст'),
        ('social', 'Социальная сеть'),
        ('contact', 'Контакт'),
    ]
    
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='widgets')
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES, default='button')
    title = models.CharField(max_length=100, verbose_name='Название')
    content = models.TextField(verbose_name='Содержимое/URL')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Иконка (Font Awesome)')
    color = models.CharField(max_length=7, default='#007AFF', verbose_name='Цвет')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_widget_type_display()})"

    class Meta:
        verbose_name = 'Виджет профиля'
        verbose_name_plural = 'Виджеты профиля'
        ordering = ['order', 'created_at']