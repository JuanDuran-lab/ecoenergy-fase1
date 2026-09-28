from django.urls import path

from . import views

app_name = "monitoring"

urlpatterns = [
    path("zonas/", views.zone_list, name="zone_list"),
    path("zonas/<int:pk>/", views.zone_detail, name="zone_detail"),
    path("resumen-zonas/", views.zone_summary, name="zone_summary"),
]
