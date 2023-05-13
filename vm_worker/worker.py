
# Constantes
import json
import os
import tarfile
import tempfile
import psycopg2
import py7zr
from zipfile import ZIP_DEFLATED, ZipFile
from datetime import datetime
from google.cloud import storage, pubsub_v1

# Constantes
DB_USER = os.getenv("DB_USER", default="postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", default="dbpass")
DB_HOST = os.getenv("DB_HOST", default="34.27.130.169")
DB_NAME = os.getenv("DB_NAME", default="postgres")
DB_PORT = os.getenv("DB_PORT", default=5432)
SEPARATOR_SO = os.getenv("SEPARATOR_SO", default="/")
HOME_PATH = os.getenv("HOME_PATH", default="/home/gcs_shared")
FILES_PATH = f"{HOME_PATH}{SEPARATOR_SO}files{SEPARATOR_SO}"
COMPRESSED_PATH_FILES = os.getenv("COMPRESSED_PATH_FILES", default="compressed_files")
LOG_FILE = os.getenv("LOG_FILE", default="log_worker.txt")
PATH_PUBSUB_KEY = os.getenv("PATH_PUBSUB_KEY", default="misw4204-202312-swnube-pub-sub.json")
PATH_SUBSCRIBER = os.getenv("PATH_SUBSCRIBER", default="projects/misw4204-202312-swnube/subscriptions/tasks-topic-sub")
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = PATH_PUBSUB_KEY


# Funcion para el procesamiento de los archivos
def callback(message):
    try:
        registry_log(
            "INFO", f"<=================== Inicio del procesamiento de la tarea ===================>")
        registry_log("INFO", f"==> Tarea [{message.data}]")            

        jsonMessage = json.loads(message.data)
        # Validamos la tarea
        db = connect_db()
        task = get_task_by_id(db, jsonMessage['id'])
        if task == None:
            raise Exception(f"==> La tarea [{jsonMessage['id']}] fue eliminada")

        USER_FILES_PATH = f"{FILES_PATH}{jsonMessage['id_user']}{SEPARATOR_SO}{COMPRESSED_PATH_FILES}"
        # Convertimos archivo y lo subimos al servidor
        fileCompressed = compress_file_and_upload(jsonMessage["file_origin_path"], USER_FILES_PATH,
                              jsonMessage["file_name"], jsonMessage["file_new_format"], jsonMessage["file_format"])
        # Actualizamos tarea en BD
        update_task(db, jsonMessage['id'], fileCompressed)
        message.ack()
        registry_log("INFO", f"==> Se actualiza la tarea en BD [{jsonMessage['id']}]")
    except Exception as e:
        registry_log("ERROR", f"==> {str(e)}")
    finally:
        registry_log(
            "INFO", f"<=================== Fin del procesamiento de la tarea ===================>")


# Funcion para comprimir archivos
def compress_file_and_upload(fullFilePathOrigin, filePathCompressed, fileName, fileConverterExt, originExt):
    fileProcessed = None
    # Comprimimos el archivo
    if fileConverterExt.lower() == '.zip':
        fileProcessed = compress_in_zip(
            fullFilePathOrigin, filePathCompressed, fileName, fileConverterExt, originExt)
    if fileConverterExt.lower() == '.7z':
        fileProcessed = compress_in_7zip(
            fullFilePathOrigin, filePathCompressed, fileName, fileConverterExt, originExt)
    if fileConverterExt.lower() == '.tar.gz':
        fileProcessed = compress_in_tgz(
            fullFilePathOrigin, filePathCompressed, fileName, fileConverterExt, originExt)
    if fileConverterExt.lower() == '.tar.bz2':
        fileProcessed = compress_in_tbz(
            fullFilePathOrigin, filePathCompressed, fileName, fileConverterExt, originExt)
    return fileProcessed

# Funcion para comprimir en formato zip
def compress_in_zip(fullFilePathOrigin, filePathCompressed, fileName, fileConverterExt, originExt):
    registry_log("INFO", f"==> Inicia conversion en ZIP")
    # Comprimimos el archivo
    registry_log("INFO", f"==> Archivo origen [{fullFilePathOrigin}]")
    fileCompressed = f"{filePathCompressed}{SEPARATOR_SO}{fileName}{fileConverterExt}"
    registry_log("INFO", f"==> Archivo a crear [{fileCompressed}]")
    with ZipFile(file=fileCompressed, mode="w", compression=ZIP_DEFLATED) as file:
        file.write(fullFilePathOrigin, f"{fileName}{originExt}")
    registry_log("INFO", f"==> Finaliza conversion en ZIP")
    return fileCompressed

