
# # admin_panel/views.py - ИСПРАВЛЕННЫЕ ФУНКЦИИ

# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required, user_passes_test
# from django.contrib import messages
# from django.db.models import Q, Count, Max, Sum
# from django.utils import timezone
# from datetime import timedelta

# from tournaments.models import (
#     Tournament, Season, Stage, TournamentTeam, TableZone,
#     TimeSlot, Sanction, Appeal, TournamentAward, MatchConfirmation
# )
# from matches.models import Match, MatchStatistics, Goal, PlayerMatchStats
# from teams.models import Team, TeamMember
# from accounts.models import User
# from .forms import (
#     TournamentForm, StageForm, MatchForm, MatchResultForm,
#     TournamentTeamForm, TableZoneForm, TeamForm, TeamMemberForm
# )


# def is_admin(user):
#     """Проверка прав администратора"""
#     return user.is_authenticated and (
#         user.is_staff or 
#         user.is_superuser or 
#         getattr(user, 'role', None) in ['admin', 'moderator']
#     )


# # ============================================================
# # Dashboard
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def dashboard(request):
#     """Главная страница админ-панели"""
#     stats = {
#         'active_tournaments': Tournament.objects.filter(status__in=['registration', 'ongoing']).count(),
#         'total_teams': Team.objects.filter(is_active=True).count(),
#         'total_players': User.objects.filter(role='player').count(),
#         'pending_matches': Match.objects.filter(status='scheduled').count(),
#     }
    
#     recent_matches = Match.objects.filter(
#         status='finished',
#         confirmed_by_team1=False
#     ).select_related('team1', 'team2', 'tournament')[:10]
    
#     context = {
#         'stats': stats,
#         'recent_matches': recent_matches,
#     }
#     return render(request, 'admin_panel/dashboard.html', context)


# # ============================================================
# # Управление сезонами
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def season_list(request):
#     """Список сезонов"""
#     seasons = Season.objects.all().order_by('-start_date')
#     context = {'seasons': seasons}
#     return render(request, 'admin_panel/season_list.html', context)


# @login_required
# @user_passes_test(is_admin)
# def season_create(request):
#     """Создание сезона"""
#     if request.method == 'POST':
#         name = request.POST.get('name')
#         start_date = request.POST.get('start_date')
#         end_date = request.POST.get('end_date')
#         is_active = request.POST.get('is_active') == 'on'
        
#         last_season = Season.objects.order_by('-number').first()
#         number = (last_season.number + 1) if last_season else 1
        
#         if is_active:
#             Season.objects.all().update(is_active=False)
        
#         season = Season.objects.create(
#             name=name,
#             number=number,
#             start_date=start_date,
#             end_date=end_date if end_date else None,
#             is_active=is_active
#         )
        
#         messages.success(request, f'Сезон "{season.name}" успешно создан')
#         return redirect('admin_panel:season_list')
    
#     last_season = Season.objects.order_by('-number').first()
#     next_number = (last_season.number + 1) if last_season else 1
    
#     context = {'next_number': next_number}
#     return render(request, 'admin_panel/season_form.html', context)


# @login_required
# @user_passes_test(is_admin)
# def season_edit(request, season_id):
#     """Редактирование сезона"""
#     season = get_object_or_404(Season, id=season_id)
    
#     if request.method == 'POST':
#         season.name = request.POST.get('name')
#         season.start_date = request.POST.get('start_date')
#         season.end_date = request.POST.get('end_date') or None
#         is_active = request.POST.get('is_active') == 'on'
        
#         if is_active and not season.is_active:
#             Season.objects.exclude(id=season.id).update(is_active=False)
        
#         season.is_active = is_active
#         season.save()
        
#         messages.success(request, 'Сезон обновлён')
#         return redirect('admin_panel:season_list')
    
#     context = {'season': season}
#     return render(request, 'admin_panel/season_form.html', context)


# @login_required
# @user_passes_test(is_admin)
# def season_delete(request, season_id):
#     """Удаление сезона"""
#     season = get_object_or_404(Season, id=season_id)
    
#     if request.method == 'POST':
#         season_name = season.name
#         season.delete()
#         messages.success(request, f'Сезон "{season_name}" удалён')
#         return redirect('admin_panel:season_list')
    
#     return redirect('admin_panel:season_list')


# # ============================================================
# # Управление турнирами
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def tournament_list(request):
#     """Список турниров в админке"""
#     tournaments = Tournament.objects.all().select_related('season')
    
#     season_id = request.GET.get('season')
#     status = request.GET.get('status')
    
#     if season_id:
#         tournaments = tournaments.filter(season_id=season_id)
#     if status:
#         tournaments = tournaments.filter(status=status)
    
#     seasons = Season.objects.all()
    
#     context = {
#         'tournaments': tournaments,
#         'seasons': seasons,
#     }
#     return render(request, 'admin_panel/tournament_list.html', context)


# @login_required
# @user_passes_test(is_admin)
# def tournament_create(request):
#     """Создание турнира"""
#     if request.method == 'POST':
#         form = TournamentForm(request.POST, request.FILES)
#         if form.is_valid():
#             tournament = form.save()
#             messages.success(request, f'Турнир "{tournament.name}" успешно создан')
#             return redirect('admin_panel:tournament_detail', tournament.id)
#     else:
#         form = TournamentForm()
    
#     context = {'form': form}
#     return render(request, 'admin_panel/tournament_form.html', context)


# @login_required
# @user_passes_test(is_admin)
# def tournament_edit(request, tournament_id):
#     """Редактирование турнира"""
#     tournament = get_object_or_404(Tournament, id=tournament_id)
    
#     if request.method == 'POST':
#         form = TournamentForm(request.POST, request.FILES, instance=tournament)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Турнир успешно обновлён')
#             return redirect('admin_panel:tournament_detail', tournament.id)
#     else:
#         form = TournamentForm(instance=tournament)
    
#     context = {
#         'form': form,
#         'tournament': tournament,
#     }
#     return render(request, 'admin_panel/tournament_form.html', context)


# @login_required
# @user_passes_test(is_admin)
# def tournament_detail(request, tournament_id):
#     """Детальная страница турнира в админке"""
#     tournament = get_object_or_404(Tournament, id=tournament_id)
#     stages = tournament.stages.all()
#     participants = tournament.participants.select_related('team').all()
#     matches = Match.objects.filter(tournament=tournament).select_related(
#         'team1', 'team2', 'stage'
#     ).order_by('scheduled_time')
    
#     context = {
#         'tournament': tournament,
#         'stages': stages,
#         'participants': participants,
#         'matches': matches,
#     }
#     return render(request, 'admin_panel/tournament_detail.html', context)


# # ============================================================
# # Управление стадиями
# # ============================================================
# @login_required
# @user_passes_test(is_admin)
# def stage_create(request, tournament_id):
#     """Создание стадии турнира"""
#     tournament = get_object_or_404(Tournament, id=tournament_id)
    
#     if request.method == 'POST':
#         form = StageForm(request.POST)
#         if form.is_valid():
#             stage = form.save(commit=False)
#             stage.tournament = tournament
#             stage.save()
#             messages.success(request, f'Стадия "{stage.name}" создана')
#             return redirect('admin_panel:tournament_detail', tournament.id)
#     else:
#         form = StageForm()
    
#     context = {
#         'form': form,
#         'tournament': tournament,  # Эта строка должна быть
#     }
#     return render(request, 'admin_panel/stage_form.html', context)


# @login_required
# @user_passes_test(is_admin)
# def stage_edit(request, stage_id):
#     """Редактирование стадии"""
#     stage = get_object_or_404(Stage, id=stage_id)
    
#     if request.method == 'POST':
#         form = StageForm(request.POST, instance=stage)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Стадия обновлена')
#             return redirect('admin_panel:tournament_detail', stage.tournament.id)
#     else:
#         form = StageForm(instance=stage)
    
#     context = {
#         'form': form,
#         'stage': stage,
#         'tournament': stage.tournament,  # ДОБАВЬТЕ ЭТУ СТРОКУ
#     }
#     return render(request, 'admin_panel/stage_form.html', context)

# # ============================================================
# # Управление участниками
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def tournament_participants(request, tournament_id):
#     """Управление участниками турнира"""
#     tournament = get_object_or_404(Tournament, id=tournament_id)
#     participants = tournament.participants.select_related('team').all()
    
#     if request.method == 'POST':
#         form = TournamentTeamForm(request.POST)
#         if form.is_valid():
#             participant = form.save(commit=False)
#             participant.tournament = tournament
#             participant.save()
#             messages.success(request, f'Команда {participant.team.name} добавлена')
#             return redirect('admin_panel:tournament_participants', tournament.id)
#     else:
#         form = TournamentTeamForm()
    
#     context = {
#         'tournament': tournament,
#         'participants': participants,
#         'form': form,
#     }
#     return render(request, 'admin_panel/tournament_participants.html', context)


# @login_required
# @user_passes_test(is_admin)
# def participant_remove(request, participant_id):
#     """Удаление участника"""
#     participant = get_object_or_404(TournamentTeam, id=participant_id)
#     tournament_id = participant.tournament.id
    
#     if request.method == 'POST':
#         participant.delete()
#         messages.success(request, 'Команда удалена из турнира')
    
#     return redirect('admin_panel:tournament_participants', tournament_id)


# # ============================================================
# # Управление матчами
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def match_list(request):
#     """Список всех матчей"""
#     matches = Match.objects.all().select_related(
#         'tournament', 'stage', 'team1', 'team2'
#     ).order_by('-scheduled_time')
    
#     tournament_id = request.GET.get('tournament')
#     status = request.GET.get('status')
    
#     if tournament_id:
#         matches = matches.filter(tournament_id=tournament_id)
#     if status:
#         matches = matches.filter(status=status)
    
#     context = {
#         'matches': matches,
#         'tournaments': Tournament.objects.all(),
#     }
#     return render(request, 'admin_panel/match_list.html', context)



# @login_required
# @user_passes_test(is_admin)
# def match_create(request, tournament_id=None):
#     """Создание матча"""
#     tournament = None
#     if tournament_id:
#         tournament = get_object_or_404(Tournament, id=tournament_id)
    
#     if request.method == 'POST':
#         form = MatchForm(request.POST, request.FILES)
        
#         # Ограничиваем выбор стадий только для выбранного турнира
#         if form.is_valid():
#             match = form.save()
#             messages.success(request, 'Матч создан')
#             return redirect('admin_panel:match_detail', match.id)
#     else:
#         initial = {}
#         if tournament:
#             initial['tournament'] = tournament
#         form = MatchForm(initial=initial)
        
#         # Если турнир выбран, ограничиваем выбор стадий
#         if tournament:
#             form.fields['stage'].queryset = Stage.objects.filter(tournament=tournament)
#             form.fields['team1'].queryset = Team.objects.filter(tournament_teams__tournament=tournament)
#             form.fields['team2'].queryset = Team.objects.filter(tournament_teams__tournament=tournament)
    
#     context = {
#         'form': form,
#         'tournament': tournament,
#     }
#     return render(request, 'admin_panel/match_form.html', context)



# @login_required
# @user_passes_test(is_admin)
# def match_edit(request, match_id):
#     """Редактирование матча"""
#     match = get_object_or_404(Match, id=match_id)
    
#     if request.method == 'POST':
#         form = MatchForm(request.POST, request.FILES, instance=match)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Матч обновлён')
#             return redirect('admin_panel:match_detail', match.id)
#     else:
#         form = MatchForm(instance=match)
#         # Ограничиваем выбор стадий турниром матча
#         form.fields['stage'].queryset = Stage.objects.filter(tournament=match.tournament)
#         form.fields['team1'].queryset = Team.objects.filter(tournament_teams__tournament=match.tournament)
#         form.fields['team2'].queryset = Team.objects.filter(tournament_teams__tournament=match.tournament)
    
#     context = {
#         'form': form,
#         'match': match,
#     }
#     return render(request, 'admin_panel/match_form.html', context)




