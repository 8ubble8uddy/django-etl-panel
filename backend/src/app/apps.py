from django.apps import AppConfig


class AppConfig(AppConfig):  # type: ignore[no-redef]
    """Класс для настройки ETL приложения."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        """Прикрепляем сигналы при инициализации приложения."""
        from app import signals
