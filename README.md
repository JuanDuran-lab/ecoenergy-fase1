EcoEnergy — Fase 1



Aplicación web desarrollada con Django para consultar zonas de consumo energético y los dispositivos instalados en cada zona.



Requisitos

Python 3.12

Django 6.1

Instalación



Clonar el repositorio y entrar a la carpeta del proyecto.



Crear y activar un entorno virtual:



python -m venv .venv

.\\.venv\\Scripts\\Activate.ps1





Instalar las dependencias:



pip install -r requirements.txt



Ejecución



Ejecutar la comprobación de Django:



python manage.py check





Iniciar el servidor:



python manage.py runserver





Luego acceder desde el navegador a:



http://127.0.0.1:8000/zonas/



Rutas funcionales

/zonas/ — listado de zonas de consumo.

/zonas/<id>/ — detalle de una zona.

Un ID de zona inexistente responde con HTTP 404.

Datos



La aplicación utiliza tres archivos JSON como fuente de datos:



data/zonas.json

data/dispositivos.json

data/categorias.json



Las relaciones se resuelven mediante identificadores:



dispositivos.zona\_id → zonas.id

dispositivos.categoria\_id → categorias.id



No se utilizan Models, migraciones, ORM ni base de datos para los datos del caso.



Funcionalidades



La aplicación permite:



Listar todas las zonas registradas.

Mostrar el límite de consumo de cada zona.

Mostrar la cantidad de dispositivos de cada zona.

Consultar el detalle de una zona.

Mostrar los dispositivos asociados.

Mostrar la categoría de cada dispositivo.

Calcular dinámicamente el consumo total.

Determinar dinámicamente el estado NORMAL o ALERTA.

Mostrar un mensaje cuando una zona no tiene dispositivos.

Responder con 404 cuando la zona solicitada no existe.

Incorporar nuevos registros válidos desde los archivos JSON sin modificar las Views o Templates por cada elemento.

Mantener las tablas adaptables cuando aumenta la cantidad de información.

Pruebas realizadas



Se verificó el funcionamiento de:



Listado de zonas.

Detalle de las zonas 1, 2 y 3.

Estado NORMAL.

Estado ALERTA.

Zona sin dispositivos.

Identificador de zona inexistente.

Incorporación dinámica de un nuevo dispositivo mediante dispositivos.json.

Comprobación python manage.py check.

Interfaz



Los Templates utilizan herencia mediante base.html y Bootstrap para la estructura visual, navegación, tarjetas, botones, alertas y tablas adaptables.



Estructura principal

Eva 1 Fase 1/

├── data/

│   ├── zonas.json

│   ├── dispositivos.json

│   └── categorias.json

├── ecoenergy/

│   ├── settings.py

│   ├── urls.py

│   └── ...

├── zonas/

│   ├── templates/

│   │   └── zonas/

│   │       ├── base.html

│   │       ├── lista.html

│   │       └── detalle.html

│   ├── views.py

│   └── urls.py

├── manage.py

├── requirements.txt

├── .gitignore

├── README.md

├── ANALISIS.md

└── IA.md





\## Verificación final de Fase 1



La aplicación fue verificada mediante `python manage.py check` y pruebas funcionales de las rutas principales.



Se comprobaron los casos de listado de zonas, detalle de zonas, estado NORMAL, estado ALERTA, zona sin dispositivos, identificador inexistente y actualización dinámica de los datos mediante JSON.



La versión entregada corresponde al commit definido para la evaluación de la Fase 1.



