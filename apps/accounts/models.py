from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Сотрудник службы поддержки (кастомная модель пользователя)."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Администратор"
        DISPATCHER = "dispatcher", "Диспетчер"
        EXECUTOR = "executor", "Исполнитель"
        HEAD = "head", "Руководитель"

    full_name = models.CharField("ФИО", max_length=255, blank=True)
    role = models.CharField("Роль", max_length=32, choices=Role.choices, default=Role.EXECUTOR)
    position = models.CharField("Должность", max_length=255, blank=True)
    phone = models.CharField("Телефон", max_length=32, blank=True)

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ("full_name", "username")

    def save(self, *args, **kwargs):
        # суперпользователь всегда имеет роль «Администратор»
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    def has_role(self, *roles):
        return self.is_superuser or self.role in roles

    def __str__(self):
        return self.full_name or self.username
