# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации для кастомной модели User"""
    email = forms.EmailField(required=False, help_text='Необязательно')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Убираем стандартные help_text от Django
        self.fields['username'].help_text = 'Только буквы, цифры и символы @/./+/-/_'
        self.fields['password1'].help_text = 'Минимум 8 символов. Не должен быть слишком простым.'
        self.fields['password2'].help_text = 'Введите пароль еще раз для подтверждения'


class CustomAuthenticationForm(AuthenticationForm):
    """Форма входа"""
    username = forms.CharField(label='Логин')
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')


class UserProfileForm(forms.ModelForm):
    """Форма редактирования профиля"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }