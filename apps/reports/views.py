from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import CanViewReports
from apps.tickets.models import Ticket

from . import services


class KpiView(APIView):
    """GET /api/reports/kpi/ — ключевые показатели службы поддержки."""
    permission_classes = (CanViewReports,)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        data, from_cache = services.get_kpi()
        return Response({**data, "from_cache": from_cache})


class ByCategoryView(APIView):
    """GET /api/reports/by-category/ — обращения в разрезе категорий."""
    permission_classes = (CanViewReports,)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        data, from_cache = services.get_by_category()
        return Response({"results": data, "from_cache": from_cache})


class ByExecutorView(APIView):
    """GET /api/reports/by-executor/ — нагрузка на исполнителей."""
    permission_classes = (CanViewReports,)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        data, from_cache = services.get_by_executor()
        return Response({"results": data, "from_cache": from_cache})


@staff_member_required
def dashboard(request):
    """HTML-дашборд /dashboard/ для сотрудников (вход через /admin/)."""
    kpi, _ = services.get_kpi()
    by_category, _ = services.get_by_category()
    by_executor, _ = services.get_by_executor()
    overdue = (Ticket.objects.select_related("applicant", "executor")
               .filter(status__in=Ticket.OPEN_STATUSES, deadline__lt=timezone.now())
               .order_by("deadline")[:10])
    return render(request, "reports/dashboard.html", {
        "kpi": kpi, "by_category": by_category, "by_executor": by_executor, "overdue": overdue,
    })
