# tournaments/models.py

from django.db import models
from django.conf import settings


class Season(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название сезона')
    number = models.IntegerField(verbose_name='Номер сезона', default=1)
    start_date = models.DateField(verbose_name='Дата начала')
    end_date = models.DateField(blank=True, null=True, verbose_name='Дата окончания')
    is_active = models.BooleanField(default=False, verbose_name='Активный')
    
    class Meta:
        verbose_name = 'Сезон'
        verbose_name_plural = 'Сезоны'
        ordering = ['-start_date']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.number:
            last_season = Season.objects.order_by('-number').first()
            self.number = (last_season.number + 1) if last_season else 1
        
        if self.is_active:
            Season.objects.exclude(id=self.id).update(is_active=False)
        
        super().save(*args, **kwargs)


class Tournament(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Предстоящий'),
        ('registration', 'Регистрация'),
        ('ongoing', 'Идёт'),
        ('finished', 'Завершён'),
        ('cancelled', 'Отменён'),
    ]
    
    STAGE_TYPE_CHOICES = [
        ('round_robin', 'Круговая система'),
        ('swiss', 'Швейцарская система'),
        ('single_elimination', 'Single Elimination'),
        ('double_elimination', 'Double Elimination'),
        ('group_stage', 'Групповая стадия'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(unique=True)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='tournaments')
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='tournament_logos/', blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    stage_type = models.CharField(max_length=30, choices=STAGE_TYPE_CHOICES, default='round_robin')
    
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    registration_start = models.DateField(blank=True, null=True)
    registration_end = models.DateField(blank=True, null=True)
    
    max_teams = models.IntegerField(default=16)
    stream_url = models.URLField(blank=True, verbose_name='Ссылка на трансляцию')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Турнир'
        verbose_name_plural = 'Турниры'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} ({self.season})"


class TournamentTeam(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='participants')
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='tournament_teams')
    seed = models.IntegerField(verbose_name='Посев', blank=True, null=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Участник турнира'
        verbose_name_plural = 'Участники турнира'
        unique_together = ['tournament', 'team']
    
    def __str__(self):
        return f"{self.team.name} - {self.tournament.name}"


class Stage(models.Model):
    STAGE_TYPE_CHOICES = [
        ('round_robin', 'Круговая система'),
        ('swiss', 'Швейцарская система'),
        ('swiss_dutch', 'Швейцарская система (Голландская)'),
        ('swiss_accelerated', 'Швейцарская система (Ускоренная)'),
        ('single_elimination', 'Single Elimination'),
        ('double_elimination', 'Double Elimination'),
        ('group_stage', 'Групповой этап'),
    ]
    
    TIEBREAKER_CHOICES = [
        ('head_to_head', 'Личные встречи'),
        ('goal_difference', 'Разница мячей'),
        ('goals_scored', 'Забитые мячи'),
        ('goals_conceded', 'Пропущенные мячи'),
        ('wins', 'Количество побед'),
        ('buchholz', 'Бухгольц'),
        ('sonneborn_berger', 'Зоннеборн-Бергер'),
        ('random', 'Жребий'),
    ]
    
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='stages')
    name = models.CharField(max_length=100, verbose_name='Название стадии')
    order = models.IntegerField(default=1, verbose_name='Порядок')
    stage_type = models.CharField(max_length=30, choices=STAGE_TYPE_CHOICES, default='round_robin')
    
    swiss_rounds = models.IntegerField(null=True, blank=True, verbose_name='Количество раундов')
    use_accelerated_pairing = models.BooleanField(default=False, verbose_name='Ускоренные пары')
    
    groups_count = models.IntegerField(null=True, blank=True, verbose_name='Количество групп')
    teams_per_group = models.IntegerField(null=True, blank=True, verbose_name='Команд в группе')
    
    tiebreaker_1 = models.CharField(max_length=30, choices=TIEBREAKER_CHOICES, default='head_to_head')
    tiebreaker_2 = models.CharField(max_length=30, choices=TIEBREAKER_CHOICES, default='goal_difference')
    tiebreaker_3 = models.CharField(max_length=30, choices=TIEBREAKER_CHOICES, default='goals_scored')
    
    advance_count = models.IntegerField(null=True, blank=True, verbose_name='Проходят команд')
    next_stage = models.ForeignKey('tournaments.Stage', on_delete=models.SET_NULL, null=True, blank=True, related_name='previous_stages')
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Стадия турнира'
        verbose_name_plural = 'Стадии турнира'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.tournament.name} - {self.name}"


class TableZone(models.Model):
    ZONE_TYPE_CHOICES = [
        ('promotion', 'Выход в плей-офф'),
        ('playoff', 'Зона плей-офф'),
        ('tiebreaker', 'Стыковые матчи'),
        ('relegation', 'Зона вылета'),
        ('safe', 'Безопасная зона'),
    ]
    
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name='zones')
    name = models.CharField(max_length=100, verbose_name='Название зоны')
    zone_type = models.CharField(max_length=20, choices=ZONE_TYPE_CHOICES)
    start_position = models.IntegerField(verbose_name='Начальная позиция')
    end_position = models.IntegerField(verbose_name='Конечная позиция')
    color = models.CharField(max_length=7, default='#4CAF50', verbose_name='Цвет')
    description = models.TextField(blank=True, verbose_name='Описание')
    
    class Meta:
        verbose_name = 'Зона таблицы'
        verbose_name_plural = 'Зоны таблицы'
        ordering = ['start_position']
    
    def __str__(self):
        return f"{self.name} ({self.start_position}-{self.end_position})"


