# accounts/models.py

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CustomUserManager(UserManager):
    """Кастомный менеджер для автоматической установки ролей"""
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """
        Создает суперпользователя с автоматической ролью admin
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')  # Автоматически устанавливаем роль admin
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self._create_user(username, email, password, **extra_fields)
    
    def create_user(self, username, email=None, password=None, **extra_fields):
        """
        Создает обычного пользователя с ролью player по умолчанию
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('role', 'player')  # По умолчанию роль player
        
        return self._create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('player', 'Игрок'),
        ('captain', 'Капитан'),
        ('moderator', 'Модератор'),
        ('admin', 'Администратор'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='player')
    discord_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    discord_username = models.CharField(max_length=100, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    
    # Подключаем кастомный менеджер
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return self.username
    
    def save(self, *args, **kwargs):
        """
        Автоматически синхронизируем роль с правами доступа
        """
        # Если пользователь суперадмин, но роль не admin - исправляем
        if self.is_superuser and self.role != 'admin':
            self.role = 'admin'
        
        # Если пользователь staff, но роль player - делаем moderator
        elif self.is_staff and not self.is_superuser and self.role == 'player':
            self.role = 'moderator'
        
        # Если роль admin, автоматически делаем staff и superuser
        elif self.role == 'admin':
            self.is_staff = True
            self.is_superuser = True
        
        # Если роль moderator, делаем staff
        elif self.role == 'moderator':
            self.is_staff = True
        
        super().save(*args, **kwargs)