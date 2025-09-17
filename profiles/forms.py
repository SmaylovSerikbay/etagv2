from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Profile
from django.core.validators import EmailValidator

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Обязательное поле')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        
        # Русификация полей
        self.fields['username'].label = 'Имя пользователя'
        self.fields['email'].label = 'Email'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})
        
        # Русификация полей
        self.fields['username'].label = 'Имя пользователя'
        self.fields['password'].label = 'Пароль'

class ProfileForm(forms.ModelForm):
    email = forms.CharField(required=False)
    website = forms.CharField(required=False)
    class Meta:
        model = Profile
        exclude = ['user', 'hash', 'is_trial']
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),
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