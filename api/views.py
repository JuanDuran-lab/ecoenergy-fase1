"""
Vistas de la API REST (ViewSets de DRF).

Cada vista aplica, en este orden:
1. Autenticación JWT: sin token o con token inválido -> 401.
2. Rol API (api/permissions.py): sin rol o escritura del operador -> 403.
3. Scoping por organización (core/scoping.py): un registro de otra
   organización no aparece en las listas y su detalle responde 404.

DELETE hace borrado lógico (se marca deleted_at, como en la web) y responde
204; el registro deja de aparecer en las consultas. Borrar una zona o un
dispositivo borra también sus registros dependientes.
"""

from django.db import transaction
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.exceptions import APIException

from core.scoping import scope_queryset
from monitoring.models import (
    Alert,
    Category,
    ConsumptionReading,
    Device,
    Manufacturer,
    Zone,
)

from .serializers import (
    AlertSerializer,
    CategorySerializer,
    ConsumptionReadingSerializer,
    DeviceSerializer,
    ManufacturerSerializer,
    ZoneSerializer,
)


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "conflict"


def int_param(request, name):
    value = request.query_params.get(name, "").strip()
    return int(value) if value.isdigit() else None


class ScopedQuerysetMixin:
    """Filtra por organización y permite buscar con ?search=texto."""

    search_fields = ()

    def get_base_queryset(self):
        raise NotImplementedError

    def get_queryset(self):
        queryset = scope_queryset(self.get_base_queryset(), self.request.user)
        term = self.request.query_params.get("search", "").strip()
        if term and self.search_fields:
            condition = Q()
            for field in self.search_fields:
                condition |= Q(**{f"{field}__icontains": term})
            queryset = queryset.filter(condition)
        return queryset


class SoftDeleteModelViewSet(ScopedQuerysetMixin, viewsets.ModelViewSet):
    def perform_destroy(self, instance):
        with transaction.atomic():
            instance.soft_delete()


# ---------------------------------------------------------------------------
# Principales: CRUD completo
# ---------------------------------------------------------------------------


class ZoneViewSet(SoftDeleteModelViewSet):
    serializer_class = ZoneSerializer
    search_fields = ("name", "description")

    def get_base_queryset(self):
        return Zone.objects.select_related(
            "organization", "zone_type", "status"
        ).order_by("organization__name", "name", "id")


class DeviceViewSet(SoftDeleteModelViewSet):
    serializer_class = DeviceSerializer
    search_fields = ("name", "serial_number")

    def get_base_queryset(self):
        queryset = Device.objects.select_related(
            "zone__organization", "category", "manufacturer"
        ).order_by("zone__organization__name", "zone__name", "name", "id")
        zone = int_param(self.request, "zone")
        if zone is not None:
            queryset = queryset.filter(zone_id=zone)
        return queryset


class CatalogViewSet(SoftDeleteModelViewSet):
    """Catálogos compartidos por todas las organizaciones (sin scoping)."""

    search_fields = ("name",)
    in_use_message = "No se puede eliminar: el registro está asociado a dispositivos."

    def perform_destroy(self, instance):
        if instance.devices.exists():
            raise Conflict(self.in_use_message)
        super().perform_destroy(instance)


class ManufacturerViewSet(CatalogViewSet):
    serializer_class = ManufacturerSerializer
    in_use_message = (
        "No se puede eliminar el fabricante: está asociado a dispositivos. "
        "Puede marcarlo como inactivo (is_active=false)."
    )

    def get_base_queryset(self):
        return Manufacturer.objects.order_by("name", "id")


class CategoryViewSet(CatalogViewSet):
    serializer_class = CategorySerializer
    in_use_message = (
        "No se puede eliminar la categoría: está asociada a dispositivos. "
        "Puede marcarla como inactiva (is_active=false)."
    )

    def get_base_queryset(self):
        return Category.objects.order_by("name", "id")


# ---------------------------------------------------------------------------
# Operacionales: solo lista y detalle
# ---------------------------------------------------------------------------


class ConsumptionReadingViewSet(ScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = ConsumptionReadingSerializer
    search_fields = ("device__name", "device__serial_number", "notes")

    def get_base_queryset(self):
        queryset = ConsumptionReading.objects.select_related(
            "device__zone__organization"
        ).order_by("-reading_at", "-id")
        device = int_param(self.request, "device")
        if device is not None:
            queryset = queryset.filter(device_id=device)
        return queryset


class AlertViewSet(ScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = AlertSerializer
    search_fields = ("title", "description")

    def get_base_queryset(self):
        queryset = Alert.objects.select_related(
            "zone__organization", "device", "severity"
        ).order_by("-detected_at", "-id")
        alert_status = self.request.query_params.get("status", "").strip()
        if alert_status in Alert.Status.values:
            queryset = queryset.filter(status=alert_status)
        return queryset
