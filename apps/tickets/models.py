from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class Ticket(models.Model):
    """Обращение пользователя в службу поддержки."""

    class Status(models.TextChoices):
        NEW = "new", "Новое"
        IN_PROGRESS = "in_progress", "В работе"
        WAITING = "waiting", "Ожидает ответа"
        RESOLVED = "resolved", "Решено"
        CLOSED = "closed", "Закрыто"

    class Priority(models.TextChoices):
        LOW = "low", "Низкий"
        MEDIUM = "medium", "Средний"
        HIGH = "high", "Высокий"
        CRITICAL = "critical", "Критический"

    class Channel(models.TextChoices):
        PORTAL = "portal", "Веб-портал"
        PHONE = "phone", "Телефон"
        EMAIL = "email", "Электронная почта"
        VISIT = "visit", "Личное обращение"

    # Нормативный срок решения (SLA) в часах по приоритету
    SLA_HOURS = {"low": 72, "medium": 24, "high": 8, "critical": 2}

    OPEN_STATUSES = ("new", "in_progress", "waiting")
    FINAL_STATUSES = ("resolved", "closed")

    # Допустимые переходы статусов (жизненный цикл обращения)
    TRANSITIONS = {
        "new": ("in_progress", "closed"),
        "in_progress": ("waiting", "resolved"),
        "waiting": ("in_progress", "resolved"),
        "resolved": ("closed", "in_progress"),   # in_progress — повторное открытие
        "closed": (),
    }

    subject = models.CharField("Тема", max_length=255)
    description = models.TextField("Описание проблемы")
    applicant = models.ForeignKey("applicants.Applicant", on_delete=models.PROTECT,
                                  related_name="tickets", verbose_name="Заявитель")
    category = models.ForeignKey("catalog.Category", on_delete=models.PROTECT,
                                 related_name="tickets", verbose_name="Категория")
    priority = models.CharField("Приоритет", max_length=16, choices=Priority.choices,
                                default=Priority.MEDIUM)
    channel = models.CharField("Канал поступления", max_length=16, choices=Channel.choices,
                               default=Channel.PORTAL)
    status = models.CharField("Статус", max_length=16, choices=Status.choices, default=Status.NEW)
    executor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name="assigned_tickets",
                                 limit_choices_to={"role": "executor"}, verbose_name="Исполнитель")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name="created_tickets",
                                   verbose_name="Зарегистрировал")
    resolution = models.TextField("Решение", blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now=True)
    deadline = models.DateTimeField("Срок исполнения", null=True, blank=True)
    resolved_at = models.DateTimeField("Дата решения", null=True, blank=True)
    closed_at = models.DateTimeField("Дата закрытия", null=True, blank=True)

    class Meta:
        verbose_name = "Обращение"
        verbose_name_plural = "Обращения"
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["status"]), models.Index(fields=["deadline"])]

    # --- запоминаем исходные значения, чтобы понимать, что изменилось ---
    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._original_status = instance.__dict__.get("status")
        instance._original_executor_id = instance.__dict__.get("executor_id")
        return instance

    def __str__(self):
        return f"{self.code} — {self.subject}"

    @property
    def code(self):
        return f"ОБР-{self.pk:05d}" if self.pk else "ОБР-новое"

    @property
    def sla_hours(self):
        return self.SLA_HOURS.get(str(self.priority), 24)

    @property
    def is_overdue(self):
        return bool(self.deadline and self.status in self.OPEN_STATUSES
                    and timezone.now() > self.deadline)

    def can_change_to(self, new_status):
        return new_status in self.TRANSITIONS.get(str(self.status), ())

    @classmethod
    def status_label(cls, value):
        return dict(cls.Status.choices).get(value, value)

    # --- бизнес-логика (интеграция модулей) ---
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        now = timezone.now()

        # 1. Каталог → Обращения: исполнитель по умолчанию из категории
        if is_new and self.executor_id is None and self.category_id:
            self.executor_id = self.category.default_executor_id

        # 2. Назначен исполнитель — новое обращение автоматически «В работе»
        if self.executor_id and self.status == self.Status.NEW:
            self.status = self.Status.IN_PROGRESS

        # 3. Срок исполнения по SLA приоритета
        if not self.deadline:
            self.deadline = (self.created_at or now) + timedelta(hours=self.sla_hours)

        # 4. Даты решения / закрытия
        if self.status in self.FINAL_STATUSES and not self.resolved_at:
            self.resolved_at = now
        if self.status == self.Status.CLOSED and not self.closed_at:
            self.closed_at = now
        if self.status in self.OPEN_STATUSES:          # повторное открытие
            self.resolved_at = None
            self.closed_at = None

        old_status = None if is_new else getattr(self, "_original_status", None)
        old_executor = None if is_new else getattr(self, "_original_executor_id", None)

        with transaction.atomic():
            super().save(*args, **kwargs)
            self._write_history(is_new, old_status, old_executor)

        self._original_status = self.status
        self._original_executor_id = self.executor_id

    def _write_history(self, is_new, old_status, old_executor_id):
        """5. Каждое изменение статуса/исполнителя фиксируется в истории."""
        author = getattr(self, "_changed_by", None) or self.created_by
        comment = getattr(self, "_status_comment", "")
        if is_new:
            TicketComment.objects.create(ticket=self, author=author,
                                         kind=TicketComment.Kind.SYSTEM,
                                         new_status=self.status, text="Обращение зарегистрировано")
            if self.executor_id:
                TicketComment.objects.create(ticket=self, author=author,
                                             kind=TicketComment.Kind.SYSTEM,
                                             text=f"Назначен исполнитель: {self.executor}")
            return
        if old_executor_id != self.executor_id and self.executor_id:
            TicketComment.objects.create(ticket=self, author=author,
                                         kind=TicketComment.Kind.SYSTEM,
                                         text=f"Назначен исполнитель: {self.executor}")
        if old_status is not None and old_status != self.status:
            text = (f"Статус изменён: «{self.status_label(old_status)}» → "
                    f"«{self.status_label(self.status)}»")
            if comment:
                text += f". {comment}"
            TicketComment.objects.create(ticket=self, author=author,
                                         kind=TicketComment.Kind.STATUS,
                                         old_status=old_status, new_status=self.status, text=text)
        self._status_comment = ""

    def change_status(self, new_status, user=None, comment="", resolution="", force=False):
        """Смена статуса с проверкой допустимого перехода."""
        if not force and not self.can_change_to(new_status):
            raise ValidationError(
                f"Недопустимый переход: «{self.get_status_display()}» → «{self.status_label(new_status)}»"
            )
        if resolution:
            self.resolution = resolution
        self.status = new_status
        self._changed_by = user
        self._status_comment = comment
        self.save()


class TicketComment(models.Model):
    """Запись в истории обращения: комментарий, смена статуса или системное событие."""

    class Kind(models.TextChoices):
        COMMENT = "comment", "Комментарий"
        STATUS = "status", "Смена статуса"
        SYSTEM = "system", "Системное событие"

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments",
                               verbose_name="Обращение")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                               null=True, blank=True, related_name="ticket_comments",
                               verbose_name="Автор")
    kind = models.CharField("Тип записи", max_length=16, choices=Kind.choices, default=Kind.COMMENT)
    text = models.TextField("Текст")
    old_status = models.CharField("Было", max_length=16, blank=True)
    new_status = models.CharField("Стало", max_length=16, blank=True)
    created_at = models.DateTimeField("Дата", auto_now_add=True)

    class Meta:
        verbose_name = "Запись истории"
        verbose_name_plural = "История обращений"
        ordering = ("created_at", "id")

    def __str__(self):
        return f"{self.ticket.code}: {self.text[:50]}"
