"""
CRUD de alertas.
"""

from django.utils import timezone

from core.scoping import scope_queryset
from core.views import (
    ScopedCreateView,
    ScopedDetailView,
    ScopedListView,
    ScopedSoftDeleteView,
    ScopedUpdateView,
)

from ..filters import filter_alerts
from ..forms import AlertForm
from ..models import Alert, AlertSeverity, Zone


class AlertListView(ScopedListView):
    model = Alert
    template_name = "monitoring/alert_list.html"
    context_object_name = "alerts"
    search_fields = ("title", "description", "device__name", "zone__name")

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            "zone", "zone__organization", "device", "severity"
        )
        return filter_alerts(queryset, self.request.GET).order_by("-detected_at", "-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["zones"] = scope_queryset(Zone.objects.all(), self.request.user)
        context["severities"] = AlertSeverity.objects.all()
        context["statuses"] = Alert.Status.choices
        return context


class AlertDetailView(ScopedDetailView):
    model = Alert
    template_name = "monitoring/alert_detail.html"
    context_object_name = "alert"

    def get_queryset(self):
        return super().get_queryset().select_related(
            "zone", "zone__organization", "device", "severity", "reading"
        )


class AlertCreateView(ScopedCreateView):
    model = Alert
    form_class = AlertForm
    list_url_name = "monitoring:alert_list"
    success_message = "Alerta «{obj.title}» registrada correctamente."

    def get_initial(self):
        initial = super().get_initial()
        initial["detected_at"] = timezone.localtime().replace(second=0, microsecond=0)
        return initial


class AlertUpdateView(ScopedUpdateView):
    model = Alert
    form_class = AlertForm
    success_message = "Alerta «{obj.title}» actualizada correctamente."


class AlertDeleteView(ScopedSoftDeleteView):
    model = Alert
    success_url_name = "monitoring:alert_list"
    success_message = "Alerta «{label}» eliminada."
