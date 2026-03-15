# ratings/apps.py

from django.apps import AppConfig


class RatingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ratings'
    verbose_name = 'Рейтинги'

    def ready(self):
        # Импортируем сигналы при загрузке приложения
        import ratings.signals  # noqa: F401