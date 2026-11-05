from django import forms
from django.contrib import admin, messages
from django.utils.html import format_html

from apps.accounts.models import User

from .models import Ticket, TicketComment

STATUS_COLORS = {
    "new": "#2563eb", "in_progress": "#d97706", "waiting": "#7c3aed",
    "resolved": "#059669", "closed": "#6b7280",
}
PRIORITY_COLORS = {"low": "#6b7280", "medium": "#2563eb", "high": "#ea580c", "critical": "#dc2626"}


def badge(color, text):
    return format_html(
        '<span style="padding:2px 8px;border-radius:10px;background:{};color:#fff;'
        'font-size:11px;white-space:nowrap;">{}</span>', color, text)


class TicketAdminForm(forms.ModelForm):
    """Проверка жизненного цикла и обязательного решения при ручном изменении статуса."""

    class Meta:
        model = Ticket
        fields = "__all__"

    def clean(self):
        data = super().clean()
        ticket = self.instance
        new_status = data.get("status")
        if ticket.pk and new_status and new_status != ticket.status and not ticket.can_change_to(new_status):
            self.add_error("status", f"Недопустимый переход: «{ticket.get_status_display()}» → "
                                     f"«{Ticket.status_label(new_status)}»")
        if new_status in Ticket.FINAL_STATUSES and not data.get("resolution"):
            self.add_error("resolution", "Опишите решение (обязательно для статусов «Решено» и «Закрыто»).")
        return data


class TicketHistoryInline(admin.TabularInline):
    model = TicketComment
    fields = ("created_at", "kind", "author", "text")
    readonly_fields = fields
    extra = 0
    can_delete = False
    verbose_name = "Запись"
    verbose_name_plural = "История обращения"

    def has_add_permission(self, request, obj=None):
        return False


class NewCommentInline(admin.StackedInline):
    model = TicketComment
    fields = ("text",)
    extra = 1
    can_delete = False
    verbose_name = "Комментарий"
    verbose_name_plural = "Добавить комментарий"

    def get_queryset(self, request):
        return super().get_queryset(request).none()   # показываем только пустую форму


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    form = TicketAdminForm
    list_display = ("number", "subject", "applicant", "category", "priority_badge",
                    "status_badge", "executor", "deadline", "overdue")
    list_display_links = ("number", "subject")
    list_filter = ("status", "priority", "category", "executor", "channel", "created_at")
    search_fields = ("subject", "description", "applicant__full_name")
    date_hierarchy = "created_at"
    autocomplete_fields = ("applicant", "category", "executor")
    list_select_related = ("applicant", "category", "executor")
    list_per_page = 25
    readonly_fields = ("number", "created_by", "created_at", "updated_at", "resolved_at", "closed_at")
    fieldsets = (
        ("Обращение", {"fields": ("number", "subject", "description", "applicant",
                                  "category", "priority", "channel")}),
        ("Исполнение", {"fields": ("status", "executor", "deadline", "resolution")}),
        ("Служебная информация", {"classes": ("collapse",),
                                  "fields": ("created_by", "created_at", "updated_at",
                                             "resolved_at", "closed_at")}),
    )
    inlines = (TicketHistoryInline, NewCommentInline)
    actions = ("action_take", "action_resolve", "action_close")

    # --- колонки списка ---
    @admin.display(description="Номер", ordering="id")
    def number(self, obj):
        return obj.code

    @admin.display(description="Статус", ordering="status")
    def status_badge(self, obj):
        return badge(STATUS_COLORS.get(obj.status, "#6b7280"), obj.get_status_display())

    @admin.display(description="Приоритет", ordering="priority")
    def priority_badge(self, obj):
        return badge(PRIORITY_COLORS.get(obj.priority, "#6b7280"), obj.get_priority_display())

    @admin.display(description="Просрочено", boolean=True)
    def overdue(self, obj):
        return obj.is_overdue

    # --- исполнитель видит в админке только свои обращения ---
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if not user.is_superuser and user.role == User.Role.EXECUTOR:
            return qs.filter(executor=user)
        return qs

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj._changed_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for inst in instances:
            if isinstance(inst, TicketComment) and not inst.pk:
                inst.author = request.user
                inst.kind = TicketComment.Kind.COMMENT
            inst.save()
        formset.save_m2m()

    # --- массовые действия ---
    def _bulk_status(self, request, queryset, new_status, resolution=""):
        done, skipped = 0, 0
        for ticket in queryset:
            if not ticket.can_change_to(new_status):
                skipped += 1
                continue
            if new_status == Ticket.Status.IN_PROGRESS and ticket.executor_id is None \
                    and request.user.role == User.Role.EXECUTOR:
                ticket.executor = request.user
            ticket.change_status(new_status, user=request.user,
                                 resolution="" if ticket.resolution else resolution)
            done += 1
        level = messages.SUCCESS if done else messages.WARNING
        self.message_user(request, f"Изменено обращений: {done}. "
                                   f"Пропущено (недопустимый переход): {skipped}.", level)

    @admin.action(description="Взять в работу")
    def action_take(self, request, queryset):
        self._bulk_status(request, queryset, Ticket.Status.IN_PROGRESS)

    @admin.action(description="Отметить как решённые")
    def action_resolve(self, request, queryset):
        self._bulk_status(request, queryset, Ticket.Status.RESOLVED,
                          resolution="Решено (отмечено в панели управления)")

    @admin.action(description="Закрыть обращения")
    def action_close(self, request, queryset):
        self._bulk_status(request, queryset, Ticket.Status.CLOSED,
                          resolution="Закрыто (отмечено в панели управления)")


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ("created_at", "ticket", "kind", "author", "short_text")
    list_filter = ("kind", "created_at")
    search_fields = ("text", "ticket__subject")
    list_select_related = ("ticket", "author")

    @admin.display(description="Текст")
    def short_text(self, obj):
        return obj.text[:80]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
