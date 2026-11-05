"""Расчёт показателей (KPI) службы поддержки. Результаты кэшируются в Redis."""
import logging

from django.core.cache import cache
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from django.utils import timezone

from apps.accounts.models import User
from apps.catalog.models import Category
from apps.tickets.models import Ticket

from .cache_keys import BY_CATEGORY_KEY, BY_EXECUTOR_KEY, KPI_KEY

logger = logging.getLogger(__name__)
CACHE_TIMEOUT = 300   # 5 минут; при изменении обращения кэш сбрасывается сигналом


def cached(key, builder):
    """Возвращает (данные, из_кэша). При недоступном Redis считает данные напрямую."""
    try:
        data = cache.get(key)
        if data is not None:
            return data, True
    except Exception as exc:
        logger.warning("Кэш недоступен: %s", exc)
    data = builder()
    try:
        cache.set(key, data, CACHE_TIMEOUT)
    except Exception as exc:
        logger.warning("Не удалось записать кэш: %s", exc)
    return data, False


def build_kpi():
    now = timezone.now()
    qs = Ticket.objects.all()
    open_q = Q(status__in=Ticket.OPEN_STATUSES)
    agg = qs.aggregate(
        total=Count("id"),
        open=Count("id", filter=open_q),
        overdue=Count("id", filter=open_q & Q(deadline__lt=now)),
        resolved=Count("id", filter=Q(resolved_at__isnull=False)),
        resolved_in_time=Count("id", filter=Q(resolved_at__isnull=False, resolved_at__lte=F("deadline"))),
        created_today=Count("id", filter=Q(created_at__date=timezone.localdate())),
    )
    duration = ExpressionWrapper(F("resolved_at") - F("created_at"), output_field=DurationField())
    avg = qs.filter(resolved_at__isnull=False).aggregate(v=Avg(duration))["v"]

    status_counts = {row["status"]: row["c"] for row in
                     qs.values("status").annotate(c=Count("id")).order_by()}
    priority_counts = {row["priority"]: row["c"] for row in
                       qs.values("priority").annotate(c=Count("id")).order_by()}

    return {
        "total": agg["total"],
        "open": agg["open"],
        "overdue": agg["overdue"],
        "created_today": agg["created_today"],
        "resolved": agg["resolved"],
        "avg_resolution_hours": round(avg.total_seconds() / 3600, 1) if avg else 0,
        "sla_compliance_percent": (round(agg["resolved_in_time"] * 100 / agg["resolved"], 1)
                                   if agg["resolved"] else None),
        "by_status": [{"status": v, "label": label, "count": status_counts.get(v, 0)}
                      for v, label in Ticket.Status.choices],
        "by_priority": [{"priority": v, "label": label, "count": priority_counts.get(v, 0)}
                        for v, label in Ticket.Priority.choices],
        "generated_at": now.isoformat(),
    }


def build_by_category():
    now = timezone.now()
    open_q = Q(tickets__status__in=Ticket.OPEN_STATUSES)
    rows = Category.objects.annotate(
        total=Count("tickets"),
        open=Count("tickets", filter=open_q),
        overdue=Count("tickets", filter=open_q & Q(tickets__deadline__lt=now)),
    ).order_by("-total", "name")
    return [{"id": c.id, "category": c.name, "total": c.total, "open": c.open, "overdue": c.overdue}
            for c in rows]


def build_by_executor():
    now = timezone.now()
    open_q = Q(assigned_tickets__status__in=Ticket.OPEN_STATUSES)
    rows = User.objects.filter(role=User.Role.EXECUTOR, is_active=True).annotate(
        total=Count("assigned_tickets"),
        open=Count("assigned_tickets", filter=open_q),
        overdue=Count("assigned_tickets", filter=open_q & Q(assigned_tickets__deadline__lt=now)),
        resolved=Count("assigned_tickets", filter=Q(assigned_tickets__resolved_at__isnull=False)),
    ).order_by("-total", "full_name")
    return [{"id": u.id, "executor": str(u), "total": u.total, "open": u.open,
             "overdue": u.overdue, "resolved": u.resolved} for u in rows]


def get_kpi():
    return cached(KPI_KEY, build_kpi)


def get_by_category():
    return cached(BY_CATEGORY_KEY, build_by_category)


def get_by_executor():
    return cached(BY_EXECUTOR_KEY, build_by_executor)
