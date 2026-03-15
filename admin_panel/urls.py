# # admin_panel/urls.py

# from django.urls import path
# from . import views

# app_name = 'admin_panel'

# urlpatterns = [
#     # Dashboard
#     path('', views.dashboard, name='dashboard'),
    
#     # Season management
#     path('seasons/', views.season_list, name='season_list'),
#     path('seasons/create/', views.season_create, name='season_create'),
#     path('seasons/<int:season_id>/edit/', views.season_edit, name='season_edit'),
#     path('seasons/<int:season_id>/delete/', views.season_delete, name='season_delete'),
    
#     # Tournament management
#     path('tournaments/', views.tournament_list, name='tournament_list'),
#     path('tournaments/create/', views.tournament_create, name='tournament_create'),
#     path('tournaments/<int:tournament_id>/', views.tournament_detail, name='tournament_detail'),
#     path('tournaments/<int:tournament_id>/edit/', views.tournament_edit, name='tournament_edit'),
#     path('tournaments/<int:tournament_id>/generate-schedule/', views.generate_schedule, name='generate_schedule'),
    
#     # Stage management
#     path('tournaments/<int:tournament_id>/stages/create/', views.stage_create, name='stage_create'),
#     path('stages/<int:stage_id>/edit/', views.stage_edit, name='stage_edit'),
#     path('stages/<int:stage_id>/zones/create/', views.zone_create, name='zone_create'),
    
#     # Advanced tournament generation
#     path('stages/<int:stage_id>/generate-swiss/', views.generate_swiss_schedule, name='generate_swiss_schedule'),
#     path('stages/<int:stage_id>/generate-playoff/', views.generate_playoff_bracket, name='generate_playoff_bracket'),
    
#     # Time slots
#     path('tournaments/<int:tournament_id>/time-slots/', views.time_slots_manage, name='time_slots_manage'),
#     path('tournaments/<int:tournament_id>/auto-schedule/', views.auto_schedule_matches, name='auto_schedule_matches'),
    
#     # Participant management
#     path('tournaments/<int:tournament_id>/participants/', views.tournament_participants, name='tournament_participants'),
#     path('participants/<int:participant_id>/remove/', views.participant_remove, name='participant_remove'),
    
#     # Match management
#     path('matches/', views.match_list, name='match_list'),
#     path('matches/create/', views.match_create, name='match_create'),
#     path('tournaments/<int:tournament_id>/matches/create/', views.match_create, name='match_create_tournament'),
#     path('matches/<int:match_id>/', views.match_detail, name='match_detail'),
#     path('matches/<int:match_id>/edit/', views.match_edit, name='match_edit'),
#     path('matches/<int:match_id>/result/', views.match_result, name='match_result'),
#     path('matches/<int:match_id>/delete/', views.match_delete, name='match_delete'),
#     path('matches/<int:match_id>/confirmations/', views.match_confirmations, name='match_confirmations'),
#     path('matches/<int:match_id>/force-confirm/', views.force_confirm_match, name='force_confirm_match'),
    
#     # Sanctions
#     path('tournaments/<int:tournament_id>/sanctions/', views.sanctions_list, name='sanctions_list'),
#     path('tournaments/<int:tournament_id>/sanctions/create/', views.sanction_create, name='sanction_create'),
#     # В секцию Sanctions добавьте:
#     path('sanctions/<int:sanction_id>/', views.sanction_detail, name='sanction_detail'),
#     path('sanctions/<int:sanction_id>/delete/', views.sanction_delete, name='sanction_delete'),
#     # Appeals
#     path('appeals/', views.appeals_list, name='appeals_list'),
#     path('appeals/<int:appeal_id>/review/', views.appeal_review, name='appeal_review'),
    
#     # Awards
#     path('tournaments/<int:tournament_id>/awards/', views.awards_manage, name='awards_manage'),
    
#     # Team management
#     path('teams/', views.team_list, name='team_list'),
#     path('teams/create/', views.team_create, name='team_create'),
#     path('teams/<int:team_id>/', views.team_detail, name='team_detail'),
#     path('teams/<int:team_id>/members/add/', views.team_member_add, name='team_member_add'),
    
#     # Player management
#     path('players/', views.player_list, name='player_list'),
#     path('players/<int:player_id>/', views.player_detail, name='player_detail'),
#     path('players/<int:player_id>/edit/', views.player_edit, name='player_edit'),
    
#     # Удаление
#    # В конец списка urlpatterns добавьте:

# # Удаление
# path('tournaments/<int:tournament_id>/delete/', views.tournament_delete, name='tournament_delete'),
# path('teams/<int:team_id>/delete/', views.team_delete, name='team_delete'),

# # Управление ролями  
# path('users/roles/', views.user_roles, name='user_roles'),
# path('users/<int:user_id>/role/change/', views.user_role_change, name='user_role_change'),

# ]

# admin_panel/urls.py - ПОЛНАЯ ВЕРСИЯ

