from rest_framework import generics, viewsets
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .serializers import LoginSerializer, UserSerializer


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ — вход по логину и паролю, ответ: access + refresh."""
    serializer_class = LoginSerializer


class MeView(generics.RetrieveAPIView):
    """GET /api/auth/me/ — данные текущего сотрудника."""
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Список сотрудников (только чтение). Фильтр: ?role=executor"""
    queryset = User.objects.filter(is_active=True).order_by("full_name", "username")
    serializer_class = UserSerializer
    filterset_fields = ("role",)
    search_fields = ("username", "full_name", "email")
