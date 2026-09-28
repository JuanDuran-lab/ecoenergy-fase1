"""
Modelos base reutilizables por todas las apps del proyecto.

SoftDeleteModel agrega auditoría (created_at / updated_at) y borrado
lógico (deleted_at). Un registro "eliminado" sigue existiendo en la base
de datos, pero el manager por defecto (objects) lo oculta de todos los
listados y consultas normales.
"""

from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)

    def soft_delete(self):
        """Marca todos los registros del QuerySet como eliminados."""
        return self.update(deleted_at=timezone.now(), updated_at=timezone.now())

    def restore(self):
        return self.update(deleted_at=None, updated_at=timezone.now())

    def delete(self):
        """
        QuerySet.delete() también se convierte en borrado lógico, para
        que ningún flujo normal (vistas, Admin, acciones masivas)
        elimine filas físicamente. Se recorre objeto por objeto para
        respetar la cascada lógica que define cada modelo.
        """
        count = 0
        for obj in self.alive():
            obj.soft_delete()
            count += 1
        return count

    def hard_delete(self):
        """Borrado físico. Solo para scripts de mantenimiento (seed)."""
        return super().delete()


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    """Manager por defecto: solo entrega registros NO eliminados."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllObjectsManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    """Manager sin filtro: incluye registros eliminados lógicamente."""


class SoftDeleteModel(models.Model):
    created_at = models.DateTimeField("creado el", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado el", auto_now=True)
    deleted_at = models.DateTimeField(
        "eliminado el",
        null=True,
        blank=True,
        editable=False,
        db_index=True,
    )

    # El primer manager declarado es el manager por defecto de Django
    # (lo usan los formularios, el Admin y las relaciones inversas).
    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def soft_delete(self):
        """Borrado lógico: registra la fecha en vez de eliminar la fila."""
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at", "updated_at"])

    def delete(self, *args, **kwargs):
        """
        Cualquier llamada a delete() sobre una instancia se convierte en
        borrado lógico. Para un borrado físico (solo scripts de
        mantenimiento) se debe usar hard_delete().
        """
        self.soft_delete()

    def hard_delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)
