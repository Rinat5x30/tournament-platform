# ratings/management/commands/init_ratings.py

from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import User
from teams.models import Team
from ratings.models import PlayerRating, TeamRating


class Command(BaseCommand):
    help = 'Инициализация рейтингов для всех игроков и команд'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Удалить все существующие рейтинги и создать заново',
        )
        parser.add_argument(
            '--recalculate',
            action='store_true',
            help='Пересчитать рейтинги на основе завершённых матчей',
        )

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('ИНИЦИАЛИЗАЦИЯ РЕЙТИНГОВ'))
        self.stdout.write('=' * 60)

        if options['reset']:
            self.stdout.write('\n🗑️  Удаление существующих рейтингов...')
            PlayerRating.objects.all().delete()
            TeamRating.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('   Готово!'))

        with transaction.atomic():
            # Создаём рейтинги для игроков
            self.stdout.write('\n👤 Создание рейтингов игроков...')
            players = User.objects.filter(role__in=['player', 'captain'])
            players_created = 0
            players_existed = 0

            for player in players:
                rating, created = PlayerRating.objects.get_or_create(
                    player=player,
                    season=None,
                    defaults={'rating_points': 1500}
                )
                if created:
                    players_created += 1
                else:
                    players_existed += 1

            self.stdout.write(f'   ✅ Создано: {players_created}')
            self.stdout.write(f'   📋 Уже существовало: {players_existed}')

            # Создаём рейтинги для команд
            self.stdout.write('\n🏆 Создание рейтингов команд...')
            teams = Team.objects.filter(is_active=True)
            teams_created = 0
            teams_existed = 0

            for team in teams:
                rating, created = TeamRating.objects.get_or_create(
                    team=team,
                    season=None,
                    defaults={'rating_points': 1500}
                )
                if created:
                    teams_created += 1
                else:
                    teams_existed += 1

            self.stdout.write(f'   ✅ Создано: {teams_created}')
            self.stdout.write(f'   📋 Уже существовало: {teams_existed}')

        if options['recalculate']:
            self.stdout.write('\n📊 Пересчёт рейтингов на основе матчей...')
            from ratings.utils import recalculate_all_ratings
            recalculate_all_ratings()

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ ИНИЦИАЛИЗАЦИЯ ЗАВЕРШЕНА!'))
        self.stdout.write('=' * 60)

        # Итоговая статистика
        self.stdout.write(f'\n📈 Итого:')
        self.stdout.write(f'   Рейтингов игроков: {PlayerRating.objects.filter(season__isnull=True).count()}')
        self.stdout.write(f'   Рейтингов команд: {TeamRating.objects.filter(season__isnull=True).count()}')