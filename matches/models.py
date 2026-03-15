# matches/models.py

from django.db import models
from django.conf import settings
from tournaments.models import Tournament, Stage
from teams.models import Team

class Match(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Запланирован'),
        ('live', 'Идёт'),
        ('finished', 'Завершён'),
        ('postponed', 'Перенесён'),
        ('cancelled', 'Отменён'),
        ('tech_win', 'Техническая победа'),
    ]
    
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, 
                                   related_name='matches')
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, 
                             related_name='matches')
    round_number = models.IntegerField(verbose_name='Номер тура')
    
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, 
                             related_name='home_matches')
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, 
                             related_name='away_matches')
    
    scheduled_time = models.DateTimeField(verbose_name='Время начала')
    actual_start_time = models.DateTimeField(blank=True, null=True)
    actual_end_time = models.DateTimeField(blank=True, null=True)
    
    score_team1 = models.IntegerField(default=0)
    score_team2 = models.IntegerField(default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
                             default='scheduled')
    
    protocol = models.FileField(upload_to='match_protocols/', blank=True, null=True)
    stream_url = models.URLField(blank=True, verbose_name='Ссылка на трансляцию')
    
    confirmed_by_team1 = models.BooleanField(default=False)
    confirmed_by_team2 = models.BooleanField(default=False)
    
    notes = models.TextField(blank=True, verbose_name='Примечания')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Матч'
        verbose_name_plural = 'Матчи'
        ordering = ['scheduled_time']
    
    def __str__(self):
        return f"{self.team1.name} vs {self.team2.name} - Тур {self.round_number}"

class MatchStatistics(models.Model):
    match = models.OneToOneField(Match, on_delete=models.CASCADE, 
                                 related_name='statistics')
    team1_possession = models.IntegerField(default=0, verbose_name='Владение мячом')
    team2_possession = models.IntegerField(default=0)
    team1_shots = models.IntegerField(default=0, verbose_name='Удары')
    team2_shots = models.IntegerField(default=0)
    team1_saves = models.IntegerField(default=0, verbose_name='Сейвы')
    team2_saves = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'Статистика матча'
        verbose_name_plural = 'Статистика матчей'

class Goal(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, 
                             related_name='goals')
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    minute = models.IntegerField(verbose_name='Минута')
    is_own_goal = models.BooleanField(default=False)
    assist_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                  blank=True, null=True, related_name='assists')
    
    class Meta:
        verbose_name = 'Гол'
        verbose_name_plural = 'Голы'
        ordering = ['minute']

class PlayerMatchStats(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, 
                             related_name='player_stats')
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    saves = models.IntegerField(default=0)
    shots = models.IntegerField(default=0)
    passes = models.IntegerField(default=0)
    possession_time = models.IntegerField(default=0, verbose_name='Владение (сек)')
    
    class Meta:
        verbose_name = 'Статистика игрока в матче'
        verbose_name_plural = 'Статистика игроков в матчах'
        unique_together = ['match', 'player']
