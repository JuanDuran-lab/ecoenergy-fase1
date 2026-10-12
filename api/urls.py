"""
Rutas de la API REST, todas bajo /api/.

    POST /api/token/           obtener access y refresh (usuario y contraseña)
    POST /api/token/refresh/   renovar el access con el refresh
    /api/zonas/, /api/dispositivos/, /api/fabricantes/, /api/categorias/
                               CRUD (GET, POST, PUT, PATCH, DELETE)
    /api/lecturas/, /api/alertas/
                               solo GET (lista y detalle)
    GET  /api/docs/            documentación interactiva (Swagger UI)
    GET  /api/schema/          esquema OpenAPI 3

Todas las rutas aceptan la URL con o sin barra final (/api/token y
/api/token/), así un POST sin barra no falla. Cualquier otra ruta bajo /api/
responde 404 en JSON.
"""

from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

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
    re_path(r"^token/?$", views.TokenObtainView.as_view(), name="token_obtain_pair"),
    re_path(r"^token/refresh/?$", views.TokenRefreshAccessView.as_view(), name="token_refresh"),
    re_path(r"^schema/?$", SpectacularAPIView.as_view(), name="schema"),
    re_path(
        r"^docs/?$",
        SpectacularSwaggerView.as_view(url_name="api:schema"),
        name="docs",
    ),
    path("", include(router.urls)),
    # Debe ir al final: cualquier ruta no reconocida bajo /api/ -> 404 JSON.
    re_path(r"^.*$", views.api_not_found, name="not_found"),
]
