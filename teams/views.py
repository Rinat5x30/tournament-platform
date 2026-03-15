# teams/views.py - ИСПРАВЛЕННАЯ ВЕРСИЯ

from django.db.models import Q, Count, Sum
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.text import slugify
from .models import Team, TeamMember
from matches.models import Match, PlayerMatchStats
from ratings.models import TeamRating, Award
from tournaments.models import Season, Tournament, TournamentTeam, Sanction, Appeal


# ============================================================
# ПУБЛИЧНЫЕ СТРАНИЦЫ (БЕЗ АВТОРИЗАЦИИ)
# ============================================================

def team_list(request):
    """Публичная страница списка всех команд - ИСПРАВЛЕНО"""
    from django.utils.text import slugify
    
    teams = Team.objects.filter(is_active=True).annotate(
        members_count=Count('members', filter=Q(members__is_active=True))
    ).order_by('-members_count', 'name')
    
    # КРИТИЧЕСКИ ВАЖНО: Автоматически генерируем slug для команд без него
    teams_without_slug = teams.filter(Q(slug__isnull=True) | Q(slug=''))
    for team in teams_without_slug:
        slug = slugify(team.name)
        counter = 1
        original_slug = slug
        
        # Проверяем уникальность
        while Team.objects.filter(slug=slug).exclude(pk=team.pk).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        team.slug = slug
        team.save(update_fields=['slug'])
    
    # Перезапрашиваем команды после обновления slug
    teams = Team.objects.filter(is_active=True).annotate(
        members_count=Count('members', filter=Q(members__is_active=True))
    ).order_by('-members_count', 'name')
    
    context = {
        'teams': teams,
    }
    return render(request, 'teams/team_list.html', context)


def team_detail(request, slug):
    """
    Детальная информация о команде - ПУБЛИЧНАЯ СТРАНИЦА
    Доступна всем пользователям (авторизованным и неавторизованным)
    """
    from tournaments.models import TournamentAward
    
    team = get_object_or_404(Team, slug=slug)
    
    # Текущие участники
    current_members = TeamMember.objects.filter(
        team=team,
        is_active=True
    ).select_related('player').order_by('-role', 'player__username')
    
    # Прошлые участники
    past_members = TeamMember.objects.filter(
        team=team,
        is_active=False
    ).select_related('player').order_by('-left_date')
    
    # Проверяем, является ли капитан членом команды
    captain_is_member = False
    if team.captain:
        captain_is_member = current_members.filter(player=team.captain).exists()
    
    # Правильный подсчет участников
    total_members = current_members.count()
    if team.captain and not captain_is_member:
        total_members += 1
    
    # Статистика команды
    matches = Match.objects.filter(
        Q(team1=team) | Q(team2=team),
        status='finished'
    )
    
    wins = 0
    draws = 0
    losses = 0
    goals_scored = 0
    goals_conceded = 0
    
    for match in matches:
        if match.team1 == team:
            goals_scored += match.score_team1 or 0
            goals_conceded += match.score_team2 or 0
            if match.score_team1 > match.score_team2:
                wins += 1
            elif match.score_team1 < match.score_team2:
                losses += 1
            else:
                draws += 1
        else:
            goals_scored += match.score_team2 or 0
            goals_conceded += match.score_team1 or 0
            if match.score_team2 > match.score_team1:
                wins += 1
            elif match.score_team2 < match.score_team1:
                losses += 1
            else:
                draws += 1
    
    # Последние матчи
    recent_matches = matches.order_by('-scheduled_time')[:5]
    
    # Предстоящие матчи
    upcoming_matches = Match.objects.filter(
        Q(team1=team) | Q(team2=team),
        status='scheduled'
    ).order_by('scheduled_time')[:5]
    
    # Статистика игроков команды
    player_stats = []
    for member in current_members:
        stats = PlayerMatchStats.objects.filter(
            player=member.player,
            team=team
        ).aggregate(
            total_goals=Sum('goals'),
            total_assists=Sum('assists'),
            total_matches=Count('match', distinct=True)
        )
        
        player_stats.append({
            'member': member,
            'goals': stats['total_goals'] or 0,
            'assists': stats['total_assists'] or 0,
            'matches': stats['total_matches'] or 0
        })
    
    player_stats.sort(key=lambda x: x['goals'], reverse=True)
    
    # Рейтинг команды
    team_rating = None
    active_season = Season.objects.filter(is_active=True).first()
    if active_season:
        try:
            team_rating = TeamRating.objects.get(team=team, season=active_season)
        except TeamRating.DoesNotExist:
            pass
    
    if not team_rating:
        try:
            team_rating = TeamRating.objects.get(team=team, season__isnull=True)
        except TeamRating.DoesNotExist:
            pass
    
    # Награды команды
    awards = TournamentAward.objects.filter(
        team=team
    ).select_related('tournament').order_by('-awarded_at')
    
    # Проверяем права доступа (ТОЛЬКО если пользователь авторизован)
    is_captain = False
    is_member = False
    
    if request.user.is_authenticated:
        is_captain = team.captain == request.user
        is_member = current_members.filter(player=request.user).exists()
    
    context = {
        'team': team,
        'members': current_members,
        'current_members': current_members,
        'past_members': past_members,
        'total_members': total_members,
        'captain_is_member': captain_is_member,
        'stats': {
            'total_members': total_members,
            'matches_played': matches.count(),
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'goals_scored': goals_scored,
            'goals_conceded': goals_conceded,
            'goal_difference': goals_scored - goals_conceded,
            'tournaments': TournamentTeam.objects.filter(team=team).count(),
        },
        'recent_matches': recent_matches,
        'upcoming_matches': upcoming_matches,
        'player_stats': player_stats,
        'team_rating': team_rating,
        'awards': awards,
        'is_captain': is_captain,
        'is_member': is_member,
        'is_admin': request.user.is_staff if request.user.is_authenticated else False,
    }
    
    return render(request, 'teams/team_detail.html', context)


