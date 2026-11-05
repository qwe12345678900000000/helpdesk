from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.permissions import has_role

from .filters import TicketFilter
from .models import Ticket, TicketComment
from .permissions import TicketPermission
from .serializers import (TicketAssignSerializer, TicketCommentSerializer,
                          TicketSerializer, TicketStatusSerializer)

R = User.Role


class TicketViewSet(viewsets.ModelViewSet):
    """
    Обращения пользователей.
    Фильтры: ?status=new&priority=high&category=1&executor=2&overdue=true
    Поиск: ?search=принтер   Сортировка: ?ordering=deadline
    """
    serializer_class = TicketSerializer
    permission_classes = (TicketPermission,)
    filterset_class = TicketFilter
    search_fields = ("subject", "description", "applicant__full_name")
    ordering_fields = ("created_at", "deadline", "priority", "status")
    ordering = ("-created_at",)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):      # генерация схемы Swagger
            return Ticket.objects.none()
        qs = Ticket.objects.select_related("applicant", "category", "executor", "created_by")
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        if has_role(user, R.ADMIN, R.DISPATCHER, R.HEAD):
            return qs
        return qs.filter(executor=user)                    # исполнитель видит только свои

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.instance._changed_by = self.request.user
        serializer.save()

    def _ticket_response(self, ticket):
        return Response(TicketSerializer(ticket, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["patch"], url_path="status",
            serializer_class=TicketStatusSerializer)
    def change_status(self, request, pk=None):
        """PATCH /api/tickets/{id}/status/  {"status": "resolved", "resolution": "..."}"""
        ticket = self.get_object()
        ser = TicketStatusSerializer(data=request.data, context={"ticket": ticket})
        ser.is_valid(raise_exception=True)
        ticket.change_status(ser.validated_data["status"], user=request.user,
                             comment=ser.validated_data.get("comment", ""),
                             resolution=ser.validated_data.get("resolution", ""))
        return self._ticket_response(ticket)

    @action(detail=True, methods=["patch"], serializer_class=TicketAssignSerializer)
    def assign(self, request, pk=None):
        """PATCH /api/tickets/{id}/assign/  {"executor": 3}"""
        ticket = self.get_object()
        if ticket.status in Ticket.FINAL_STATUSES:
            return Response({"detail": "Нельзя назначить исполнителя решённому/закрытому обращению."},
                            status=status.HTTP_400_BAD_REQUEST)
        ser = TicketAssignSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ticket.executor = ser.validated_data["executor"]
        ticket._changed_by = request.user
        ticket.save()
        return self._ticket_response(ticket)

    @action(detail=True, methods=["get", "post"], serializer_class=TicketCommentSerializer)
    def comments(self, request, pk=None):
        """GET — история обращения, POST — добавить комментарий {"text": "..."}"""
        ticket = self.get_object()
        if request.method == "POST":
            ser = TicketCommentSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            ser.save(ticket=ticket, author=request.user, kind=TicketComment.Kind.COMMENT)
            return Response(ser.data, status=status.HTTP_201_CREATED)
        history = ticket.comments.select_related("author")
        return Response(TicketCommentSerializer(history, many=True).data)
