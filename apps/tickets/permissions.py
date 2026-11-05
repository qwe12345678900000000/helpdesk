from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.models import User
from apps.accounts.permissions import has_role

R = User.Role


class TicketPermission(BasePermission):
    """
    Диспетчер/администратор — регистрируют и редактируют обращения, назначают исполнителя.
    Исполнитель — видит только свои обращения, меняет их статус, пишет комментарии.
    Руководитель — только просмотр.
    """
    message = "Недостаточно прав для этого действия."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if view.action in ("create", "update", "partial_update", "assign"):
            return has_role(user, R.ADMIN, R.DISPATCHER)
        if view.action == "destroy":
            return has_role(user, R.ADMIN)
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if has_role(user, R.ADMIN, R.DISPATCHER):
            return True
        is_own = obj.executor_id == user.id
        if view.action == "change_status":
            return is_own
        if view.action == "comments":
            return is_own or (request.method in SAFE_METHODS and has_role(user, R.HEAD))
        if request.method in SAFE_METHODS:
            return is_own or has_role(user, R.HEAD)
        return False
