from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User

PASSWORD = "Pass12345!"


class AuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="disp", password=PASSWORD,
            full_name="Диспетчер Тестовый", role=User.Role.DISPATCHER,
        )

    def login(self, password=PASSWORD):
        return self.client.post(reverse("auth-login"),
                                {"username": "disp", "password": password}, format="json")

    def test_login_returns_jwt_pair(self):
        r = self.login()
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("access", r.data)
        self.assertIn("refresh", r.data)
        self.assertEqual(r.data["user"]["role"], "dispatcher")

    def test_login_wrong_password(self):
        self.assertEqual(self.login("wrong").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_requires_token(self):
        r = self.client.get(reverse("auth-me"))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_with_token(self):
        token = self.login().data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        r = self.client.get(reverse("auth-me"))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["username"], "disp")

    def test_refresh_token(self):
        refresh = self.login().data["refresh"]
        r = self.client.post(reverse("auth-refresh"), {"refresh": refresh}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("access", r.data)

    def test_superuser_gets_admin_role(self):
        su = User.objects.create_superuser("root", "root@college.local", PASSWORD)
        self.assertEqual(su.role, User.Role.ADMIN)
