# ratings/signals.py - ИСПРАВЛЕННАЯ ВЕРСИЯ С ПОДДЕРЖКОЙ САНКЦИЙ

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.conf import settings


# ============================================================
# АВТОМАТИЧЕСКОЕ СОЗДАНИЕ РЕЙТИНГОВ ДЛЯ НОВЫХ ИГРОКОВ/КОМАНД
# ============================================================

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_player_rating_on_user_save(sender, instance, created, **kwargs):
    """
    Автоматически создаёт рейтинг для нового игрока.
    """
    from .models import PlayerRating
    
    # Создаём рейтинг только для игроков и капитанов
    if instance.role in ['player', 'captain']:
        PlayerRating.objects.get_or_create(
            player=instance,
            season=None,
            defaults={'rating_points': 1500}
        )


@receiver(post_save, sender='teams.Team')
def create_team_rating_on_team_save(sender, instance, created, **kwargs):
    """
    Автоматически создаёт рейтинг для новой команды.
    """
    from .models import TeamRating
    
    # Создаём рейтинг только для активных команд
    if instance.is_active:
        TeamRating.objects.get_or_create(
            team=instance,
            season=None,
            defaults={'rating_points': 1500}
        )


# ============================================================
# АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ РЕЙТИНГОВ ПОСЛЕ МАТЧА
# ============================================================

# Храним предыдущий статус матча
_match_previous_status = {}


@receiver(pre_save, sender='matches.Match')
def store_previous_match_status(sender, instance, **kwargs):
    """
    Сохраняем предыдущий статус матча перед сохранением.
    """
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _match_previous_status[instance.pk] = old_instance.status
        except sender.DoesNotExist:
            _match_previous_status[instance.pk] = None
    else:
        _match_previous_status[instance.pk] = None


@receiver(post_save, sender='matches.Match')
def update_ratings_on_match_finish(sender, instance, created, **kwargs):
    """
    Автоматически обновляет рейтинги когда матч завершается.
    """
    from .utils import update_ratings_for_match
    
    previous_status = _match_previous_status.get(instance.pk)
    
    # Обновляем рейтинги только если:
    # 1. Матч только что стал finished (статус изменился на finished)
    # 2. Или это новый матч со статусом finished
    if instance.status == 'finished':
        if previous_status != 'finished' or created:
            print(f"🔄 Сигнал: Матч #{instance.id} завершён, обновляем рейтинги...")
            try:
                update_ratings_for_match(instance)
                print(f"✅ Рейтинги обновлены для матча #{instance.id}")
            except Exception as e:
                print(f"❌ Ошибка обновления рейтингов: {e}")
    
    # Очищаем кэш
    if instance.pk in _match_previous_status:
        del _match_previous_status[instance.pk]


# ============================================================
# СИГНАЛ ДЛЯ PlayerMatchStats ОТКЛЮЧЕН
# ============================================================
# ВАЖНО: Сигнал для PlayerMatchStats удалён, чтобы избежать дублирования.
# Все рейтинги обновляются централизованно через update_ratings_for_match
# когда матч завершается.

# @receiver(post_save, sender='matches.PlayerMatchStats')
# def update_player_stats_on_save(sender, instance, created, **kwargs):
#     """
#     ОТКЛЮЧЕНО: Вызывало дублирование рейтингов.
#     """
#     pass


# ============================================================
# АВТОМАТИЧЕСКОЕ ПРИМЕНЕНИЕ САНКЦИЙ
# ============================================================

@receiver(post_save, sender='tournaments.Sanction')
def apply_sanction_on_create(sender, instance, created, **kwargs):
    """
    Автоматически применяет санкцию к рейтингам при создании.
    """
    from .utils import apply_sanction_to_ratings
    
    # Применяем только при создании новой активной санкции
    if created and instance.status == 'active':
        print(f"🔄 Сигнал: Новая санкция #{instance.id}, применяем к рейтингам...")
        try:
            apply_sanction_to_ratings(instance)
            print(f"✅ Санкция #{instance.id} применена")
        except Exception as e:
            print(f"❌ Ошибка применения санкции: {e}")


# Храним предыдущий статус санкции
_sanction_previous_status = {}


@receiver(pre_save, sender='tournaments.Sanction')
def store_previous_sanction_status(sender, instance, **kwargs):
    """
    Сохраняем предыдущий статус санкции перед сохранением.
    """
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _sanction_previous_status[instance.pk] = old_instance.status
        except sender.DoesNotExist:
            _sanction_previous_status[instance.pk] = None
    else:
        _sanction_previous_status[instance.pk] = None


@receiver(post_save, sender='tournaments.Sanction')
def handle_sanction_status_change(sender, instance, created, **kwargs):
    """
    Обрабатывает изменение статуса санкции (отмена/восстановление).
    """
    if created:
        # Новые санкции обрабатываются в apply_sanction_on_create
        return
    
    from .utils import apply_sanction_to_ratings, revoke_sanction_from_ratings
    
    previous_status = _sanction_previous_status.get(instance.pk)
    current_status = instance.status
    
    # Санкция была отменена
    if previous_status == 'active' and current_status in ['cancelled', 'expired']:
        print(f"🔄 Сигнал: Санкция #{instance.id} отменена, возвращаем очки...")
        try:
            revoke_sanction_from_ratings(instance)
        except Exception as e:
            print(f"❌ Ошибка отмены санкции: {e}")
    
    # Санкция была восстановлена
    elif previous_status in ['cancelled', 'expired'] and current_status == 'active':
        print(f"🔄 Сигнал: Санкция #{instance.id} восстановлена, снимаем очки...")
        try:
            apply_sanction_to_ratings(instance)
        except Exception as e:
            print(f"❌ Ошибка восстановления санкции: {e}")
    
    # Очищаем кэш
    if instance.pk in _sanction_previous_status:
        del _sanction_previous_status[instance.pk]


@receiver(post_delete, sender='tournaments.Sanction')
def revoke_sanction_on_delete(sender, instance, **kwargs):
    """
    Автоматически отменяет санкцию при удалении.
    """
    from .utils import revoke_sanction_from_ratings
    
    # Возвращаем очки только если санкция была активной
    if instance.status == 'active':
        print(f"🔄 Сигнал: Санкция #{instance.id} удалена, возвращаем очки...")
        try:
            revoke_sanction_from_ratings(instance)
        except Exception as e:
            print(f"❌ Ошибка отмены санкции: {e}")