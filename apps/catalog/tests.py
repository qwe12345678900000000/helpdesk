from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import Category


class CategoryApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user("adm", password="Pass12345!", role=User.Role.ADMIN)
        self.executor = User.objects.create_user("ex", password="Pass12345!", role=User.Role.EXECUTOR)
        Category.objects.create(name="Сеть и интернет")

    def test_list_for_any_employee(self):
        self.client.force_authenticate(self.executor)
        r = self.client.get(reverse("category-list"))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["count"], 1)

    def test_executor_cannot_create(self):
        self.client.force_authenticate(self.executor)
        r = self.client.post(reverse("category-list"), {"name": "Печать"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create(self):
        self.client.force_authenticate(self.admin)
        r = self.client.post(reverse("category-list"),
                             {"name": "Печать", "default_executor": self.executor.id}, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_name_is_unique(self):
        self.client.force_authenticate(self.admin)
        r = self.client.post(reverse("category-list"), {"name": "Сеть и интернет"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
