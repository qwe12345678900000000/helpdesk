import django_filters
from django.db.models import Q
from django.utils import timezone

from .models import Ticket


class TicketFilter(django_filters.FilterSet):
    overdue = django_filters.BooleanFilter(method="filter_overdue", label="Просрочено")
    created_from = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte",
                                             label="Создано с")
    created_to = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte",
                                           label="Создано по")

    class Meta:
        model = Ticket
        fields = ("status", "priority", "category", "executor", "applicant", "channel")

    def filter_overdue(self, queryset, name, value):
        cond = Q(status__in=Ticket.OPEN_STATUSES, deadline__lt=timezone.now())
        return queryset.filter(cond) if value else queryset.exclude(cond)
