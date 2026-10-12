"""
Ajustes del esquema OpenAPI (drf-spectacular).

add_error_responses agrega a cada operación de la API las respuestas de error
reales del proyecto, que drf-spectacular no deduce por sí solo:

    400  datos inválidos (POST, PUT, PATCH) -> errores por campo
    401  sin token, token inválido o vencido
    403  sin rol API, u Operador API que intenta escribir
    404  id inexistente o de otra organización (rutas con {id})
    409  fabricante o categoría con dispositivos (DELETE)
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view

ERROR = {"$ref": "#/components/schemas/Error"}
VALIDATION_ERRORS = {"$ref": "#/components/schemas/ErroresValidacion"}

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
CATALOG_PATHS = ("/api/fabricantes/", "/api/categorias/")


def search_param(fields):
    return OpenApiParameter(
        "search", OpenApiTypes.STR, description=f"Busca texto en: {fields}."
    )


def id_param(name, description):
    return OpenApiParameter(name, OpenApiTypes.INT, description=description)


def resource_docs(singular, plural, list_params=(), read_only=False):
    """Resúmenes en español y filtros de cada recurso para /api/docs/."""
    actions = {
        "list": extend_schema(
            summary=f"Listar {plural}",
            description=f"Lista paginada de {plural} (20 por página; ?page= y ?page_size=, máx. 100).",
            parameters=list(list_params),
        ),
        "retrieve": extend_schema(summary=f"Ver {singular}"),
    }
    if not read_only:
        actions.update(
            create=extend_schema(summary=f"Crear {singular}"),
            update=extend_schema(summary=f"Reemplazar {singular} (PUT)"),
            partial_update=extend_schema(summary=f"Modificar {singular} (PATCH)"),
            destroy=extend_schema(
                summary=f"Eliminar {singular}",
                description="Borrado lógico: marca deleted_at y responde 204; "
                "el registro deja de aparecer en las consultas.",
            ),
        )
    return extend_schema_view(**actions)


def add_error_responses(result, generator, request, public):
    schemas = result.setdefault("components", {}).setdefault("schemas", {})
    schemas["Error"] = {
        "type": "object",
        "properties": {"detail": {"type": "string"}},
        "required": ["detail"],
    }
    schemas["ErroresValidacion"] = {
        "type": "object",
        "description": "Lista de mensajes por campo, por ejemplo "
        '{"serial_number": ["Ya existe un dispositivo con este número de serie."]}.',
        "additionalProperties": {"type": "array", "items": {"type": "string"}},
    }

    for path, operations in result.get("paths", {}).items():
        for method, operation in operations.items():
            if method not in HTTP_METHODS:
                continue
            responses = operation.setdefault("responses", {})

            def add(code, description, schema=ERROR):
                responses.setdefault(
                    str(code),
                    {"description": description, "content": {"application/json": {"schema": schema}}},
                )

            if path.startswith("/api/token"):
                add(400, "Faltan campos obligatorios.", VALIDATION_ERRORS)
                add(401, "Credenciales incorrectas, o refresh token inválido o vencido.")
                continue

            add(401, "Sin token JWT, o token inválido o vencido.")
            add(403, "El usuario no tiene rol API, o es Operador API e intenta escribir.")
            if "{id}" in path:
                add(404, "El registro no existe o no pertenece a la organización del usuario.")
            if method in {"post", "put", "patch"}:
                add(400, "Datos inválidos: errores de validación por campo.", VALIDATION_ERRORS)
            if method == "delete" and path.startswith(CATALOG_PATHS):
                add(409, "No se puede eliminar: el registro está asociado a dispositivos.")
    return result
