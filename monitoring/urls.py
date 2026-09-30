from django.urls import path

from .views import alerts, dashboard, devices, readings, zones

app_name = "monitoring"

urlpatterns = [
    path("", dashboard.DashboardView.as_view(), name="dashboard"),
    path("resumen-zonas/", zones.ZoneSummaryView.as_view(), name="zone_summary"),
    path("zonas/", zones.ZoneListView.as_view(), name="zone_list"),
    path("zonas/nueva/", zones.ZoneCreateView.as_view(), name="zone_create"),
    path("zonas/<int:pk>/", zones.ZoneDetailView.as_view(), name="zone_detail"),
    path("zonas/<int:pk>/editar/", zones.ZoneUpdateView.as_view(), name="zone_update"),
    path("zonas/<int:pk>/eliminar/", zones.ZoneDeleteView.as_view(), name="zone_delete"),
    path("dispositivos/", devices.DeviceListView.as_view(), name="device_list"),
    path("dispositivos/nuevo/", devices.DeviceCreateView.as_view(), name="device_create"),
    path("dispositivos/<int:pk>/", devices.DeviceDetailView.as_view(), name="device_detail"),
    path("dispositivos/<int:pk>/editar/", devices.DeviceUpdateView.as_view(), name="device_update"),
    path("dispositivos/<int:pk>/eliminar/", devices.DeviceDeleteView.as_view(), name="device_delete"),
    path("lecturas/", readings.ReadingListView.as_view(), name="reading_list"),
    path("lecturas/exportar/", readings.ReadingExportView.as_view(), name="reading_export"),
    path("lecturas/nueva/", readings.ReadingCreateView.as_view(), name="reading_create"),
    path("lecturas/<int:pk>/", readings.ReadingDetailView.as_view(), name="reading_detail"),
    path("lecturas/<int:pk>/editar/", readings.ReadingUpdateView.as_view(), name="reading_update"),
    path("lecturas/<int:pk>/eliminar/", readings.ReadingDeleteView.as_view(), name="reading_delete"),
    path("alertas/", alerts.AlertListView.as_view(), name="alert_list"),
    path("alertas/nueva/", alerts.AlertCreateView.as_view(), name="alert_create"),
    path("alertas/<int:pk>/", alerts.AlertDetailView.as_view(), name="alert_detail"),
    path("alertas/<int:pk>/editar/", alerts.AlertUpdateView.as_view(), name="alert_update"),
    path("alertas/<int:pk>/eliminar/", alerts.AlertDeleteView.as_view(), name="alert_delete"),
]
