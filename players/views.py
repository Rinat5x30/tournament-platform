
# players/views.py

from django.shortcuts import render, get_object_or_404, redirect
from accounts.models import User
from ratings.models import PlayerRating
from django.db.models import Q

def player_list(request):
    """Список всех игроков"""
    players = User.objects.filter(role='player').order_by('username')
    
    # Поиск
    search = request.GET.get('search', '')
    if search:
        players = players.filter(
            Q(username__icontains=search) | 
            Q(discord_username__icontains=search)
        )
    
    context = {
        'players': players,
        'search': search,
    }
    return render(request, 'players/player_list.html', context)

def player_detail(request, username):
    """Детальная страница игрока - редирект на профиль"""
    return redirect('accounts:profile', username=username)
