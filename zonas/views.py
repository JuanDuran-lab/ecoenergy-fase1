from decimal import Decimal

from django.db.models import Count
from django.shortcuts import get_object_or_404, render

from .models import Dispositivo, Zona


def lista_zonas(request):
    zonas = (
        Zona.objects
        .select_related(
            "organizacion",
            "tipo",
            "estado",
        )
        .annotate(
            cantidad_dispositivos=Count("dispositivos")
        )
        .order_by(
            "organizacion__nombre",
            "nombre",
        )
    )

    return render(
        request,
        "zonas/lista.html",
        {
            "zonas": zonas,
        },
    )


def detalle_zona(request, zona_id):
    zona = get_object_or_404(
        Zona.objects.select_related(
            "organizacion",
            "tipo",
            "estado",
        ),
        pk=zona_id,
    )

    dispositivos_zona = list(
        zona.dispositivos
        .select_related("categoria")
        .order_by("nombre")
    )

    cantidad_dispositivos = len(dispositivos_zona)

    consumo_total = sum(
        (
            dispositivo.consumo_kwh
            for dispositivo in dispositivos_zona
        ),
        Decimal("0.00"),
    )

    if consumo_total > zona.limite_kwh:
        estado = "ALERTA"
    else:
        estado = "NORMAL"

    return render(
        request,
        "zonas/detalle.html",
        {
            "zona": zona,
            "dispositivos": dispositivos_zona,
            "cantidad_dispositivos": cantidad_dispositivos,
            "consumo_total": consumo_total,
            "estado": estado,
        },
    )


def resumen_zonas(request):
    zonas = (
        Zona.objects
        .select_related("organizacion")
        .prefetch_related("dispositivos")
        .order_by(
            "organizacion__nombre",
            "nombre",
        )
    )

    resumen = []

    total_dispositivos = 0
    consumo_total_general = Decimal("0.00")

    for zona in zonas:
        dispositivos_zona = list(
            zona.dispositivos.all()
        )

        cantidad_dispositivos = len(
            dispositivos_zona
        )

        consumo_total = sum(
            (
                dispositivo.consumo_kwh
                for dispositivo in dispositivos_zona
            ),
            Decimal("0.00"),
        )

        if consumo_total <= zona.limite_kwh:
            estado = "DENTRO DEL LÍMITE"
        else:
            estado = "LÍMITE SUPERADO"

        resumen.append(
            {
                "id": zona.id,
                "nombre": zona.nombre,
                "organizacion": zona.organizacion.nombre,
                "cantidad_dispositivos": cantidad_dispositivos,
                "consumo_total": consumo_total,
                "limite_kwh": zona.limite_kwh,
                "estado": estado,
            }
        )

        total_dispositivos += cantidad_dispositivos
        consumo_total_general += consumo_total

    total_zonas = len(resumen)

    return render(
        request,
        "zonas/resumen.html",
        {
            "resumen": resumen,
            "total_zonas": total_zonas,
            "total_dispositivos": total_dispositivos,
            "consumo_total_general": consumo_total_general,
        },
    )