# ============================================================
# СТРАНИЦЫ С АВТОРИЗАЦИЕЙ
# ============================================================

@login_required
def team_create(request):
    """Создание команды - ТОЛЬКО для игроков и капитанов"""
    
    # Проверка роли
    if request.user.role not in ['player', 'captain']:
        messages.error(
            request, 
            'Только игроки и капитаны могут создавать команды. '
            'Администраторы могут создавать команды через админ-панель.'
        )
        if request.user.is_staff or request.user.role in ['admin', 'moderator']:
            return redirect('admin_panel:team_create')
        return redirect('teams:team_list')
    
    # Проверяем, не является ли пользователь уже капитаном другой команды
    existing_team = Team.objects.filter(captain=request.user).first()
    if existing_team:
        messages.warning(request, f'Вы уже являетесь капитаном команды {existing_team.name}')
        return redirect('teams:team_detail', slug=existing_team.slug)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        tag = request.POST.get('tag', '')
        slug_field = request.POST.get('slug', '')
        founded_date = request.POST.get('founded_date')
        description = request.POST.get('description', '')
        logo = request.FILES.get('logo')
        
        if not name:
            messages.error(request, 'Укажите название команды')
            return render(request, 'teams/team_create.html')
        
        if Team.objects.filter(name__iexact=name).exists():
            messages.error(request, 'Команда с таким названием уже существует')
            return render(request, 'teams/team_create.html')
        
        if not slug_field:
            slug_field = slugify(name)
            counter = 1
            original_slug = slug_field
            while Team.objects.filter(slug=slug_field).exists():
                slug_field = f"{original_slug}-{counter}"
                counter += 1
        
        team = Team.objects.create(
            name=name,
            tag=tag,
            slug=slug_field,
            captain=request.user,
            founded_date=founded_date if founded_date else timezone.now().date(),
            description=description,
            is_active=True
        )
        
        if logo:
            team.logo = logo
            team.save()
        
        if not TeamMember.objects.filter(team=team, player=request.user).exists():
            TeamMember.objects.create(
                team=team,
                player=request.user,
                role='captain',
                joined_date=team.founded_date,
                is_active=True
            )
        
        messages.success(request, f'Команда "{team.name}" успешно создана!')
        return redirect('teams:team_detail', slug=team.slug)
    
    return render(request, 'teams/team_create.html')