from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Главная страница
    path('', views.dashboard, name='dashboard'),
    
    # Сезоны
    path('seasons/', views.season_list, name='season_list'),
    path('seasons/create/', views.season_create, name='season_create'),
    path('seasons/<int:season_id>/edit/', views.season_edit, name='season_edit'),
    path('seasons/<int:season_id>/delete/', views.season_delete, name='season_delete'),
    
    # Турниры
    path('tournaments/', views.tournament_list, name='tournament_list'),
    path('tournaments/create/', views.tournament_create, name='tournament_create'),
    path('tournaments/<int:tournament_id>/', views.tournament_detail, name='tournament_detail'),
    path('tournaments/<int:tournament_id>/edit/', views.tournament_edit, name='tournament_edit'),
    path('tournaments/<int:tournament_id>/delete/', views.tournament_delete, name='tournament_delete'),
       path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),

    # Стадии турнира
    path('tournaments/<int:tournament_id>/stage/create/', views.stage_create, name='stage_create'),
    path('stages/<int:stage_id>/edit/', views.stage_edit, name='stage_edit'),
    
    # Участники турнира
    path('tournaments/<int:tournament_id>/participants/', views.tournament_participants, name='tournament_participants'),
    path('participants/<int:participant_id>/remove/', views.participant_remove, name='participant_remove'),
    
    # Матчи
    path('matches/', views.match_list, name='match_list'),
    path('matches/create/', views.match_create, name='match_create'),
    path('tournaments/<int:tournament_id>/matches/create/', views.match_create, name='match_create_for_tournament'),
    path('matches/<int:match_id>/', views.match_detail, name='match_detail'),
    path('matches/<int:match_id>/edit/', views.match_edit, name='match_edit'),
    path('matches/<int:match_id>/delete/', views.match_delete, name='match_delete'),
    path('matches/<int:match_id>/result/', views.match_result, name='match_result'),
    path('matches/<int:match_id>/confirmations/', views.match_confirmations, name='match_confirmations'),
    path('matches/<int:match_id>/force-confirm/', views.force_confirm_match, name='force_confirm_match'),
    
    # Команды
    path('teams/', views.team_list, name='team_list'),
    path('teams/create/', views.team_create, name='team_create'),
    path('teams/<int:team_id>/', views.team_detail, name='team_detail'),
    path('teams/<int:team_id>/edit/', views.team_edit, name='team_edit'),
    path('teams/<int:team_id>/delete/', views.team_delete, name='team_delete'),
    path('teams/<int:team_id>/add-member/', views.team_member_add, name='team_member_add'),
    path('teams/members/<int:member_id>/remove/', views.team_member_remove, name='team_member_remove'),
    path('teams/<int:team_id>/toggle-status/', views.team_toggle_status, name='team_toggle_status'),
    
    # Игроки
   path('players/', views.player_list, name='player_list'),
    path('players/<int:player_id>/', views.player_detail, name='player_detail'),
    path('players/<int:player_id>/edit/', views.player_edit, name='player_edit'),
    path('players/<int:player_id>/delete/', views.user_delete, name='user_delete'),  # ДОБАВЬТЕ ЭТУ СТРОКУ
    
    # Роли пользователей
    path('users/roles/', views.user_roles, name='user_roles'),
    path('users/<int:user_id>/role/change/', views.user_role_change, name='user_role_change'),
    
    # Генерация расписания
    path('tournaments/<int:tournament_id>/generate-schedule/', views.generate_schedule, name='generate_schedule'),
    path('stages/<int:stage_id>/generate-swiss/', views.generate_swiss_schedule, name='generate_swiss_schedule'),
    path('stages/<int:stage_id>/generate-playoff/', views.generate_playoff_bracket, name='generate_playoff_bracket'),
    
    # Временные слоты
    path('tournaments/<int:tournament_id>/time-slots/', views.time_slots_manage, name='time_slots_manage'),
    path('tournaments/<int:tournament_id>/auto-schedule/', views.auto_schedule_matches, name='auto_schedule_matches'),
    
    # Зоны таблицы
    path('stages/<int:stage_id>/zone/create/', views.zone_create, name='zone_create'),
    
    # Санкции
    path('tournaments/<int:tournament_id>/sanctions/', views.sanctions_list, name='sanctions_list'),
    path('tournaments/<int:tournament_id>/sanctions/create/', views.sanction_create, name='sanction_create'),
    path('sanctions/<int:sanction_id>/', views.sanction_detail, name='sanction_detail'),
    path('sanctions/<int:sanction_id>/delete/', views.sanction_delete, name='sanction_delete'),
    
    # Апелляции
    path('appeals/', views.appeals_list, name='appeals_list'),
    path('appeals/<int:appeal_id>/review/', views.appeal_review, name='appeal_review'),
    
    # Награды
    path('tournaments/<int:tournament_id>/awards/', views.awards_manage, name='awards_manage'),
]