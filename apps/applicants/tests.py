from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import Applicant


class ApplicantApiTests(APITestCase):
    def setUp(self):
        self.disp = User.objects.create_user("disp", password="Pass12345!", role=User.Role.DISPATCHER)
        self.executor = User.objects.create_user("ex", password="Pass12345!", role=User.Role.EXECUTOR)
        Applicant.objects.create(full_name="Иванова Анна Сергеевна", department="Бухгалтерия")
        Applicant.objects.create(full_name="Орлов Павел Ильич", department="Учебная часть")

    def test_dispatcher_can_create(self):
        self.client.force_authenticate(self.disp)
        r = self.client.post(reverse("applicant-list"),
                             {"full_name": "Новиков Олег", "department": "Библиотека"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_executor_cannot_create(self):
        self.client.force_authenticate(self.executor)
        r = self.client.post(reverse("applicant-list"),
                             {"full_name": "Новиков Олег", "department": "Библиотека"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_search_by_name(self):
        self.client.force_authenticate(self.executor)
        r = self.client.get(reverse("applicant-list"), {"search": "Иванова"})
        self.assertEqual(r.data["count"], 1)
