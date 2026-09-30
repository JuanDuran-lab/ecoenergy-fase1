"""
Métricas reutilizables: dispositivos por zona y consumo de los últimos 30
días. Las anotaciones (Count / Sum) filtran deleted_at explícitamente,
porque los JOIN no pasan por el manager que oculta los eliminados.
"""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

CONSUMPTION_WINDOW_DAYS = 30


def consumption_since():
    return timezone.now() - timedelta(days=CONSUMPTION_WINDOW_DAYS)


def annotate_zone_metrics(queryset):
    since = consumption_since()
    alive_devices = Q(devices__deleted_at__isnull=True)
    return queryset.annotate(
        device_count=Count("devices", filter=alive_devices, distinct=True),
        consumption_kwh=Coalesce(
            Sum(
                "devices__readings__consumption_kwh",
                filter=alive_devices
                & Q(devices__readings__deleted_at__isnull=True)
                & Q(devices__readings__reading_at__gte=since),
            ),
            Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
    )


def annotate_device_metrics(queryset):
    since = consumption_since()
    recent = Q(readings__deleted_at__isnull=True) & Q(readings__reading_at__gte=since)
    return queryset.annotate(
        reading_count=Count("readings", filter=Q(readings__deleted_at__isnull=True)),
        consumption_kwh=Coalesce(
            Sum("readings__consumption_kwh", filter=recent),
            Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
    )
