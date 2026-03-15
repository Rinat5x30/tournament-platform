# tournaments/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from .models import Tournament, Season, Stage
from matches.models import Match
from teams.models import Team
from ratings.models import PlayerRating, TeamRating
from accounts.models import User


def is_admin(user):
    """Проверка прав администратора"""
    return user.is_authenticated and (
        user.is_staff or 
        user.is_superuser or 
        getattr(user, 'role', None) in ['admin', 'moderator']
    )


def index(request):
    """Главная страница"""
    active_season = Season.objects.filter(is_active=True).first()
    upcoming_tournaments = Tournament.objects.filter(
        status__in=['upcoming', 'registration', 'ongoing']
    )[:6]
    latest_matches = Match.objects.filter(
        status='finished'
    ).order_by('-actual_end_time')[:10]
    
    context = {
        'active_season': active_season,
        'upcoming_tournaments': upcoming_tournaments,
        'latest_matches': latest_matches,
    }
    return render(request, 'index.html', context)


def tournament_list(request):
    """Список всех турниров"""
    season_id = request.GET.get('season')
    status = request.GET.get('status')
    
    tournaments = Tournament.objects.all()
    
    if season_id:
        tournaments = tournaments.filter(season_id=season_id)
    if status:
        tournaments = tournaments.filter(status=status)
    
    seasons = Season.objects.all()
    
    context = {
        'tournaments': tournaments,
        'seasons': seasons,
        'selected_season': season_id,
        'selected_status': status,
    }
    return render(request, 'tournaments/tournament_list.html', context)


def tournament_detail(request, slug):
    """Детальная страница турнира"""
    tournament = get_object_or_404(Tournament, slug=slug)
    stages = tournament.stages.all()
    participants = tournament.participants.select_related('team').all()
    
    # Получаем матчи турнира
    matches = Match.objects.filter(tournament=tournament).select_related(
        'team1', 'team2', 'stage'
    ).order_by('scheduled_time')
    
    context = {
        'tournament': tournament,
        'stages': stages,
        'participants': participants,
        'matches': matches,
    }
    return render(request, 'tournaments/tournament_detail.html', context)


def tournament_table(request, slug, stage_id=None):
    """Турнирная таблица"""
    tournament = get_object_or_404(Tournament, slug=slug)
    
    if stage_id:
        stage = get_object_or_404(Stage, id=stage_id, tournament=tournament)
    else:
        stage = tournament.stages.first()
    
    # Получаем все матчи стадии
    matches = Match.objects.filter(
        stage=stage, 
        status='finished'
    ).select_related('team1', 'team2')
    
    # Формируем таблицу
    table_data = {}
    for participant in tournament.participants.all():
        team = participant.team
        table_data[team.id] = {
            'team': team,
            'matches': 0,
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'goals_for': 0,
            'goals_against': 0,
            'goal_diff': 0,
            'points': 0,
        }
    
    # Подсчитываем статистику
    for match in matches:
        # Команда 1
        data1 = table_data[match.team1.id]
        data1['matches'] += 1
        data1['goals_for'] += match.score_team1
        data1['goals_against'] += match.score_team2
        
        # Команда 2
        data2 = table_data[match.team2.id]
        data2['matches'] += 1
        data2['goals_for'] += match.score_team2
        data2['goals_against'] += match.score_team1
        
        # Определяем победителя
        if match.score_team1 > match.score_team2:
            data1['wins'] += 1
            data1['points'] += 3
            data2['losses'] += 1
        elif match.score_team1 < match.score_team2:
            data2['wins'] += 1
            data2['points'] += 3
            data1['losses'] += 1
        else:
            data1['draws'] += 1
            data2['draws'] += 1
            data1['points'] += 1
            data2['points'] += 1
    
    # Вычисляем разницу мячей
    for data in table_data.values():
        data['goal_diff'] = data['goals_for'] - data['goals_against']
    
    # Сортируем таблицу
    table = sorted(
        table_data.values(),
        key=lambda x: (x['points'], x['goal_diff'], x['goals_for']),
        reverse=True
    )
    
    # Добавляем позиции
    for i, row in enumerate(table, 1):
        row['position'] = i
    
    # Получаем зоны таблицы
    zones = stage.zones.all() if stage else []
    
    context = {
        'tournament': tournament,
        'stage': stage,
        'stages': tournament.stages.all(),
        'table': table,
        'zones': zones,
    }
    return render(request, 'tournaments/tournament_table.html', context)


def tournament_schedule(request, slug):
    """Расписание турнира"""
    tournament = get_object_or_404(Tournament, slug=slug)
    
    # Группируем матчи по турам
    matches_by_round = {}
    matches = Match.objects.filter(tournament=tournament).select_related(
        'team1', 'team2', 'stage'
    ).order_by('round_number', 'scheduled_time')
    
    for match in matches:
        round_key = f"Тур {match.round_number}"
        if round_key not in matches_by_round:
            matches_by_round[round_key] = []
        matches_by_round[round_key].append(match)
    
    context = {
        'tournament': tournament,
        'matches_by_round': matches_by_round,
    }
    return render(request, 'tournaments/tournament_schedule.html', context)


def tournament_bracket(request, slug, stage_id=None):
    """Сетка плей-офф"""
    tournament = get_object_or_404(Tournament, slug=slug)
    
    if stage_id:
        stage = get_object_or_404(Stage, id=stage_id, tournament=tournament)
    else:
        stage = tournament.stages.filter(
            stage_type__in=['single_elimination', 'double_elimination']
        ).first()
    
    if not stage:
        return render(request, 'tournaments/tournament_bracket.html', {
            'tournament': tournament,
            'error': 'Нет стадии плей-офф'
        })
    
    matches = Match.objects.filter(stage=stage).select_related(
        'team1', 'team2'
    ).order_by('round_number')
    
    # Группируем по раундам
    rounds = {}
    for match in matches:
        if match.round_number not in rounds:
            rounds[match.round_number] = []
        rounds[match.round_number].append(match)
    
    context = {
        'tournament': tournament,
        'stage': stage,
        'rounds': rounds,
    }
    return render(request, 'tournaments/tournament_bracket.html', context)


