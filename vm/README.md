# converter-microservices

## Instalación

El ejemplo del caso Foto Alpes es un proyecto en Flask que implementa microservicios y las tácticas vistas en el curso Arquitecturas ágiles de software. El presente repositorio contiene el código del ejemplo en diferentes ramas de acuerdo a los temas vistos. Las ramas del proyecto son:

- main: Rama que implementa CQRS, uso de tokens y comunicación asíncrona

Para ejecutar el proyecto localmente, es necesario instalar [Oracle VirtualBox](https://www.virtualbox.org/wiki/Downloads) en su pc. Una vez instalado, se debe descargar la imagen de la máquina virtual ([MISW4204-202312-SWNube_VM.zip](https://drive.google.com/file/d/14PT9IbhUV4ZkEBdkTz9K21rhILMzq3KJ/view)) e importarla en Virtualbox. Para importar la imagen se deben seguir los siguientes pasos:

1. Descargar el archivo MISW4204-202312-SWNube_VM.zip

2. Descomprimir el archivo descargado en el paso anterior

3. Abrir Oracle Virtualbox e ir al menú Máquina --> Añadir

   <img src="https://github.com/ci-cortesg/fotoalpes-microservices-examples/blob/main/img/Agregar_VM.png" alt="Agregar_VM" style="zoom:75%;" />

4. Ubicar la carpeta donde se descomprimió el archivo zip y seleccionar el archivo MISW4202-FotoAlpes-Microservicios-New.ovdx

   <img src="https://user-images.githubusercontent.com/110913673/231838077-83291dec-ab59-48e1-b333-1d7e63775689.png" alt="Seleccionar_Archivo_VM" style="zoom:75%;" />

5. En el menú izquierdo debe aparecer la máquina con el nombre del archivo seleccionado

6. Dar clic en el botón Configuración en la parte superior

7. En el menú izquierdo dar clic sobre la opción Sistema

8. En la opción Chipset seleccionar la opción ICH9

   <img src="https://github.com/ci-cortesg/fotoalpes-microservices-examples/blob/main/img/Change_Chipset_CH9.png" alt="Change_Chipset_CH9" style="zoom:75%;" />
   
9. En el menú izquierdo dar clic sobre la opción USB y desmarcar la opción "Habilitar Controlador USB"

   <img src="https://github.com/ci-cortesg/fotoalpes-microservices-examples/blob/main/img/Disable_USB.png" alt="Disable_USB" style="zoom:75%;" />
   
10. Dar clic en el botón Aceptar en la parte inferior derecha

11. Dar clic de nuevo en el botón Configuración en la parte superior

12. En el menú izquierdo dar clic otra vez sobre la opción Sistema

13. En la opción Chipset seleccionar la opción PIIX3

   <img src="https://github.com/ci-cortesg/fotoalpes-microservices-examples/blob/main/img/Change_Chipset_PIIX3.png" alt="Change_Chipset_PIIX3" style="zoom:75%;" />

14. Dar clic en el botón Aceptar en la parte inferior derecha

15. Dar clic en el botón Iniciar ubicado en la parte superior

   <img src="https://user-images.githubusercontent.com/110913673/231838904-3807ce00-8c40-43fb-9680-8e946bdaa72e.png" alt="Iniciar_VM" style="zoom:75%;" />

16. Una vez la máquina termine de cargar, debe visualizar la pantalla de inicio

   <img src="https://github.com/ci-cortesg/fotoalpes-microservices-examples/blob/main/img/Pantalla_Inicio_VM.png" alt="Pantalla_Inicio_VM" style="zoom:75%;" />

17. Ingresar con el usuario **estudiante** y la contraseña **Estudiante2021**

18. Ejecutar el siguiente comando:

   ```
   hostname -I
   ```

19. Tomar nota de la dirección ip que se despliega en pantalla, como aparece en la siguiente imagen:

    <img src="https://user-images.githubusercontent.com/110913673/231840937-b744124a-392a-41df-a106-4a63b4a9f33e.png" alt="Direccion_IP_VM" style="zoom:75%;" />

20. La dirección IP obtenida en el paso anterior corresponde a la dirección asociada al adaptador de red de la máquina virtual. Tome nota de esta dirección porque se utilizará para acceder a los servicios desde su pc local

21. Ubíquese en el directorio fotoalpes-microservices-examples ejecutando el siguiente comando:

    ```
    cd MISW4204-202312-SWNube
    ```

22. Para ejecutar los servicios, corra el siguiente comando:

    ```
    sudo docker-compose up
    ```
23. Una vez termine la instalación se debera ver la consola de la siguiente manera, lo que indicará que ya esta listo para recibir peticiones.
    
   <img src="https://user-images.githubusercontent.com/110913673/231844481-f3638266-e68b-42c0-bc36-129294961708.png" alt="Direccion_IP_VM" style="zoom:75%;" />
