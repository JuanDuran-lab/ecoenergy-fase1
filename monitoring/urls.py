from django.urls import path

from .views import dashboard, zones

app_name = "monitoring"

urlpatterns = [
    path("", dashboard.DashboardView.as_view(), name="dashboard"),
    # Zonas
    path("zonas/", zones.ZoneListView.as_view(), name="zone_list"),
    path("zonas/<int:pk>/", zones.ZoneDetailView.as_view(), name="zone_detail"),
    path("resumen-zonas/", zones.ZoneSummaryView.as_view(), name="zone_summary"),
]
