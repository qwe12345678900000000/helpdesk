from django.contrib import admin
from django.db.models import Count, Q

from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "default_executor", "is_active", "open_tickets")
    list_filter = ("is_active",)
    search_fields = ("name",)
    autocomplete_fields = ("default_executor",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _open=Count("tickets", filter=Q(tickets__status__in=("new", "in_progress", "waiting")))
        )

    @admin.display(description="Открытых обращений", ordering="_open")
    def open_tickets(self, obj):
        return obj._open
