from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Profile, ProfileWidget
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from .widget_utils import get_storage_content

MAX_AVATAR_MB = 5  # Целевой размер после сжатия
MAX_BACKGROUND_MB = 5
# Жёсткий лимит входного файла (до сжатия), чтобы не грузить сервер чрезмерно
HARD_MAX_UPLOAD_MB = 25

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Обязательное поле')
    full_name = forms.CharField(max_length=150, label='Имя и фамилия')
    # скрытое поле для совместимости с UserCreationForm, заполняем из email
    username = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = User
        fields = ('full_name', 'email', 'password1', 'password2', 'username')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Стили
        for f in ['full_name', 'email', 'password1', 'password2']:
            if f in self.fields:
                self.fields[f].widget.attrs.update({'class': 'form-control'})
        # Подписи
        self.fields['email'].label = 'Email'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'

    def _generate_username(self) -> str:
        email: str = self.cleaned_data.get('email', '')
        base = (email.split('@')[0] or 'user').strip().replace(' ', '_')[:20]
        # Гарантия уникальности
        candidate = base
        idx = 1
        from django.contrib.auth.models import User as DjangoUser
        while DjangoUser.objects.filter(username=candidate).exists():
            suffix = f"_{idx}"
            candidate = f"{base[: max(1, 20 - len(suffix))]}{suffix}"
            idx += 1
        return candidate

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        # Задаём username и email принудительно
        user.username = self._generate_username()
        user.email = self.cleaned_data.get('email')
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})
        
        # Русификация полей
        self.fields['username'].label = 'Email'
        self.fields['password'].label = 'Пароль'

    def clean(self):
        # Позволяем вход по email (поле username формы содержит email)
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        from django.contrib.auth import authenticate
        from django.contrib.auth.models import User as DjangoUser

        user = None
        if email and password:
            # Находим пользователя по email (без учёта регистра)
            email_user = DjangoUser.objects.filter(email__iexact=email).first()
            if email_user:
                user = authenticate(self.request, username=email_user.username, password=password)

        if user is None:
            # Сохраняем совместимость с классическим входом (если вдруг введён username)
            user = authenticate(self.request, username=email, password=password)

        if user is None:
            raise forms.ValidationError('Неверный email или пароль')

        self.confirm_login_allowed(user)
        self.user_cache = user
        return self.cleaned_data

