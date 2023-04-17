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

## Arquitectura del proyecto

### Vista de contexto

<img src="https://user-images.githubusercontent.com/110913673/232339273-2ff1d417-6aee-47cb-90d6-b0ffae5343fc.png" alt="Vista_contexto" style="zoom:75%;" />

### Vista funcional

<img src="https://user-images.githubusercontent.com/110913673/232339339-b1eb6bde-9ea1-49bd-b352-7aecb81e2992.png" alt="Vista_funcional" style="zoom:75%;" />

### Vista de información
#### Modelo de información

<img src="https://user-images.githubusercontent.com/110913673/232339391-b32ccaf3-597e-4285-a641-2b358f488c28.png" alt="Modelo_informacion" style="zoom:75%;" />

#### Flujo de navegación

<img src="https://user-images.githubusercontent.com/110913673/232339408-da0898ba-8efd-499c-81b8-1b37682ea838.png" alt="flujo_navegacion" style="zoom:75%;" />

### Vista de despliegue

<img src="https://user-images.githubusercontent.com/110913673/232339420-2d9592d8-cf77-4b58-9e9b-3b7fa5c8d409.png" alt="vista_despliegue" style="zoom:75%;" />

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

### Estructura de carpetas del proyecto

El proyecto esta compuesto por la siguiente estructura de carpetas:

<img src="https://user-images.githubusercontent.com/110913673/232340051-7cd0d19b-e288-4d72-8d14-d5e24c5de5c4.png" alt="estructura_carpetas" style="zoom:75%;" />

- **collections:** En esta carpeta se encuentra el proyecto en Postman, que contiene la configuración para poder realizar la ejecución o consumo de las diferentes funcionalidades que expone la aplicación

- **jmeter:** En esta carpeta se encuentra los TestCase que se implementarón con la herramienta JMeter, para validar la carga que puede soportar la aplicación. También se encuentra los archivos utilizados para estas pruebas 

- **nginx:** En esta carpeta se encuentra el archivo de configuración de NGinx para la implementación como Proxy Reverse, que permite exponer las funcionalidades a través de un único punto de entrada (<IP_HOST>:8080) 

- **rabbit_mq:** En esta carpeta se encuentran los archivos de configuración de Rabbit MQ, que se utiliza en el proyecto como Broker de mensajeria para alojar tareas que serán procesadas de manera asíncrona 

- **servies:** En esta carpeta se encuentran los componentes que hacen parte del Microservicio **mcs_converter** que expone las funcionalidad mencionadas anteriormente

- **vm:** En esta carpeta se encuentra el README.md que contiene la información para realizar la descarga, configuración y lanzamiento de la maquina virtual que contiene todo el proyecto funcional


## Instalación de componentes:
- En primera instancia se debe tener instalado **Docker**. Para esto se comparten los siguientes enlaces:
  - **Instalación de docker en Windows**: https://docs.docker.com/desktop/install/windows-install
  - **Instalación de docker en Linux Ubuntu**: https://docs.docker.com/engine/install/ubuntu
  - **Instalación de docker en Mac**: https://docs.docker.
  - Se debe clonar el proyecto **MISW4204-202312-SWNube**: [Repositorio](https://github.com/shiomar-salazar/MISW4204-202312-SWNube)
  
- **Docker**:
  - Desde la raiz del proyecto, se debe ejecutar en una terminal el siguiente comando **`docker compose up -d`** para que docker a través del archivo **`docker-compose.yaml`** realice la creación de las imagenes y el despliegue de los contenedores. Y esperamos a que las instancias queden arriba:

<img src="https://user-images.githubusercontent.com/110913673/232261466-389ebce9-0214-4644-8ab7-5f30d0375300.png" alt="Comando_docker_compose" style="zoom:75%;" />
  
- **JMeter**:

Para realizar la descarga de JMeter se puede hacer desde la página oficial [Descarga JMeter](https://jmeter.apache.org/download_jmeter.cgi)
<br/>
Una vez realizada la descarga y descompresión de los archivos -> Ir a la carpeta **`bin`** donde se instalo JMeter y ejecutar el archivo **`jmeter.bat`**.

<img src="https://user-images.githubusercontent.com/110913673/221445381-c93eefe5-b9c1-40eb-9d31-daf2de0bcacc.png" alt="jmeter" style="zoom:75%;" />

Una vez abierto JMeter ir a **`File`** -> **`Open`**.

<img src="https://user-images.githubusercontent.com/110913673/221445579-d0d7dd73-03d1-4ac6-908c-e716b8ea956d.png" alt="import_proyecto_jmeter" style="zoom:75%;" />

Seleccionamos el archivo de prueba del caso a lanzar **`TestCases_1_MISW4204-202312-SWNube.jmx o TestCases_2_MISW4204-202312-SWNube.jmx`** que se encuentra en la ruta **`MISW4204-202312-SWNube/jmeter`**.

<img src="https://user-images.githubusercontent.com/110913673/232346888-e9eef331-a21b-4e98-9a59-75ad51f0467c.png" alt="import_proyecto_jmeter" style="zoom:75%;" />

Por ultimo se ejecuta las pruebas.

<img src="https://user-images.githubusercontent.com/110913673/221446161-bda2d2ba-2fe6-41cb-9c9e-6338cac4f3d5.png" alt="ejecucion_pruebas" style="zoom:75%;" />

- **Máquina virtual**:

Como prerequisito se debe tener instalado VirtualBox y se puede descarga desde la página oficial Descarga [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
<br/>

Para realizar la instalación y configuración de la máquina virtual, la cual contiene todo el ambiente ya configurado para la ejecución de la aplicación. Se debe seguir la información consignada en el [README.md](https://github.com/shiomar-salazar/MISW4204-202312-SWNube/tree/development/vm)

<img src="https://user-images.githubusercontent.com/110913673/231838904-3807ce00-8c40-43fb-9680-8e946bdaa72e.png" alt="Iniciar_VM" style="zoom:75%;" />
