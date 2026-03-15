# ratings/utils.py - ИСПРАВЛЕННАЯ ВЕРСИЯ С ПОДДЕРЖКОЙ САНКЦИЙ И ЗАЩИТОЙ ОТ ДУБЛИРОВАНИЯ

from django.db import transaction
from django.db.models import F
from .models import PlayerRating, TeamRating


# Кэш обработанных матчей для предотвращения дублирования
_processed_matches = set()


def update_ratings_for_match(match, force=False):
    """
    ГЛАВНАЯ ФУНКЦИЯ: Обновление всех рейтингов после завершения матча.
    Вызывается автоматически через сигнал при завершении матча.
    
    Args:
        match: объект Match
        force: если True, игнорирует проверку на дублирование
    """
    if match.status != 'finished':
        print(f"⚠️ Матч #{match.id} не завершен (статус: {match.status})")
        return False
    
    # Проверяем, что есть счёт
    if match.score_team1 is None or match.score_team2 is None:
        print(f"⚠️ Матч #{match.id} не имеет счёта")
        return False
    
    # ЗАЩИТА ОТ ДУБЛИРОВАНИЯ: проверяем, не обработан ли уже этот матч
    if not force and match.id in _processed_matches:
        print(f"⏭️ Матч #{match.id} уже обработан, пропускаем")
        return False
    
    print(f"\n📊 Обновление рейтингов для матча #{match.id}")
    print(f"   {match.team1.name} {match.score_team1}:{match.score_team2} {match.team2.name}")
    
    with transaction.atomic():
        # Обновляем рейтинги команд
        _update_team_rating(match.team1, match)
        _update_team_rating(match.team2, match)
        
        # Обновляем рейтинги игроков на основе PlayerMatchStats
        from matches.models import PlayerMatchStats
        player_stats = PlayerMatchStats.objects.filter(match=match)
        
        print(f"   Найдено статистики игроков: {player_stats.count()}")
        
        for stat in player_stats:
            _update_player_rating_from_stats(stat.player, match, stat)
        
        # Если нет PlayerMatchStats, создаём базовые рейтинги для членов команд
        if player_stats.count() == 0:
            print(f"   ⚠️ Нет статистики игроков, обновляем только команды")
        
        # Помечаем матч как обработанный
        _processed_matches.add(match.id)
    
    print(f"✅ Рейтинги обновлены для матча #{match.id}")
    return True


def _update_team_rating(team, match):
    """
    Внутренняя функция: Обновление рейтинга одной команды.
    """
    # Получаем или создаём глобальный рейтинг
    rating, created = TeamRating.objects.get_or_create(
        team=team,
        season=None,
        defaults={'rating_points': 1500}
    )
    
    if created:
        print(f"   ✨ Создан новый рейтинг для команды {team.name}")
    
    # Получаем или создаём рейтинг сезона
    season_rating = None
    if match.tournament and match.tournament.season:
        season_rating, created = TeamRating.objects.get_or_create(
            team=team,
            season=match.tournament.season,
            defaults={'rating_points': 1500}
        )
        if created:
            print(f"   ✨ Создан рейтинг сезона для команды {team.name}")
    
    # Определяем результат
    if match.team1 == team:
        goals_for = match.score_team1
        goals_against = match.score_team2
    else:
        goals_for = match.score_team2
        goals_against = match.score_team1
    
    if goals_for > goals_against:
        result = 'win'
    elif goals_for < goals_against:
        result = 'loss'
    else:
        result = 'draw'
    
    # Обновляем статистику
    def apply_stats(r):
        r.matches_played += 1
        r.goals_scored += goals_for
        r.goals_conceded += goals_against
        r.goal_difference = r.goals_scored - r.goals_conceded
        
        if result == 'win':
            r.wins += 1
            r.points += 3
            r.rating_points += 25
        elif result == 'draw':
            r.draws += 1
            r.points += 1
            r.rating_points += 5
        else:
            r.losses += 1
            r.rating_points = max(0, r.rating_points - 20)
        
        r.save()
    
    apply_stats(rating)
    if season_rating:
        apply_stats(season_rating)
    
    print(f"   ✅ {team.name}: {result.upper()} | Рейтинг: {rating.rating_points}")


