# ratings/views.py - ФИНАЛЬНАЯ ВЕРСИЯ

from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import PlayerRating, TeamRating
from tournaments.models import Season


def team_ratings(request):
    """Рейтинг команд"""
    season_id = request.GET.get('season')
    sort = request.GET.get('sort', 'rating_points')
    
    if season_id:
        ratings = TeamRating.objects.filter(season_id=season_id)
    else:
        # Общий рейтинг (без сезона)
        ratings = TeamRating.objects.filter(season__isnull=True)
    
    # Сортировка
    if sort == 'points':
        ratings = ratings.order_by('-points', '-rating_points')
    elif sort == 'wins':
        ratings = ratings.order_by('-wins', '-rating_points')
    elif sort == 'goal_difference':
        ratings = ratings.order_by('-goal_difference', '-rating_points')
    else:  # rating_points
        ratings = ratings.order_by('-rating_points')
    
    ratings = ratings.select_related('team', 'season')
    
    # Преобразуем в список и присваиваем ранги
    ratings_list = list(ratings)
    for index, rating in enumerate(ratings_list, start=1):
        rating.rank = index
    
    seasons = Season.objects.all()
    
    context = {
        'ratings': ratings_list,
        'seasons': seasons,
        'selected_season': season_id,
        'sort': sort,
    }
    return render(request, 'ratings/team_ratings.html', context)


def player_ratings(request):
    """Рейтинг игроков"""
    season_id = request.GET.get('season')
    search = request.GET.get('search', '')
    sort = request.GET.get('sort', 'rating_points')
    
    if season_id:
        ratings = PlayerRating.objects.filter(season_id=season_id)
    else:
        # Общий рейтинг (без сезона)
        ratings = PlayerRating.objects.filter(season__isnull=True)
    
    # Поиск по имени игрока
    if search:
        ratings = ratings.filter(
            Q(player__username__icontains=search) |
            Q(player__discord_username__icontains=search)
        )
    
    # Сортировка
    if sort == 'goals':
        ratings = ratings.order_by('-goals', '-rating_points')
    elif sort == 'assists':
        ratings = ratings.order_by('-assists', '-rating_points')
    elif sort == 'matches_played':
        ratings = ratings.order_by('-matches_played', '-rating_points')
    else:  # rating_points
        ratings = ratings.order_by('-rating_points')
    
    ratings = ratings.select_related('player', 'season')
    
    # Преобразуем в список и присваиваем ранги
    ratings_list = list(ratings)
    for index, rating in enumerate(ratings_list, start=1):
        rating.rank = index
    
    seasons = Season.objects.all()
    
    context = {
        'ratings': ratings_list,
        'seasons': seasons,
        'selected_season': season_id,
        'search': search,
        'sort': sort,
    }
    return render(request, 'ratings/player_ratings.html', context)


def is_admin(user):
    """Проверка прав администратора"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(is_admin)
def recalculate_ratings(request):
    """
    Страница для пересчёта рейтингов.
    Доступна только администраторам.
    """
    from .utils import recalculate_all_ratings, init_missing_ratings
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'init':
            # Только создать недостающие рейтинги
            players_created, teams_created = init_missing_ratings()
            messages.success(
                request, 
                f'✅ Создано: {players_created} рейтингов игроков, {teams_created} рейтингов команд'
            )
        
        elif action == 'recalculate':
            # Полный пересчёт
            recalculate_all_ratings()
            messages.success(request, '✅ Все рейтинги пересчитаны!')
        
        return redirect('ratings:recalculate')
    
    # Статистика
    from accounts.models import User
    from teams.models import Team
    from matches.models import Match
    
    context = {
        'total_players': User.objects.filter(role__in=['player', 'captain']).count(),
        'total_teams': Team.objects.filter(is_active=True).count(),
        'player_ratings_count': PlayerRating.objects.filter(season__isnull=True).count(),
        'team_ratings_count': TeamRating.objects.filter(season__isnull=True).count(),
        'finished_matches': Match.objects.filter(status='finished').count(),
    }
    return render(request, 'ratings/recalculate.html', context)