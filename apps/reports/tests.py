from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.applicants.models import Applicant
from apps.catalog.models import Category
from apps.tickets.models import Ticket


class ReportsTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.head = User.objects.create_user("head", password="Pass12345!", role=User.Role.HEAD)
        self.ex = User.objects.create_user("ex", password="Pass12345!", role=User.Role.EXECUTOR)
        self.cat = Category.objects.create(name="Сеть", default_executor=self.ex)
        app = Applicant.objects.create(full_name="Заявитель", department="Учебная часть")
        self.t1 = Ticket.objects.create(subject="Нет сети", description="-", applicant=app, category=self.cat)
        self.t2 = Ticket.objects.create(subject="Нет почты", description="-", applicant=app, category=self.cat)

    def test_kpi_counts(self):
        self.client.force_authenticate(self.head)
        r = self.client.get(reverse("reports-kpi"))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["total"], 2)
        self.assertEqual(r.data["open"], 2)

    def test_kpi_refreshes_after_resolve(self):
        self.client.force_authenticate(self.head)
        self.assertEqual(self.client.get(reverse("reports-kpi")).data["resolved"], 0)
        self.assertTrue(self.client.get(reverse("reports-kpi")).data["from_cache"])
        self.t1.change_status("resolved", user=self.ex, resolution="Перезагружен коммутатор")
        r = self.client.get(reverse("reports-kpi"))
        self.assertFalse(r.data["from_cache"])        # кэш сброшен сигналом
        self.assertEqual(r.data["resolved"], 1)

    def test_executor_forbidden(self):
        self.client.force_authenticate(self.ex)
        self.assertEqual(self.client.get(reverse("reports-kpi")).status_code, status.HTTP_403_FORBIDDEN)

    def test_by_executor(self):
        self.client.force_authenticate(self.head)
        r = self.client.get(reverse("reports-by-executor"))
        self.assertEqual(r.data["results"][0]["total"], 2)
