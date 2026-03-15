# teams/forms.py - СОЗДАЙТЕ ЭТОТ ФАЙЛ

from django import forms
from django.utils.text import slugify
from .models import Team


class TeamForm(forms.ModelForm):
    """Форма создания/редактирования команды"""
    
    class Meta:
        model = Team
        fields = ['name', 'tag', 'slug', 'logo', 'founded_date', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название команды',
                'required': True
            }),
            'tag': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'FC, TM, UNI...',
                'maxlength': '5'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Оставьте пустым для автоматической генерации'
            }),
            'founded_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Описание команды (необязательно)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем необязательными
        self.fields['slug'].required = False
        self.fields['tag'].required = False
        self.fields['founded_date'].required = False
        self.fields['description'].required = False
        self.fields['logo'].required = False
        
        # Формат даты
        if 'founded_date' in self.fields:
            self.fields['founded_date'].input_formats = ['%Y-%m-%d']
    
    def clean_slug(self):
        """Автоматическая генерация slug"""
        slug = self.cleaned_data.get('slug')
        name = self.cleaned_data.get('name')
        
        # Если slug пустой, генерируем из названия
        if not slug and name:
            slug = slugify(name)
            # Проверяем уникальность
            counter = 1
            original_slug = slug
            while Team.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
        
        return slug
    
    def clean_name(self):
        """Проверка уникальности названия"""
        name = self.cleaned_data.get('name')
        if Team.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Команда с таким названием уже существует')
        return name