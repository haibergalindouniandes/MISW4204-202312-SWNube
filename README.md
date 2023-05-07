# MISW4204-202312-SWNube

## Equipo 16

## Integrantes:

|   Nombre                         |   Correo                      |
|----------------------------------|-------------------------------|
| Jhon Fredy Guzmán Caicedo        | jf.guzmanc1@uniandes.edu.co   |
| Haiber Humberto Galindo Sanchez  | h.galindos@uniandes.edu.co    |
| Jorge M. Carrillo                | jm.carrillo@uniandes.edu.co   |
| Shiomar Alberto Salazar Castillo | s.salazarc@uniandes.edu.co    |

## Objetivo del proyecto

Este proyecto tiene como objetivo brindar las funcionalidades que permitan la creación de cuentas de usuario, subir archivos en un formato especifico, crear tareas de conversión de formato (zip, 7zip, tar.gz, tar.bz2), convertir dichos archivos al formato deseado, consultar el estado de la tarea de conversión y descargar los archivos (original o convertido). 

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


### Estructura de carpetas del proyecto

El proyecto esta compuesto por la siguiente estructura de carpetas:

<img src="https://user-images.githubusercontent.com/110913673/232340051-7cd0d19b-e288-4d72-8d14-d5e24c5de5c4.png" alt="estructura_carpetas" style="zoom:75%;" />

- **collections:** En esta carpeta se encuentra el proyecto en Postman, que contiene la configuración para poder realizar la ejecución o consumo de las diferentes funcionalidades que expone la aplicación

- **jmeter:** En esta carpeta se encuentra los TestCase que se implementarón con la herramienta JMeter, para validar la carga que puede soportar la aplicación. También se encuentra los archivos utilizados para estas pruebas 

- **nginx:** En esta carpeta se encuentra el archivo de configuración de NGinx para la implementación como Proxy Reverse, que permite exponer las funcionalidades a través de un único punto de entrada (<IP_HOST>:8080) 

- **rabbit_mq:** En esta carpeta se encuentran los archivos de configuración de Rabbit MQ, que se utiliza en el proyecto como Broker de mensajeria para alojar tareas que serán procesadas de manera asíncrona 

- **servies:** En esta carpeta se encuentran los componentes que hacen parte del Microservicio **mcs_converter** que expone las funcionalidad mencionadas anteriormente

- **vm:** En esta carpeta se encuentra el README.md que contiene la información para realizar la descarga, configuración y lanzamiento de la maquina virtual que contiene todo el proyecto funcional

### Documentacion de Postman
https://documenter.getpostman.com/view/5238096/2s93Y5Nef1


