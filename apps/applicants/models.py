from django.db import models


class Applicant(models.Model):
    """Заявитель — сотрудник организации, который подаёт обращение."""

    full_name = models.CharField("ФИО", max_length=255)
    department = models.CharField("Подразделение", max_length=255)
    position = models.CharField("Должность", max_length=255, blank=True)
    room = models.CharField("Кабинет", max_length=32, blank=True)
    phone = models.CharField("Телефон", max_length=32, blank=True)
    email = models.EmailField("E-mail", blank=True)
    created_at = models.DateTimeField("Добавлен", auto_now_add=True)

    class Meta:
        verbose_name = "Заявитель"
        verbose_name_plural = "Заявители"
        ordering = ("full_name",)

    def __str__(self):
        return self.full_name
