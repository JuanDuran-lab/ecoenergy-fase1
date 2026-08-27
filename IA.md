Registro de uso de IA — EcoEnergy Fase 1

1\. Herramienta utilizada



Se utilizó ChatGPT como herramienta de apoyo durante el desarrollo de la Fase 1.



La IA fue utilizada como apoyo para comprender conceptos, revisar código, proponer estructuras y detectar errores durante el desarrollo.



La solución fue implementada y probada en el entorno local del estudiante.



2\. Uso de la IA



La IA se utilizó principalmente para:



Comprender conceptos relacionados con Django, Views, Templates y archivos JSON.

Analizar errores mostrados por Django durante la ejecución.

Revisar y corregir código Python.

Proponer estructuras HTML utilizando Bootstrap.

Revisar la organización de los Templates.

Ayudar a identificar los criterios de aceptación que debía cumplir la aplicación.

Proponer pruebas para comprobar el comportamiento dinámico de la aplicación.

Apoyar la elaboración de la documentación del proyecto.

3\. Prompts y solicitudes realizadas



Entre las solicitudes realizadas durante el desarrollo se encuentran:



Explicar en términos simples qué solicita la Fase 1.

Explicar qué es JSON y cómo se utilizaría en el proyecto.

Explicar qué son los Templates de Django y por qué se utilizan con HTML.

Guiar paso a paso la creación de un proyecto Django.

Analizar errores de ejecución como ModuleNotFoundError, FileNotFoundError y NameError.

Revisar la carga de archivos JSON desde Django.

Implementar el listado de zonas.

Implementar el detalle de una zona.

Relacionar dispositivos con zonas mediante zona\_id.

Relacionar dispositivos con categorías mediante categoria\_id.

Calcular dinámicamente la cantidad de dispositivos y el consumo total.

Implementar los estados NORMAL y ALERTA.

Implementar una respuesta 404 para una zona inexistente.

Manejar una zona sin dispositivos.

Comprobar que los nuevos registros agregados al JSON se incorporen dinámicamente.

Mejorar la interfaz mediante Templates y Bootstrap.

Revisar los archivos de documentación requeridos para la entrega.

4\. Partes utilizadas de las respuestas de IA



Se utilizaron como apoyo algunas propuestas de código relacionadas con:



Carga de archivos JSON mediante Python.

Filtrado de dispositivos por zona\_id.

Búsqueda de categorías mediante categoria\_id.

Cálculo de cantidades y consumo.

Determinación del estado de una zona.

Manejo de respuestas 404.

Uso de estructuras de Templates de Django.

Uso de componentes Bootstrap.

Uso de table-responsive para tablas extensas.

Estructuración de la documentación del proyecto.



Las propuestas fueron adaptadas e integradas al proyecto según los archivos y estructura existentes.



5\. Cambios realizados por el estudiante



Durante el desarrollo se realizaron modificaciones propias sobre las propuestas recibidas, entre ellas:



Creación y configuración del proyecto Django.

Creación de la aplicación zonas.

Organización de las carpetas del proyecto.

Creación y organización de los archivos JSON.

Configuración de las URLs.

Integración de Views y Templates.

Adaptación de las rutas y nombres utilizados por el proyecto.

Corrección de rutas de acceso a los archivos JSON.

Corrección de errores encontrados durante la ejecución.

Pruebas de las rutas /zonas/ y /zonas/<id>/.

Prueba de una zona inexistente mediante /zonas/999/.

Prueba temporal con dispositivos.json vacío.

Prueba agregando temporalmente un nuevo dispositivo.

Restauración de los datos originales después de las pruebas.

Verificación final mediante python manage.py check.

6\. Verificación de la solución



Las propuestas de IA no fueron consideradas como resultado final sin comprobación.



La aplicación fue ejecutada localmente y se verificaron los siguientes casos:



Listado de zonas.

Detalle de las zonas existentes.

Cálculo del consumo total.

Cálculo de la cantidad de dispositivos.

Estado NORMAL.

Estado ALERTA.

Zona sin dispositivos.

Zona inexistente con respuesta 404.

Incorporación dinámica de un nuevo dispositivo desde el JSON.

Visualización de las categorías.

Adaptación de tablas extensas.

Ejecución correcta de python manage.py check.

7\. Declaración



La IA fue utilizada como herramienta de apoyo para aprendizaje, análisis, revisión y desarrollo.



El estudiante revisó, adaptó, integró y probó las propuestas utilizadas en el proyecto y debe ser capaz de explicar el funcionamiento de la solución presentada.