@login_required
def captain_dashboard(request):
    """Панель управления капитана - ПОЛНОСТЬЮ ИСПРАВЛЕНО"""
    
    # Проверяем, является ли пользователь капитаном АКТИВНОЙ команды
    captain_teams = Team.objects.filter(captain=request.user, is_active=True)
    
    if not captain_teams.exists():
        messages.error(request, 'Вы не являетесь капитаном команды')
        return redirect('tournaments:index')
    
    team = captain_teams.first()
    
    # Матчи на подтверждение
    matches_to_confirm = Match.objects.filter(
        Q(team1=team, confirmed_by_team1=False) | 
        Q(team2=team, confirmed_by_team2=False),
        status='finished'
    ).select_related('team1', 'team2', 'tournament').order_by('-scheduled_time')
    
    today = timezone.now().date()
    
    # Открытые турниры (где команда ЕЩЁ НЕ ЗАРЕГИСТРИРОВАНА)
    open_tournaments = Tournament.objects.filter(
        status='registration',
        registration_end__gte=today
    ).exclude(
        participants__team=team
    ).order_by('registration_end')
    
    # КРИТИЧЕСКИ ВАЖНО: Турниры на подтверждение (где is_confirmed=False)
    pending_tournaments = TournamentTeam.objects.filter(
        team=team,
        is_confirmed=False
    ).select_related('tournament').order_by('registered_at')
    
    print(f"DEBUG: Команда {team.name}")
    print(f"DEBUG: Всего записей TournamentTeam: {TournamentTeam.objects.filter(team=team).count()}")
    print(f"DEBUG: Из них не подтверждённых: {pending_tournaments.count()}")
    for pt in pending_tournaments:
        print(f"  - {pt.tournament.name}, подтверждено: {pt.is_confirmed}, зарегистрирован: {pt.registered_at}")
    
    # Активные турниры (где is_confirmed=True)
    active_tournaments = TournamentTeam.objects.filter(
        team=team,
        is_confirmed=True,
        tournament__status__in=['registration', 'ongoing']
    ).select_related('tournament')
    
    # Состав команды
    members = TeamMember.objects.filter(
        team=team
    ).select_related('player').order_by('-is_active', 'joined_date')
    
    # Предстоящие матчи
    upcoming_matches = Match.objects.filter(
        Q(team1=team) | Q(team2=team),
        status='scheduled'
    ).select_related('team1', 'team2', 'tournament').order_by('scheduled_time')[:5]
    
    # Активные санкции
    active_sanctions = Sanction.objects.filter(
        Q(team=team) | Q(player__in=members.values_list('player', flat=True)),
        status='active'
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gte=timezone.now())
    ).select_related('team', 'player', 'tournament', 'issued_by').order_by('-issued_at')
    
    context = {
        'team': team,
        'matches_to_confirm': matches_to_confirm,
        'open_tournaments': open_tournaments,
        'pending_tournaments': pending_tournaments,
        'active_tournaments': active_tournaments,
        'members': members,
        'upcoming_matches': upcoming_matches,
        'active_sanctions': active_sanctions,
    }
    return render(request, 'teams/captain_dashboard.html', context)

