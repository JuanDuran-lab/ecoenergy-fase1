EcoEnergy

Aplicación web desarrollada con Django para la gestión y consulta de zonas de consumo energético, dispositivos asociados y control administrativo mediante Django Admin.

El proyecto utiliza Django ORM y una base de datos SQLite, con configuración mediante variables de entorno y datos de demostración reproducibles.

Requisitos

Python 3.12 o superior

Django 6.1

python-dotenv

Las dependencias completas se encuentran en:

requirements.txt

Instalación

Clonar el repositorio:

git clone https://github.com/JuanDuran-lab/ecoenergy-fase1.git
cd ecoenergy-fase1

Crear un entorno virtual:

python -m venv .venv

Activarlo en PowerShell:

.\.venv\Scripts\Activate.ps1

Instalar las dependencias:

pip install -r requirements.txt

Variables de entorno

El proyecto utiliza un archivo .env para la configuración local.

Crear el archivo .env a partir del archivo de ejemplo:

Copy-Item .env.example .env

El archivo .env.example contiene las variables necesarias:

DJANGO_SECRET_KEY=coloca-aqui-una-clave-de-desarrollo
DJANGO_DEBUG=True
DJANGO_DB_NAME=db.sqlite3

El archivo .env está excluido del repositorio mediante .gitignore.

Base de datos

Aplicar las migraciones:

python manage.py migrate

El proyecto utiliza SQLite por defecto.

La configuración de la base de datos se obtiene mediante variables de entorno definidas en .env.

Datos de demostración

El proyecto incluye un Management Command para cargar datos iniciales de forma reproducible:

python manage.py cargar_datos_demo

Este comando crea o actualiza organizaciones, categorías, tipos de zona, estados de zona, zonas, dispositivos, perfiles de usuario, usuarios de demostración y permisos asociados.

El comando utiliza update_or_create, por lo que puede ejecutarse más de una vez sin duplicar los datos principales.

Usuarios de demostración

Administrador completo

Usuario: admin_demo
Contraseña: EcoDemo2026!

Tiene permisos completos sobre Django Admin.

Operador EcoEnergy Norte

Usuario: operador_norte
Contraseña: EcoNorte2026!

Solo puede visualizar y modificar zonas y dispositivos pertenecientes a EcoEnergy Norte.

Operador EcoEnergy Sur

Usuario: operador_sur
Contraseña: EcoSur2026!

Solo puede visualizar y modificar zonas y dispositivos pertenecientes a EcoEnergy Sur.

Los operadores no poseen permisos de eliminación.

Ejecución

python manage.py check
python manage.py runserver

Rutas principales

http://127.0.0.1:8000/zonas/ — listado de zonas.

http://127.0.0.1:8000/zonas/<id>/ — detalle de zona.

http://127.0.0.1:8000/resumen-zonas/ — resumen de consumo.

http://127.0.0.1:8000/admin/ — Django Admin.

Modelo de datos

Tablas maestras

Organizacion

Categoria

TipoZona

EstadoZona

Tablas operacionales

Zona

Dispositivo

Tabla de apoyo para seguridad

PerfilUsuario

Relaciones principales:

Organizacion 1 ---- N Zona
TipoZona     1 ---- N Zona
EstadoZona   1 ---- N Zona

Zona         1 ---- N Dispositivo
Categoria    1 ---- N Dispositivo

User         1 ---- 1 PerfilUsuario
Organizacion 1 ---- N PerfilUsuario

Django Admin

El administrador incluye:

list_display

search_fields

list_filter

ordering

list_select_related

Inline de dispositivos dentro de una zona

acciones personalizadas para activar y desactivar dispositivos

validación controlada mediante clean()

filtros dinámicos según usuario

restricción de ForeignKey según organización

Scoping por organización

Los usuarios limitados solo pueden acceder a registros de su propia organización.

operador_norte solo accede a EcoEnergy Norte y operador_sur solo accede a EcoEnergy Sur.

El scoping se aplica mediante get_queryset() en Django Admin. También se restringen ForeignKey y el acceso directo por URL a objetos de otra organización.

Validaciones

La entidad Zona exige:

limite_kwh > 0

Si se intenta guardar un valor igual o inferior a cero, Django Admin muestra un error y no guarda el registro.

Consumo energético

Si:

consumo_total > limite_kwh

el estado calculado es ALERTA. En caso contrario, es NORMAL.

Fuente de datos

La aplicación utiliza Django ORM y SQLite.

Las vistas /zonas/, /zonas/<id>/ y /resumen-zonas/ consultan directamente los modelos mediante Django ORM.

Los archivos JSON de la Fase 1 ya no son la fuente principal de datos.

Puesta en marcha desde un entorno limpio

git clone https://github.com/JuanDuran-lab/ecoenergy-fase1.git
cd ecoenergy-fase1

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
Copy-Item .env.example .env

python manage.py migrate
python manage.py cargar_datos_demo
python manage.py check
python manage.py runserver

Verificación realizada

Se verificó manualmente:

migraciones

carga reproducible de datos demo

acceso al Django Admin

Inline de dispositivos

acciones personalizadas

validación de límite energético

restricciones por organización

acceso con operador Norte y operador Sur

bloqueo de acceso directo a objetos de otra organización

listado público de zonas

detalle de zona

resumen energético

cálculo NORMAL y ALERTA

HTTP 404 para identificadores inexistentes

python manage.py check

Estado actual

La aplicación se encuentra preparada para ejecutarse mediante Django ORM, SQLite, variables de entorno y carga reproducible de datos demo.