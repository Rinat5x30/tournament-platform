# accounts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from .models import User
from .forms import UserProfileForm  # ДОБАВЛЕНО
from teams.models import TeamMember
from matches.models import Match, PlayerMatchStats, Goal
from tournaments.models import TournamentAward, Season
from ratings.models import PlayerRating


def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        discord_username = request.POST.get('discord_username', '')
        
        # Валидация
        if not username or not password:
            messages.error(request, 'Заполните все обязательные поля')
            return render(request, 'accounts/signup.html')
        
        if password != password_confirm:
            messages.error(request, 'Пароли не совпадают')
            return render(request, 'accounts/signup.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь с таким именем уже существует')
            return render(request, 'accounts/signup.html')
        
        if email and User.objects.filter(email=email).exists():
            messages.error(request, 'Email уже используется')
            return render(request, 'accounts/signup.html')
        
        # Создаем пользователя
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            discord_username=discord_username,
            role='player'
        )
        
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        messages.success(request, f'Добро пожаловать, {username}!')
        return redirect('tournaments:index')
    
    return render(request, 'accounts/signup.html')


def login_view(request):
    """Вход в систему"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'Добро пожаловать, {user.username}!')
            
            next_url = request.GET.get('next', 'tournaments:index')
            return redirect(next_url)
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    
    return render(request, 'accounts/login.html')


def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('tournaments:index')


def profile(request, username):
    """Профиль пользователя с полной статистикой"""
    from tournaments.models import Sanction
    from django.utils import timezone
    from ratings.models import PlayerRating
    
    user = get_object_or_404(User, username=username)
    
    # Текущая команда
    current_team = TeamMember.objects.filter(
        player=user, 
        is_active=True
    ).select_related('team').first()
    
    # История команд
    team_history = TeamMember.objects.filter(
        player=user
    ).select_related('team').order_by('-joined_date')
    
    # Общая статистика
    player_stats = PlayerMatchStats.objects.filter(player=user)
    
    total_matches = player_stats.count()
    total_goals = player_stats.aggregate(Sum('goals'))['goals__sum'] or 0
    total_assists = player_stats.aggregate(Sum('assists'))['assists__sum'] or 0
    total_saves = player_stats.aggregate(Sum('saves'))['saves__sum'] or 0
    total_shots = player_stats.aggregate(Sum('shots'))['shots__sum'] or 0
    
    # Подсчет побед/поражений/ничьих
    matches_played = Match.objects.filter(
        Q(team1__members__player=user, team1__members__is_active=True) | 
        Q(team2__members__player=user, team2__members__is_active=True),
        status='finished'
    ).distinct()
    
    wins = 0
    draws = 0
    losses = 0
    
    for match in matches_played:
        player_team = None
        if match.team1.members.filter(player=user, is_active=True).exists():
            player_team = match.team1
        elif match.team2.members.filter(player=user, is_active=True).exists():
            player_team = match.team2
        
        if player_team:
            if player_team == match.team1:
                if match.score_team1 > match.score_team2:
                    wins += 1
                elif match.score_team1 < match.score_team2:
                    losses += 1
                else:
                    draws += 1
            elif player_team == match.team2:
                if match.score_team2 > match.score_team1:
                    wins += 1
                elif match.score_team2 < match.score_team1:
                    losses += 1
                else:
                    draws += 1
    
    # Последние 10 матчей с деталями
    recent_matches_data = []
    recent_matches = Match.objects.filter(
        Q(team1__members__player=user, team1__members__is_active=True) | 
        Q(team2__members__player=user, team2__members__is_active=True),
        status='finished'
    ).select_related('team1', 'team2', 'tournament').distinct().order_by('-scheduled_time')[:10]
    
    for match in recent_matches:
        try:
            match_stats = PlayerMatchStats.objects.get(match=match, player=user)
        except PlayerMatchStats.DoesNotExist:
            match_stats = None
        
        player_team = None
        opponent_team = None
        result = None
        
        if match.team1.members.filter(player=user, is_active=True).exists():
            player_team = match.team1
            opponent_team = match.team2
            if match.score_team1 > match.score_team2:
                result = 'win'
            elif match.score_team1 < match.score_team2:
                result = 'loss'
            else:
                result = 'draw'
        elif match.team2.members.filter(player=user, is_active=True).exists():
            player_team = match.team2
            opponent_team = match.team1
            if match.score_team2 > match.score_team1:
                result = 'win'
            elif match.score_team2 < match.score_team1:
                result = 'loss'
            else:
                result = 'draw'
        
        recent_matches_data.append({
            'match': match,
            'player_team': player_team,
            'opponent_team': opponent_team,
            'result': result,
            'stats': match_stats
        })
    
    # Достижения и награды
    awards = TournamentAward.objects.filter(
        player=user
    ).select_related('tournament').order_by('-awarded_at')
    
    # Рейтинг игрока
    player_rating = None
    active_season = Season.objects.filter(is_active=True).first()
    
    if active_season:
        try:
            player_rating = PlayerRating.objects.get(player=user, season=active_season)
        except PlayerRating.DoesNotExist:
            pass
    
    if not player_rating:
        try:
            player_rating = PlayerRating.objects.get(player=user, season__isnull=True)
        except PlayerRating.DoesNotExist:
            pass
    
    if not player_rating:
        player_rating = PlayerRating.objects.filter(player=user).order_by('-season__start_date').first()
    
    # Статистика по сезонам
    career_by_season = []
    seasons = Season.objects.all().order_by('-start_date')[:5]
    
    for season in seasons:
        season_stats = PlayerMatchStats.objects.filter(
            player=user,
            match__tournament__season=season
        )
        
        if season_stats.exists():
            season_matches = season_stats.count()
            season_goals = season_stats.aggregate(Sum('goals'))['goals__sum'] or 0
            season_assists = season_stats.aggregate(Sum('assists'))['assists__sum'] or 0
            
            try:
                season_rating = PlayerRating.objects.get(player=user, season=season)
            except PlayerRating.DoesNotExist:
                season_rating = None
            
            season_awards = TournamentAward.objects.filter(
                player=user,
                tournament__season=season
            )
            
            career_by_season.append({
                'season': season,
                'matches': season_matches,
                'goals': season_goals,
                'assists': season_assists,
                'rating': season_rating,
                'awards': season_awards
            })
    
    is_own_profile = request.user.is_authenticated and request.user == user
    
    active_sanctions = []
    if is_own_profile:
        active_sanctions = Sanction.objects.filter(
            player=user,
            status='active'
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gte=timezone.now())
        ).select_related('tournament', 'issued_by').order_by('-issued_at')
    
    context = {
        'profile_user': user,
        'is_own_profile': is_own_profile,
        'current_team': current_team,
        'team_history': team_history,
        'total_matches': total_matches,
        'wins': wins,
        'draws': draws,
        'losses': losses,
        'total_goals': total_goals,
        'total_assists': total_assists,
        'total_saves': total_saves,
        'total_shots': total_shots,
        'recent_matches': recent_matches_data,
        'awards': awards,
        'player_rating': player_rating,
        'career_by_season': career_by_season,
        'active_sanctions': active_sanctions,
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit(request):
    """Редактирование профиля - ИСПРАВЛЕНО"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлён')
            return redirect('accounts:profile', username=request.user.username)
    else:
        form = UserProfileForm(instance=request.user)
    
    context = {
        'form': form,
        'user': request.user
    }
    return render(request, 'accounts/profile_edit.html', context)


@login_required
def change_password(request):
    """Смена пароля"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'Неверный текущий пароль')
            return render(request, 'accounts/change_password.html')
        
        if new_password != confirm_password:
            messages.error(request, 'Новые пароли не совпадают')
            return render(request, 'accounts/change_password.html')
        
        if len(new_password) < 6:
            messages.error(request, 'Пароль должен содержать минимум 6 символов')
            return render(request, 'accounts/change_password.html')
        
        request.user.set_password(new_password)
        request.user.save()
        
        user = authenticate(username=request.user.username, password=new_password)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        messages.success(request, 'Пароль успешно изменён')
        return redirect('accounts:profile', username=request.user.username)
    
    return render(request, 'accounts/change_password.html')