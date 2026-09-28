from core.views import ScopedCreateView, ScopedDetailView, ScopedListView, ScopedUpdateView

from ..forms import ZoneForm
from ..models import Zone
from ..queries import CONSUMPTION_WINDOW_DAYS, annotate_device_metrics, annotate_zone_metrics


class ZoneListView(ScopedListView):
    model = Zone
    template_name = "monitoring/zone_list.html"
    context_object_name = "zones"
    search_fields = ("name", "description", "zone_type__name", "status__name")

    def get_queryset(self):
        queryset = super().get_queryset().select_related("organization", "zone_type", "status")
        return annotate_zone_metrics(queryset).order_by("organization__name", "name")


class ZoneDetailView(ScopedDetailView):
    model = Zone
    template_name = "monitoring/zone_detail.html"
    context_object_name = "zone"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("organization", "zone_type", "status")
        return annotate_zone_metrics(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        zone = self.object
        context["devices"] = annotate_device_metrics(
            zone.devices.select_related("category", "manufacturer")
        ).order_by("name")
        context["over_limit"] = zone.consumption_kwh > zone.consumption_limit_kwh
        context["window_days"] = CONSUMPTION_WINDOW_DAYS
        return context


class ZoneCreateView(ScopedCreateView):
    model = Zone
    form_class = ZoneForm
    list_url_name = "monitoring:zone_list"
    success_message = "Zona «{obj.name}» creada correctamente."


class ZoneUpdateView(ScopedUpdateView):
    model = Zone
    form_class = ZoneForm
    success_message = "Zona «{obj.name}» actualizada correctamente."


class ZoneSummaryView(ScopedListView):
    model = Zone
    template_name = "monitoring/zone_summary.html"
    context_object_name = "zones"

    def get_paginate_by(self, queryset):
        # El resumen muestra todas las zonas en una sola tabla.
        return None

    def get_queryset(self):
        queryset = super().get_queryset().select_related("organization")
        return annotate_zone_metrics(queryset).order_by("organization__name", "name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        zones = list(context["zones"])
        for zone in zones:
            zone.over_limit = zone.consumption_kwh > zone.consumption_limit_kwh
        context["zones"] = zones
        context["total_zones"] = len(zones)
        context["total_devices"] = sum(zone.device_count for zone in zones)
        context["total_consumption"] = sum(zone.consumption_kwh for zone in zones)
        context["zones_over_limit"] = sum(1 for zone in zones if zone.over_limit)
        context["window_days"] = CONSUMPTION_WINDOW_DAYS
        return context
