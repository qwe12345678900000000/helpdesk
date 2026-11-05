"""Корневые URL-маршруты: админка, API, Swagger, дашборд."""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import SimpleRouter

from apps.accounts.views import UserViewSet
from apps.applicants.views import ApplicantViewSet
from apps.catalog.views import CategoryViewSet
from apps.reports.views import dashboard
from apps.tickets.views import TicketViewSet

from .api_root import api_root

admin.site.site_header = "Система регистрации обращений"
admin.site.site_title = "HelpDesk"
admin.site.index_title = "Панель управления"
admin.site.site_url = "/dashboard/"          # ссылка «Открыть сайт» ведёт на дашборд

router = SimpleRouter()
router.register("users", UserViewSet, basename="user")
router.register("categories", CategoryViewSet, basename="category")
router.register("applicants", ApplicantViewSet, basename="applicant")
router.register("tickets", TicketViewSet, basename="ticket")

urlpatterns = [
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
    path("admin/", admin.site.urls),
    path("dashboard/", dashboard, name="dashboard"),
    path("api/", api_root, name="api-root"),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/reports/", include("apps.reports.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/", include(router.urls)),
]