def tournament_archive(request):
    """Архив завершенных турниров"""
    tournaments = Tournament.objects.filter(
        status='finished'
    ).select_related('season').order_by('-end_date')
    
    # Фильтры
    season_id = request.GET.get('season')
    year = request.GET.get('year')
    
    if season_id:
        tournaments = tournaments.filter(season_id=season_id)
    
    if year:
        tournaments = tournaments.filter(start_date__year=year)
    
    # Получаем статистику
    tournaments = tournaments.annotate(
        teams_count=Count('participants', distinct=True),
        matches_count=Count('matches', distinct=True)
    )
    
    # Получаем доступные сезоны и года
    seasons = Season.objects.all()
    years = Tournament.objects.dates('start_date', 'year', order='DESC')
    
    context = {
        'tournaments': tournaments,
        'seasons': seasons,
        'years': years,
        'selected_season': season_id,
        'selected_year': year,
    }
    return render(request, 'tournaments/archive.html', context)


def player_career(request, username):
    """Карьера игрока по сезонам"""
    player = get_object_or_404(User, username=username)
    
    # Получаем статистику по сезонам
    from matches.models import PlayerMatchStats
    from tournaments.models import TournamentAward
    
    career_by_season = []
    seasons = Season.objects.all().order_by('-start_date')
    
    for season in seasons:
        # Рейтинг в сезоне
        try:
            rating = PlayerRating.objects.get(player=player, season=season)
        except PlayerRating.DoesNotExist:
            rating = None
        
        # Статистика матчей
        player_stats = PlayerMatchStats.objects.filter(
            player=player,
            match__tournament__season=season
        )
        
        total_matches = player_stats.count()
        total_goals = player_stats.aggregate(Sum('goals'))['goals__sum'] or 0
        total_assists = player_stats.aggregate(Sum('assists'))['assists__sum'] or 0
        
        # Награды в сезоне
        awards = TournamentAward.objects.filter(
            player=player,
            tournament__season=season
        )
        
        if total_matches > 0 or awards.exists():
            career_by_season.append({
                'season': season,
                'rating': rating,
                'matches': total_matches,
                'goals': total_goals,
                'assists': total_assists,
                'awards': awards
            })
    
    context = {
        'player': player,
        'career_by_season': career_by_season,
    }
    return render(request, 'tournaments/player_career.html', context)


def team_history(request, slug):
    """История команды по сезонам"""
    team = get_object_or_404(Team, slug=slug)
    
    # Получаем статистику по сезонам
    from teams.models import TeamMember
    from tournaments.models import TournamentAward
    
    history_by_season = []
    seasons = Season.objects.all().order_by('-start_date')
    
    for season in seasons:
        # Рейтинг в сезоне
        try:
            rating = TeamRating.objects.get(team=team, season=season)
        except TeamRating.DoesNotExist:
            rating = None
        
        # Статистика матчей
        season_matches = Match.objects.filter(
            Q(team1=team) | Q(team2=team),
            tournament__season=season,
            status='finished'
        )
        
        wins = 0
        draws = 0
        losses = 0
        
        for match in season_matches:
            if (match.team1 == team and match.score_team1 > match.score_team2) or \
               (match.team2 == team and match.score_team2 > match.score_team1):
                wins += 1
            elif match.score_team1 == match.score_team2:
                draws += 1
            else:
                losses += 1
        
        # Награды в сезоне
        awards = TournamentAward.objects.filter(
            team=team,
            tournament__season=season
        )
        
        # Состав в сезоне
        roster = TeamMember.objects.filter(
            team=team,
            joined_date__lte=season.end_date if season.end_date else timezone.now(),
        ).filter(
            Q(left_date__isnull=True) | Q(left_date__gte=season.start_date)
        ).select_related('player')
        
        if season_matches.exists() or awards.exists():
            history_by_season.append({
                'season': season,
                'rating': rating,
                'matches': season_matches.count(),
                'wins': wins,
                'draws': draws,
                'losses': losses,
                'awards': awards,
                'roster': roster
            })
    
    context = {
        'team': team,
        'history_by_season': history_by_season,
    }
    return render(request, 'tournaments/team_history.html', context)


def search(request):
    """Поиск по сайту (турниры, команды, игроки)"""
    query = request.GET.get('q', '').strip()
    
    results = {
        'tournaments': [],
        'teams': [],
        'players': [],
    }
    
    if query and len(query) >= 2:  # Минимум 2 символа для поиска
        # Поиск турниров
        results['tournaments'] = Tournament.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).select_related('season')[:10]
        
        # Поиск команд
        results['teams'] = Team.objects.filter(
            Q(name__icontains=query) | 
            Q(tag__icontains=query) | 
            Q(description__icontains=query)
        ).filter(is_active=True)[:10]
        
        # Поиск игроков
        results['players'] = User.objects.filter(
            Q(username__icontains=query) | 
            Q(discord_username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).filter(role__in=['player', 'captain'])[:10]
    
    # Подсчет результатов
    total_results = (
        len(results['tournaments']) + 
        len(results['teams']) + 
        len(results['players'])
    )
    
    context = {
        'query': query,
        'results': results,
        'total_results': total_results,
    }
    return render(request, 'search.html', context)