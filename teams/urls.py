# teams/urls.py

from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    path('', views.team_list, name='team_list'),
    path('<slug:slug>/', views.team_detail, name='team_detail'),
    
    # ДОБАВЬТЕ ЭТУ СТРОКУ для создания команды
    path('create/', views.team_create, name='team_create'),
    
    # Капитанские функции
    path('captain/dashboard/', views.captain_dashboard, name='captain_dashboard'),
    path('captain/match/<int:match_id>/confirm/', views.confirm_match_result, name='confirm_match_result'),
    path('captain/tournament/<int:tournament_id>/register/', views.register_for_tournament, name='register_for_tournament'),
    path('captain/tournament/<int:tournament_id>/withdraw/', views.withdraw_from_tournament, name='withdraw_from_tournament'),
    path('captain/tournament/<int:tournament_id>/confirm/', views.confirm_tournament_participation, name='confirm_tournament_participation'),
    
    # Апелляции
    path('sanction/<int:sanction_id>/appeal/', views.submit_appeal, name='submit_appeal'),
    path('appeal/<int:appeal_id>/', views.view_appeal, name='view_appeal'),
]