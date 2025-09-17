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