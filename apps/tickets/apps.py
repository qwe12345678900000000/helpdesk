from django.apps import AppConfig


class TicketsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tickets"
    verbose_name = "Обращения"

    def ready(self):
        from . import signals  # noqa: F401  — подключаем обработчики сигналов