# @login_required
# @user_passes_test(is_admin)
# def match_detail(request, match_id):
#     """Детальная информация о матче"""
#     match = get_object_or_404(Match, id=match_id)
#     goals = match.goals.all().select_related('player', 'team', 'assist_by')
#     player_stats = match.player_stats.all().select_related('player', 'team')
    
#     # Проверяем, можно ли вводить результат
#     can_enter_result = match.status in ['scheduled', 'live', 'finished']
    
#     context = {
#         'match': match,
#         'goals': goals,
#         'player_stats': player_stats,
#         'can_enter_result': can_enter_result,
#     }
#     return render(request, 'admin_panel/match_detail.html', context)



# @login_required
# @user_passes_test(is_admin)
# def match_result(request, match_id):
#     """Ввод результата матча С ОБНОВЛЕНИЕМ РЕЙТИНГОВ"""
#     match = get_object_or_404(Match, id=match_id)
    
#     if request.method == 'POST':
#         form = MatchResultForm(request.POST, instance=match)
#         if form.is_valid():
#             match = form.save(commit=False)
#             match.status = 'finished'
#             match.save()
            
#             # КРИТИЧЕСКИ ВАЖНО: Обновляем рейтинги после завершения матча
#             try:
#                 from ratings.utils import update_ratings
#                 update_ratings(match)
#                 messages.success(request, 'Результат матча сохранён и рейтинги обновлены')
#             except Exception as e:
#                 messages.warning(request, f'Результат сохранён, но ошибка при обновлении рейтингов: {e}')
            
#             return redirect('admin_panel:match_detail', match.id)
#     else:
#         form = MatchResultForm(instance=match)
    
#     context = {
#         'form': form,
#         'match': match,
#     }
#     return render(request, 'admin_panel/match_result_form.html', context)








# # admin_panel/views.py - ДОБАВЬТЕ ЭТИ ФУНКЦИИ В КОНЕЦ ФАЙЛА

# # ============================================================
# # УДАЛЕНИЕ ТУРНИРА
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def tournament_delete(request, tournament_id):
#     """Удаление турнира"""
#     tournament = get_object_or_404(Tournament, id=tournament_id)
    
#     if request.method == 'POST':
#         tournament_name = tournament.name
#         tournament.delete()
#         messages.success(request, f'Турнир "{tournament_name}" успешно удалён')
#         return redirect('admin_panel:tournament_list')
    
#     context = {
#         'tournament': tournament,
#         'matches_count': Match.objects.filter(tournament=tournament).count(),
#         'participants_count': tournament.participants.count(),
#     }
#     return render(request, 'admin_panel/tournament_delete_confirm.html', context)


# # ============================================================
# # УДАЛЕНИЕ КОМАНДЫ
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def team_delete(request, team_id):
#     """Удаление команды"""
#     team = get_object_or_404(Team, id=team_id)
    
#     if request.method == 'POST':
#         team_name = team.name
#         team.delete()
#         messages.success(request, f'Команда "{team_name}" успешно удалена')
#         return redirect('admin_panel:team_list')
    
#     # Проверяем, есть ли связанные данные
#     context = {
#         'team': team,
#         'members_count': team.members.count(),
#         'matches_count': Match.objects.filter(Q(team1=team) | Q(team2=team)).count(),
#         'tournaments_count': team.tournament_teams.count(),
#     }
#     return render(request, 'admin_panel/team_delete_confirm.html', context)


# # ============================================================
# # УПРАВЛЕНИЕ РОЛЯМИ ПОЛЬЗОВАТЕЛЕЙ
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def user_roles(request):
#     """Управление ролями пользователей"""
#     users = User.objects.all().order_by('username')
    
#     # Фильтры
#     role = request.GET.get('role')
#     search = request.GET.get('search')
    
#     if role:
#         users = users.filter(role=role)
    
#     if search:
#         users = users.filter(
#             Q(username__icontains=search) |
#             Q(discord_username__icontains=search) |
#             Q(email__icontains=search)
#         )
    
#     context = {
#         'users': users,
#         'selected_role': role,
#         'search': search,
#     }
#     return render(request, 'admin_panel/user_roles.html', context)


# @login_required
# @user_passes_test(is_admin)
# def user_role_change(request, user_id):
#     """Изменение роли пользователя"""
#     user = get_object_or_404(User, id=user_id)
    
#     if request.method == 'POST':
#         new_role = request.POST.get('role')
#         if new_role in dict(User.ROLE_CHOICES):
#             old_role = user.get_role_display()
#             user.role = new_role
#             user.save()
#             messages.success(request, f'Роль пользователя {user.username} изменена: {old_role} → {user.get_role_display()}')
#         else:
#             messages.error(request, 'Недопустимая роль')
        
#         return redirect('admin_panel:user_roles')
    
#     context = {'user': user}
#     return render(request, 'admin_panel/user_role_change.html', context)












# @login_required
# @user_passes_test(is_admin)
# def match_delete(request, match_id):
#     """Удаление матча"""
#     match = get_object_or_404(Match, id=match_id)
    
#     if request.method == 'POST':
#         tournament_id = match.tournament.id
#         match.delete()
#         messages.success(request, 'Матч удалён')
#         return redirect('admin_panel:tournament_detail', tournament_id)
    
#     return redirect('admin_panel:match_detail', match_id)


# # ============================================================
# # Управление зонами таблицы
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def zone_create(request, stage_id):
#     """Создание зоны таблицы"""
#     stage = get_object_or_404(Stage, id=stage_id)
    
#     if request.method == 'POST':
#         form = TableZoneForm(request.POST)
#         if form.is_valid():
#             zone = form.save(commit=False)
#             zone.stage = stage
#             zone.save()
#             messages.success(request, f'Зона "{zone.name}" создана')
#             return redirect('admin_panel:tournament_detail', stage.tournament.id)
#     else:
#         form = TableZoneForm()
    
#     context = {
#         'form': form,
#         'stage': stage,
#     }
#     return render(request, 'admin_panel/zone_form.html', context)


# # ============================================================
# # Управление командами
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def team_list(request):
#     """Список команд"""
#     teams = Team.objects.all().annotate(
#         members_count=Count('members', filter=Q(members__is_active=True))
#     )
    
#     context = {'teams': teams}
#     return render(request, 'admin_panel/team_list.html', context)


# @login_required
# @user_passes_test(is_admin)
# def team_create(request):
#     """Создание команды"""
#     if request.method == 'POST':
#         form = TeamForm(request.POST, request.FILES)
#         if form.is_valid():
#             team = form.save()
#             messages.success(request, f'Команда "{team.name}" создана')
#             return redirect('admin_panel:team_detail', team.id)
#     else:
#         form = TeamForm()
    
#     context = {'form': form}
#     return render(request, 'admin_panel/team_form.html', context)


# @login_required
# @user_passes_test(is_admin)
# def team_detail(request, team_id):
#     """Детальная информация о команде - ИСПРАВЛЕНО"""
#     from django.utils.text import slugify
    
#     team = get_object_or_404(Team, id=team_id)
#     members = TeamMember.objects.filter(team=team).select_related('player').order_by('-is_active', 'joined_date')
    
#     # КРИТИЧЕСКИ ВАЖНО: Если slug пустой - генерируем его
#     if not team.slug:
#         team.slug = slugify(team.name)
        
#         # Проверяем уникальность
#         counter = 1
#         original_slug = team.slug
#         while Team.objects.filter(slug=team.slug).exclude(pk=team.pk).exists():
#             team.slug = f"{original_slug}-{counter}"
#             counter += 1
        
#         team.save()
#         messages.info(request, f'Автоматически создан slug: {team.slug}')
    
#     context = {
#         'team': team,
#         'members': members,
#     }
#     return render(request, 'admin_panel/teams/team_detail.html', context)

# @login_required
# @user_passes_test(is_admin)
# def team_member_add(request, team_id):
#     """Добавление игрока в команду - ИСПРАВЛЕНО"""
#     team = get_object_or_404(Team, id=team_id)
    
#     if request.method == 'POST':
#         player_id = request.POST.get('player')
        
#         if not player_id:
#             messages.error(request, 'Выберите игрока')
#             return redirect('admin_panel:team_detail', team_id)
        
#         player = get_object_or_404(User, id=player_id)
        
#         # Проверяем, не состоит ли игрок уже в этой команде
#         if TeamMember.objects.filter(team=team, player=player, is_active=True).exists():
#             messages.warning(request, f'{player.username} уже состоит в этой команде')
#             return redirect('admin_panel:team_detail', team_id)
        
#         # Проверяем, не состоит ли игрок в другой активной команде
#         existing_membership = TeamMember.objects.filter(player=player, is_active=True).exclude(team=team).first()
#         if existing_membership:
#             messages.error(request, f'{player.username} уже состоит в команде {existing_membership.team.name}')
#             return redirect('admin_panel:team_detail', team_id)
        
#         role = request.POST.get('role', 'player')
#         jersey_number = request.POST.get('jersey_number')
#         joined_date = request.POST.get('joined_date')
        
#         if not joined_date:
#             joined_date = timezone.now().date()
        
#         # Создаем участника команды
#         TeamMember.objects.create(
#             team=team,
#             player=player,
#             role=role,
#             jersey_number=int(jersey_number) if jersey_number else None,
#             joined_date=joined_date,
#             is_active=True
#         )
        
#         messages.success(request, f'{player.username} добавлен в команду {team.name}')
#         return redirect('admin_panel:team_detail', team_id)
    
#     # GET запрос - показываем форму
#     # ИСПРАВЛЕНО: Получаем только игроков БЕЗ активной команды
#     existing_player_ids = TeamMember.objects.filter(
#         is_active=True
#     ).values_list('player_id', flat=True)
    
#     available_players = User.objects.filter(
#         role__in=['player', 'captain']
#     ).exclude(
#         id__in=existing_player_ids
#     ).order_by('username')
    
#     context = {
#         'team': team,
#         'available_players': available_players,
#     }
#     return render(request, 'admin_panel/team_member_form.html', context)

# # ============================================================
# # Управление игроками
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def player_list(request):
#     """Список всех игроков"""
#     players = User.objects.all().select_related().order_by('username')
    
#     role = request.GET.get('role')
#     search = request.GET.get('search')
    
#     if role:
#         players = players.filter(role=role)
    
#     if search:
#         players = players.filter(
#             Q(username__icontains=search) |
#             Q(discord_username__icontains=search) |
#             Q(first_name__icontains=search) |
#             Q(last_name__icontains=search)
#         )
    
#     players = players.annotate(
#         matches_played=Count('playermatchstats', distinct=True)
#     )
    
#     context = {
#         'players': players,
#         'search': search,
#         'role': role,
#     }
#     return render(request, 'admin_panel/player_list.html', context)


# @login_required
# @user_passes_test(is_admin)
# def player_detail(request, player_id):
#     """Детальная информация об игроке"""
#     player = get_object_or_404(User, id=player_id)
    
#     from ratings.models import PlayerRating
    
#     teams = TeamMember.objects.filter(player=player).select_related('team')
    
#     player_stats = PlayerMatchStats.objects.filter(
#         player=player
#     ).select_related('match', 'team').order_by('-match__scheduled_time')[:10]
    
#     matches = [stat.match for stat in player_stats]
    
#     goals = Goal.objects.filter(player=player).count()
#     assists = Goal.objects.filter(assist_by=player).count()
    
#     try:
#         rating = PlayerRating.objects.get(player=player, season__isnull=True)
#     except PlayerRating.DoesNotExist:
#         rating = None
    
#     context = {
#         'player': player,
#         'teams': teams,
#         'matches': matches,
#         'goals': goals,
#         'assists': assists,
#         'rating': rating,
#     }
#     return render(request, 'admin_panel/player_detail.html', context)

# @login_required
# @user_passes_test(is_admin)
# def player_edit(request, player_id):
#     """Редактирование игрока - ДЛЯ АДМИНОВ"""
#     player = get_object_or_404(User, id=player_id)
    