@login_required
def confirm_match_result(request, match_id):
    """Подтверждение результата матча капитаном"""
    match = get_object_or_404(Match, id=match_id)
    
    user_team = None
    if match.team1.captain == request.user:
        user_team = match.team1
    elif match.team2.captain == request.user:
        user_team = match.team2
    else:
        messages.error(request, 'У вас нет прав для подтверждения этого матча')
        return redirect('teams:captain_dashboard')
    
    if match.status != 'finished':
        messages.error(request, 'Матч еще не завершен')
        return redirect('teams:captain_dashboard')
    
    if user_team == match.team1 and match.confirmed_by_team1:
        messages.info(request, 'Результат уже подтвержден вашей командой')
        return redirect('teams:captain_dashboard')
    
    if user_team == match.team2 and match.confirmed_by_team2:
        messages.info(request, 'Результат уже подтвержден вашей командой')
        return redirect('teams:captain_dashboard')
    
    if request.method == 'POST':
        from tournaments.models import MatchConfirmation
        
        MatchConfirmation.objects.get_or_create(
            match=match,
            team=user_team,
            defaults={
                'confirmed_by': request.user,
                'score_team1': match.score_team1,
                'score_team2': match.score_team2,
                'notes': request.POST.get('notes', '')
            }
        )
        
        if user_team == match.team1:
            match.confirmed_by_team1 = True
        else:
            match.confirmed_by_team2 = True
        
        match.save()
        
        messages.success(request, 'Результат матча подтвержден')
        return redirect('teams:captain_dashboard')
    
    context = {
        'match': match,
        'user_team': user_team,
    }
    return render(request, 'teams/confirm_match.html', context)


@login_required
def register_for_tournament(request, tournament_id):
    """Регистрация команды на турнир"""
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    captain_teams = Team.objects.filter(captain=request.user, is_active=True)
    if not captain_teams.exists():
        messages.error(request, 'Вы не являетесь капитаном команды')
        return redirect('tournaments:tournament_detail', slug=tournament.slug)
    
    team = captain_teams.first()
    
    if tournament.status != 'registration':
        messages.error(request, 'Регистрация на турнир закрыта')
        return redirect('tournaments:tournament_detail', slug=tournament.slug)
    
    if tournament.registration_end and tournament.registration_end < timezone.now().date():
        messages.error(request, 'Срок регистрации истек')
        return redirect('tournaments:tournament_detail', slug=tournament.slug)
    
    if TournamentTeam.objects.filter(tournament=tournament, team=team).exists():
        messages.warning(request, 'Ваша команда уже зарегистрирована на этот турнир')
        return redirect('tournaments:tournament_detail', slug=tournament.slug)
    
    if tournament.participants.count() >= tournament.max_teams:
        messages.error(request, 'Турнир заполнен')
        return redirect('tournaments:tournament_detail', slug=tournament.slug)
    
    if request.method == 'POST':
        TournamentTeam.objects.create(
            tournament=tournament,
            team=team,
            is_confirmed=False
        )
        
        messages.success(request, f'Команда {team.name} зарегистрирована на турнир {tournament.name}')
        return redirect('teams:captain_dashboard')
    
    context = {
        'tournament': tournament,
        'team': team,
    }
    return render(request, 'teams/register_tournament.html', context)


@login_required
def withdraw_from_tournament(request, tournament_id):
    """Отмена регистрации на турнир"""
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    captain_teams = Team.objects.filter(captain=request.user, is_active=True)
    if not captain_teams.exists():
        messages.error(request, 'У вас нет прав')
        return redirect('tournaments:tournament_detail', slug=tournament.slug)
    
    team = captain_teams.first()
    
    if tournament.status not in ['upcoming', 'registration']:
        messages.error(request, 'Невозможно отменить регистрацию - турнир уже начался')
        return redirect('tournaments:tournament_detail', slug=tournament.slug)
    
    if request.method == 'POST':
        participant = TournamentTeam.objects.filter(tournament=tournament, team=team).first()
        if participant:
            participant.delete()
            messages.success(request, 'Регистрация отменена')
        
        return redirect('teams:captain_dashboard')
    
    return redirect('tournaments:tournament_detail', slug=tournament.slug)


