"""
Manejo de errores de la API: todas las respuestas de error son JSON.

- Un id inexistente y un registro de otra organización responden igual (404),
  así la API no revela qué registros existen fuera del scoping del usuario.
- Una excepción no controlada responde 500 con un mensaje genérico en JSON
  (también con DEBUG=True); el detalle completo queda en el log del servidor.
- Las rutas inexistentes bajo /api/ las responde api.views.api_not_found.
"""

import logging

from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import exception_handler, set_rollback

logger = logging.getLogger("api")

NOT_FOUND_MESSAGE = "El registro no existe o no pertenece a tu organización."
SERVER_ERROR_MESSAGE = "Error interno del servidor. El detalle quedó registrado en el log."


def api_exception_handler(exc, context):
    if isinstance(exc, Http404):
        exc = NotFound(NOT_FOUND_MESSAGE)

    response = exception_handler(exc, context)
    if response is not None:
        return response

    view = context.get("view")
    logger.error(
        "Error no controlado en %s", type(view).__name__ if view else "la API", exc_info=exc
    )
    set_rollback()
    return Response(
        {"detail": SERVER_ERROR_MESSAGE}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
