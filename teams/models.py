# teams/models.py - ПОЛНАЯ ВЕРСИЯ

from django.db import models
from django.conf import settings
from django.utils import timezone

class Team(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    tag = models.CharField(max_length=5, verbose_name='Тег', blank=True, default='')
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to='team_logos/', blank=True, null=True)
    captain = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='captained_teams'
    )
    founded_date = models.DateField(verbose_name='Дата основания', null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Команда'
        verbose_name_plural = 'Команды'
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        """Переопределяем save для автоматического добавления капитана в состав"""
        is_new = self.pk is None
        old_captain = None
        
        # Если команда уже существует, сохраняем старого капитана
        if not is_new:
            try:
                old_team = Team.objects.get(pk=self.pk)
                old_captain = old_team.captain
            except Team.DoesNotExist:
                pass
        
        # Сохраняем команду
        super().save(*args, **kwargs)
        
        # Если это новая команда или сменился капитан
        if self.captain and (is_new or old_captain != self.captain):
            # Проверяем, не является ли капитан уже членом команды
            member_exists = TeamMember.objects.filter(
                team=self,
                player=self.captain,
                is_active=True
            ).exists()
            
            # Если капитана нет в составе - добавляем
            if not member_exists:
                TeamMember.objects.create(
                    team=self,
                    player=self.captain,
                    role='captain',
                    joined_date=timezone.now().date(),
                    is_active=True
                )
            else:
                # Если есть - обновляем роль на captain
                TeamMember.objects.filter(
                    team=self,
                    player=self.captain,
                    is_active=True
                ).update(role='captain')
    
    def get_active_members(self):
        """Получить всех активных участников"""
        return self.members.filter(is_active=True).select_related('player').order_by('-role', 'joined_date')
    
    def get_members_count(self):
        """Получить количество активных участников"""
        return self.members.filter(is_active=True).count()
    
    def __str__(self):
        return self.name


class TeamMember(models.Model):
    ROLE_CHOICES = [
        ('player', 'Игрок'),
        ('captain', 'Капитан'),
        ('manager', 'Менеджер'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='player')
    jersey_number = models.IntegerField(null=True, blank=True, verbose_name='Номер')
    joined_date = models.DateField()
    left_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Состав команды'
        verbose_name_plural = 'Составы команд'
        unique_together = ['team', 'player', 'joined_date']
    
    def __str__(self):
        return f"{self.player.username} - {self.team.name}"