from django.db.models import Count, ProtectedError
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.accounts.permissions import IsDispatcherOrReadOnly

from .models import Applicant
from .serializers import ApplicantSerializer


class ApplicantViewSet(viewsets.ModelViewSet):
    """CRUD заявителей. Поиск: ?search=Иванов, фильтр: ?department=Бухгалтерия"""
    serializer_class = ApplicantSerializer
    permission_classes = (IsDispatcherOrReadOnly,)
    filterset_fields = ("department",)
    search_fields = ("full_name", "department", "phone", "email")
    ordering_fields = ("full_name", "created_at")

    def get_queryset(self):
        return Applicant.objects.annotate(tickets_count=Count("tickets")).order_by("full_name")

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response({"detail": "Нельзя удалить заявителя, у которого есть обращения."},
                            status=status.HTTP_409_CONFLICT)
