from core.scoping import scope_queryset
from core.views import (
    ScopedCreateView,
    ScopedDetailView,
    ScopedListView,
    ScopedSoftDeleteView,
    ScopedUpdateView,
)

from ..filters import filter_devices
from ..forms import DeviceForm
from ..models import Category, Device, Zone
from ..queries import CONSUMPTION_WINDOW_DAYS, annotate_device_metrics


class DeviceListView(ScopedListView):
    model = Device
    template_name = "monitoring/device_list.html"
    context_object_name = "devices"
    search_fields = ("name", "serial_number", "zone__name", "manufacturer__name")

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            "zone", "zone__organization", "category", "manufacturer"
        )
        queryset = filter_devices(queryset, self.request.GET)
        return annotate_device_metrics(queryset).order_by("zone__organization__name", "zone__name", "name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["zones"] = scope_queryset(Zone.objects.all(), self.request.user)
        context["categories"] = Category.objects.all()
        context["window_days"] = CONSUMPTION_WINDOW_DAYS
        return context


class DeviceDetailView(ScopedDetailView):
    model = Device
    template_name = "monitoring/device_detail.html"
    context_object_name = "device"

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            "zone", "zone__organization", "category", "manufacturer"
        )
        return annotate_device_metrics(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recent_readings"] = self.object.readings.order_by("-reading_at")[:10]
        context["recent_alerts"] = self.object.alerts.select_related("severity").order_by("-detected_at")[:5]
        context["window_days"] = CONSUMPTION_WINDOW_DAYS
        return context


class DeviceCreateView(ScopedCreateView):
    model = Device
    form_class = DeviceForm
    list_url_name = "monitoring:device_list"
    success_message = "Dispositivo «{obj.name}» creado correctamente."

    def get_initial(self):
        initial = super().get_initial()
        zone_id = self.request.GET.get("zone", "")
        if zone_id.isdigit():
            initial["zone"] = zone_id
        return initial


class DeviceUpdateView(ScopedUpdateView):
    model = Device
    form_class = DeviceForm
    success_message = "Dispositivo «{obj.name}» actualizado correctamente."


class DeviceDeleteView(ScopedSoftDeleteView):
    model = Device
    success_url_name = "monitoring:device_list"
    success_message = "Dispositivo «{label}» eliminado junto a sus lecturas y alertas."
