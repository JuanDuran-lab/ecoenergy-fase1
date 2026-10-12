"""
Rutas de la API REST, todas bajo /api/.

    POST /api/token/           obtener access y refresh (usuario y contraseña)
    POST /api/token/refresh/   renovar el access con el refresh
    /api/zonas/, /api/dispositivos/, /api/fabricantes/, /api/categorias/
                               CRUD (GET, POST, PUT, PATCH, DELETE)
    /api/lecturas/, /api/alertas/
                               solo GET (lista y detalle)
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

app_name = "api"

router = DefaultRouter()
router.register("zonas", views.ZoneViewSet, basename="zone")
router.register("dispositivos", views.DeviceViewSet, basename="device")
router.register("fabricantes", views.ManufacturerViewSet, basename="manufacturer")
router.register("categorias", views.CategoryViewSet, basename="category")
router.register("lecturas", views.ConsumptionReadingViewSet, basename="reading")
router.register("alertas", views.AlertViewSet, basename="alert")

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("", include(router.urls)),
]
