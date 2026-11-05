from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.applicants.models import Applicant
from apps.catalog.models import Category

from .models import Ticket

P = "Pass12345!"


class TicketTests(APITestCase):
    def setUp(self):
        self.disp = User.objects.create_user("disp", password=P, role=User.Role.DISPATCHER)
        self.ex1 = User.objects.create_user("ex1", password=P, role=User.Role.EXECUTOR, full_name="Исполнитель 1")
        self.ex2 = User.objects.create_user("ex2", password=P, role=User.Role.EXECUTOR, full_name="Исполнитель 2")
        self.cat = Category.objects.create(name="Оборудование", default_executor=self.ex1)
        self.cat_free = Category.objects.create(name="Прочее")
        self.applicant = Applicant.objects.create(full_name="Иванов Иван", department="Бухгалтерия")

    def create_ticket(self, category=None, priority="medium"):
        self.client.force_authenticate(self.disp)
        r = self.client.post(reverse("ticket-list"), {
            "subject": "Не печатает принтер", "description": "Принтер в каб. 205 не печатает",
            "applicant": self.applicant.id, "category": (category or self.cat).id, "priority": priority,
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.data)
        return Ticket.objects.get(pk=r.data["id"])

    def set_status(self, ticket, new_status, user=None, **extra):
        self.client.force_authenticate(user or self.disp)
        return self.client.patch(reverse("ticket-change-status", args=[ticket.id]),
                                 {"status": new_status, **extra}, format="json")

    # --- интеграция «Каталог → Обращения» ---
    def test_auto_assign_from_category(self):
        t = self.create_ticket()
        self.assertEqual(t.executor, self.ex1)
        self.assertEqual(t.status, Ticket.Status.IN_PROGRESS)

    def test_deadline_by_priority(self):
        t = self.create_ticket(priority="high")
        self.assertAlmostEqual((t.deadline - t.created_at).total_seconds(), 8 * 3600, delta=5)

    def test_without_default_executor_stays_new(self):
        t = self.create_ticket(category=self.cat_free)
        self.assertIsNone(t.executor)
        self.assertEqual(t.status, Ticket.Status.NEW)

    def test_history_written(self):
        t = self.create_ticket()
        self.assertEqual(t.comments.first().text, "Обращение зарегистрировано")

    def test_assign_moves_to_in_progress(self):
        t = self.create_ticket(category=self.cat_free)
        r = self.client.patch(reverse("ticket-assign", args=[t.id]), {"executor": self.ex2.id}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["status"], "in_progress")
        self.assertTrue(t.comments.filter(text__startswith="Назначен исполнитель").exists())

    # --- жизненный цикл ---
    def test_invalid_transition_rejected(self):
        t = self.create_ticket()                       # в работе
        r = self.set_status(t, "closed")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resolve_requires_resolution(self):
        t = self.create_ticket()
        self.assertEqual(self.set_status(t, "resolved").status_code, status.HTTP_400_BAD_REQUEST)
        r = self.set_status(t, "resolved", resolution="Заменён картридж")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(r.data["resolved_at"])

    def test_close_sets_closed_at(self):
        t = self.create_ticket()
        self.set_status(t, "resolved", resolution="Готово")
        r = self.set_status(t, "closed")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(r.data["closed_at"])

    # --- права доступа ---
    def test_executor_sees_only_own(self):
        self.create_ticket()                            # ex1
        t2 = self.create_ticket(category=self.cat_free)
        t2.executor = self.ex2
        t2.save()
        self.client.force_authenticate(self.ex2)
        r = self.client.get(reverse("ticket-list"))
        self.assertEqual(r.data["count"], 1)

    def test_executor_changes_status_of_own(self):
        t = self.create_ticket()
        r = self.set_status(t, "waiting", user=self.ex1, comment="Ждём ответа пользователя")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_executor_cannot_create(self):
        self.client.force_authenticate(self.ex1)
        r = self.client.post(reverse("ticket-list"), {"subject": "x"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_overdue_filter(self):
        t = self.create_ticket()
        Ticket.objects.filter(pk=t.pk).update(deadline=timezone.now() - timedelta(hours=1))
        r = self.client.get(reverse("ticket-list"), {"overdue": "true"})
        self.assertEqual(r.data["count"], 1)
        self.assertTrue(r.data["results"][0]["is_overdue"])