def _update_player_rating_from_stats(player, match, player_stats):
    """
    Внутренняя функция: Обновление рейтинга игрока на основе PlayerMatchStats.
    """
    # Получаем или создаём глобальный рейтинг
    rating, created = PlayerRating.objects.get_or_create(
        player=player,
        season=None,
        defaults={'rating_points': 1500}
    )
    
    if created:
        print(f"   ✨ Создан новый рейтинг для игрока {player.username}")
    
    # Получаем или создаём рейтинг сезона
    season_rating = None
    if match.tournament and match.tournament.season:
        season_rating, created = PlayerRating.objects.get_or_create(
            player=player,
            season=match.tournament.season,
            defaults={'rating_points': 1500}
        )
        if created:
            print(f"   ✨ Создан рейтинг сезона для игрока {player.username}")
    
    # Определяем результат для команды игрока
    player_team = player_stats.team
    
    if match.team1 == player_team:
        team_goals = match.score_team1
        opponent_goals = match.score_team2
    else:
        team_goals = match.score_team2
        opponent_goals = match.score_team1
    
    if team_goals > opponent_goals:
        result = 'win'
    elif team_goals < opponent_goals:
        result = 'loss'
    else:
        result = 'draw'
    
    # Получаем статистику игрока
    goals = player_stats.goals or 0
    assists = player_stats.assists or 0
    saves = player_stats.saves or 0
    shots = player_stats.shots or 0
    
    def apply_stats(r):
        r.matches_played += 1
        r.goals += goals
        r.assists += assists
        r.saves += saves
        r.shots += shots
        
        # Результаты матча
        if result == 'win':
            r.wins += 1
            r.rating_points += 20
        elif result == 'draw':
            r.draws += 1
            r.rating_points += 5
        else:
            r.losses += 1
            r.rating_points = max(0, r.rating_points - 15)
        
        # Бонусы за достижения
        r.rating_points += goals * 10
        r.rating_points += assists * 5
        r.rating_points += saves * 2
        
        # Точность ударов
        if r.shots > 0:
            r.shot_accuracy = (r.goals / r.shots) * 100
        
        r.save()
    
    apply_stats(rating)
    if season_rating:
        apply_stats(season_rating)
    
    print(f"   ✅ {player.username}: {result.upper()} | "
          f"Рейтинг: {rating.rating_points} | "
          f"Голы: {goals} | Передачи: {assists}")


def update_single_player_rating(player_stats):
    """
    Обновляет рейтинг одного игрока при изменении его статистики.
    ОТКЛЮЧЕНО: теперь всё обновляется через update_ratings_for_match
    """
    # ОТКЛЮЧЕНО для предотвращения дублирования
    # Рейтинги обновляются централизованно через update_ratings_for_match
    pass


# ============================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С САНКЦИЯМИ
# ============================================================

def apply_sanction_to_ratings(sanction):
    """
    Применяет санкцию к рейтингам команды/игрока.
    Вызывается при создании санкции.
    """
    print(f"\n⚖️ Применение санкции #{sanction.id}")
    
    with transaction.atomic():
        # Снятие очков с команды
        if sanction.team and sanction.points_deducted > 0:
            _apply_team_sanction(sanction)
        
        # Снятие очков с игрока (если санкция персональная)
        if sanction.player and sanction.points_deducted > 0:
            _apply_player_sanction(sanction)
    
    print(f"✅ Санкция #{sanction.id} применена")


def _apply_team_sanction(sanction):
    """Применить санкцию к рейтингу команды"""
    team = sanction.team
    points_to_deduct = sanction.points_deducted
    
    # Глобальный рейтинг
    try:
        rating = TeamRating.objects.get(team=team, season=None)
        rating.points = max(0, rating.points - points_to_deduct)
        rating.rating_points = max(0, rating.rating_points - points_to_deduct * 5)  # Штраф к рейтингу
        rating.save()
        print(f"   📉 {team.name}: -${points_to_deduct} очков (глобально)")
    except TeamRating.DoesNotExist:
        print(f"   ⚠️ Рейтинг команды {team.name} не найден")
    
    # Рейтинг сезона турнира
    if sanction.tournament and sanction.tournament.season:
        try:
            season_rating = TeamRating.objects.get(
                team=team, 
                season=sanction.tournament.season
            )
            season_rating.points = max(0, season_rating.points - points_to_deduct)
            season_rating.rating_points = max(0, season_rating.rating_points - points_to_deduct * 5)
            season_rating.save()
            print(f"   📉 {team.name}: -{points_to_deduct} очков (сезон {sanction.tournament.season})")
        except TeamRating.DoesNotExist:
            print(f"   ⚠️ Сезонный рейтинг команды {team.name} не найден")


