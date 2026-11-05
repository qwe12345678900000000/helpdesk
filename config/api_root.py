"""Корневая страница /api/ — список всех эндпоинтов системы."""
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse


@extend_schema(exclude=True)
@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request, format=None):
    def url(name):
        return reverse(name, request=request)

    return Response({
        "auth_login": url("auth-login"),
        "auth_refresh": url("auth-refresh"),
        "auth_me": url("auth-me"),
        "users": url("user-list"),
        "categories": url("category-list"),
        "applicants": url("applicant-list"),
        "tickets": url("ticket-list"),
        "reports_kpi": url("reports-kpi"),
        "reports_by_category": url("reports-by-category"),
        "reports_by_executor": url("reports-by-executor"),
        "swagger": url("swagger-ui"),
    })
