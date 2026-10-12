"""
Rutas de la API REST, todas bajo /api/.

    POST /api/token/           obtener access y refresh (usuario y contraseña)
    POST /api/token/refresh/   renovar el access con el refresh
    /api/zonas/, /api/dispositivos/, /api/fabricantes/, /api/categorias/
                               CRUD (GET, POST, PUT, PATCH, DELETE)
    /api/lecturas/, /api/alertas/
                               solo GET (lista y detalle)

Todas las rutas aceptan la URL con o sin barra final (/api/token y
/api/token/), así un POST sin barra no falla. Cualquier otra ruta bajo /api/
responde 404 en JSON.
"""

from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

app_name = "api"

router = DefaultRouter()
router.trailing_slash = "/?"  # barra final opcional en todas las rutas
router.register("zonas", views.ZoneViewSet, basename="zone")
router.register("dispositivos", views.DeviceViewSet, basename="device")
router.register("fabricantes", views.ManufacturerViewSet, basename="manufacturer")
router.register("categorias", views.CategoryViewSet, basename="category")
router.register("lecturas", views.ConsumptionReadingViewSet, basename="reading")
router.register("alertas", views.AlertViewSet, basename="alert")

urlpatterns = [
    re_path(r"^token/?$", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    re_path(r"^token/refresh/?$", TokenRefreshView.as_view(), name="token_refresh"),
    path("", include(router.urls)),
    # Debe ir al final: cualquier ruta no reconocida bajo /api/ -> 404 JSON.
    re_path(r"^.*$", views.api_not_found, name="not_found"),
]
