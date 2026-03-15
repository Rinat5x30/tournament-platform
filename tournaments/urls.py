# tournaments/urls.py

from django.urls import path
from . import views

app_name = 'tournaments'

urlpatterns = [
    # Главная страница
    path('', views.index, name='index'),
    
    # Список и архив турниров
    path('tournaments/', views.tournament_list, name='tournament_list'),
    path('archive/', views.tournament_archive, name='archive'),
    
    # Поиск
    path('search/', views.search, name='search'),  # ДОБАВЬТЕ ЭТУ СТРОКУ
    
    # Детали турнира
    path('tournaments/<slug:slug>/', views.tournament_detail, name='tournament_detail'),
    path('tournaments/<slug:slug>/table/', views.tournament_table, name='tournament_table'),
    path('tournaments/<slug:slug>/table/<int:stage_id>/', views.tournament_table, name='tournament_table_stage'),
    path('tournaments/<slug:slug>/schedule/', views.tournament_schedule, name='tournament_schedule'),
    path('tournaments/<slug:slug>/bracket/', views.tournament_bracket, name='tournament_bracket'),
    
    # Карьера и история
    path('player/<str:username>/career/', views.player_career, name='player_career'),
    path('team/<slug:slug>/history/', views.team_history, name='team_history'),
]