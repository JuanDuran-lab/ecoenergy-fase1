from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404, render

from .models import Device, Zone


@login_required
def zone_list(request):
    zones = (
        Zone.objects.select_related("organization", "zone_type", "status")
        .annotate(device_count=Count("devices"))
        .order_by("organization__name", "name")
    )
    return render(request, "monitoring/zone_list.html", {"zones": zones})


@login_required
def zone_detail(request, pk):
    zone = get_object_or_404(
        Zone.objects.select_related("organization", "zone_type", "status"), pk=pk
    )
    devices = list(zone.devices.select_related("category").order_by("name"))
    total_consumption = sum(
        (device.nominal_consumption_kwh for device in devices), Decimal("0.00")
    )
    return render(
        request,
        "monitoring/zone_detail.html",
        {
            "zone": zone,
            "devices": devices,
            "device_count": len(devices),
            "total_consumption": total_consumption,
            "over_limit": total_consumption > zone.consumption_limit_kwh,
        },
    )


@login_required
def zone_summary(request):
    zones = (
        Zone.objects.select_related("organization")
        .prefetch_related(Prefetch("devices", queryset=Device.objects.all()))
        .order_by("organization__name", "name")
    )

    summary = []
    total_devices = 0
    total_consumption = Decimal("0.00")

    for zone in zones:
        devices = list(zone.devices.all())
        zone_consumption = sum(
            (device.nominal_consumption_kwh for device in devices), Decimal("0.00")
        )
        summary.append(
            {
                "zone": zone,
                "device_count": len(devices),
                "total_consumption": zone_consumption,
                "over_limit": zone_consumption > zone.consumption_limit_kwh,
            }
        )
        total_devices += len(devices)
        total_consumption += zone_consumption

    return render(
        request,
        "monitoring/zone_summary.html",
        {
            "summary": summary,
            "total_zones": len(summary),
            "total_devices": total_devices,
            "total_consumption": total_consumption,
        },
    )