class ProfileForm(forms.ModelForm):
    email = forms.CharField(required=False)
    website = forms.CharField(required=False)
    class Meta:
        model = Profile
        exclude = ['user', 'hash', 'is_trial']
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),
            'theme_background_color': forms.TextInput(attrs={'type': 'color'}),
            'theme_line_color': forms.TextInput(attrs={'type': 'color'}),
            'theme_page_background_color': forms.TextInput(attrs={'type': 'color'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        # Гарантируем класс для переопределенных полей
        if 'email' in self.fields:
            self.fields['email'].widget.attrs.update({'class': 'form-control'})
        if 'website' in self.fields:
            self.fields['website'].widget.attrs.update({'class': 'form-control'})
        # Обновим подсказки по изображениям с учетом ограничений
        if 'avatar' in self.fields:
            self.fields['avatar'].label = 'АВАТАР'
            self.fields['avatar'].help_text = (
                f"Рекомендуемый размер 100x100. Файлы до {HARD_MAX_UPLOAD_MB} МБ принимаются и автоматически сжимаются до {MAX_AVATAR_MB} МБ"
            )
        if 'background' in self.fields:
            self.fields['background'].help_text = (
                f"Рекомендуемый размер 530x200. Файлы до {HARD_MAX_UPLOAD_MB} МБ принимаются и автоматически сжимаются до {MAX_BACKGROUND_MB} МБ"
            )
        # Новые цветовые поля
        if 'theme_background_color' in self.fields:
            self.fields['theme_background_color'].label = 'ЦВЕТ ФОНА СТРАНИЦЫ'
            self.fields['theme_background_color'].help_text = 'Общий фон страницы (за кнопками)'
            self.fields['theme_background_color'].widget.attrs.update({'class': 'form-control', 'style': 'padding:0;height:42px;'})
        if 'theme_line_color' in self.fields:
            self.fields['theme_line_color'].label = 'ЦВЕТ ЛИНИЙ/ГРАНИЦ'
            self.fields['theme_line_color'].help_text = 'Линии разделителей и границы карточек'
            self.fields['theme_line_color'].widget.attrs.update({'class': 'form-control', 'style': 'padding:0;height:42px;'})
        if 'theme_page_background_color' in self.fields:
            self.fields['theme_page_background_color'].label = 'ВНЕШНИЙ ФОН СТРАНИЦЫ'
            self.fields['theme_page_background_color'].help_text = 'Фон за всей страницей'
            self.fields['theme_page_background_color'].widget.attrs.update({'class': 'form-control', 'style': 'padding:0;height:42px;'})
        # Телефоны: позволяем хранить несколько через запятую (увеличим длину, проверим поэлементно)
        if 'phone' in self.fields:
            self.fields['phone'] = forms.CharField(required=False, max_length=255)
            self.fields['phone'].widget.attrs.update({'class': 'form-control'})

    def clean_phone(self):
        phone_raw = self.cleaned_data.get('phone', '') or ''
        items = [p.strip() for p in phone_raw.split(',') if p.strip()]
        errors = []
        for p in items:
            if len(p) > 20:
                errors.append(f"'{p}' — более 20 символов")
        if errors:
            raise forms.ValidationError('Каждый номер должен быть не длиннее 20 символов: ' + '; '.join(errors))
        return ','.join(items)

    def clean_email(self):
        email_raw = self.cleaned_data.get('email', '') or ''
        items = [e.strip() for e in email_raw.split(',') if e.strip()]
        validator = EmailValidator()
        bad = []
        for e in items:
            try:
                validator(e)
            except Exception:
                bad.append(e)
        if bad:
            raise forms.ValidationError('Неверный email: ' + ', '.join(bad))
        return ','.join(items)

    def clean_website(self):
        website_raw = self.cleaned_data.get('website', '') or ''
        items = [w.strip() for w in website_raw.split(',') if w.strip()]
        return ','.join(items)

    def _validate_file_size(self, f, max_mb: int, label: str):
        if not f:
            return f
        # Разрешаем файлы больше целевого лимита (они будут сжаты на сервере),
        # но вводим жёсткий верхний предел для защиты сервера
        hard_limit = HARD_MAX_UPLOAD_MB * 1024 * 1024
        size = getattr(f, 'size', None)
        if size is not None and size > hard_limit:
            raise ValidationError(f"{label}: файл больше {HARD_MAX_UPLOAD_MB} МБ")
        return f

    def clean_avatar(self):
        f = self.cleaned_data.get('avatar')
        return self._validate_file_size(f, MAX_AVATAR_MB, 'Аватар')

    def clean_background(self):
        f = self.cleaned_data.get('background')
        return self._validate_file_size(f, MAX_BACKGROUND_MB, 'Фон')

    # Общая вспомогательная проверка длины элементов для соцсетей
    def _validate_list_items_length(self, raw_value: str, max_len: int, label: str):
        items = [v.strip() for v in (raw_value or '').split(',') if v.strip()]
        too_long = [v for v in items if len(v) > max_len]
        if too_long:
            raise forms.ValidationError(f'Каждый {label} должен быть не длиннее {max_len} символов: ' + ', '.join(too_long))
        return ','.join(items)

    def clean_instagram(self):
        return self._validate_list_items_length(self.cleaned_data.get('instagram', ''), 100, 'Instagram')

    def clean_facebook(self):
        return self._validate_list_items_length(self.cleaned_data.get('facebook', ''), 100, 'Facebook')

    def clean_twitter(self):
        return self._validate_list_items_length(self.cleaned_data.get('twitter', ''), 100, 'Twitter')

    def clean_linkedin(self):
        return self._validate_list_items_length(self.cleaned_data.get('linkedin', ''), 100, 'LinkedIn')

    def clean_telegram(self):
        return self._validate_list_items_length(self.cleaned_data.get('telegram', ''), 100, 'Telegram')

    def clean_whatsapp(self):
        return self._validate_list_items_length(self.cleaned_data.get('whatsapp', ''), 100, 'WhatsApp')


class ProfileWidgetForm(forms.ModelForm):
    class Meta:
        model = ProfileWidget
        fields = ['widget_type', 'title', 'content', 'icon', 'color', 'is_active', 'order']
        widgets = {
            'widget_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fas fa-heart'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Русские ярлыки
        self.fields['title'].label = 'Название'
        self.fields['content'].label = 'Содержимое'
        self.fields['icon'].label = 'Иконка (Font Awesome)'
        self.fields['color'].label = 'Цвет кнопки'
        self.fields['is_active'].label = 'Активен'
        self.fields['order'].label = 'Порядок'

        # Placeholder'ы как на макете
        self.fields['title'].widget.attrs.update({'placeholder': 'Ваша кнопка'})
        self.fields['content'].widget.attrs.update({'placeholder': 'Введите содержимое'})

        # Значения по умолчанию для кастомной кнопки (если форма не связана с существующей записью)
        if not self.is_bound and not getattr(self.instance, 'pk', None):
            self.initial.setdefault('widget_type', 'button')
            self.initial.setdefault('title', 'Ваша кнопка')
            self.initial.setdefault('icon', 'fas fa-cog')
            self.initial.setdefault('color', '#111111')
            self.initial.setdefault('is_active', True)

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        widget_type = self.cleaned_data.get('widget_type', 'button')
        
        if not content:
            raise forms.ValidationError('Содержимое не может быть пустым')
        
        # Валидация в зависимости от типа виджета
        if widget_type == 'contact':
            # Для контактов принимаем телефоны, email, адреса
            if content.startswith(('tel:', 'mailto:', 'sms:')):
                return content
            # Если не протокол, проверяем что это может быть телефон или email
            if '@' in content or content.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
                return content
            raise forms.ValidationError('Для контакта укажите телефон, email или адрес')
        
        elif widget_type == 'social':
            # Для соцсетей принимаем username, ссылки, номера
            if content.startswith(('http://', 'https://', '@')):
                return content
            # Username без @ тоже принимаем
            if content.replace('_', '').replace('.', '').isalnum():
                return content
            # Номера телефонов для WhatsApp
            if content.replace('+', '').replace('-', '').replace(' ', '').isdigit():
                return content
            raise forms.ValidationError('Для социальной сети укажите username, ссылку или номер телефона')
        
        elif widget_type == 'link':
            # Для ссылок принимаем URL или текст
            if content.startswith(('http://', 'https://', 'tel:', 'mailto:', 'sms:')):
                return content
            # Если не URL, принимаем как есть (может быть обработан в view)
            return content
        
        elif widget_type == 'button':
            # Для кнопок принимаем все - URL, текст, номера, email
            return content
        
        elif widget_type == 'text':
            # Для текста принимаем любой текст
            return content
        
        return content