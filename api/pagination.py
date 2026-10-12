"""
Paginación de las listas de la API.

20 registros por página. Otra página: ?page=2. Otro tamaño: ?page_size=50
(máximo 100). La respuesta indica el total de registros y de páginas.
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )

    def get_paginated_response_schema(self, schema):
        # Documenta en OpenAPI la misma forma que get_paginated_response.
        return {
            "type": "object",
            "required": ["count", "total_pages", "page", "page_size", "results"],
            "properties": {
                "count": {"type": "integer", "example": 600},
                "total_pages": {"type": "integer", "example": 30},
                "page": {"type": "integer", "example": 2},
                "page_size": {"type": "integer", "example": 20},
                "next": {"type": "string", "nullable": True, "format": "uri"},
                "previous": {"type": "string", "nullable": True, "format": "uri"},
                "results": schema,
            },
        }
