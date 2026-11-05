from django.urls import path

from .views import ByCategoryView, ByExecutorView, KpiView

urlpatterns = [
    path("kpi/", KpiView.as_view(), name="reports-kpi"),
    path("by-category/", ByCategoryView.as_view(), name="reports-by-category"),
    path("by-executor/", ByExecutorView.as_view(), name="reports-by-executor"),
]
