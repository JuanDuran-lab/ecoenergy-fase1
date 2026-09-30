"""
CRUD de lecturas de consumo y exportación a Excel.
"""

from django.http import HttpResponse
from django.utils import timezone
from django.views import View

from core.mixins import ModelPermissionMixin
from core.scoping import scope_queryset
from core.views import (
    ScopedCreateView,
    ScopedDetailView,
    ScopedListView,
    ScopedSoftDeleteView,
    ScopedUpdateView,
)

from ..exports import XLSX_CONTENT_TYPE, build_readings_workbook
from ..filters import filter_readings
from ..forms import ConsumptionReadingForm
from ..models import ConsumptionReading, Zone


class ReadingListView(ScopedListView):
    model = ConsumptionReading
    template_name = "monitoring/reading_list.html"
    context_object_name = "readings"

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            "device", "device__zone", "device__zone__organization"
        )
        return filter_readings(queryset, self.request.GET).order_by("-reading_at", "-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["zones"] = scope_queryset(Zone.objects.all(), self.request.user)
        return context


class ReadingDetailView(ScopedDetailView):
    model = ConsumptionReading
    template_name = "monitoring/reading_detail.html"
    context_object_name = "reading"

    def get_queryset(self):
        return super().get_queryset().select_related(
            "device", "device__zone", "device__zone__organization"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["alerts"] = self.object.alerts.select_related("severity")
        return context


class ReadingCreateView(ScopedCreateView):
    model = ConsumptionReading
    form_class = ConsumptionReadingForm
    list_url_name = "monitoring:reading_list"
    success_message = "Lectura registrada correctamente."

    def get_initial(self):
        initial = super().get_initial()
        initial["reading_at"] = timezone.localtime().replace(second=0, microsecond=0)
        device_id = self.request.GET.get("device", "")
        if device_id.isdigit():
            initial["device"] = device_id
        return initial


class ReadingUpdateView(ScopedUpdateView):
    model = ConsumptionReading
    form_class = ConsumptionReadingForm
    success_message = "Lectura actualizada correctamente."


class ReadingDeleteView(ScopedSoftDeleteView):
    model = ConsumptionReading
    success_url_name = "monitoring:reading_list"
    success_message = "Lectura «{label}» eliminada."


# Exportación: exige permisos view y export, aplica scoping y los mismos
# filtros del listado, y excluye los registros eliminados.
class ReadingExportView(ModelPermissionMixin, View):
    model = ConsumptionReading
    permission_required = (
        "monitoring.view_consumptionreading",
        "monitoring.export_consumptionreading",
    )
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        queryset = ConsumptionReading.objects.select_related(
            "device", "device__category", "device__zone", "device__zone__organization"
        )
        queryset = scope_queryset(queryset, request.user)
        queryset = filter_readings(queryset, request.GET).order_by("-reading_at", "-pk")

        filters = ", ".join(
            f"{key}={value}"
            for key, value in request.GET.items()
            if key in {"q", "zone", "date_from", "date_to"} and value
        )
        buffer, _ = build_readings_workbook(
            queryset, user=request.user, filters_description=filters
        )

        filename = f"lecturas_{timezone.localtime():%Y%m%d_%H%M}.xlsx"
        response = HttpResponse(buffer.getvalue(), content_type=XLSX_CONTENT_TYPE)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
