from django.core.management.base import BaseCommand
from shop.models import ServiceCategory, Service


class Command(BaseCommand):
    help = 'Создает начальные категории и услуги для магазина'

    def handle(self, *args, **kwargs):
        self.stdout.write('Создание категорий и услуг...')

        # Создание категорий
        league_category, _ = ServiceCategory.objects.get_or_create(
            slug='league-services',
            defaults={
                'name': 'Услуги лиги',
                'category_type': 'league',
                'description': 'Услуги, связанные с участием в лиге',
                'icon': '🏆',
                'order': 1,
                'is_active': True,
            }
        )
        self.stdout.write(f'✅ Категория: {league_category.name}')

        server_category, _ = ServiceCategory.objects.get_or_create(
            slug='server-services',
            defaults={
                'name': 'Услуги игрового сервера',
                'category_type': 'server',
                'description': 'Услуги, связанные с игровым сервером',
                'icon': '🎮',
                'order': 2,
                'is_active': True,
            }
        )
        self.stdout.write(f'✅ Категория: {server_category.name}')

        other_category, _ = ServiceCategory.objects.get_or_create(
            slug='other-services',
            defaults={
                'name': 'Другие услуги',
                'category_type': 'other',
                'description': 'Прочие доступные услуги',
                'icon': '⚙️',
                'order': 3,
                'is_active': True,
            }
        )
        self.stdout.write(f'✅ Категория: {other_category.name}')

        # Создание услуг для категории "Лига"
        Service.objects.get_or_create(
            slug='remove-league-ban',
            defaults={
                'category': league_category,
                'name': 'Снятие бана в лиге',
                'description': '''Эта услуга позволяет снять активный бан в лиге.

Обработка: автоматическая, мгновенно.

После оформления заказа все ваши активные баны в лиге будут сняты, и вы сможете продолжить участие в турнирах.''',
                'processing_type': 'auto',
                'auto_action': 'remove_league_ban',
                'is_active': True,
                'is_featured': True,
                'order': 1,
                'max_uses_per_user': 3,
                'cooldown_days': 30,
            }
        )
        self.stdout.write('  ✅ Услуга: Снятие бана в лиге')

        Service.objects.get_or_create(
            slug='appeal-sanction',
            defaults={
                'category': league_category,
                'name': 'Апелляция на санкцию',
                'description': '''Подайте апелляцию на полученную санкцию или дисквалификацию.

Обработка: ручная, до 24 часов.

Администратор рассмотрит ваше обращение и примет решение. Вы сможете отслеживать статус через систему тикетов.''',
                'processing_type': 'manual',
                'is_active': True,
                'order': 2,
            }
        )
        self.stdout.write('  ✅ Услуга: Апелляция на санкцию')

        # Создание услуг для категории "Сервер"
        Service.objects.get_or_create(
            slug='remove-server-ban',
            defaults={
                'category': server_category,
                'name': 'Снятие бана на сервере',
                'description': '''Снятие бана на игровом сервере.

Обработка: ручная, до 24 часов.

Администратор проверит ваш запрос и снимет бан на сервере. После выполнения вы получите уведомление.''',
                'processing_type': 'manual',
                'is_active': True,
                'is_featured': True,
                'order': 1,
                'max_uses_per_user': 2,
                'cooldown_days': 60,
            }
        )
        self.stdout.write('  ✅ Услуга: Снятие бана на сервере')

        Service.objects.get_or_create(
            slug='vip-access',
            defaults={
                'category': server_category,
                'name': 'VIP доступ на сервер',
                'description': '''Получите VIP статус на игровом сервере.

Обработка: ручная, до 24 часов.

После обработки заказа администратор выдаст вам VIP статус с расширенными возможностями.

VIP включает:
- Приоритетное подключение
- Дополнительные команды
- Эксклюзивный контент''',
                'processing_type': 'manual',
                'is_active': True,
                'is_featured': True,
                'order': 2,
            }
        )
        self.stdout.write('  ✅ Услуга: VIP доступ на сервер')

        # Создание услуг для категории "Другое"
        Service.objects.get_or_create(
            slug='change-nickname',
            defaults={
                'category': other_category,
                'name': 'Смена никнейма',
                'description': '''Измените свой игровой никнейм.

Обработка: автоматическая, мгновенно.

Новый никнейм должен быть уникальным и соответствовать правилам платформы.''',
                'processing_type': 'auto',
                'auto_action': 'change_nickname',
                'is_active': True,
                'is_featured': True,
                'order': 1,
                'max_uses_per_user': 1,
                'cooldown_days': 90,
            }
        )
        self.stdout.write('  ✅ Услуга: Смена никнейма')

        Service.objects.get_or_create(
            slug='technical-support',
            defaults={
                'category': other_category,
                'name': 'Техническая поддержка',
                'description': '''Получите помощь по техническим вопросам.

Обработка: ручная, до 24 часов.

Опишите вашу проблему, и администратор поможет её решить через систему тикетов.''',
                'processing_type': 'manual',
                'is_active': True,
                'order': 2,
            }
        )
        self.stdout.write('  ✅ Услуга: Техническая поддержка')

        self.stdout.write(self.style.SUCCESS('\n✨ Все категории и услуги успешно созданы!'))