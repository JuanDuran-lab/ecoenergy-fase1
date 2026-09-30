"""
Vistas base de los CRUD (listar, detalle, crear, editar, eliminar).

Cada CRUD del proyecto hereda de estas clases y solo define modelo,
formulario y plantillas, así login, permisos y scoping se aplican siempre
de la misma forma.
"""

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from .mixins import ModelPermissionMixin, OrganizationScopedMixin
from .pagination import SessionPaginationMixin


class ScopedListView(
    ModelPermissionMixin, OrganizationScopedMixin, SessionPaginationMixin, ListView
):
    permission_action = "view"
    search_fields = ()

    def get_search_term(self):
        return self.request.GET.get("q", "").strip()

    def apply_search(self, queryset):
        term = self.get_search_term()
        if term and self.search_fields:
            condition = Q()
            for field in self.search_fields:
                condition |= Q(**{f"{field}__icontains": term})
            queryset = queryset.filter(condition)
        return queryset

    def get_queryset(self):
        return self.apply_search(super().get_queryset())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_term"] = self.get_search_term()
        return context


class ScopedDetailView(ModelPermissionMixin, OrganizationScopedMixin, DetailView):
    permission_action = "view"


class ScopedFormMixin:
    success_message = "Registro guardado correctamente."
    list_url_name = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        if getattr(self, "object", None) is not None:
            context["cancel_url"] = self.object.get_absolute_url()
        else:
            context["cancel_url"] = reverse(self.list_url_name)
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message.format(obj=self.object))
        return response

    def form_invalid(self, form):
        for name in form.errors:
            if name in form.fields:
                widget = form.fields[name].widget
                widget.attrs["class"] = f"{widget.attrs.get('class', '')} is-invalid".strip()
        messages.error(self.request, "Revisa los errores del formulario.")
        return super().form_invalid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


class ScopedCreateView(ModelPermissionMixin, ScopedFormMixin, CreateView):
    permission_action = "add"
    template_name = "core/form.html"


class ScopedUpdateView(
    ModelPermissionMixin, OrganizationScopedMixin, ScopedFormMixin, UpdateView
):
    permission_action = "change"
    template_name = "core/form.html"


# Eliminación: solo acepta POST con token CSRF, exige el permiso delete,
# responde 404 si el registro es de otra organización y hace borrado
# lógico. La confirmación con SweetAlert2 es solo visual.
class ScopedSoftDeleteView(
    ModelPermissionMixin, OrganizationScopedMixin, SingleObjectMixin, View
):
    permission_action = "delete"
    http_method_names = ["post"]
    success_url_name = None
    success_message = "Registro eliminado correctamente."

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        label = str(self.object)
        with transaction.atomic():
            self.object.soft_delete()
        messages.success(request, self.success_message.format(label=label))
        return redirect(self.success_url_name)