#     if request.method == 'POST':
#         player.username = request.POST.get('username', player.username)
#         player.first_name = request.POST.get('first_name', '')
#         player.last_name = request.POST.get('last_name', '')
#         player.email = request.POST.get('email', '')
#         player.discord_username = request.POST.get('discord_username', '')
#         player.bio = request.POST.get('bio', '')
#         player.role = request.POST.get('role', player.role)
#         player.is_active = request.POST.get('is_active') == 'on'
#         player.is_staff = request.POST.get('is_staff') == 'on'
        
#         # Обработка аватара
#         if 'avatar' in request.FILES:
#             player.avatar = request.FILES['avatar']
        
#         player.save()
#         messages.success(request, f'Игрок {player.username} обновлён')
#         return redirect('admin_panel:player_detail', player.id)
    
#     context = {'player': player}
#     return render(request, 'admin_panel/player_edit.html', context)

# # ============================================================
# # Генерация расписания (базовая круговая система)
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def generate_schedule(request, tournament_id):
#     """Генерация расписания матчей"""
#     tournament = get_object_or_404(Tournament, id=tournament_id)
#     stage = tournament.stages.first()
    
#     if not stage:
#         messages.error(request, 'Сначала создайте стадию турнира')
#         return redirect('admin_panel:tournament_detail', tournament.id)
    
#     participants = list(tournament.participants.all())
    
#     if len(participants) < 2:
#         messages.error(request, 'Недостаточно участников')
#         return redirect('admin_panel:tournament_detail', tournament.id)
    
#     from datetime import datetime, timedelta
    
#     teams = [p.team for p in participants]
#     n = len(teams)
    
#     if n % 2:
#         teams.append(None)
#         n += 1
    
#     schedule = []
#     for round_num in range(1, n):
#         for i in range(n // 2):
#             team1 = teams[i]
#             team2 = teams[n - 1 - i]
            
#             if team1 and team2:
#                 schedule.append((round_num, team1, team2))
        
#         teams = [teams[0]] + [teams[-1]] + teams[1:-1]
    
#     start_date = tournament.start_date
#     match_time = datetime.combine(start_date, datetime.min.time().replace(hour=19))
    
#     for round_num, team1, team2 in schedule:
#         Match.objects.create(
#             tournament=tournament,
#             stage=stage,
#             round_number=round_num,
#             team1=team1,
#             team2=team2,
#             scheduled_time=match_time + timedelta(days=round_num - 1),
#             status='scheduled'
#         )
    
#     messages.success(request, f'Создано {len(schedule)} матчей')
#     return redirect('admin_panel:tournament_detail', tournament.id)


# # ============================================================
# # Генерация швейцарской системы
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def generate_swiss_schedule(request, stage_id):
#     """Генерация расписания швейцарской системы"""
#     stage = get_object_or_404(Stage, id=stage_id)
    
#     if request.method == 'POST':
#         round_number = int(request.POST.get('round_number', 1))
        
#         participants = stage.tournament.participants.all()
#         teams = [p.team for p in participants]
        
#         if SwissSystemGenerator:
#             generator = SwissSystemGenerator(stage, teams)
#             pairings = generator.generate_pairings(round_number)
            
#             for team1, team2 in pairings:
#                 Match.objects.create(
#                     tournament=stage.tournament,
#                     stage=stage,
#                     round_number=round_number,
#                     team1=team1,
#                     team2=team2,
#                     status='scheduled'
#                 )
            
#             messages.success(request, f'Создано {len(pairings)} матчей для раунда {round_number}')
#         else:
#             messages.error(request, 'Модуль швейцарской системы не найден')
        
#         return redirect('admin_panel:tournament_detail', stage.tournament.id)
    
#     context = {
#         'stage': stage,
#         'current_round': Match.objects.filter(stage=stage).aggregate(Max('round_number'))['round_number__max'] or 0
#     }
#     return render(request, 'admin_panel/swiss_schedule.html', context)


# # ============================================================
# # Генерация сетки плей-офф
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def generate_playoff_bracket(request, stage_id):
#     """Генерация сетки плей-офф"""
#     stage = get_object_or_404(Stage, id=stage_id)
    
#     if request.method == 'POST':
#         if stage.order > 1:
#             previous_stage = Stage.objects.filter(
#                 tournament=stage.tournament,
#                 order=stage.order - 1
#             ).first()
#             teams = [p.team for p in stage.tournament.participants.all()][:stage.advance_count or 8]
#         else:
#             teams = [p.team for p in stage.tournament.participants.all()]
        
#         if EliminationBracketGenerator:
#             is_double = stage.stage_type == 'double_elimination'
#             generator = EliminationBracketGenerator(stage, teams, is_double)
#             bracket = generator.generate_bracket()
            
#             if isinstance(bracket, dict):
#                 matches_data = bracket['winners']
#             else:
#                 matches_data = bracket
            
#             for match_data in matches_data:
#                 if match_data['team1'] and match_data['team2']:
#                     Match.objects.create(
#                         tournament=stage.tournament,
#                         stage=stage,
#                         round_number=match_data['round'],
#                         team1=match_data['team1'],
#                         team2=match_data['team2'],
#                         status='scheduled'
#                     )
            
#             messages.success(request, f'Создана сетка плей-офф: {len(matches_data)} матчей')
#         else:
#             messages.error(request, 'Модуль генерации плей-офф не найден')
        
#         return redirect('admin_panel:tournament_detail', stage.tournament.id)
    
#     context = {'stage': stage}
#     return render(request, 'admin_panel/playoff_bracket.html', context)


# # ============================================================
# # Управление временными слотами
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def time_slots_manage(request, tournament_id):
#     """Управление временными слотами"""
#     tournament = get_object_or_404(Tournament, id=tournament_id)
#     slots = TimeSlot.objects.filter(tournament=tournament)
    
#     if request.method == 'POST':
#         TimeSlot.objects.create(
#             tournament=tournament,
#             day_of_week=int(request.POST.get('day_of_week')),
#             start_time=request.POST.get('start_time'),
#             duration_minutes=int(request.POST.get('duration_minutes', 30)),
#             max_matches=int(request.POST.get('max_matches', 1))
#         )
#         messages.success(request, 'Временной слот добавлен')
#         return redirect('admin_panel:time_slots_manage', tournament_id)
    
#     context = {
#         'tournament': tournament,
#         'slots': slots
#     }
#     return render(request, 'admin_panel/time_slots.html', context)



# @login_required
# @user_passes_test(is_admin)
# def auto_schedule_matches(request, tournament_id):
#     """Автоматическое распределение матчей по слотам"""
#     tournament = get_object_or_404(Tournament, id=tournament_id)
    
#     if request.method == 'POST':
#         # Получаем незапланированные матчи
#         unscheduled = Match.objects.filter(
#             tournament=tournament,
#             scheduled_time__isnull=True
#         )
        
#         # Получаем слоты
#         slots = TimeSlot.objects.filter(tournament=tournament, is_active=True)
        
#         if not slots.exists():
#             messages.error(request, 'Нет доступных временных слотов')
#             return redirect('admin_panel:tournament_detail', tournament_id)
        
#         # Генерируем расписание
#         generator = ScheduleGenerator(tournament, slots)
#         scheduled = generator.schedule_matches(unscheduled)
        
#         # Применяем расписание
#         for match, match_time in scheduled:
#             match.scheduled_time = match_time
#             match.save()
        
#         messages.success(request, f'Запланировано {len(scheduled)} матчей')
#         return redirect('admin_panel:tournament_detail', tournament_id)
    
#     return redirect('admin_panel:tournament_detail', tournament_id)


# # ============================================================
# # Управление санкциями
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def sanctions_list(request, tournament_id):
#     """Список санкций турнира"""
#     tournament = get_object_or_404(Tournament, id=tournament_id)
#     sanctions = Sanction.objects.filter(tournament=tournament).select_related(
#         'team', 'player', 'issued_by'
#     ).order_by('-issued_at')
    
#     context = {
#         'tournament': tournament,
#         'sanctions': sanctions
#     }
#     return render(request, 'admin_panel/sanctions_list.html', context)



# # admin_panel/views.py - ОБНОВЛЕННЫЕ ФУНКЦИИ ДЛЯ САНКЦИЙ

# @login_required
# @user_passes_test(is_admin)
# def sanction_create(request, tournament_id):
#     """Создание санкции - ИСПРАВЛЕНО"""
#     from django.db import models as django_models
    
#     tournament = get_object_or_404(Tournament, id=tournament_id)
    
#     if request.method == 'POST':
#         sanction = Sanction.objects.create(
#             tournament=tournament,
#             team_id=request.POST.get('team') if request.POST.get('team') else None,
#             player_id=request.POST.get('player') if request.POST.get('player') else None,
#             sanction_type=request.POST.get('sanction_type'),
#             reason=request.POST.get('reason'),
#             points_deducted=int(request.POST.get('points_deducted', 0)),
#             ban_duration_days=int(request.POST.get('ban_duration_days')) if request.POST.get('ban_duration_days') else None,
#             issued_by=request.user
#         )
        
#         if sanction.ban_duration_days:
#             sanction.expires_at = timezone.now() + timedelta(days=sanction.ban_duration_days)
#             sanction.save()
        
#         messages.success(request, 'Санкция применена')
#         return redirect('admin_panel:sanctions_list', tournament_id)
    
#     # ИСПРАВЛЕНО: Получаем только команды-участники турнира
#     tournament_teams = Team.objects.filter(tournament_teams__tournament=tournament)
    
#     # ИСПРАВЛЕНО: Получаем только игроков из команд-участников турнира
#     tournament_players = User.objects.filter(
#         teammember__team__in=tournament_teams,
#         teammember__is_active=True
#     ).distinct().annotate(
#         current_team=django_models.F('teammember__team__name')
#     )
    
#     context = {
#         'tournament': tournament,
#         'teams': tournament_teams,
#         'players': tournament_players,
#     }
#     return render(request, 'admin_panel/sanction_form.html', context)



# @login_required
# @user_passes_test(is_admin)
# def sanction_detail(request, sanction_id):
#     """Просмотр санкции"""
#     sanction = get_object_or_404(Sanction, id=sanction_id)
    
#     context = {
#         'sanction': sanction,
#         'tournament': sanction.tournament,
#     }
#     return render(request, 'admin_panel/sanction_detail.html', context)


# @login_required
# @user_passes_test(is_admin)
# def sanction_delete(request, sanction_id):
#     """Удаление санкции"""
#     sanction = get_object_or_404(Sanction, id=sanction_id)
#     tournament_id = sanction.tournament.id
    
#     if request.method == 'POST':
#         sanction.delete()
#         messages.success(request, 'Санкция удалена')
#         return redirect('admin_panel:sanctions_list', tournament_id)
    
#     # Если GET запрос - просто редирект на детали
#     return redirect('admin_panel:sanction_detail', sanction_id)
# # ============================================================
# # Управление апелляциями
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def appeals_list(request):
#     """Список апелляций"""
#     appeals = Appeal.objects.all().select_related(
#         'submitted_by', 'reviewed_by', 'sanction', 'match'
#     ).order_by('-submitted_at')
    
#     # Фильтр по статусу
#     status = request.GET.get('status')
#     if status:
#         appeals = appeals.filter(status=status)
    
#     context = {
#         'appeals': appeals,
#         'selected_status': status
#     }
#     return render(request, 'admin_panel/appeals_list.html', context)


# @login_required
# @user_passes_test(is_admin)
# def appeal_review(request, appeal_id):
#     """Рассмотрение апелляции"""
#     appeal = get_object_or_404(Appeal, id=appeal_id)
    
#     if request.method == 'POST':
#         decision = request.POST.get('decision')  # approved / rejected
#         review_notes = request.POST.get('review_notes')
        
#         appeal.status = decision
#         appeal.review_notes = review_notes
#         appeal.reviewed_by = request.user
#         appeal.reviewed_at = timezone.now()
#         appeal.save()
        
#         # Если одобрена - отменяем санкцию
#         if decision == 'approved' and appeal.sanction:
#             appeal.sanction.status = 'cancelled'
#             appeal.sanction.save()
        
#         messages.success(request, f'Апелляция {appeal.get_status_display()}')
#         return redirect('admin_panel:appeals_list')
    