# Funcion para comprimir en formato 7Zip
def compress_in_7zip(fullFilePathOrigin, filePathCompressed, fileName, fileConverterExt, originExt):
    registry_log("INFO", f"==> Inicia conversion en 7ZIP")
    # Comprimimos el archivo
    registry_log("INFO", f"==> Archivo origen [{fullFilePathOrigin}]")
    fileCompressed = f"{filePathCompressed}{SEPARATOR_SO}{fileName}{fileConverterExt}"
    registry_log("INFO", f"==> Archivo a crear [{fileCompressed}]")
    with py7zr.SevenZipFile(fileCompressed, 'w') as file:
        file.writeall(f"{fullFilePathOrigin}", f"{fileName}{originExt}")
    registry_log("INFO", f"==> Finaliza conversion en 7ZIP")
    return fileCompressed

# Funcion para comprimir en formato TGZ
def compress_in_tgz(fullFilePathOrigin, filePathCompressed, fileName, fileConverterExt, originExt):
    registry_log("INFO", f"==> Inicia conversion en TAR.GZ")
    # Comprimimos el archivo
    registry_log("INFO", f"==> Archivo origen [{fullFilePathOrigin}]")
    fileCompressed = f"{filePathCompressed}{SEPARATOR_SO}{fileName}{fileConverterExt}"
    registry_log("INFO", f"==> Archivo a crear [{fileCompressed}]")
    with tarfile.open(f"{fileCompressed}", 'w:gz') as file:
        file.add(f"{fullFilePathOrigin}", f"{fileName}{originExt}")
    registry_log("INFO", f"==> Finaliza conversion en TAR.GZ")
    return fileCompressed

# Funcion para comprimir en formato BZ2
def compress_in_tbz(fullFilePathOrigin, filePathCompressed, fileName, fileConverterExt, originExt):
    registry_log("INFO", f"==> Inicia conversion en TAR.BZ2")
    # Comprimimos el archivo
    registry_log("INFO", f"==> Archivo origen [{fullFilePathOrigin}]")
    fileCompressed = f"{filePathCompressed}{SEPARATOR_SO}{fileName}{fileConverterExt}"
    registry_log("INFO", f"==> Archivo a crear [{fileCompressed}]")
    with tarfile.open(f"{fileCompressed}", 'w:bz2') as file:
        file.add(f"{fullFilePathOrigin}", f"{fileName}{originExt}")
    registry_log("INFO", f"==> Finaliza conversion en TAR.BZ2")
    return fileCompressed

# Funcion que retorna la conexion con BD
def connect_db():
    return psycopg2.connect(
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

# Funcion para obtener tarea
def get_task_by_id(db, id):
    try:
        cur = db.cursor()
        cur.execute(f"SELECT * FROM tasks WHERE id = {id}")
        # Fetch the data
        task = cur.fetchall()
        cur.close()
        return task
    except:
        if db is not None:
            db.close()
     
# Funcion para actualizar tarea
def update_task(db, id, file_convert_path):
    try:
        cur = db.cursor()
        stmt = f"UPDATE tasks  SET updated  = '{datetime.now()}', file_convert_path = '{file_convert_path}', status = 'compressed' WHERE id = {id}"
        cur.execute(stmt)
        db.commit()
        cur.close()
    except Exception as e:
        raise(str(e))
    finally:
        if db is not None:
            db.close()    

# Funcion para resgitrar logs
def registry_log(severity, message):
    with open(LOG_FILE, 'a') as file:
        file.write(
            f"[{severity}]-[{datetime.now()}]-[{message}]\n")


# Configuracion subscriber
subscriber = pubsub_v1.SubscriberClient()
streaming_pull_future = subscriber.subscribe(PATH_SUBSCRIBER, callback=callback)
print(f"Escuchando mensajes desde [{PATH_SUBSCRIBER}]")

with subscriber:
    try:
        streaming_pull_future.result()
    except:
        streaming_pull_future.cancel()
        streaming_pull_future.result()