def _apply_player_sanction(sanction):
    """Применить санкцию к рейтингу игрока"""
    player = sanction.player
    points_to_deduct = sanction.points_deducted
    
    # Глобальный рейтинг
    try:
        rating = PlayerRating.objects.get(player=player, season=None)
        rating.rating_points = max(0, rating.rating_points - points_to_deduct * 10)  # Штраф
        rating.save()
        print(f"   📉 {player.username}: -{points_to_deduct * 10} рейтинга (глобально)")
    except PlayerRating.DoesNotExist:
        print(f"   ⚠️ Рейтинг игрока {player.username} не найден")
    
    # Рейтинг сезона
    if sanction.tournament and sanction.tournament.season:
        try:
            season_rating = PlayerRating.objects.get(
                player=player,
                season=sanction.tournament.season
            )
            season_rating.rating_points = max(0, season_rating.rating_points - points_to_deduct * 10)
            season_rating.save()
            print(f"   📉 {player.username}: -{points_to_deduct * 10} рейтинга (сезон)")
        except PlayerRating.DoesNotExist:
            print(f"   ⚠️ Сезонный рейтинг игрока {player.username} не найден")


def revoke_sanction_from_ratings(sanction):
    """
    Отменяет санкцию (возвращает очки).
    Вызывается при отмене/удалении санкции.
    """
    print(f"\n🔄 Отмена санкции #{sanction.id}")
    
    with transaction.atomic():
        # Возврат очков команде
        if sanction.team and sanction.points_deducted > 0:
            _revoke_team_sanction(sanction)
        
        # Возврат очков игроку
        if sanction.player and sanction.points_deducted > 0:
            _revoke_player_sanction(sanction)
    
    print(f"✅ Санкция #{sanction.id} отменена")


def _revoke_team_sanction(sanction):
    """Вернуть очки команде"""
    team = sanction.team
    points_to_return = sanction.points_deducted
    
    try:
        rating = TeamRating.objects.get(team=team, season=None)
        rating.points += points_to_return
        rating.rating_points += points_to_return * 5
        rating.save()
        print(f"   📈 {team.name}: +{points_to_return} очков возвращено")
    except TeamRating.DoesNotExist:
        pass
    
    if sanction.tournament and sanction.tournament.season:
        try:
            season_rating = TeamRating.objects.get(
                team=team,
                season=sanction.tournament.season
            )
            season_rating.points += points_to_return
            season_rating.rating_points += points_to_return * 5
            season_rating.save()
        except TeamRating.DoesNotExist:
            pass


def _revoke_player_sanction(sanction):
    """Вернуть очки игроку"""
    player = sanction.player
    points_to_return = sanction.points_deducted
    
    try:
        rating = PlayerRating.objects.get(player=player, season=None)
        rating.rating_points += points_to_return * 10
        rating.save()
        print(f"   📈 {player.username}: +{points_to_return * 10} рейтинга возвращено")
    except PlayerRating.DoesNotExist:
        pass
    
    if sanction.tournament and sanction.tournament.season:
        try:
            season_rating = PlayerRating.objects.get(
                player=player,
                season=sanction.tournament.season
            )
            season_rating.rating_points += points_to_return * 10
            season_rating.save()
        except PlayerRating.DoesNotExist:
            pass


# ============================================================
# LEGACY ФУНКЦИИ (для обратной совместимости)
# ============================================================

def update_ratings(match):
    """
    Legacy функция для обратной совместимости.
    Используйте update_ratings_for_match вместо неё.
    """
    return update_ratings_for_match(match)


def update_team_rating(team, match):
    """Legacy wrapper"""
    return _update_team_rating(team, match)


def update_player_rating(player, match, player_stats):
    """Legacy wrapper"""
    return _update_player_rating_from_stats(player, match, player_stats)


# ============================================================
# ПЕРЕСЧЁТ РЕЙТИНГОВ
# ============================================================

