#!/bin/sh
# Validamos si existe el directorio gcs_shared 
if [ -d "/home/gcs_shared" ] 
then
    echo "Desmontando directorio /home/gcs_shared ..."
    umount /home/gcs_shared
    echo "Eliminando directorio /home/gcs_shared ..."
    rm -rf /home/gcs_shared
    echo "Creando directorio /home/gcs_shared ..."
    mkdir /home/gcs_shared
    echo "Otorngando permisos al directorio /home/gcs_shared ..."
    chmod 777 /home/gcs_shared
else
    echo "Creando directorio /home/gcs_shared ..."
    mkdir /home/gcs_shared
    echo "Otorgando permisos al directorio /home/gcs_shared ..."
    chmod 777 /home/gcs_shared
fi
echo "Montando bucket en el directorio /home/gcs_shared ..."
gcsfuse bucket-converter-web-app /home/gcs_shared