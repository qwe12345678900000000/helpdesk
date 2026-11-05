from django.contrib import admin
from django.db.models import Count

from apps.tickets.models import Ticket

from .models import Applicant


class ApplicantTicketInline(admin.TabularInline):
    model = Ticket
    fields = ("subject", "category", "status", "priority", "created_at")
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True
    verbose_name_plural = "Обращения заявителя"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ("full_name", "department", "position", "room", "phone", "email", "tickets_total")
    list_filter = ("department",)
    search_fields = ("full_name", "department", "phone", "email")
    inlines = (ApplicantTicketInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_tickets=Count("tickets"))

    @admin.display(description="Обращений", ordering="_tickets")
    def tickets_total(self, obj):
        return obj._tickets
