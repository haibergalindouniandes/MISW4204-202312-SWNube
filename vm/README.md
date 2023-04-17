# converter-microservices

## Instalación

Para ejecutar el proyecto localmente, es necesario instalar [Oracle VirtualBox](https://www.virtualbox.org/wiki/Downloads) en su pc. Una vez instalado, se debe descargar la imagen de la máquina virtual ([MISW4204-202312-SWNube_VM.zip](https://drive.google.com/file/d/14PT9IbhUV4ZkEBdkTz9K21rhILMzq3KJ/view)) e importarla en Virtualbox. Para importar la imagen se deben seguir los siguientes pasos:

1. Descargar el archivo MISW4204-202312-SWNube_VM.zip

2. Descomprimir el archivo descargado en el paso anterior

3. Abrir Oracle Virtualbox e ir al menú Máquina --> Añadir

   <img src="https://github.com/ci-cortesg/fotoalpes-microservices-examples/blob/main/img/Agregar_VM.png" alt="Agregar_VM" style="zoom:75%;" />

4. Ubicar la carpeta donde se descomprimió el archivo zip y seleccionar el archivo MISW4204-202312-SWNube_VM.ovdx

   ![image](https://user-images.githubusercontent.com/111320185/231919291-be90d829-8000-4937-a367-37834a9ee004.png)

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

18. Postaerior a lo anterior, iniciaremos sesión como usuario root, ingresando el siguiente commando `sudo su` y se nos pedira la contraseña del usuario root `Estudiante2021`

   <img src="https://user-images.githubusercontent.com/110913673/232261339-b7528a24-660f-4f1e-b242-919599002951.png" alt="Logueo_como_root" style="zoom:75%;" />

19. Ejecutar el siguiente comando:
   ```
   hostname -I
   ```

20. Tomar nota de la  primera dirección ip que se despliega en pantalla, como aparece en la siguiente imagen:

   <img src="https://user-images.githubusercontent.com/111320185/231919100-1793bee6-5752-4aca-8357-a804bbad01f1.png" alt="Comando_docker_compose" style="zoom:75%;" />

21. La dirección IP obtenida en el paso anterior corresponde a la dirección asociada al adaptador de red de la máquina virtual. Tome nota de esta dirección porque se utilizará para acceder a los servicios desde su pc local

22. Ubíquese en el directorio MISW4204-202312-SWNube ejecutando el siguiente comando:

    ```
    cd MISW4204-202312-SWNube
    ```

23. Para ejecutar los servicios, corra el siguiente comando y validar que queden en estado `done`:
    ```
    sudo docker-compose up -d
    ```       
24. Una vez los servicios esten arriba iniciaremos nuestro worker, para que este a la escuha de las diferente tareas de conversión que se envian. 

   <img src="https://user-images.githubusercontent.com/110913673/232261466-389ebce9-0214-4644-8ab7-5f30d0375300.png" alt="Comando_docker_compose" style="zoom:75%;" />

25. Ingresamos el siguiente comando en la consola de nuestra maquina virtual para conectarnos con el contenedor mcs_converter:
```
docker exec -ti mcs_converter sh
``` 
   <img src="https://user-images.githubusercontent.com/110913673/232261598-1764218c-e7d7-4673-9cbc-77eeb9c5389f.png" alt="Comando_terminal_contenedor" style="zoom:75%;" />

26. Despues ingresamos el siguiente comando para inicializar nuestro worker:
```
celery -A worker.celery worker --pool=solo -l info
```
   <img src="https://user-images.githubusercontent.com/110913673/232261619-5d3ac13f-26a7-4dfb-80b6-0836816bbab7.png" alt="Comando_Worker" style="zoom:75%;" />

27. Cuando suba el worker debera visualizarse de la siguiente manera y ya se podra dar inicio con las pruebas correspondiente:

   <img src="https://user-images.githubusercontent.com/110913673/232261729-0ab8e906-a2f8-4e5d-aaa3-0acfcde93119.png" alt="Inicio_Celery_Worker" style="zoom:75%;" />

