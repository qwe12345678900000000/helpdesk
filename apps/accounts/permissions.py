"""Права доступа на основе ролей сотрудников."""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import User

R = User.Role


def has_role(user, *roles):
    """True, если пользователь аутентифицирован и имеет одну из ролей (или суперпользователь)."""
    return bool(
        user
        and user.is_authenticated
        and (user.is_superuser or getattr(user, "role", None) in roles)
    )


class IsAdminOrReadOnly(BasePermission):
    """Читать могут все сотрудники, изменять — только администратор."""
    message = "Изменять справочник может только администратор."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.method in SAFE_METHODS or has_role(request.user, R.ADMIN)


class IsDispatcherOrReadOnly(BasePermission):
    """Читать могут все, изменять — администратор и диспетчер."""
    message = "Изменять данные может только диспетчер или администратор."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.method in SAFE_METHODS or has_role(request.user, R.ADMIN, R.DISPATCHER)


class CanViewReports(BasePermission):
    """Отчёты доступны руководителю и администратору."""
    message = "Отчёты доступны только руководителю и администратору."

    def has_permission(self, request, view):
        return has_role(request.user, R.ADMIN, R.HEAD)
