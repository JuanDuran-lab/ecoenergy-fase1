"""
Paginación con tamaño de página persistente en la sesión.

- El usuario elige 5, 15 o 30 registros por página (?per_page=N).
- La elección se guarda en request.session y se mantiene al navegar
  entre páginas y entre listados, incluso después de cerrar el navegador
  mientras la sesión siga vigente.
- Cualquier otro valor (0, 1000, "abc", -5) se normaliza al valor por
  defecto (15) y se informa al usuario. El servidor nunca confía en el
  valor que llega desde el navegador.
"""

from django.contrib import messages

PAGE_SIZE_OPTIONS = (5, 15, 30)
DEFAULT_PAGE_SIZE = 15
SESSION_KEY = "page_size"
QUERY_PARAM = "per_page"


def resolve_page_size(request):
    raw_value = request.GET.get(QUERY_PARAM)

    if raw_value is not None:
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            value = None

        if value not in PAGE_SIZE_OPTIONS:
            messages.warning(
                request,
                f"Tamaño de página no permitido. Se usarán {DEFAULT_PAGE_SIZE} registros por página.",
            )
            value = DEFAULT_PAGE_SIZE

        request.session[SESSION_KEY] = value
        return value

    value = request.session.get(SESSION_KEY, DEFAULT_PAGE_SIZE)
    if value not in PAGE_SIZE_OPTIONS:
        # La sesión también se valida (defensa en profundidad).
        value = DEFAULT_PAGE_SIZE
        request.session[SESSION_KEY] = value
    return value


class SessionPaginationMixin:
    def get_paginate_by(self, queryset):
        return resolve_page_size(self.request)

    def paginate_queryset(self, queryset, page_size):
        """
        Igual que ListView, pero una página inexistente (?page=999) muestra
        la última página válida en vez de responder 404.
        """
        paginator = self.get_paginator(
            queryset,
            page_size,
            orphans=self.get_paginate_orphans(),
            allow_empty_first_page=self.get_allow_empty(),
        )
        page = paginator.get_page(self.request.GET.get(self.page_kwarg))
        return paginator, page, page.object_list, page.has_other_pages()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_size_options"] = PAGE_SIZE_OPTIONS
        context["current_page_size"] = self.request.session.get(SESSION_KEY, DEFAULT_PAGE_SIZE)
        return context
