"""
Manejo de errores de la API: todas las respuestas de error son JSON.

Un id inexistente y un registro de otra organización responden igual (404),
así la API no revela qué registros existen fuera del scoping del usuario.
"""

from django.http import Http404
from rest_framework.exceptions import NotFound
from rest_framework.views import exception_handler

NOT_FOUND_MESSAGE = "El registro no existe o no pertenece a tu organización."


def api_exception_handler(exc, context):
    if isinstance(exc, Http404):
        exc = NotFound(NOT_FOUND_MESSAGE)
    return exception_handler(exc, context)
