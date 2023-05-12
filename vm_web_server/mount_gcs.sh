#!/bin/sh
# Validamos si existe el directorio gcs_shared 
if [ -d "/home/gcs_shared" ] 
then
    echo "Directory /path/to/dir exists." 
else
    mkdir /home/gcs_shared
    chmod 777 /home/gcs_shared
fi
# Montamos el cloud storage
gcsfuse bucket-converter-web-app /home/gcs_shared