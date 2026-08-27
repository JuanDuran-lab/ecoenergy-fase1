Análisis — EcoEnergy Fase 1

1\. Descripción de la solución



La aplicación EcoEnergy fue desarrollada con Django utilizando archivos JSON como fuente de datos.



La aplicación permite consultar las zonas de consumo energético y revisar el detalle de los dispositivos asociados a cada zona.



Los datos se cargan desde:



data/zonas.json

data/dispositivos.json

data/categorias.json



Las relaciones entre los registros se resuelven mediante identificadores en Python.



No se utilizan Models, migraciones, ORM ni una base de datos para almacenar los datos del caso.



2\. Estructura de los datos

Zonas



Archivo:



data/zonas.json



Claves principales:



id

nombre

limite\_kwh



Cada zona posee un identificador único.



Dispositivos



Archivo:



data/dispositivos.json



Claves principales:



id

nombre

consumo\_kwh

zona\_id

categoria\_id



Cada dispositivo posee un identificador único.



Categorías



Archivo:



data/categorias.json



Claves principales:



id

nombre

descripcion



Cada categoría posee un identificador único.



3\. Relaciones

Dispositivo → Zona



La relación se establece mediante:



dispositivos.zona\_id → zonas.id



Un dispositivo pertenece a una zona.



Una zona puede tener cero, uno o varios dispositivos.



Multiplicidad:



Zona 1 : N Dispositivos



Esto permite que una zona no tenga dispositivos sin que la aplicación deje de funcionar.



Dispositivo → Categoría



La relación se establece mediante:



dispositivos.categoria\_id → categorias.id



Cada dispositivo pertenece a una categoría.



Una categoría puede estar asociada a cero, uno o varios dispositivos.



Multiplicidad:



Categoría 1 : N Dispositivos



4\. Claves de conexión



Las claves utilizadas para resolver las relaciones son:



Relación	Clave origen	Clave destino

Dispositivo → Zona	zona\_id	zonas.id

Dispositivo → Categoría	categoria\_id	categorias.id



Estas relaciones se resuelven mediante estructuras y operaciones de Python.



5\. Procesamiento de la información



La aplicación utiliza una función para cargar los archivos JSON.



Las Views realizan posteriormente las operaciones necesarias:



Cargar los datos desde los archivos JSON.

Buscar la zona solicitada.

Filtrar los dispositivos correspondientes a la zona.

Contar los dispositivos.

Sumar el consumo de los dispositivos.

Buscar la categoría correspondiente a cada dispositivo.

Comparar el consumo total con el límite de la zona.

Determinar el estado NORMAL o ALERTA.

Enviar los resultados al Template.



El HTML se utiliza para presentar la información y no para realizar los cálculos principales.



6\. Regla de estado



El estado de una zona se determina mediante la siguiente regla:



consumo\_total > limite\_kwh → ALERTA

consumo\_total <= limite\_kwh → NORMAL



Ejemplo:



Zona Sur:



300 + 600 = 900 kWh



Límite:



800 kWh



Como:



900 > 800



el estado corresponde a:



ALERTA



7\. Comportamiento dinámico



La aplicación no depende de una cantidad fija de registros.



Los dispositivos de una zona se obtienen recorriendo dispositivos.json y filtrando mediante zona\_id.



Por esta razón, si se agregan nuevos registros válidos al JSON, la aplicación puede incorporarlos automáticamente sin crear una View o un bloque HTML específico para cada elemento.



También se contempla el caso en que una zona no tenga dispositivos.



En ese caso:



La cantidad de dispositivos es 0.

El consumo total es 0.

La aplicación continúa funcionando.

El Template muestra el mensaje Esta zona no tiene dispositivos.

8\. Manejo de zona inexistente



Cuando se solicita una zona mediante un identificador que no existe en zonas.json, la View genera una respuesta HTTP 404 mediante Http404.



Ejemplo:



/zonas/999/



Resultado:



404 — La zona no existe



Esto evita que una zona inexistente produzca un error interno de servidor.



9\. Templates



Los Templates utilizan herencia mediante:



base.html



Las páginas principales son:



lista.html

detalle.html



base.html contiene la estructura común de la aplicación, incluyendo el encabezado, navegación y carga de Bootstrap.



Los Templates reciben información calculada por las Views mediante el contexto de Django.



10\. Matriz de criterios de aceptación

Criterio	Archivo / Componente	Prueba

CA-01	views.py, lista.html, zonas.json	Abrir /zonas/ y comprobar que aparecen todas las zonas

CA-02	views.py, lista.html, dispositivos.json	Comprobar nombre, límite, cantidad de dispositivos y botón de detalle

CA-03	views.py, detalle.html, JSON	Abrir el detalle y comprobar dispositivos, categorías, consumo y métricas

CA-04	views.py	Agregar/modificar datos y comprobar que cantidades y sumas cambian automáticamente

CA-05	views.py, detalle.html	Comprobar NORMAL y ALERTA con diferentes consumos

CA-06	dispositivos.json, views.py, Templates	Agregar un dispositivo válido y comprobar que aparece sin modificar código

CA-07	views.py, detalle.html	Dejar dispositivos.json sin registros y comprobar el mensaje de zona sin dispositivos

CA-08	views.py	Solicitar /zonas/999/ y comprobar respuesta HTTP 404

CA-09	Templates, Bootstrap	Aumentar registros y comprobar que navegación y controles siguen accesibles

CA-10	detalle.html	Comprobar que una tabla extensa permite desplazamiento dentro de su contenedor

CA-11	base.html, lista.html, detalle.html	Revisar jerarquía visual, navegación, títulos, tarjetas, botones y tablas

CA-12	detalle.html	Comprobar que NORMAL y ALERTA utilizan texto e indicadores visuales

CA-13	Proyecto completo	Ejecutar python manage.py check y ejecutar el proyecto desde el repositorio

11\. Pruebas realizadas



Se realizaron las siguientes pruebas:



python manage.py check sin errores.

Listado de zonas mediante /zonas/.

Consulta de Zona Norte.

Consulta de Zona Centro.

Consulta de Zona Sur.

Verificación del estado NORMAL.

Verificación del estado ALERTA.

Consulta de una zona inexistente mediante /zonas/999/.

Prueba temporal con una colección de dispositivos vacía.

Prueba agregando un nuevo dispositivo válido al JSON.

Verificación de que los cálculos se actualizan dinámicamente.

Verificación de que las tablas utilizan un contenedor adaptable.

12\. Conclusión



La solución implementa el alcance solicitado para la Fase 1 utilizando Django, Python, archivos JSON y Templates.



La información se procesa dinámicamente desde los archivos JSON y las relaciones se resuelven mediante identificadores en Python, sin utilizar Models, ORM, migraciones ni CRUD.