#     context = {'appeal': appeal}
#     return render(request, 'admin_panel/appeal_review.html', context)


# # ============================================================
# # Подтверждение результатов
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def match_confirmations(request, match_id):
#     """Просмотр подтверждений результата матча"""
#     match = get_object_or_404(Match, id=match_id)
#     confirmations = MatchConfirmation.objects.filter(match=match).select_related(
#         'team', 'confirmed_by'
#     )
    
#     context = {
#         'match': match,
#         'confirmations': confirmations
#     }
#     return render(request, 'admin_panel/match_confirmations.html', context)


# @login_required
# @user_passes_test(is_admin)
# def force_confirm_match(request, match_id):
#     """Принудительное подтверждение результата матча"""
#     match = get_object_or_404(Match, id=match_id)
    
#     if request.method == 'POST':
#         match.confirmed_by_team1 = True
#         match.confirmed_by_team2 = True
#         match.status = 'finished'
#         match.save()
        
#         messages.success(request, 'Результат матча подтвержден принудительно')
#         return redirect('admin_panel:match_detail', match_id)
    
#     return redirect('admin_panel:match_detail', match_id)


# # ============================================================
# # Управление наградами
# # ============================================================

# # Добавьте эти views в admin_panel/views.py

# from tournaments.utils import (
#     SwissSystemGenerator, 
#     EliminationBracketGenerator,
#     ScheduleGenerator,
#     TiebreakerResolver
# )
# from tournaments.models import TimeSlot, Sanction, Appeal, TournamentAward, MatchConfirmation


# # ============================================================
# # Генерация швейцарской системы
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def generate_swiss_schedule(request, stage_id):
#     """Генерация расписания швейцарской системы"""
#     stage = get_object_or_404(Stage, id=stage_id)
    
#     if request.method == 'POST':
#         round_number = int(request.POST.get('round_number', 1))
        
#         # Получаем участников
#         participants = stage.tournament.participants.all()
#         teams = [p.team for p in participants]
        
#         # Генерируем пары
#         generator = SwissSystemGenerator(stage, teams)
#         pairings = generator.generate_pairings(round_number)
        
#         # Создаем матчи
#         for team1, team2 in pairings:
#             Match.objects.create(
#                 tournament=stage.tournament,
#                 stage=stage,
#                 round_number=round_number,
#                 team1=team1,
#                 team2=team2,
#                 status='scheduled'
#             )
        
#         messages.success(request, f'Создано {len(pairings)} матчей для раунда {round_number}')
#         return redirect('admin_panel:tournament_detail', stage.tournament.id)
    
#     context = {
#         'stage': stage,
#         'current_round': Match.objects.filter(stage=stage).aggregate(Max('round_number'))['round_number__max'] or 0
#     }
#     return render(request, 'admin_panel/swiss_schedule.html', context)


# # ============================================================
# # Генерация сетки плей-офф
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def generate_playoff_bracket(request, stage_id):
#     """Генерация сетки плей-офф"""
#     stage = get_object_or_404(Stage, id=stage_id)
    
#     if request.method == 'POST':
#         # Получаем команды (из предыдущей стадии или все участники)
#         if stage.order > 1:
#             # Берем команды из предыдущей стадии
#             previous_stage = Stage.objects.filter(
#                 tournament=stage.tournament,
#                 order=stage.order - 1
#             ).first()
            
#             # TODO: Получить топ команд из предыдущей стадии
#             teams = [p.team for p in stage.tournament.participants.all()][:stage.advance_count or 8]
#         else:
#             teams = [p.team for p in stage.tournament.participants.all()]
        
#         # Генерируем сетку
#         is_double = stage.stage_type == 'double_elimination'
#         generator = EliminationBracketGenerator(stage, teams, is_double)
#         bracket = generator.generate_bracket()
        
#         # Создаем матчи
#         if isinstance(bracket, dict):  # Double elimination
#             matches_data = bracket['winners']
#         else:  # Single elimination
#             matches_data = bracket
        
#         for match_data in matches_data:
#             if match_data['team1'] and match_data['team2']:
#                 Match.objects.create(
#                     tournament=stage.tournament,
#                     stage=stage,
#                     round_number=match_data['round'],
#                     team1=match_data['team1'],
#                     team2=match_data['team2'],
#                     status='scheduled'
#                 )
        
#         messages.success(request, f'Создана сетка плей-офф: {len(matches_data)} матчей')
#         return redirect('admin_panel:tournament_detail', stage.tournament.id)
    
#     context = {'stage': stage}
#     return render(request, 'admin_panel/playoff_bracket.html', context)


# # ============================================================
# # Управление временными слотами
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def time_slots_manage(request, tournament_id):
#     """Управление временными слотами"""
#     tournament = get_object_or_404(Tournament, id=tournament_id)
#     slots = TimeSlot.objects.filter(tournament=tournament)
    
#     if request.method == 'POST':
#         # Создание нового слота
#         TimeSlot.objects.create(
#             tournament=tournament,
#             day_of_week=int(request.POST.get('day_of_week')),
#             start_time=request.POST.get('start_time'),
#             duration_minutes=int(request.POST.get('duration_minutes', 30)),
#             max_matches=int(request.POST.get('max_matches', 1))
#         )
#         messages.success(request, 'Временной слот добавлен')
#         return redirect('admin_panel:time_slots_manage', tournament_id)
    
#     context = {
#         'tournament': tournament,
#         'slots': slots
#     }
#     return render(request, 'admin_panel/time_slots.html', context)


# @login_required
# @user_passes_test(is_admin)
# def auto_schedule_matches(request, tournament_id):
#     """Автоматическое распределение матчей по слотам"""
#     tournament = get_object_or_404(Tournament, id=tournament_id)
    
#     if request.method == 'POST':
#         # Получаем незапланированные матчи
#         unscheduled = Match.objects.filter(
#             tournament=tournament,
#             scheduled_time__isnull=True
#         )
        
#         # Получаем слоты
#         slots = TimeSlot.objects.filter(tournament=tournament, is_active=True)
        
#         if not slots.exists():
#             messages.error(request, 'Нет доступных временных слотов')
#             return redirect('admin_panel:tournament_detail', tournament_id)
        
#         # Генерируем расписание
#         generator = ScheduleGenerator(tournament, slots)
#         scheduled = generator.schedule_matches(unscheduled)
        
#         # Применяем расписание
#         for match, match_time in scheduled:
#             match.scheduled_time = match_time
#             match.save()
        
#         messages.success(request, f'Запланировано {len(scheduled)} матчей')
#         return redirect('admin_panel:tournament_detail', tournament_id)
    
#     return redirect('admin_panel:tournament_detail', tournament_id)


# # ============================================================
# # Управление санкциями
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def sanctions_list(request, tournament_id):
#     """Список санкций турнира"""
#     tournament = get_object_or_404(Tournament, id=tournament_id)
#     sanctions = Sanction.objects.filter(tournament=tournament).select_related(
#         'team', 'player', 'issued_by'
#     )
    
#     context = {
#         'tournament': tournament,
#         'sanctions': sanctions
#     }
#     return render(request, 'admin_panel/sanctions_list.html', context)


# @login_required
# @user_passes_test(is_admin)
# def sanction_create(request, tournament_id):
#     """Создание санкции"""
#     tournament = get_object_or_404(Tournament, id=tournament_id)
    
#     if request.method == 'POST':
#         sanction = Sanction.objects.create(
#             tournament=tournament,
#             team_id=request.POST.get('team') if request.POST.get('team') else None,
#             player_id=request.POST.get('player') if request.POST.get('player') else None,
#             sanction_type=request.POST.get('sanction_type'),
#             reason=request.POST.get('reason'),
#             points_deducted=int(request.POST.get('points_deducted', 0)),
#             ban_duration_days=int(request.POST.get('ban_duration_days')) if request.POST.get('ban_duration_days') else None,
#             issued_by=request.user
#         )
        
#         # Устанавливаем дату истечения для банов
#         if sanction.ban_duration_days:
#             from datetime import timedelta
#             sanction.expires_at = timezone.now() + timedelta(days=sanction.ban_duration_days)
#             sanction.save()
        
#         messages.success(request, 'Санкция применена')
#         return redirect('admin_panel:sanctions_list', tournament_id)
    
#     context = {
#         'tournament': tournament,
#         'teams': Team.objects.filter(tournament_teams__tournament=tournament),
#         'players': User.objects.filter(role__in=['player', 'captain'])
#     }
#     return render(request, 'admin_panel/sanction_form.html', context)


# # ============================================================
# # Управление апелляциями
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def appeals_list(request):
#     """Список апелляций"""
#     appeals = Appeal.objects.all().select_related(
#         'submitted_by', 'reviewed_by', 'sanction', 'match'
#     ).order_by('-submitted_at')
    
#     # Фильтр по статусу
#     status = request.GET.get('status')
#     if status:
#         appeals = appeals.filter(status=status)
    
#     context = {
#         'appeals': appeals,
#         'selected_status': status
#     }
#     return render(request, 'admin_panel/appeals_list.html', context)


# @login_required
# @user_passes_test(is_admin)
# def appeal_review(request, appeal_id):
#     """Рассмотрение апелляции"""
#     appeal = get_object_or_404(Appeal, id=appeal_id)
    
#     if request.method == 'POST':
#         decision = request.POST.get('decision')  # approved / rejected
#         review_notes = request.POST.get('review_notes')
        
#         appeal.status = decision
#         appeal.review_notes = review_notes
#         appeal.reviewed_by = request.user
#         appeal.reviewed_at = timezone.now()
#         appeal.save()
        
#         # Если одобрена - отменяем санкцию
#         if decision == 'approved' and appeal.sanction:
#             appeal.sanction.status = 'cancelled'
#             appeal.sanction.save()
        
#         messages.success(request, f'Апелляция {appeal.get_status_display()}')
#         return redirect('admin_panel:appeals_list')
    
#     context = {'appeal': appeal}
#     return render(request, 'admin_panel/appeal_review.html', context)


# # ============================================================
# # Подтверждение результатов
# # ============================================================

# @login_required
# @user_passes_test(is_admin)
# def match_confirmations(request, match_id):
#     """Просмотр подтверждений результата матча"""
#     match = get_object_or_404(Match, id=match_id)
#     confirmations = MatchConfirmation.objects.filter(match=match).select_related(
#         'team', 'confirmed_by'
#     )
    
#     context = {
#         'match': match,
#         'confirmations': confirmations
#     }
#     return render(request, 'admin_panel/match_confirmations.html', context)


# @login_required
# @user_passes_test(is_admin)
# def force_confirm_match(request, match_id):
#     """Принудительное подтверждение результата матча"""
#     match = get_object_or_404(Match, id=match_id)
    
#     if request.method == 'POST':
#         match.confirmed_by_team1 = True
#         match.confirmed_by_team2 = True
#         match.status = 'finished'
#         match.save()
        
#         messages.success(request, 'Результат матча подтвержден принудительно')
#         return redirect('admin_panel:match_detail', match_id)
    
#     return redirect('admin_panel:match_detail', match_id)


# # ============================================================
# # Управление наградами
# # ============================================================


# @login_required
# @user_passes_test(is_admin)
# def awards_manage(request, tournament_id):
#     """Управление наградами турнира - ИСПРАВЛЕНО"""
#     tournament = get_object_or_404(Tournament, id=tournament_id)
#     awards = TournamentAward.objects.filter(tournament=tournament).select_related(
#         'team', 'player'
#     )
    
#     if request.method == 'POST':
#         TournamentAward.objects.create(
#             tournament=tournament,
#             award_type=request.POST.get('award_type'),
#             team_id=request.POST.get('team') if request.POST.get('team') else None,
#             player_id=request.POST.get('player') if request.POST.get('player') else None,
#             value=int(request.POST.get('value')) if request.POST.get('value') else None,
#             description=request.POST.get('description', '')
#         )
#         messages.success(request, 'Награда добавлена')
#         return redirect('admin_panel:awards_manage', tournament_id)
    
