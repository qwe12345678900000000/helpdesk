from django.conf import settings
from django.db import models


class Category(models.Model):
    """Категория обращения (оборудование, сеть, ПО и т.д.)."""

    name = models.CharField("Название", max_length=150, unique=True)
    description = models.TextField("Описание", blank=True)
    default_executor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,          # уволили сотрудника — категория остаётся
        null=True, blank=True,
        related_name="default_categories",
        limit_choices_to={"role": "executor"},
        verbose_name="Ответственный по умолчанию",
    )
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Категория обращений"
        verbose_name_plural = "Категории обращений"
        ordering = ("name",)

    def __str__(self):
        return self.name