@login_required
def confirm_tournament_participation(request, tournament_id):
    """Подтверждение участия команды в турнире"""
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    captain_teams = Team.objects.filter(captain=request.user, is_active=True)
    if not captain_teams.exists():
        messages.error(request, 'Вы не являетесь капитаном команды')
        return redirect('tournaments:tournament_detail', slug=tournament.slug)
    
    team = captain_teams.first()
    
    try:
        participant = TournamentTeam.objects.get(tournament=tournament, team=team)
    except TournamentTeam.DoesNotExist:
        messages.error(request, 'Ваша команда не зарегистрирована на этот турнир')
        return redirect('tournaments:tournament_detail', slug=tournament.slug)
    
    if participant.is_confirmed:
        messages.info(request, 'Участие уже подтверждено')
        return redirect('teams:captain_dashboard')
    
    if request.method == 'POST':
        participant.is_confirmed = True
        participant.save()
        
        messages.success(request, f'Участие команды {team.name} в турнире {tournament.name} подтверждено')
        return redirect('teams:captain_dashboard')
    
    context = {
        'tournament': tournament,
        'team': team,
        'participant': participant,
    }
    return render(request, 'teams/confirm_participation.html', context)


@login_required
def submit_appeal(request, sanction_id):
    """Подача апелляции на санкцию"""
    sanction = get_object_or_404(Sanction, id=sanction_id)
    
    can_appeal = False
    
    if sanction.player:
        if sanction.player == request.user:
            can_appeal = True
    
    if sanction.team:
        if sanction.team.members.filter(player=request.user, is_active=True).exists():
            can_appeal = True
        if sanction.team.captain == request.user:
            can_appeal = True
    
    if not can_appeal:
        messages.error(request, 'Вы не можете подать апелляцию на эту санкцию')
        return redirect('accounts:profile', username=request.user.username)
    
    existing_appeal = Appeal.objects.filter(
        sanction=sanction,
        submitted_by=request.user,
        status__in=['pending', 'in_review']
    ).first()
    
    if existing_appeal:
        messages.warning(request, 'Вы уже подали апелляцию на эту санкцию')
        return redirect('accounts:profile', username=request.user.username)
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        evidence_text = request.POST.get('evidence_text', '')
        evidence_file = request.FILES.get('evidence_file')
        
        if not reason:
            messages.error(request, 'Укажите причину апелляции')
            return render(request, 'teams/submit_appeal.html', {'sanction': sanction})
        
        appeal = Appeal.objects.create(
            submitted_by=request.user,
            sanction=sanction,
            reason=reason,
            evidence_text=evidence_text,
            evidence_file=evidence_file,
            status='pending'
        )
        
        sanction.status = 'appealed'
        sanction.save()
        
        messages.success(request, 'Апелляция успешно подана и будет рассмотрена в течение 3-5 дней')
        return redirect('accounts:profile', username=request.user.username)
    
    context = {
        'sanction': sanction
    }
    return render(request, 'teams/submit_appeal.html', context)


@login_required
def view_appeal(request, appeal_id):
    """Просмотр апелляции"""
    appeal = get_object_or_404(Appeal, id=appeal_id)
    
    has_permission = False
    
    if appeal.submitted_by == request.user:
        has_permission = True
    
    if appeal.sanction.team and appeal.sanction.team.captain == request.user:
        has_permission = True
    
    if appeal.sanction.player:
        player_team = TeamMember.objects.filter(
            player=appeal.sanction.player,
            is_active=True
        ).select_related('team').first()
        
        if player_team and player_team.team.captain == request.user:
            has_permission = True
    
    if not has_permission:
        messages.error(request, 'У вас нет доступа к этой апелляции')
        return redirect('teams:captain_dashboard')
    
    context = {
        'appeal': appeal,
    }
    return render(request, 'teams/view_appeal.html', context)