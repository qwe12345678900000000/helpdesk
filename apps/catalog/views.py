from django.db.models import Count, ProtectedError, Q
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrReadOnly

from .models import Category
from .serializers import CategorySerializer

OPEN = ("new", "in_progress", "waiting")


class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD категорий обращений. Изменять может только администратор."""
    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)
    filterset_fields = ("is_active",)
    search_fields = ("name", "description")
    ordering_fields = ("name",)

    def get_queryset(self):
        return Category.objects.select_related("default_executor").annotate(
            tickets_count=Count("tickets"),
            open_count=Count("tickets", filter=Q(tickets__status__in=OPEN)),
        ).order_by("name")

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response({"detail": "Нельзя удалить категорию: по ней есть обращения. "
                                       "Сделайте её неактивной."},
                            status=status.HTTP_409_CONFLICT)
