from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "full_name", "role", "role_display",
                  "position", "email", "phone", "is_active")


class LoginSerializer(TokenObtainPairSerializer):
    """Выдаёт пару JWT-токенов и добавляет в ответ данные сотрудника."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role            # роль попадает внутрь токена
        token["full_name"] = user.full_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
