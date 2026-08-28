from django.urls import path
from . import views


urlpatterns = [
    path("", views.lista_zonas, name="lista_zonas"),
    path("<int:zona_id>/", views.detalle_zona, name="detalle_zona"),
]