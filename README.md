# MISW4204-202312-SWNube

## Equipo 16

## Integrantes:

|   Nombre                         |   Correo                      |
|----------------------------------|-------------------------------|
| Jhon Fredy Guzmán Caicedo        | jf.guzmanc1@uniandes.edu.co   |
| Haiber Humberto Galindo Sanchez  | h.galindos@uniandes.edu.co    |
| Jorge M. Carrillo                | jm.carrillo@uniandes.edu.co   |
| Shiomar Alberto Salazar Castillo | s.salazarc@uniandes.edu.co    |

## Arquitectura del proyecto

### Vista de contexto

![image](https://user-images.githubusercontent.com/110913673/232339273-2ff1d417-6aee-47cb-90d6-b0ffae5343fc.png)

### Vista funcional

![image](https://user-images.githubusercontent.com/110913673/232339339-b1eb6bde-9ea1-49bd-b352-7aecb81e2992.png)

### Vista de información
#### Modelo de información

![image](https://user-images.githubusercontent.com/110913673/232339391-b32ccaf3-597e-4285-a641-2b358f488c28.png)

#### Flujo de navegación

![image](https://user-images.githubusercontent.com/110913673/232339408-da0898ba-8efd-499c-81b8-1b37682ea838.png)

### Vista de despliegue

![image](https://user-images.githubusercontent.com/110913673/232339420-2d9592d8-cf77-4b58-9e9b-3b7fa5c8d409.png)

### Descripción de componentes utilizados en el proyecto
#### NGINX

Servidor web que también actúa como proxy de correo electrónico, proxy inverso y balanceador de carga. La estructura del software es asíncrona y controlada por eventos; lo cual permite el procesamiento de muchas solicitudes al mismo tiempo. En base a esta característica, dicho servidor web se adapta de manera perfecta para lo esperado en nuestras pruebas de esfuerzo

#### mcs_converter

Microservicio que encapsula todas las APIs diseñadas:
- **/api/auth/signup (POST):** para crear una cuenta de usuario en la aplicación. Para crear una cuenta se deben especificar los campos: usuario, correo electrónico y contraseña. El correo electrónico debe ser único en la plataforma dado que este se usa para la autenticación de los usuarios en la aplicación.
- **/api/auth/login (POST):** para iniciar sesión en la aplicación web, el usuario proveer el correo electrónico/usuario y la contraseña con la que creó la cuenta de usuario en la aplicación. La aplicación retorna un token de sesión si el usuario se autenticó de forma correcta, de lo contrario indica un error de autenticación y no permite utilizar los recursos de la aplicación.
- **/api/tasks (GET):** para listar todas las tareas de conversión de un usuario, el servicio entrega el identificador de la tarea, el nombre y la extensión del archivo original, a qué extensión desea convertir y si está disponible o no. El usuario debe proveer el token de autenticación para realizar dicha operación.
- **/api/tasks (POST):** para subir y cambiar el formato de un archivo. El usuario debe proveer el archivo que desea convertir, el formato al cual desea cambiarlo y el token de autenticación para realizar dicha operación. El archivo debe ser almacenado en la plataforma, se debe guardar en base datos la marca de tiempo en el que fue subido el archivo y el estado del proceso de API conversión (uploaded o processed). 
- **/api/tasks/<int:id_task> (GET):** para obtener la información de una tarea de conversión específica. El usuario debe proveer el token de autenticación para realizar dicha operación.
- **/api/files/<int:id_task> (GET):** que permite recuperar/descargar el archivo original o el archivo procesado de un usuario.
- **/api/tasks/<int:id_task>  (DELETE):** para borrar el archivo original y el archivo convertido de un usuario, si y solo si el estado del proceso de conversión es Disponible. El usuario debe proveer el identificador de la tarea y el token de autenticación para realizar dicha operación.

#### Celery

Biblioteca de Python de código abierto que se utiliza para la ejecución de tareas paralelas de forma distribuida fuera del ciclo de solicitud respuesta de HTTP. Permite ejecutar trabajos de forma asíncrona para no bloquear la ejecución normal del programa

#### Postgres

Sistema de gestión de bases de datos relacional orientado a objetos y de código abierto. Para nuestra aplicación, utilizamos dicho motor para levantar nuestra base de datos

#### RabbitMQ

Software de negociación de mensajes de código abierto que funciona como un broker de mensajería

#### Docker

Plataforma de contenerización de código abierto. Permite a los empaquetar aplicaciones en contenedores: componentes ejecutables estandarizados que combinan el código fuente de la aplicación con las bibliotecas del sistema operativo (SO) y las dependencias necesarias para ejecutar dicho código en cualquier entorno

#### New Relic APM

Herramienta de medición del rendimiento de una infraestructura de servicios, desde backend hasta frontend: medición del rendimiento de navegadores, APIs, servidores, aplicaciones móviles
