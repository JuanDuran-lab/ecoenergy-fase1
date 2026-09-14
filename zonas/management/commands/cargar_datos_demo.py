from decimal import Decimal

from django.contrib.auth.models import Permission, User
from django.core.management.base import BaseCommand

from zonas.models import (
    Categoria,
    Dispositivo,
    EstadoZona,
    Organizacion,
    PerfilUsuario,
    TipoZona,
    Zona,
)


class Command(BaseCommand):
    help = "Carga datos reproducibles de demostración para EcoEnergy"

    def handle(self, *args, **options):
        self.stdout.write("Cargando datos de demostración de EcoEnergy...")

        # ---------------------------------------------------------
        # ORGANIZACIONES
        # ---------------------------------------------------------

        organizacion_norte, _ = Organizacion.objects.update_or_create(
            rut="76.111.111-1",
            defaults={
                "nombre": "EcoEnergy Norte",
                "activa": True,
            },
        )

        organizacion_sur, _ = Organizacion.objects.update_or_create(
            rut="76.222.222-2",
            defaults={
                "nombre": "EcoEnergy Sur",
                "activa": True,
            },
        )

        # ---------------------------------------------------------
        # CATEGORÍAS
        # ---------------------------------------------------------

        climatizacion, _ = Categoria.objects.update_or_create(
            nombre="Climatización",
            defaults={
                "descripcion": "Equipos destinados a climatización.",
                "activa": True,
            },
        )

        iluminacion, _ = Categoria.objects.update_or_create(
            nombre="Iluminación",
            defaults={
                "descripcion": "Equipos de iluminación.",
                "activa": True,
            },
        )

        computacion, _ = Categoria.objects.update_or_create(
            nombre="Computación",
            defaults={
                "descripcion": "Equipos computacionales y electrónicos.",
                "activa": True,
            },
        )

        # ---------------------------------------------------------
        # TIPOS DE ZONA
        # ---------------------------------------------------------

        oficina, _ = TipoZona.objects.update_or_create(
            nombre="Oficina",
            defaults={
                "descripcion": "Espacios destinados a trabajo administrativo.",
                "activo": True,
            },
        )

        bodega, _ = TipoZona.objects.update_or_create(
            nombre="Bodega",
            defaults={
                "descripcion": "Espacios destinados a almacenamiento.",
                "activo": True,
            },
        )

        sala_tecnica, _ = TipoZona.objects.update_or_create(
            nombre="Sala técnica",
            defaults={
                "descripcion": "Espacios con equipamiento técnico.",
                "activo": True,
            },
        )

        # ---------------------------------------------------------
        # ESTADOS DE ZONA
        # ---------------------------------------------------------

        operativa, _ = EstadoZona.objects.update_or_create(
            nombre="Operativa",
            defaults={
                "descripcion": "Zona disponible para funcionamiento normal.",
            },
        )

        mantenimiento, _ = EstadoZona.objects.update_or_create(
            nombre="Mantenimiento",
            defaults={
                "descripcion": "Zona temporalmente en mantenimiento.",
            },
        )

        # ---------------------------------------------------------
        # ZONAS
        # ---------------------------------------------------------

        recepcion_norte, _ = Zona.objects.update_or_create(
            organizacion=organizacion_norte,
            nombre="Recepción",
            defaults={
                "tipo": oficina,
                "estado": operativa,
                "descripcion": "Recepción principal de EcoEnergy Norte.",
                "limite_kwh": Decimal("100.00"),
            },
        )

        oficina_norte, _ = Zona.objects.update_or_create(
            organizacion=organizacion_norte,
            nombre="Oficina administrativa",
            defaults={
                "tipo": oficina,
                "estado": operativa,
                "descripcion": "Área administrativa de EcoEnergy Norte.",
                "limite_kwh": Decimal("80.00"),
            },
        )

        servidores_norte, _ = Zona.objects.update_or_create(
            organizacion=organizacion_norte,
            nombre="Sala de servidores",
            defaults={
                "tipo": sala_tecnica,
                "estado": operativa,
                "descripcion": "Infraestructura tecnológica principal.",
                "limite_kwh": Decimal("150.00"),
            },
        )

        recepcion_sur, _ = Zona.objects.update_or_create(
            organizacion=organizacion_sur,
            nombre="Recepción",
            defaults={
                "tipo": oficina,
                "estado": operativa,
                "descripcion": "Recepción principal de EcoEnergy Sur.",
                "limite_kwh": Decimal("90.00"),
            },
        )

        bodega_sur, _ = Zona.objects.update_or_create(
            organizacion=organizacion_sur,
            nombre="Bodega principal",
            defaults={
                "tipo": bodega,
                "estado": mantenimiento,
                "descripcion": "Bodega general de EcoEnergy Sur.",
                "limite_kwh": Decimal("60.00"),
            },
        )

        # ---------------------------------------------------------
        # DISPOSITIVOS
        # ---------------------------------------------------------

        dispositivos = [
            {
                "zona": recepcion_norte,
                "categoria": climatizacion,
                "nombre": "Aire acondicionado recepción",
                "consumo_kwh": Decimal("45.00"),
                "activo": True,
            },
            {
                "zona": recepcion_norte,
                "categoria": iluminacion,
                "nombre": "Iluminación recepción",
                "consumo_kwh": Decimal("25.00"),
                "activo": True,
            },
            {
                "zona": oficina_norte,
                "categoria": computacion,
                "nombre": "Estaciones de trabajo",
                "consumo_kwh": Decimal("50.00"),
                "activo": True,
            },
            {
                "zona": servidores_norte,
                "categoria": computacion,
                "nombre": "Servidor principal",
                "consumo_kwh": Decimal("120.00"),
                "activo": True,
            },
            {
                "zona": servidores_norte,
                "categoria": climatizacion,
                "nombre": "Climatización servidores",
                "consumo_kwh": Decimal("55.00"),
                "activo": True,
            },
            {
                "zona": recepcion_sur,
                "categoria": iluminacion,
                "nombre": "Iluminación recepción sur",
                "consumo_kwh": Decimal("30.00"),
                "activo": True,
            },
            {
                "zona": bodega_sur,
                "categoria": iluminacion,
                "nombre": "Iluminación bodega",
                "consumo_kwh": Decimal("20.00"),
                "activo": False,
            },
        ]

        for datos in dispositivos:
            Dispositivo.objects.update_or_create(
                zona=datos["zona"],
                nombre=datos["nombre"],
                defaults={
                    "categoria": datos["categoria"],
                    "consumo_kwh": datos["consumo_kwh"],
                    "activo": datos["activo"],
                },
            )

                # ---------------------------------------------------------
        # USUARIOS DE PRUEBA
        # ---------------------------------------------------------

        admin_demo, _ = User.objects.get_or_create(
            username="admin_demo",
        )
        admin_demo.first_name = "Administrador"
        admin_demo.last_name = "Demo"
        admin_demo.email = "admin@ecoenergy.demo"
        admin_demo.is_staff = True
        admin_demo.is_superuser = True
        admin_demo.set_password("EcoDemo2026!")
        admin_demo.save()

        operador_norte, _ = User.objects.get_or_create(
            username="operador_norte",
        )
        operador_norte.first_name = "Operador"
        operador_norte.last_name = "Norte"
        operador_norte.email = "norte@ecoenergy.demo"
        operador_norte.is_staff = True
        operador_norte.is_superuser = False
        operador_norte.set_password("EcoNorte2026!")
        operador_norte.save()

        operador_sur, _ = User.objects.get_or_create(
            username="operador_sur",
        )
        operador_sur.first_name = "Operador"
        operador_sur.last_name = "Sur"
        operador_sur.email = "sur@ecoenergy.demo"
        operador_sur.is_staff = True
        operador_sur.is_superuser = False
        operador_sur.set_password("EcoSur2026!")
        operador_sur.save()

        # ---------------------------------------------------------
        # PERMISOS DE LOS OPERADORES
        # ---------------------------------------------------------

        permisos_operador = Permission.objects.filter(
            content_type__app_label="zonas",
            codename__in=[
                "view_zona",
                "add_zona",
                "change_zona",
                "view_dispositivo",
                "add_dispositivo",
                "change_dispositivo",
            ],
        )

        operador_norte.user_permissions.set(permisos_operador)
        operador_sur.user_permissions.set(permisos_operador)

        # ---------------------------------------------------------
        # PERFILES / ORGANIZACIONES
        # ---------------------------------------------------------

        PerfilUsuario.objects.update_or_create(
            usuario=operador_norte,
            defaults={
                "organizacion": organizacion_norte,
            },
        )

        PerfilUsuario.objects.update_or_create(
            usuario=operador_sur,
            defaults={
                "organizacion": organizacion_sur,
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Datos de demostración cargados correctamente."
            )
        )

        self.stdout.write("")
        self.stdout.write("Usuarios de prueba:")
        self.stdout.write(
            "  admin_demo     / EcoDemo2026!"
        )
        self.stdout.write(
            "  operador_norte / EcoNorte2026!"
        )
        self.stdout.write(
            "  operador_sur   / EcoSur2026!"
        )