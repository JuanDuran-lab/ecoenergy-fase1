from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from core.scoping import scope_queryset

from ..models import Alert, ConsumptionReading, Device, Zone
from ..queries import CONSUMPTION_WINDOW_DAYS, annotate_zone_metrics


class DashboardView(LoginRequiredMixin, TemplateView):
    """Resumen de la organización del usuario (o de todas, si es admin)."""

    template_name = "monitoring/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        def scoped(model):
            return scope_queryset(model.objects.all(), user)

        stats = []
        for model, perm, icon, url in [
            (Zone, "view_zone", "bi-grid-3x3-gap", "monitoring:zone_list"),
            (Device, "view_device", "bi-cpu", "monitoring:device_list"),
            (ConsumptionReading, "view_consumptionreading", "bi-activity", "monitoring:reading_list"),
            (Alert, "view_alert", "bi-exclamation-triangle", "monitoring:alert_list"),
        ]:
            if user.has_perm(f"monitoring.{perm}"):
                stats.append(
                    {
                        "label": model._meta.verbose_name_plural.capitalize(),
                        "value": scoped(model).count(),
                        "icon": icon,
                        "url": url,
                    }
                )
        context["stats"] = stats

        if user.has_perm("monitoring.view_alert"):
            context["open_alerts"] = (
                scoped(Alert)
                .exclude(status=Alert.Status.RESOLVED)
                .select_related("zone", "device", "severity")
                .order_by("-severity__level", "-detected_at")[:8]
            )

        if user.has_perm("monitoring.view_zone"):
            zones = annotate_zone_metrics(scoped(Zone))
            context["zones_over_limit"] = [
                zone for zone in zones.select_related("organization")
                if zone.consumption_kwh > zone.consumption_limit_kwh
            ]
        context["window_days"] = CONSUMPTION_WINDOW_DAYS
        return context