#     # ИСПРАВЛЕНО: Получаем только команды-участники турнира
#     tournament_teams = Team.objects.filter(tournament_teams__tournament=tournament)
    
#     # ИСПРАВЛЕНО: Получаем только игроков из команд-участников турнира
#     tournament_players = User.objects.filter(
#         teammember__team__in=tournament_teams,
#         teammember__is_active=True
#     ).distinct()
    
#     context = {
#         'tournament': tournament,
#         'awards': awards,
#         'teams': tournament_teams,
#         'players': tournament_players,
#     }
#     return render(request, 'admin_panel/awards_manage.html', context)


# @login_required
# @user_passes_test(is_admin)
# def team_edit(request, team_id):
#     """Редактирование команды"""
#     from django.utils.text import slugify
    
#     team = get_object_or_404(Team, id=team_id)
    
#     if request.method == 'POST':
#         form = TeamForm(request.POST, request.FILES, instance=team)
#         if form.is_valid():
#             team = form.save()
#             messages.success(request, f'Команда "{team.name}" успешно обновлена!')
#             return redirect('admin_panel:team_detail', team_id=team.id)
#         else:
#             messages.error(request, 'Ошибка при сохранении команды')
#     else:
#         form = TeamForm(instance=team)
    
#     context = {
#         'form': form,
#         'team': team,
#         'title': f'Редактирование: {team.name}',
#     }
#     return render(request, 'admin_panel/teams/team_form.html', context)


# @login_required
# @user_passes_test(is_admin)
# def team_member_remove(request, member_id):
#     """Удаление игрока из команды"""
#     member = get_object_or_404(TeamMember, id=member_id)
#     team_id = member.team.id
    
#     # Не даем удалить капитана
#     if member.player == member.team.captain:
#         messages.error(request, 'Нельзя удалить капитана из команды')
#         return redirect('admin_panel:team_detail', team_id)
    
#     if request.method == 'POST':
#         player_name = member.player.username
#         member.delete()
#         messages.success(request, f'Игрок {player_name} удален из команды')
    
#     return redirect('admin_panel:team_detail', team_id)


# @login_required
# @user_passes_test(is_admin)
# def team_toggle_status(request, team_id):
#     """Активация/деактивация команды"""
#     team = get_object_or_404(Team, id=team_id)
    
#     if request.method == 'POST':
#         team.is_active = not team.is_active
#         team.save()
        
#         status = 'активирована' if team.is_active else 'деактивирована'
#         messages.success(request, f'Команда {team.name} {status}')
    
#     return redirect('admin_panel:team_detail', team_id)



# admin_panel/views.py - ИСПРАВЛЕННАЯ ВЕРСИЯ

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Max, Sum
from django.utils import timezone
from datetime import timedelta

from tournaments.models import (
    Tournament, Season, Stage, TournamentTeam, TableZone,
    TimeSlot, Sanction, Appeal, TournamentAward, MatchConfirmation
)
from matches.models import Match, MatchStatistics, Goal, PlayerMatchStats
from teams.models import Team, TeamMember
from accounts.models import User
from .forms import (
    TournamentForm, StageForm, MatchForm, MatchResultForm,
    TournamentTeamForm, TableZoneForm, TeamForm, TeamMemberForm
)


def is_admin(user):
    """
    ИСПРАВЛЕНО: Проверка прав администратора
    Только staff и superuser имеют доступ к админ-панели
    """
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# ============================================================
# Dashboard
# ============================================================

