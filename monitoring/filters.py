"""
Filtros de los listados. Se usan en el listado HTML y en la exportación a
Excel, para que el archivo contenga lo mismo que el usuario está viendo.
"""

from django.db.models import Q
from django.utils.dateparse import parse_date


def _int_param(params, name):
    value = params.get(name, "")
    return int(value) if value.isdigit() else None


def filter_readings(queryset, params):
    term = params.get("q", "").strip()
    if term:
        queryset = queryset.filter(
            Q(device__name__icontains=term)
            | Q(device__serial_number__icontains=term)
            | Q(device__zone__name__icontains=term)
        )

    zone_id = _int_param(params, "zone")
    if zone_id:
        queryset = queryset.filter(device__zone_id=zone_id)

    date_from = parse_date(params.get("date_from", "") or "")
    if date_from:
        queryset = queryset.filter(reading_at__date__gte=date_from)

    date_to = parse_date(params.get("date_to", "") or "")
    if date_to:
        queryset = queryset.filter(reading_at__date__lte=date_to)

    return queryset


def filter_devices(queryset, params):
    zone_id = _int_param(params, "zone")
    if zone_id:
        queryset = queryset.filter(zone_id=zone_id)
    category_id = _int_param(params, "category")
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    active = params.get("active", "")
    if active in {"1", "0"}:
        queryset = queryset.filter(is_active=active == "1")
    return queryset


def filter_alerts(queryset, params):
    status = params.get("status", "")
    if status:
        queryset = queryset.filter(status=status)
    severity_id = _int_param(params, "severity")
    if severity_id:
        queryset = queryset.filter(severity_id=severity_id)
    zone_id = _int_param(params, "zone")
    if zone_id:
        queryset = queryset.filter(zone_id=zone_id)
    return queryset