def recalculate_all_ratings():
    """
    Полный пересчёт всех рейтингов с нуля.
    Используется для исправления сбоев.
    """
    from matches.models import Match
    from accounts.models import User
    from teams.models import Team
    from tournaments.models import Sanction
    
    global _processed_matches
    _processed_matches.clear()  # Очищаем кэш обработанных матчей
    
    print("=" * 60)
    print("ПОЛНЫЙ ПЕРЕСЧЕТ РЕЙТИНГОВ")
    print("=" * 60)
    
    # Сбрасываем все рейтинги до начальных значений
    print("\n🔄 Сброс рейтингов до начальных значений...")
    
    PlayerRating.objects.update(
        matches_played=0, wins=0, losses=0, draws=0,
        goals=0, assists=0, saves=0, shots=0,
        shot_accuracy=0, rating_points=1500
    )
    
    TeamRating.objects.update(
        matches_played=0, wins=0, losses=0, draws=0,
        goals_scored=0, goals_conceded=0, goal_difference=0,
        points=0, rating_points=1500
    )
    
    print("   ✅ Рейтинги сброшены")
    
    # Создаём рейтинги для тех, у кого их нет
    print("\n📝 Проверка и создание недостающих рейтингов...")
    
    players = User.objects.filter(role__in=['player', 'captain'])
    for player in players:
        PlayerRating.objects.get_or_create(
            player=player,
            season=None,
            defaults={'rating_points': 1500}
        )
    
    teams = Team.objects.filter(is_active=True)
    for team in teams:
        TeamRating.objects.get_or_create(
            team=team,
            season=None,
            defaults={'rating_points': 1500}
        )
    
    print(f"   ✅ Игроков: {players.count()}, Команд: {teams.count()}")
    
    # Обновляем рейтинги на основе завершённых матчей
    print("\n📈 Обновление рейтингов на основе матчей...")
    finished_matches = Match.objects.filter(status='finished').order_by('scheduled_time')
    
    success = 0
    errors = 0
    
    for match in finished_matches:
        try:
            # Используем внутренние функции напрямую, чтобы избежать сигналов
            with transaction.atomic():
                _update_team_rating(match.team1, match)
                _update_team_rating(match.team2, match)
                
                from matches.models import PlayerMatchStats
                for stat in PlayerMatchStats.objects.filter(match=match):
                    _update_player_rating_from_stats(stat.player, match, stat)
            
            success += 1
        except Exception as e:
            print(f"   ❌ Ошибка для матча #{match.id}: {e}")
            errors += 1
    
    print(f"\n✅ Успешно обработано: {success} матчей")
    if errors > 0:
        print(f"❌ Ошибок: {errors}")
    
    # Применяем активные санкции
    print("\n⚖️ Применение активных санкций...")
    active_sanctions = Sanction.objects.filter(status='active')
    sanctions_applied = 0
    
    for sanction in active_sanctions:
        try:
            if sanction.team and sanction.points_deducted > 0:
                _apply_team_sanction(sanction)
                sanctions_applied += 1
            if sanction.player and sanction.points_deducted > 0:
                _apply_player_sanction(sanction)
                sanctions_applied += 1
        except Exception as e:
            print(f"   ❌ Ошибка при применении санкции #{sanction.id}: {e}")
    
    print(f"   ✅ Применено санкций: {sanctions_applied}")
    
    print("\n" + "=" * 60)
    print("ПЕРЕСЧЕТ ЗАВЕРШЕН!")
    print("=" * 60)


def init_missing_ratings():
    """
    Создаёт рейтинги только для тех игроков и команд, 
    у которых их ещё нет. Не сбрасывает существующие.
    """
    from accounts.models import User
    from teams.models import Team
    
    print("📝 Создание недостающих рейтингов...")
    
    players_created = 0
    players = User.objects.filter(role__in=['player', 'captain'])
    for player in players:
        _, created = PlayerRating.objects.get_or_create(
            player=player,
            season=None,
            defaults={'rating_points': 1500}
        )
        if created:
            players_created += 1
    
    teams_created = 0
    teams = Team.objects.filter(is_active=True)
    for team in teams:
        _, created = TeamRating.objects.get_or_create(
            team=team,
            season=None,
            defaults={'rating_points': 1500}
        )
        if created:
            teams_created += 1
    
    print(f"✅ Создано: {players_created} рейтингов игроков, {teams_created} рейтингов команд")
    return players_created, teams_created


def clear_processed_matches_cache():
    """Очищает кэш обработанных матчей"""
    global _processed_matches
    _processed_matches.clear()
    print("🗑️ Кэш обработанных матчей очищен")