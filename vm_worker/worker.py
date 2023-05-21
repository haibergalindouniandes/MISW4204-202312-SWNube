
# Constantes
import json
import os
import tarfile
import tempfile
import psycopg2
import py7zr
from zipfile import ZIP_DEFLATED, ZipFile
from celery import Celery
from datetime import datetime
from google.cloud import storage

# Constantes
DB_USER = os.getenv("DB_USER", default="postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", default="dbpass")
DB_HOST = os.getenv("DB_HOST", default="postgres")
DB_NAME = os.getenv("DB_NAME", default="postgres")
DB_PORT = os.getenv("DB_PORT", default=5432)
RABBIT_USER = os.getenv("RABBIT_USER", default="ConverterUser")
RABBIT_PASSWORD = os.getenv("RABBIT_PASSWORD", default="ConverterPass")
RABBIT_HOST = os.getenv("RABBIT_HOST", default="rabbitmq_broker")
RABBIT_PORT = os.getenv("RABBIT_PORT", default=5672)
RABBIT_VHOST = os.getenv("RABBIT_VHOST", default="vhost_converter")
SEPARATOR_SO = os.getenv("SEPARATOR_SO", default="/")
TMP_PATH = os.getenv("TMP_PATH", default="tmp")
CELERY_TASK_NAME = os.getenv("CELERY_TASK_NAME", default="celery")
BROKER_URL = f"pyamqp://{RABBIT_USER}:{RABBIT_PASSWORD}@{RABBIT_HOST}//"
FILES_PATH = f"files{SEPARATOR_SO}"
COMPRESSED_PATH_FILES = os.getenv("COMPRESSED_PATH_FILES", default="compressed_files")
LOG_FILE = os.getenv("LOG_FILE", default="log_worker.txt")
BUCKET_GOOGLE = os.getenv("BUCKET_GOOGLE", default="bucket-converter-app")
PATH_PRIVATE_KEY = os.getenv("PATH_PRIVATE_KEY", default="dauntless-bay-384421-56876ce150d4.json")

# Configuramos Celery
celery = Celery(CELERY_TASK_NAME, broker=BROKER_URL)

# Funcion para el procesamiento de los archivos
@celery.task(name=CELERY_TASK_NAME)
def process_file(args):
    message = args
    try:
        registry_log(
            "INFO", f"<=================== Inicio del procesamiento de la tarea ===================>")
        registry_log("INFO", f"==> Tarea [{str(args)}]")            

        # Validamos la tarea
        db = connect_db()
        task = get_task_by_id(db, message['id'])
        if task == None:
            raise Exception(f"==> La tarea [{message['id']}] fue eliminada")

        userFilePathDestination = f"{FILES_PATH}{message['id_user']}{SEPARATOR_SO}{COMPRESSED_PATH_FILES}"
        registry_log("INFO", f"==> Ruta del archivo [{userFilePathDestination}]")   
        
        # Creamos directory temporal si no existe
        create_temp_directory()
        
        # Convertimos archivo y lo subimos al servidor
        fileCompressed = compress_file_and_upload(message["file_origin_path"], userFilePathDestination,
                              message["file_name"], message["file_new_format"], message["file_format"])
        
        # Actualizamos tarea en BD
        update_task(db, message['id'], fileCompressed)
        registry_log("INFO", f"==> Se actualiza la tarea en BD [{message['id']}]")
    except Exception as e:
        registry_log("ERROR", f"==> {str(e)}")
    finally:
        registry_log(
            "INFO", f"<=================== Fin del procesamiento de la tarea ===================>")


# Funcion para comprimir archivos
def compress_file_and_upload(fullFilePathOrigin, filePathCompressed, fileName, fileConverterExt, originExt):
    fileProcessed = None
    temporaryPath = TMP_PATH
    tempDir = tempfile.TemporaryDirectory(dir=temporaryPath)
    registry_log("INFO", f"==> Se crea temporalmente el directorio [{tempDir.name}]")
    # Descargamos el archivo temporalmente
    fileDownloaded = download_file(fullFilePathOrigin, tempDir, fileName, originExt)
    
    # Comprimimos el archivo
    if fileConverterExt.lower() == '.zip':
        fileProcessed = compress_in_zip(
            fileDownloaded.name, tempDir.name, fileName, fileConverterExt, originExt)
    if fileConverterExt.lower() == '.7z':
        fileProcessed = compress_in_7zip(
            fileDownloaded.name, tempDir.name, fileName, fileConverterExt, originExt)
    if fileConverterExt.lower() == '.tar.gz':
        fileProcessed = compress_in_tgz(
            fileDownloaded.name, tempDir.name, fileName, fileConverterExt, originExt)
    if fileConverterExt.lower() == '.tar.bz2':
        fileProcessed = compress_in_tbz(
            fileDownloaded.name, tempDir.name, fileName, fileConverterExt, originExt)
    
    # Subimos el archivo comprimido
    fileUpload = upload_file(fileProcessed, filePathCompressed, f"{fileName}{fileConverterExt}")
    
    return fileUpload

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

# Funcion que permite conectarnos a google storage
def download_file(fullFilePathOrigin, tempDir, fileName, originExt):
    # Nos conectamos al bucket
    client = connect_storage()
    bucket = storage.Bucket(client, BUCKET_GOOGLE)
    blob = bucket.blob(fullFilePathOrigin)
    pathFileToDownload = f"{tempDir.name}{SEPARATOR_SO}{fileName}{originExt}"
    # Descargamos temporalmente el archivo
    with open(pathFileToDownload, 'wb') as fileDownloaded:
        blob.download_to_filename(pathFileToDownload)
    
    registry_log("INFO", f"==> Se realiza la descarga de archivos [{fileDownloaded.name}]")    
    return fileDownloaded

# Funcion que permite subir un archivo al bucket
def upload_file(fileCompressed, filePathDestination, fileNameSanitized):
    client = connect_storage()
    # Nos conectamos al bucket
    bucket = storage.Bucket(client, BUCKET_GOOGLE)
    fullFilePathUpload = f"{filePathDestination}{SEPARATOR_SO}{fileNameSanitized}"
    blob = bucket.blob(fullFilePathUpload)
    blob.upload_from_filename(fileCompressed)
    registry_log("INFO", f"==> Se realiza la subid de archivos [{fullFilePathUpload}]")
    return fullFilePathUpload
    
    
# Funcion que permite conectarnos a google storage
def connect_storage():
    # Nos Autenticamos con el service account private key
    return storage.Client.from_service_account_json(PATH_PRIVATE_KEY)

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

# Funcion para crear el diretorio temporal
def create_temp_directory():
    isExist = os.path.exists(TMP_PATH)
    if not isExist:
        os.makedirs(TMP_PATH)
        registry_log("INFO",f"==> Se crea directorio [{TMP_PATH}]")

# Funcion para resgitrar logs
def registry_log(severity, message):
    with open(LOG_FILE, 'a') as file:
        file.write(
            f"[{severity}]-[{datetime.now()}]-[{message}]\n")

