# ratings/models.py

from django.db import models
from django.conf import settings
from tournaments.models import Season
from teams.models import Team
from tournaments.models import Tournament



class PlayerRating(models.Model):
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                               related_name='ratings')
    season = models.ForeignKey(Season, on_delete=models.CASCADE, 
                               related_name='player_ratings', blank=True, null=True)
    
    # Общая статистика
    matches_played = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)
    
    # Голы и передачи
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    own_goals = models.IntegerField(default=0)
    
    # Дополнительная статистика
    saves = models.IntegerField(default=0)
    shots = models.IntegerField(default=0)
    shot_accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Рейтинг
    rating_points = models.IntegerField(default=1500)
    rank = models.IntegerField(default=0)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Рейтинг игрока'
        verbose_name_plural = 'Рейтинги игроков'
        unique_together = ['player', 'season']
    
    def __str__(self):
        season_str = f" - {self.season}" if self.season else " (Общий)"
        return f"{self.player.username}{season_str}"

class TeamRating(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, 
                            related_name='ratings')
    season = models.ForeignKey(Season, on_delete=models.CASCADE, 
                               related_name='team_ratings', blank=True, null=True)
    
    matches_played = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)
    
    goals_scored = models.IntegerField(default=0)
    goals_conceded = models.IntegerField(default=0)
    goal_difference = models.IntegerField(default=0)
    
    points = models.IntegerField(default=0)
    rating_points = models.IntegerField(default=1500)
    rank = models.IntegerField(default=0)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Рейтинг команды'
        verbose_name_plural = 'Рейтинги команд'
        unique_together = ['team', 'season']
    
    def __str__(self):
        season_str = f" - {self.season}" if self.season else " (Общий)"
        return f"{self.team.name}{season_str}"

class Award(models.Model):
    AWARD_TYPE_CHOICES = [
        ('champion', 'Чемпион'),
        ('runner_up', 'Вице-чемпион'),
        ('third_place', 'Третье место'),
        ('top_scorer', 'Лучший бомбардир'),
        ('best_player', 'Лучший игрок'),
        ('best_goalkeeper', 'Лучший вратарь'),
    ]
    
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, 
                                   related_name='awards')
    award_type = models.CharField(max_length=20, choices=AWARD_TYPE_CHOICES)
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, blank=True, null=True)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                               blank=True, null=True)
    
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Награда'
        verbose_name_plural = 'Награды'
    
    def __str__(self):
        recipient = self.team.name if self.team else self.player.username
        return f"{self.get_award_type_display()} - {recipient}"
