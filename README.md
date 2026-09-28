# EcoEnergy

Aplicación web Django para la gestión de zonas de consumo energético y sus
dispositivos, con scoping por organización.

> README en construcción durante la Evaluación 2. La versión completa se
> integra en la rama `docs/readme`.

## Estructura

| App | Responsabilidad |
|---|---|
| `core` | Modelo base con borrado lógico (`SoftDeleteModel`), scoping por organización y clases base del Admin |
| `accounts` | Perfil de usuario (`UserProfile`) y seguridad |
| `monitoring` | Modelos del negocio, vistas y carga de datos |

## Puesta en marcha

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # completar los valores
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Las contraseñas de los usuarios de prueba se definen en `.env`
(`SEED_*_PASSWORD`) y **no se publican en el repositorio**.
