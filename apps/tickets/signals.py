"""Интеграция Обращения → Отчёты: при любом изменении обращения сбрасываем кэш KPI."""
import logging

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.reports.cache_keys import ALL_KEYS

from .models import Ticket

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Ticket)
@receiver(post_delete, sender=Ticket)
def invalidate_reports_cache(sender, **kwargs):
    try:
        cache.delete_many(ALL_KEYS)
    except Exception as exc:  # Redis недоступен — работа системы не должна останавливаться
        logger.warning("Не удалось сбросить кэш отчётов: %s", exc)
