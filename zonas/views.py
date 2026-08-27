import json
from pathlib import Path

from django.shortcuts import render
from django.http import Http404


def cargar_json(nombre_archivo):
    ruta = Path(__file__).resolve().parent.parent / "data" / nombre_archivo

    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def lista_zonas(request):
    zonas = cargar_json("zonas.json")
    dispositivos = cargar_json("dispositivos.json")

    for zona in zonas:
        zona["cantidad_dispositivos"] = sum(
            1
            for dispositivo in dispositivos
            if dispositivo["zona_id"] == zona["id"]
        )

    return render(request, "zonas/lista.html", {"zonas": zonas})


def detalle_zona(request, zona_id):
    zonas = cargar_json("zonas.json")
    dispositivos = cargar_json("dispositivos.json")
    categorias = cargar_json("categorias.json")

    zona = next(
        (zona for zona in zonas if zona["id"] == zona_id),
        None
    )

    if zona is None:
        raise Http404("La zona no existe")

    dispositivos_zona = [
        dispositivo
        for dispositivo in dispositivos
        if dispositivo["zona_id"] == zona_id
    ]

    cantidad_dispositivos = len(dispositivos_zona)

    consumo_total = sum(
        dispositivo["consumo_kwh"]
        for dispositivo in dispositivos_zona
    )
    
    # Bloque condicional corregido (indentación y comilla)
    if consumo_total > zona["limite_kwh"]:
        estado = "ALERTA"
    else:
        estado = "NORMAL"

    for dispositivo in dispositivos_zona:
        categoria = next(
            (
                categoria
                for categoria in categorias
                if categoria["id"] == dispositivo["categoria_id"]
            ),
            None
        )

        dispositivo["categoria"] = categoria

    return render(
        request,
        "zonas/detalle.html",
        {
            "zona": zona,
            "dispositivos": dispositivos_zona,
            "cantidad_dispositivos": cantidad_dispositivos,
            "consumo_total": consumo_total,
            "estado": estado,
        }
    )