@login_required
@user_passes_test(is_admin)
def dashboard(request):
    """Главная страница админ-панели"""
    stats = {
        'active_tournaments': Tournament.objects.filter(status__in=['registration', 'ongoing']).count(),
        'total_teams': Team.objects.filter(is_active=True).count(),  # ИСПРАВЛЕНО
        'total_players': User.objects.filter(role='player').count(),
        'pending_matches': Match.objects.filter(status='scheduled').count(),
    }
    
    recent_matches = Match.objects.filter(
        status='finished',
        confirmed_by_team1=False
    ).select_related('team1', 'team2', 'tournament')[:10]
    
    context = {
        'stats': stats,
        'recent_matches': recent_matches,
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ============================================================
# Управление сезонами
# ============================================================

@login_required
@user_passes_test(is_admin)
def season_list(request):
    """Список сезонов"""
    seasons = Season.objects.all().order_by('-start_date')
    context = {'seasons': seasons}
    return render(request, 'admin_panel/season_list.html', context)


@login_required
@user_passes_test(is_admin)
def season_create(request):
    """Создание сезона"""
    if request.method == 'POST':
        name = request.POST.get('name')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_active = request.POST.get('is_active') == 'on'
        
        last_season = Season.objects.order_by('-number').first()
        number = (last_season.number + 1) if last_season else 1
        
        if is_active:
            Season.objects.all().update(is_active=False)
        
        season = Season.objects.create(
            name=name,
            number=number,
            start_date=start_date,
            end_date=end_date if end_date else None,
            is_active=is_active
        )
        
        messages.success(request, f'Сезон "{season.name}" успешно создан')
        return redirect('admin_panel:season_list')
    
    last_season = Season.objects.order_by('-number').first()
    next_number = (last_season.number + 1) if last_season else 1
    
    context = {'next_number': next_number}
    return render(request, 'admin_panel/season_form.html', context)


@login_required
@user_passes_test(is_admin)
def season_edit(request, season_id):
    """Редактирование сезона"""
    season = get_object_or_404(Season, id=season_id)
    
    if request.method == 'POST':
        season.name = request.POST.get('name')
        season.start_date = request.POST.get('start_date')
        season.end_date = request.POST.get('end_date') or None
        is_active = request.POST.get('is_active') == 'on'
        
        if is_active and not season.is_active:
            Season.objects.exclude(id=season.id).update(is_active=False)
        
        season.is_active = is_active
        season.save()
        
        messages.success(request, 'Сезон обновлён')
        return redirect('admin_panel:season_list')
    
    context = {'season': season}
    return render(request, 'admin_panel/season_form.html', context)


@login_required
@user_passes_test(is_admin)
def season_delete(request, season_id):
    """Удаление сезона"""
    season = get_object_or_404(Season, id=season_id)
    
    if request.method == 'POST':
        season_name = season.name
        season.delete()
        messages.success(request, f'Сезон "{season_name}" удалён')
        return redirect('admin_panel:season_list')
    
    return redirect('admin_panel:season_list')


# ============================================================
# Управление турнирами
# ============================================================

@login_required
@user_passes_test(is_admin)
def tournament_list(request):
    """Список турниров в админке"""
    tournaments = Tournament.objects.all().select_related('season')
    
    season_id = request.GET.get('season')
    status = request.GET.get('status')
    
    if season_id:
        tournaments = tournaments.filter(season_id=season_id)
    if status:
        tournaments = tournaments.filter(status=status)
    
    seasons = Season.objects.all()
    
    context = {
        'tournaments': tournaments,
        'seasons': seasons,
    }
    return render(request, 'admin_panel/tournament_list.html', context)


@login_required
@user_passes_test(is_admin)
def tournament_create(request):
    """Создание турнира"""
    if request.method == 'POST':
        form = TournamentForm(request.POST, request.FILES)
        if form.is_valid():
            tournament = form.save()
            messages.success(request, f'Турнир "{tournament.name}" успешно создан')
            return redirect('admin_panel:tournament_detail', tournament_id=tournament.id)  # ИСПРАВЛЕНО
    else:
        form = TournamentForm()
    
    context = {'form': form}
    return render(request, 'admin_panel/tournament_form.html', context)


@login_required
@user_passes_test(is_admin)
def tournament_edit(request, tournament_id):
    """Редактирование турнира"""
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    if request.method == 'POST':
        form = TournamentForm(request.POST, request.FILES, instance=tournament)
        if form.is_valid():
            form.save()
            messages.success(request, 'Турнир успешно обновлён')
            return redirect('admin_panel:tournament_detail', tournament_id=tournament.id)  # ИСПРАВЛЕНО
    else:
        form = TournamentForm(instance=tournament)
    
    context = {
        'form': form,
        'tournament': tournament,
    }
    return render(request, 'admin_panel/tournament_form.html', context)


@login_required
@user_passes_test(is_admin)
def tournament_detail(request, tournament_id):
    """Детальная страница турнира в админке"""
    tournament = get_object_or_404(Tournament, id=tournament_id)
    stages = tournament.stages.all()
    participants = tournament.participants.select_related('team').all()
    matches = Match.objects.filter(tournament=tournament).select_related(
        'team1', 'team2', 'stage'
    ).order_by('scheduled_time')
    
    context = {
        'tournament': tournament,
        'stages': stages,
        'participants': participants,
        'matches': matches,
    }
    return render(request, 'admin_panel/tournament_detail.html', context)


@login_required
@user_passes_test(is_admin)
def tournament_delete(request, tournament_id):
    """Удаление турнира"""
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    if request.method == 'POST':
        tournament_name = tournament.name
        tournament.delete()
        messages.success(request, f'Турнир "{tournament_name}" успешно удалён')
        return redirect('admin_panel:tournament_list')
    
    context = {
        'tournament': tournament,
        'matches_count': Match.objects.filter(tournament=tournament).count(),
        'participants_count': tournament.participants.count(),
    }
    return render(request, 'admin_panel/tournament_delete_confirm.html', context)


# ============================================================
# Управление стадиями
# ============================================================

@login_required
@user_passes_test(is_admin)
def stage_create(request, tournament_id):
    """Создание стадии турнира"""
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    if request.method == 'POST':
        form = StageForm(request.POST)
        if form.is_valid():
            stage = form.save(commit=False)
            stage.tournament = tournament
            stage.save()
            messages.success(request, f'Стадия "{stage.name}" создана')
            return redirect('admin_panel:tournament_detail', tournament_id=tournament.id)  # ИСПРАВЛЕНО
    else:
        form = StageForm()
    
    context = {
        'form': form,
        'tournament': tournament,
    }
    return render(request, 'admin_panel/stage_form.html', context)


@login_required
@user_passes_test(is_admin)
def stage_edit(request, stage_id):
    """Редактирование стадии"""
    stage = get_object_or_404(Stage, id=stage_id)
    
    if request.method == 'POST':
        form = StageForm(request.POST, instance=stage)
        if form.is_valid():
            form.save()
            messages.success(request, 'Стадия обновлена')
            return redirect('admin_panel:tournament_detail', tournament_id=stage.tournament.id)  # ИСПРАВЛЕНО
    else:
        form = StageForm(instance=stage)
    
    context = {
        'form': form,
        'stage': stage,
        'tournament': stage.tournament,
    }
    return render(request, 'admin_panel/stage_form.html', context)


# ============================================================
# Управление участниками
# ============================================================

# admin_panel/views.py
# ЗАМЕНИТЕ функцию tournament_participants на эту версию

@login_required
@user_passes_test(is_admin)
def tournament_participants(request, tournament_id):
    """Управление участниками турнира - ФИНАЛЬНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    tournament = get_object_or_404(Tournament, id=tournament_id)
    participants = tournament.participants.select_related('team', 'team__captain').all()
    
    if request.method == 'POST':
        # Получаем данные напрямую из POST (без формы Django)
        team_id = request.POST.get('team')
        seed = request.POST.get('seed')
        
        if not team_id:
            messages.error(request, 'Выберите команду')
            return redirect('admin_panel:tournament_participants', tournament_id=tournament_id)
        
        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            messages.error(request, 'Команда не найдена')
            return redirect('admin_panel:tournament_participants', tournament_id=tournament_id)
        
        # Проверка: команда уже участвует?
        if TournamentTeam.objects.filter(tournament=tournament, team=team).exists():
            messages.warning(request, f'Команда {team.name} уже участвует в этом турнире')
            return redirect('admin_panel:tournament_participants', tournament_id=tournament_id)
        
        # Создаем участника
        TournamentTeam.objects.create(
            tournament=tournament,
            team=team,
            seed=int(seed) if seed else None,
            is_confirmed=True  # Автоматически подтверждаем при добавлении админом
        )
        
        messages.success(request, f'✅ Команда {team.name} успешно добавлена в турнир')
        return redirect('admin_panel:tournament_participants', tournament_id=tournament_id)
    
    # GET запрос - показываем форму
    # Доступные команды (ещё не участвуют в турнире)
    participating_team_ids = participants.values_list('team_id', flat=True)
    available_teams = Team.objects.filter(is_active=True).exclude(
        id__in=participating_team_ids
    ).order_by('name')
    
    context = {
        'tournament': tournament,
        'participants': participants,
        'available_teams': available_teams,
    }
    return render(request, 'admin_panel/tournament_participants.html', context)

@login_required
@user_passes_test(is_admin)
def participant_remove(request, participant_id):
    """Удаление участника"""
    participant = get_object_or_404(TournamentTeam, id=participant_id)
    tournament_id = participant.tournament.id
    
    if request.method == 'POST':
        participant.delete()
        messages.success(request, 'Команда удалена из турнира')
    
    return redirect('admin_panel:tournament_participants', tournament_id=tournament_id)  # ИСПРАВЛЕНО


# ============================================================
# Управление матчами
# ============================================================

@login_required
@user_passes_test(is_admin)
def match_list(request):
    """Список всех матчей"""
    matches = Match.objects.all().select_related(
        'tournament', 'stage', 'team1', 'team2'
    ).order_by('-scheduled_time')
    
    tournament_id = request.GET.get('tournament')
    status = request.GET.get('status')
    
    if tournament_id:
        matches = matches.filter(tournament_id=tournament_id)
    if status:
        matches = matches.filter(status=status)
    
    context = {
        'matches': matches,
        'tournaments': Tournament.objects.all(),
    }
    return render(request, 'admin_panel/match_list.html', context)


@login_required
@user_passes_test(is_admin)
def match_create(request, tournament_id=None):
    """Создание матча"""
    tournament = None
    if tournament_id:
        tournament = get_object_or_404(Tournament, id=tournament_id)
    
    if request.method == 'POST':
        form = MatchForm(request.POST, request.FILES)
        
        if form.is_valid():
            match = form.save()
            messages.success(request, 'Матч создан')
            return redirect('admin_panel:match_detail', match_id=match.id)  # ИСПРАВЛЕНО
    else:
        initial = {}
        if tournament:
            initial['tournament'] = tournament
        form = MatchForm(initial=initial)
        
        if tournament:
            form.fields['stage'].queryset = Stage.objects.filter(tournament=tournament)
            form.fields['team1'].queryset = Team.objects.filter(tournament_teams__tournament=tournament)
            form.fields['team2'].queryset = Team.objects.filter(tournament_teams__tournament=tournament)
    
    context = {
        'form': form,
        'tournament': tournament,
    }
    return render(request, 'admin_panel/match_form.html', context)


@login_required
@user_passes_test(is_admin)
def match_edit(request, match_id):
    """Редактирование матча"""
    match = get_object_or_404(Match, id=match_id)
    
    if request.method == 'POST':
        form = MatchForm(request.POST, request.FILES, instance=match)
        if form.is_valid():
            form.save()
            messages.success(request, 'Матч обновлён')
            return redirect('admin_panel:match_detail', match_id=match.id)  # ИСПРАВЛЕНО
    else:
        form = MatchForm(instance=match)
        form.fields['stage'].queryset = Stage.objects.filter(tournament=match.tournament)
        form.fields['team1'].queryset = Team.objects.filter(tournament_teams__tournament=match.tournament)
        form.fields['team2'].queryset = Team.objects.filter(tournament_teams__tournament=match.tournament)
    
    context = {
        'form': form,
        'match': match,
    }
    return render(request, 'admin_panel/match_form.html', context)


@login_required
@user_passes_test(is_admin)
def match_detail(request, match_id):
    """Детальная информация о матче"""
    match = get_object_or_404(Match, id=match_id)
    goals = match.goals.all().select_related('player', 'team', 'assist_by')
    player_stats = match.player_stats.all().select_related('player', 'team')
    
    can_enter_result = match.status in ['scheduled', 'live', 'finished']
    
    context = {
        'match': match,
        'goals': goals,
        'player_stats': player_stats,
        'can_enter_result': can_enter_result,
    }
    return render(request, 'admin_panel/match_detail.html', context)


@login_required
@user_passes_test(is_admin)
def match_result(request, match_id):
    """Ввод результата матча - ИСПРАВЛЕНО БЕЗ ДУБЛИРОВАНИЯ РЕЙТИНГОВ"""
    match = get_object_or_404(Match, id=match_id)
    
    from matches.models import PlayerMatchStats
    from teams.models import TeamMember
    from ratings.utils import clear_processed_matches_cache
    
    # Получаем игроков обеих команд
    team1_members = TeamMember.objects.filter(
        team=match.team1, 
        is_active=True
    ).select_related('player')
    
    team2_members = TeamMember.objects.filter(
        team=match.team2, 
        is_active=True
    ).select_related('player')
    
    if request.method == 'POST':
        score_team1 = request.POST.get('score_team1')
        score_team2 = request.POST.get('score_team2')
        
        if not score_team1 or not score_team2:
            messages.error(request, 'Введите счёт для обеих команд')
            return redirect('admin_panel:match_result', match_id=match_id)
        
        try:
            from django.db import transaction
            
            with transaction.atomic():
                # ВАЖНО: Сначала создаём статистику игроков БЕЗ сохранения матча
                
                # Создаём/обновляем статистику для игроков команды 1
                for member in team1_members:
                    player_key = f'player_{member.player.id}'
                    
                    goals = int(request.POST.get(f'{player_key}_goals', 0) or 0)
                    assists = int(request.POST.get(f'{player_key}_assists', 0) or 0)
                    saves = int(request.POST.get(f'{player_key}_saves', 0) or 0)
                    shots = int(request.POST.get(f'{player_key}_shots', 0) or 0)
                    
                    PlayerMatchStats.objects.update_or_create(
                        match=match,
                        player=member.player,
                        defaults={
                            'team': match.team1,
                            'goals': goals,
                            'assists': assists,
                            'saves': saves,
                            'shots': shots,
                        }
                    )
                
                # Создаём/обновляем статистику для игроков команды 2
                for member in team2_members:
                    player_key = f'player_{member.player.id}'
                    
                    goals = int(request.POST.get(f'{player_key}_goals', 0) or 0)
                    assists = int(request.POST.get(f'{player_key}_assists', 0) or 0)
                    saves = int(request.POST.get(f'{player_key}_saves', 0) or 0)
                    shots = int(request.POST.get(f'{player_key}_shots', 0) or 0)
                    
                    PlayerMatchStats.objects.update_or_create(
                        match=match,
                        player=member.player,
                        defaults={
                            'team': match.team2,
                            'goals': goals,
                            'assists': assists,
                            'saves': saves,
                            'shots': shots,
                        }
                    )
                
                # ТЕПЕРЬ сохраняем результат матча
                # Сигнал update_ratings_on_match_finish сработает и обновит рейтинги
                match.score_team1 = int(score_team1)
                match.score_team2 = int(score_team2)
                match.status = 'finished'
                
                # Опциональные поля
                if request.POST.get('actual_start_time'):
                    match.actual_start_time = request.POST.get('actual_start_time')
                if request.POST.get('actual_end_time'):
                    match.actual_end_time = request.POST.get('actual_end_time')
                if request.POST.get('notes'):
                    match.notes = request.POST.get('notes')
                
                # Сохраняем матч - сигнал автоматически обновит рейтинги
                match.save()
                
                messages.success(request, '✅ Результат матча сохранён и рейтинги обновлены!')
                
        except Exception as e:
            messages.error(request, f'Ошибка при сохранении: {e}')
            return redirect('admin_panel:match_result', match_id=match_id)
        
        return redirect('admin_panel:match_detail', match_id=match.id)
    
    # GET запрос - показываем форму
    context = {
        'match': match,
        'team1_members': team1_members,
        'team2_members': team2_members,
    }
    return render(request, 'admin_panel/match_result_form.html', context)


@login_required
@user_passes_test(is_admin)
def sanction_create(request, tournament_id):
    """Создание санкции - ИСПРАВЛЕНО С ПРИМЕНЕНИЕМ К РЕЙТИНГАМ"""
    from django.db import models as django_models
    from ratings.utils import apply_sanction_to_ratings
    
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    if request.method == 'POST':
        # Создаем санкцию
        sanction = Sanction.objects.create(
            tournament=tournament,
            team_id=request.POST.get('team') if request.POST.get('team') else None,
            player_id=request.POST.get('player') if request.POST.get('player') else None,
            sanction_type=request.POST.get('sanction_type'),
            reason=request.POST.get('reason'),
            points_deducted=int(request.POST.get('points_deducted', 0)),
            ban_duration_days=int(request.POST.get('ban_duration_days')) if request.POST.get('ban_duration_days') else None,
            issued_by=request.user,
            status='active'  # Явно устанавливаем статус
        )
        
        # Устанавливаем срок истечения бана
        if sanction.ban_duration_days:
            sanction.expires_at = timezone.now() + timedelta(days=sanction.ban_duration_days)
            sanction.save()
        
        # ВАЖНО: Санкция теперь автоматически применяется через сигнал
        # Но для надёжности можно вызвать явно:
        # apply_sanction_to_ratings(sanction)
        
        # Формируем сообщение
        target = sanction.team.name if sanction.team else sanction.player.username
        msg = f'Санкция применена к {target}'
        if sanction.points_deducted > 0:
            msg += f' (-{sanction.points_deducted} очков)'
        
        messages.success(request, msg)
        return redirect('admin_panel:sanctions_list', tournament_id=tournament_id)
    
    # GET запрос - показываем форму
    tournament_teams = Team.objects.filter(tournament_teams__tournament=tournament)
    
    tournament_players = User.objects.filter(
        teammember__team__in=tournament_teams,
        teammember__is_active=True
    ).distinct().annotate(
        current_team=django_models.F('teammember__team__name')
    )
    
    context = {
        'tournament': tournament,
        'teams': tournament_teams,
        'players': tournament_players,
    }
    return render(request, 'admin_panel/sanction_form.html', context)





@login_required
@user_passes_test(is_admin)
def match_delete(request, match_id):
    """Удаление матча"""
    match = get_object_or_404(Match, id=match_id)
    
    if request.method == 'POST':
        tournament_id = match.tournament.id
        match.delete()
        messages.success(request, 'Матч удалён')
        return redirect('admin_panel:tournament_detail', tournament_id=tournament_id)  # ИСПРАВЛЕНО
    
    return redirect('admin_panel:match_detail', match_id=match_id)  # ИСПРАВЛЕНО


# ============================================================
# Управление командами
# ============================================================

@login_required
@user_passes_test(is_admin)
def team_list(request):
    """Список команд"""
    teams = Team.objects.all().annotate(
        members_count=Count('members', filter=Q(members__is_active=True))
    )
    
    context = {'teams': teams}
    return render(request, 'admin_panel/team_list.html', context)


@login_required
@user_passes_test(is_admin)
def team_create(request):
    """Создание команды - ИСПРАВЛЕНО"""
    if request.method == 'POST':
        form = TeamForm(request.POST, request.FILES)
        if form.is_valid():
            team = form.save(commit=False)
            # КРИТИЧЕСКИ ВАЖНО: Устанавливаем is_active=True при создании
            if team.is_active is None:
                team.is_active = True
            team.save()
            
            # Если есть капитан - добавляем в состав
            if team.captain:
                TeamMember.objects.get_or_create(
                    team=team,
                    player=team.captain,
                    defaults={
                        'role': 'captain',
                        'joined_date': team.founded_date or timezone.now().date(),
                        'is_active': True
                    }
                )
            
            messages.success(request, f'Команда "{team.name}" создана')
            return redirect('admin_panel:team_detail', team_id=team.id)
        else:
            messages.error(request, 'Ошибка при создании команды')
    else:
        form = TeamForm()
    
    context = {
        'form': form,
        'title': 'Создание команды'
    }
    return render(request, 'admin_panel/teams/team_form.html', context)

@login_required
@user_passes_test(is_admin)
def team_edit(request, team_id):
    """Редактирование команды"""
    from django.utils.text import slugify
    
    team = get_object_or_404(Team, id=team_id)
    
    if request.method == 'POST':
        form = TeamForm(request.POST, request.FILES, instance=team)
        if form.is_valid():
            team = form.save()
            messages.success(request, f'Команда "{team.name}" успешно обновлена!')
            return redirect('admin_panel:team_detail', team_id=team.id)  # ИСПРАВЛЕНО
        else:
            messages.error(request, 'Ошибка при сохранении команды')
    else:
        form = TeamForm(instance=team)
    
    context = {
        'form': form,
        'team': team,
        'title': f'Редактирование: {team.name}',
    }
    return render(request, 'admin_panel/teams/team_form.html', context)


@login_required
@user_passes_test(is_admin)
def team_detail(request, team_id):
    """Детальная информация о команде - ИСПРАВЛЕНО"""
    from django.utils.text import slugify
    
    team = get_object_or_404(Team, id=team_id)
    members = TeamMember.objects.filter(team=team).select_related('player').order_by('-is_active', 'joined_date')
    
    # КРИТИЧЕСКИ ВАЖНО: Если slug пустой - генерируем его
    if not team.slug:
        team.slug = slugify(team.name)
        
        counter = 1
        original_slug = team.slug
        while Team.objects.filter(slug=team.slug).exclude(pk=team.pk).exists():
            team.slug = f"{original_slug}-{counter}"
            counter += 1
        
        team.save()
        messages.info(request, f'Автоматически создан slug: {team.slug}')
    
    context = {
        'team': team,
        'members': members,
    }
    return render(request, 'admin_panel/teams/team_detail.html', context)


@login_required
@user_passes_test(is_admin)
def team_delete(request, team_id):
    """Удаление команды"""
    team = get_object_or_404(Team, id=team_id)
    
    if request.method == 'POST':
        team_name = team.name
        team.delete()
        messages.success(request, f'Команда "{team_name}" успешно удалена')
        return redirect('admin_panel:team_list')
    
    context = {
        'team': team,
        'members_count': team.members.count(),
        'matches_count': Match.objects.filter(Q(team1=team) | Q(team2=team)).count(),
        'tournaments_count': team.tournament_teams.count(),
    }
    return render(request, 'admin_panel/team_delete_confirm.html', context)


@login_required
@user_passes_test(is_admin)
def team_member_add(request, team_id):
    """Добавление игрока в команду - ИСПРАВЛЕНО"""
    team = get_object_or_404(Team, id=team_id)
    
    if request.method == 'POST':
        player_id = request.POST.get('player')
        
        if not player_id:
            messages.error(request, 'Выберите игрока')
            return redirect('admin_panel:team_detail', team_id=team_id)  # ИСПРАВЛЕНО
        
        player = get_object_or_404(User, id=player_id)
        
        if TeamMember.objects.filter(team=team, player=player, is_active=True).exists():
            messages.warning(request, f'{player.username} уже состоит в этой команде')
            return redirect('admin_panel:team_detail', team_id=team_id)  # ИСПРАВЛЕНО
        
        existing_membership = TeamMember.objects.filter(player=player, is_active=True).exclude(team=team).first()
        if existing_membership:
            messages.error(request, f'{player.username} уже состоит в команде {existing_membership.team.name}')
            return redirect('admin_panel:team_detail', team_id=team_id)  # ИСПРАВЛЕНО
        
        role = request.POST.get('role', 'player')
        jersey_number = request.POST.get('jersey_number')
        joined_date = request.POST.get('joined_date')
        
        if not joined_date:
            joined_date = timezone.now().date()
        
        TeamMember.objects.create(
            team=team,
            player=player,
            role=role,
            jersey_number=int(jersey_number) if jersey_number else None,
            joined_date=joined_date,
            is_active=True
        )
        
        messages.success(request, f'{player.username} добавлен в команду {team.name}')
        return redirect('admin_panel:team_detail', team_id=team_id)  # ИСПРАВЛЕНО
    
    existing_player_ids = TeamMember.objects.filter(
        is_active=True
    ).values_list('player_id', flat=True)
    
    available_players = User.objects.filter(
        role__in=['player', 'captain']
    ).exclude(
        id__in=existing_player_ids
    ).order_by('username')
    
    context = {
        'team': team,
        'available_players': available_players,
    }
    return render(request, 'admin_panel/team_member_form.html', context)


@login_required
@user_passes_test(is_admin)
def team_member_remove(request, member_id):
    """Удаление игрока из команды - ИСПРАВЛЕНО"""
    member = get_object_or_404(TeamMember, id=member_id)
    team_id = member.team.id
    
    if member.player == member.team.captain:
        messages.error(request, 'Нельзя удалить капитана из команды')
        return redirect('admin_panel:team_detail', team_id=team_id)  # ИСПРАВЛЕНО
    
    if request.method == 'POST':
        player_name = member.player.username
        member.delete()
        messages.success(request, f'Игрок {player_name} удален из команды')
    
    return redirect('admin_panel:team_detail', team_id=team_id)  # ИСПРАВЛЕНО


@login_required
@user_passes_test(is_admin)
def team_toggle_status(request, team_id):
    """Активация/деактивация команды"""
    team = get_object_or_404(Team, id=team_id)
    
    if request.method == 'POST':
        team.is_active = not team.is_active
        team.save()
        
        status = 'активирована' if team.is_active else 'деактивирована'
        messages.success(request, f'Команда {team.name} {status}')
    
    return redirect('admin_panel:team_detail', team_id=team_id)  # ИСПРАВЛЕНО


# ============================================================
# Управление игроками
# ============================================================

@login_required
@user_passes_test(is_admin)
def player_list(request):
    """Список всех игроков"""
    players = User.objects.all().select_related().order_by('username')
    
    role = request.GET.get('role')
    search = request.GET.get('search')
    
    if role:
        players = players.filter(role=role)
    
    if search:
        players = players.filter(
            Q(username__icontains=search) |
            Q(discord_username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    players = players.annotate(
        matches_played=Count('playermatchstats', distinct=True)
    )
    
    context = {
        'players': players,
        'search': search,
        'role': role,
    }
    return render(request, 'admin_panel/player_list.html', context)


@login_required
@user_passes_test(is_admin)
def player_detail(request, player_id):
    """Детальная информация об игроке"""
    player = get_object_or_404(User, id=player_id)
    
    from ratings.models import PlayerRating
    
    teams = TeamMember.objects.filter(player=player).select_related('team')
    
    player_stats = PlayerMatchStats.objects.filter(
        player=player
    ).select_related('match', 'team').order_by('-match__scheduled_time')[:10]
    
    matches = [stat.match for stat in player_stats]
    
    goals = Goal.objects.filter(player=player).count()
    assists = Goal.objects.filter(assist_by=player).count()
    
    try:
        rating = PlayerRating.objects.get(player=player, season__isnull=True)
    except PlayerRating.DoesNotExist:
        rating = None
    
    context = {
        'player': player,
        'teams': teams,
        'matches': matches,
        'goals': goals,
        'assists': assists,
        'rating': rating,
    }
    return render(request, 'admin_panel/player_detail.html', context)


@login_required
@user_passes_test(is_admin)
def player_edit(request, player_id):
    """Редактирование игрока - ДЛЯ АДМИНОВ"""
    player = get_object_or_404(User, id=player_id)
    
    if request.method == 'POST':
        player.username = request.POST.get('username', player.username)
        player.first_name = request.POST.get('first_name', '')
        player.last_name = request.POST.get('last_name', '')
        player.email = request.POST.get('email', '')
        player.discord_username = request.POST.get('discord_username', '')
        player.bio = request.POST.get('bio', '')
        player.role = request.POST.get('role', player.role)
        player.is_active = request.POST.get('is_active') == 'on'
        player.is_staff = request.POST.get('is_staff') == 'on'
        
        if 'avatar' in request.FILES:
            player.avatar = request.FILES['avatar']
        
        player.save()
        messages.success(request, f'Игрок {player.username} обновлён')
        return redirect('admin_panel:player_detail', player_id=player.id)  # ИСПРАВЛЕНО
    
    context = {'player': player}
    return render(request, 'admin_panel/player_edit.html', context)


# ============================================================
# Управление ролями пользователей
# ============================================================

@login_required
@user_passes_test(is_admin)
def user_roles(request):
    """Управление ролями пользователей"""
    users = User.objects.all().order_by('username')
    
    role = request.GET.get('role')
    search = request.GET.get('search')
    
    if role:
        users = users.filter(role=role)
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(discord_username__icontains=search) |
            Q(email__icontains=search)
        )
    
    context = {
        'users': users,
        'selected_role': role,
        'search': search,
    }
    return render(request, 'admin_panel/user_roles.html', context)


@login_required
@user_passes_test(is_admin)
def user_role_change(request, user_id):
    """Изменение роли пользователя"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in dict(User.ROLE_CHOICES):
            old_role = user.get_role_display()
            user.role = new_role
            user.save()
            messages.success(request, f'Роль пользователя {user.username} изменена: {old_role} → {user.get_role_display()}')
        else:
            messages.error(request, 'Недопустимая роль')
        
        return redirect('admin_panel:user_roles')
    
    context = {'user': user}
    return render(request, 'admin_panel/user_role_change.html', context)


# ============================================================
# Генерация расписания
# ============================================================

@login_required
@user_passes_test(is_admin)
def generate_schedule(request, tournament_id):
    """Генерация расписания матчей"""
    tournament = get_object_or_404(Tournament, id=tournament_id)
    stage = tournament.stages.first()
    
    if not stage:
        messages.error(request, 'Сначала создайте стадию турнира')
        return redirect('admin_panel:tournament_detail', tournament_id=tournament.id)  # ИСПРАВЛЕНО
    
    participants = list(tournament.participants.all())
    
    if len(participants) < 2:
        messages.error(request, 'Недостаточно участников')
        return redirect('admin_panel:tournament_detail', tournament_id=tournament.id)  # ИСПРАВЛЕНО
    
    from datetime import datetime, timedelta
    
    teams = [p.team for p in participants]
    n = len(teams)
    
    if n % 2:
        teams.append(None)
        n += 1
    
    schedule = []
    for round_num in range(1, n):
        for i in range(n // 2):
            team1 = teams[i]
            team2 = teams[n - 1 - i]
            
            if team1 and team2:
                schedule.append((round_num, team1, team2))
        
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
    
    start_date = tournament.start_date
    match_time = datetime.combine(start_date, datetime.min.time().replace(hour=19))
    
    for round_num, team1, team2 in schedule:
        Match.objects.create(
            tournament=tournament,
            stage=stage,
            round_number=round_num,
            team1=team1,
            team2=team2,
            scheduled_time=match_time + timedelta(days=round_num - 1),
            status='scheduled'
        )
    
    messages.success(request, f'Создано {len(schedule)} матчей')
    return redirect('admin_panel:tournament_detail', tournament_id=tournament.id)  # ИСПРАВЛЕНО


# ============================================================
# Управление зонами таблицы
# ============================================================

@login_required
@user_passes_test(is_admin)
def zone_create(request, stage_id):
    """Создание зоны таблицы"""
    stage = get_object_or_404(Stage, id=stage_id)
    
    if request.method == 'POST':
        form = TableZoneForm(request.POST)
        if form.is_valid():
            zone = form.save(commit=False)
            zone.stage = stage
            zone.save()
            messages.success(request, f'Зона "{zone.name}" создана')
            return redirect('admin_panel:tournament_detail', tournament_id=stage.tournament.id)  # ИСПРАВЛЕНО
    else:
        form = TableZoneForm()
    
    context = {
        'form': form,
        'stage': stage,
    }
    return render(request, 'admin_panel/zone_form.html', context)


# ============================================================
# Управление санкциями
# ============================================================

@login_required
@user_passes_test(is_admin)
def sanctions_list(request, tournament_id):
    """Список санкций турнира"""
    tournament = get_object_or_404(Tournament, id=tournament_id)
    sanctions = Sanction.objects.filter(tournament=tournament).select_related(
        'team', 'player', 'issued_by'
    ).order_by('-issued_at')
    
    context = {
        'tournament': tournament,
        'sanctions': sanctions
    }
    return render(request, 'admin_panel/sanctions_list.html', context)


@login_required
@user_passes_test(is_admin)
def sanction_create(request, tournament_id):
    """Создание санкции - ИСПРАВЛЕНО"""
    from django.db import models as django_models
    
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    if request.method == 'POST':
        sanction = Sanction.objects.create(
            tournament=tournament,
            team_id=request.POST.get('team') if request.POST.get('team') else None,
            player_id=request.POST.get('player') if request.POST.get('player') else None,
            sanction_type=request.POST.get('sanction_type'),
            reason=request.POST.get('reason'),
            points_deducted=int(request.POST.get('points_deducted', 0)),
            ban_duration_days=int(request.POST.get('ban_duration_days')) if request.POST.get('ban_duration_days') else None,
            issued_by=request.user
        )
        
        if sanction.ban_duration_days:
            sanction.expires_at = timezone.now() + timedelta(days=sanction.ban_duration_days)
            sanction.save()
        
        messages.success(request, 'Санкция применена')
        return redirect('admin_panel:sanctions_list', tournament_id=tournament_id)  # ИСПРАВЛЕНО
    
    tournament_teams = Team.objects.filter(tournament_teams__tournament=tournament)
    
    tournament_players = User.objects.filter(
        teammember__team__in=tournament_teams,
        teammember__is_active=True
    ).distinct().annotate(
        current_team=django_models.F('teammember__team__name')
    )
    
    context = {
        'tournament': tournament,
        'teams': tournament_teams,
        'players': tournament_players,
    }
    return render(request, 'admin_panel/sanction_form.html', context)


@login_required
@user_passes_test(is_admin)
def sanction_detail(request, sanction_id):
    """Просмотр санкции"""
    sanction = get_object_or_404(Sanction, id=sanction_id)
    
    context = {
        'sanction': sanction,
        'tournament': sanction.tournament,
    }
    return render(request, 'admin_panel/sanction_detail.html', context)


@login_required
@user_passes_test(is_admin)
def sanction_delete(request, sanction_id):
    """Удаление санкции"""
    sanction = get_object_or_404(Sanction, id=sanction_id)
    tournament_id = sanction.tournament.id
    
    if request.method == 'POST':
        sanction.delete()
        messages.success(request, 'Санкция удалена')
        return redirect('admin_panel:sanctions_list', tournament_id=tournament_id)  # ИСПРАВЛЕНО
    
    return redirect('admin_panel:sanction_detail', sanction_id=sanction_id)  # ИСПРАВЛЕНО


# ============================================================
# Управление апелляциями
# ============================================================

@login_required
@user_passes_test(is_admin)
def appeals_list(request):
    """Список апелляций"""
    appeals = Appeal.objects.all().select_related(
        'submitted_by', 'reviewed_by', 'sanction', 'match'
    ).order_by('-submitted_at')
    
    status = request.GET.get('status')
    if status:
        appeals = appeals.filter(status=status)
    
    context = {
        'appeals': appeals,
        'selected_status': status
    }
    return render(request, 'admin_panel/appeals_list.html', context)


@login_required
@user_passes_test(is_admin)
def appeal_review(request, appeal_id):
    """Рассмотрение апелляции"""
    appeal = get_object_or_404(Appeal, id=appeal_id)
    
    if request.method == 'POST':
        decision = request.POST.get('decision')
        review_notes = request.POST.get('review_notes')
        
        appeal.status = decision
        appeal.review_notes = review_notes
        appeal.reviewed_by = request.user
        appeal.reviewed_at = timezone.now()
        appeal.save()
        
        if decision == 'approved' and appeal.sanction:
            appeal.sanction.status = 'cancelled'
            appeal.sanction.save()
        
        messages.success(request, f'Апелляция {appeal.get_status_display()}')
        return redirect('admin_panel:appeals_list')
    
    context = {'appeal': appeal}
    return render(request, 'admin_panel/appeal_review.html', context)


# ============================================================
# Подтверждение результатов
# ============================================================

@login_required
@user_passes_test(is_admin)
def match_confirmations(request, match_id):
    """Просмотр подтверждений результата матча"""
    match = get_object_or_404(Match, id=match_id)
    confirmations = MatchConfirmation.objects.filter(match=match).select_related(
        'team', 'confirmed_by'
    )
    
    context = {
        'match': match,
        'confirmations': confirmations
    }
    return render(request, 'admin_panel/match_confirmations.html', context)


@login_required
@user_passes_test(is_admin)
def force_confirm_match(request, match_id):
    """Принудительное подтверждение результата матча"""
    match = get_object_or_404(Match, id=match_id)
    
    if request.method == 'POST':
        match.confirmed_by_team1 = True
        match.confirmed_by_team2 = True
        match.status = 'finished'
        match.save()
        
        messages.success(request, 'Результат матча подтвержден принудительно')
        return redirect('admin_panel:match_detail', match_id=match_id)  # ИСПРАВЛЕНО
    
    return redirect('admin_panel:match_detail', match_id=match_id)  # ИСПРАВЛЕНО


# ============================================================
# Управление наградами
# ============================================================

@login_required
@user_passes_test(is_admin)
def awards_manage(request, tournament_id):
    """Управление наградами турнира - ИСПРАВЛЕНО"""
    tournament = get_object_or_404(Tournament, id=tournament_id)
    awards = TournamentAward.objects.filter(tournament=tournament).select_related(
        'team', 'player'
    )
    
    if request.method == 'POST':
        TournamentAward.objects.create(
            tournament=tournament,
            award_type=request.POST.get('award_type'),
            team_id=request.POST.get('team') if request.POST.get('team') else None,
            player_id=request.POST.get('player') if request.POST.get('player') else None,
            value=int(request.POST.get('value')) if request.POST.get('value') else None,
            description=request.POST.get('description', '')
        )
        messages.success(request, 'Награда добавлена')
        return redirect('admin_panel:awards_manage', tournament_id=tournament_id)  # ИСПРАВЛЕНО
    
    tournament_teams = Team.objects.filter(tournament_teams__tournament=tournament)
    
    tournament_players = User.objects.filter(
        teammember__team__in=tournament_teams,
        teammember__is_active=True
    ).distinct()
    
    context = {
        'tournament': tournament,
        'awards': awards,
        'teams': tournament_teams,
        'players': tournament_players,
    }
    return render(request, 'admin_panel/awards_manage.html', context)


# ============================================================
# Временные слоты и генераторы
# ============================================================

@login_required
@user_passes_test(is_admin)
def time_slots_manage(request, tournament_id):
    """Управление временными слотами"""
    tournament = get_object_or_404(Tournament, id=tournament_id)
    slots = TimeSlot.objects.filter(tournament=tournament)
    
    if request.method == 'POST':
        TimeSlot.objects.create(
            tournament=tournament,
            day_of_week=int(request.POST.get('day_of_week')),
            start_time=request.POST.get('start_time'),
            duration_minutes=int(request.POST.get('duration_minutes', 30)),
            max_matches=int(request.POST.get('max_matches', 1))
        )
        messages.success(request, 'Временной слот добавлен')
        return redirect('admin_panel:time_slots_manage', tournament_id=tournament_id)  # ИСПРАВЛЕНО
    
    context = {
        'tournament': tournament,
        'slots': slots
    }
    return render(request, 'admin_panel/time_slots.html', context)


@login_required
@user_passes_test(is_admin)
def auto_schedule_matches(request, tournament_id):
    """Автоматическое распределение матчей по слотам"""
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    if request.method == 'POST':
        unscheduled = Match.objects.filter(
            tournament=tournament,
            scheduled_time__isnull=True
        )
        
        slots = TimeSlot.objects.filter(tournament=tournament, is_active=True)
        
        if not slots.exists():
            messages.error(request, 'Нет доступных временных слотов')
            return redirect('admin_panel:tournament_detail', tournament_id=tournament_id)  # ИСПРАВЛЕНО
        
        from tournaments.utils import ScheduleGenerator
        generator = ScheduleGenerator(tournament, slots)
        scheduled = generator.schedule_matches(unscheduled)
        
        for match, match_time in scheduled:
            match.scheduled_time = match_time
            match.save()
        
        messages.success(request, f'Запланировано {len(scheduled)} матчей')
        return redirect('admin_panel:tournament_detail', tournament_id=tournament_id)  # ИСПРАВЛЕНО
    
    return redirect('admin_panel:tournament_detail', tournament_id=tournament_id)  # ИСПРАВЛЕНО


@login_required
@user_passes_test(is_admin)
def generate_swiss_schedule(request, stage_id):
    """Генерация расписания швейцарской системы"""
    stage = get_object_or_404(Stage, id=stage_id)
    
    if request.method == 'POST':
        round_number = int(request.POST.get('round_number', 1))
        
        participants = stage.tournament.participants.all()
        teams = [p.team for p in participants]
        
        from tournaments.utils import SwissSystemGenerator
        generator = SwissSystemGenerator(stage, teams)
        pairings = generator.generate_pairings(round_number)
        
        for team1, team2 in pairings:
            Match.objects.create(
                tournament=stage.tournament,
                stage=stage,
                round_number=round_number,
                team1=team1,
                team2=team2,
                status='scheduled'
            )
        
        messages.success(request, f'Создано {len(pairings)} матчей для раунда {round_number}')
        return redirect('admin_panel:tournament_detail', tournament_id=stage.tournament.id)  # ИСПРАВЛЕНО
    
    context = {
        'stage': stage,
        'current_round': Match.objects.filter(stage=stage).aggregate(Max('round_number'))['round_number__max'] or 0
    }
    return render(request, 'admin_panel/swiss_schedule.html', context)





@login_required
@user_passes_test(is_admin)
def generate_playoff_bracket(request, stage_id):
    """Генерация сетки плей-офф"""
    stage = get_object_or_404(Stage, id=stage_id)
    
    if request.method == 'POST':
        if stage.order > 1:
            previous_stage = Stage.objects.filter(
                tournament=stage.tournament,
                order=stage.order - 1
            ).first()
            teams = [p.team for p in stage.tournament.participants.all()][:stage.advance_count or 8]
        else:
            teams = [p.team for p in stage.tournament.participants.all()]
        
        from tournaments.utils import EliminationBracketGenerator
        is_double = stage.stage_type == 'double_elimination'
        generator = EliminationBracketGenerator(stage, teams, is_double)
        bracket = generator.generate_bracket()
        
        if isinstance(bracket, dict):
            matches_data = bracket['winners']
        else:
            matches_data = bracket
        
        for match_data in matches_data:
            if match_data['team1'] and match_data['team2']:
                Match.objects.create(
                    tournament=stage.tournament,
                    stage=stage,
                    round_number=match_data['round'],
                    team1=match_data['team1'],
                    team2=match_data['team2'],
                    status='scheduled'
                )
        
        messages.success(request, f'Создана сетка плей-офф: {len(matches_data)} матчей')
        return redirect('admin_panel:tournament_detail', tournament_id=stage.tournament.id)  # ИСПРАВЛЕНО
    
    context = {'stage': stage}
    return render(request, 'admin_panel/playoff_bracket.html', context)









@login_required
@user_passes_test(is_admin)
def user_delete(request, player_id):  # ИСПРАВЛЕНО: player_id вместо user_id
    """Удаление пользователя"""
    user = get_object_or_404(User, id=player_id)  # ИСПРАВЛЕНО: используем player_id
    
    # Проверка: нельзя удалить самого себя
    if user == request.user:
        messages.error(request, 'Вы не можете удалить свой собственный аккаунт')
        return redirect('admin_panel:player_list')
    
    # Проверка: нельзя удалить superuser
    if user.is_superuser:
        messages.error(request, 'Нельзя удалить суперпользователя')
        return redirect('admin_panel:player_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'Пользователь {username} успешно удалён')
        return redirect('admin_panel:player_list')
    
    return redirect('admin_panel:player_detail', player_id=player_id)  