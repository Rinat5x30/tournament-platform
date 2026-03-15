# ratings/urls.py

from django.urls import path
from . import views

app_name = 'ratings'

urlpatterns = [
    path('players/', views.player_ratings, name='player_ratings'),
    path('teams/', views.team_ratings, name='team_ratings'),
    path('recalculate/', views.recalculate_ratings, name='recalculate'),
]