class TimeSlot(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='time_slots')
    day_of_week = models.IntegerField(choices=[
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    ])
    start_time = models.TimeField(verbose_name='Время начала')
    duration_minutes = models.IntegerField(default=30, verbose_name='Длительность (минут)')
    max_matches = models.IntegerField(default=1, verbose_name='Максимум матчей')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Временной слот'
        verbose_name_plural = 'Временные слоты'
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.start_time}"


class Sanction(models.Model):
    SANCTION_TYPE_CHOICES = [
        ('warning', 'Предупреждение'),
        ('technical_loss', 'Техническое поражение'),
        ('disqualification', 'Дисквалификация'),
        ('points_deduction', 'Снятие очков'),
        ('ban', 'Бан'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('expired', 'Истекла'),
        ('appealed', 'Обжалуется'),
        ('cancelled', 'Отменена'),
    ]
    
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='sanctions')
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, null=True, blank=True)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    
    sanction_type = models.CharField(max_length=30, choices=SANCTION_TYPE_CHOICES)
    reason = models.TextField(verbose_name='Причина')
    points_deducted = models.IntegerField(default=0, verbose_name='Снято очков')
    ban_duration_days = models.IntegerField(null=True, blank=True, verbose_name='Длительность бана (дней)')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='issued_sanctions')
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Санкция'
        verbose_name_plural = 'Санкции'
        ordering = ['-issued_at']
    
    def __str__(self):
        target = self.team.name if self.team else self.player.username
        return f"{self.get_sanction_type_display()} - {target}"


class Appeal(models.Model):
    """Апелляция на решение или санкцию"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает рассмотрения'),
        ('in_review', 'На рассмотрении'),
        ('approved', 'Одобрена'),
        ('rejected', 'Отклонена'),
    ]
    
    sanction = models.ForeignKey(
        Sanction, 
        on_delete=models.CASCADE, 
        related_name='appeals', 
        null=True, 
        blank=True
    )
    match = models.ForeignKey(
        'matches.Match', 
        on_delete=models.CASCADE, 
        related_name='appeals', 
        null=True, 
        blank=True
    )
    
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='submitted_appeals'
    )
    reason = models.TextField(verbose_name='Причина апелляции')
    
    # ОБНОВЛЕНО: Разделены текстовые доказательства и файлы
    evidence_text = models.TextField(
        blank=True,
        default='',
        verbose_name='Доказательства (текст/ссылка)',
        help_text='Введите текстовое описание или ссылку на доказательства'
    )
    evidence_file = models.FileField(
        upload_to='appeals/', 
        blank=True, 
        null=True, 
        verbose_name='Файл доказательства',
        help_text='Загрузите файл (скриншот, видео и т.д.)'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_appeals'
    )
    review_notes = models.TextField(blank=True, verbose_name='Примечания')
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Апелляция'
        verbose_name_plural = 'Апелляции'
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"Апелляция от {self.submitted_by.username} - {self.get_status_display()}"


class MatchConfirmation(models.Model):
    match = models.ForeignKey('matches.Match', on_delete=models.CASCADE, related_name='confirmations')
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE)
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    confirmed_at = models.DateTimeField(auto_now_add=True)
    score_team1 = models.IntegerField()
    score_team2 = models.IntegerField()
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Подтверждение результата'
        verbose_name_plural = 'Подтверждения результатов'
        unique_together = ['match', 'team']
    
    def __str__(self):
        return f"{self.team.name} подтвердила {self.match}"


class TournamentAward(models.Model):
    AWARD_TYPE_CHOICES = [
        ('champion', 'Чемпион'),
        ('runner_up', 'Серебряный призер'),
        ('third_place', 'Бронзовый призер'),
        ('mvp', 'MVP турнира'),
        ('top_scorer', 'Лучший бомбардир'),
        ('best_goalkeeper', 'Лучший вратарь'),
        ('fair_play', 'Fair Play'),
    ]
    
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='tournament_awards')
    award_type = models.CharField(max_length=30, choices=AWARD_TYPE_CHOICES)
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, null=True, blank=True, related_name='tournament_awards')
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='tournament_awards')
    
    value = models.IntegerField(null=True, blank=True, verbose_name='Значение (голы, очки и т.д.)')
    description = models.TextField(blank=True)
    awarded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Награда турнира'
        verbose_name_plural = 'Награды турниров'
        ordering = ['-awarded_at']
    
    def __str__(self):
        recipient = self.team.name if self.team else self.player.username
        return f"{self.get_award_type_display()} - {recipient}"