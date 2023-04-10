from base import db, Task, celery, ftplib, task_schema, os, tempfile, tarfile, py7zr, datetime, ZipFile, ZIP_DEFLATED

# Constantes
FTP_SERVER = os.getenv("FTP_SERVER", default="ftp_server")
FTP_PORT = os.getenv("FTP_PORT", default=21)
FTP_USER = os.getenv("FTP_USER", default="ftp_user")
FTP_PASSWORD = os.getenv("FTP_PASSWORD", default="ftp_password")
FTP_ENCODING = os.getenv("FTP_ENCODING", default="utf-8")
SHARED_PATH = os.getenv("SHARED_PATH", default="shared")
ORIGIN_PATH_FILES = os.getenv("ORIGIN_PATH_FILES", default="origin_files")
COMPRESSED_PATH_FILES = os.getenv("COMPRESSED_PATH_FILES", default="compressed_files")
SEPARATOR_SO = os.getenv("SEPARATOR_SO", default="/")
TMP_PATH = os.getenv("TMP_PATH", default="tmp")
CELERY_TASK_NAME = os.getenv("CELERY_TASK_NAME", default="celery")
LOG_FILE = os.getenv("LOG_FILE", default="log_worker.txt")
HOME_PATH = os.getcwd()


# Funcion para el procesamiento de los archivos
@celery.task(name=CELERY_TASK_NAME)
def process_file(args):
    try:
        registry_log("INFO", f"<=================== Inicio del procesamiento de la tarea ===================>")
        registry_log("INFO", f"==> Tarea [{str(args)}]")
        message = args
        # Validamos la tarea
        updateTask = Task.query.filter(Task.id == int(message["id"])).first()
        if updateTask is None:
            raise Exception(f"La tarea [{message['id']}] fue eliminada")
        # Creamos directory temporal si no existe
        createTempDirectory()
        # Convertimos archivo
        compressFileAndUpload(message["file_origin_path"], message["file_name"],
                              message["file_format"], message["file_new_format"])
        
        updateTask.updated = datetime.now()
        updateTask.file_convert_path = f"/{SHARED_PATH}/{COMPRESSED_PATH_FILES}/{message['file_name']}{message['file_new_format']}"
        updateTask.status = 'processed'
        db.session.commit()
        registry_log("INFO", f"==> Se actualiza la tarea en BD [{task_schema.dump(updateTask)}]")
    except Exception as e:
        registry_log("ERROR", str(e))
    finally:
        registry_log("INFO", f"<=================== Fin del procesamiento de la tarea ===================>")

# Funcion para resgitrar logs
def registry_log(severity, message):
    with open(LOG_FILE, 'a') as file:
        file.write(
            f"[{severity}]-[{datetime.now()}]-[{message}]\n")

# Funcion para crear el diretorio temporal
def createTempDirectory():
    isExist = os.path.exists(TMP_PATH)
    if not isExist:
        os.makedirs(TMP_PATH)
        registry_log("INFO",f"==> Se crea directorio [{TMP_PATH}]")

# Funcion para comprimir archivos
def compressFileAndUpload(filePath, fileName, originExt, fileConverterExt):
    # Creamos directorio temporal
    temporaryPath = f"{HOME_PATH}{SEPARATOR_SO}{TMP_PATH}"
    tempDir = tempfile.TemporaryDirectory(dir=temporaryPath)
    registry_log("INFO", f"==> Directorio temporal creado [{tempDir.name}]")
    # Creamos directorio temporal
    fileProcessed = None
    # Conectamos con el servidor FTP
    ftp_server = ftplib.FTP()
    ftp_server.connect(FTP_SERVER, FTP_PORT)
    ftp_server.login(FTP_USER, FTP_PASSWORD)
    # force UTF-8 encoding
    ftp_server.encoding = FTP_ENCODING
    ftp_server.cwd(SHARED_PATH)
    registry_log("INFO", f"==> Se crea conexion con el servidor FTP y se accede a [{SHARED_PATH}]")
    # Validamos si existe el directorio file origin si no exite se crea
    if not COMPRESSED_PATH_FILES in ftp_server.nlst():
        # Create a new directory called foo on the server.
        ftp_server.mkd(COMPRESSED_PATH_FILES)
        registry_log("INFO", f"==> Se crea directorio [{COMPRESSED_PATH_FILES}]")
    # Descargamos el archivo original temporalmente
    with open(f"{tempDir.name}{SEPARATOR_SO}{fileName}{originExt}", 'wb') as fileDownloaded:
        ftp_server.retrbinary(f"RETR /{filePath}", fileDownloaded.write)
    registry_log("INFO", f"==> Se descarga temporalmente el archivo [{tempDir.name}{SEPARATOR_SO}{fileName}{originExt}]")
    # Comprimimos el archivo
    if fileConverterExt.lower() == '.zip':
        fileProcessed = compressInZip(tempDir.name, fileName, originExt, fileConverterExt)
    if fileConverterExt.lower() == '.7z':
        fileProcessed = compressIn7Zip(tempDir.name, fileName, originExt, fileConverterExt)
    if fileConverterExt.lower() == '.tar.gz':
        fileProcessed = compressInTgz(tempDir.name, fileName, originExt, fileConverterExt)
    if fileConverterExt.lower() == '.tar.bz2':
        fileProcessed = compressInTbz(tempDir.name, fileName, originExt, fileConverterExt)
    # Subimos el archivo
    if fileProcessed:
        ftp_server.cwd(COMPRESSED_PATH_FILES)
        file = open(f"{tempDir.name}{SEPARATOR_SO}{fileName}{fileConverterExt}", 'rb')
        ftp_server.storbinary(f"STOR {fileName}{fileConverterExt}", file)
        registry_log("INFO", f"==> Se sube archivo [{tempDir.name}{SEPARATOR_SO}{fileName}{fileConverterExt}]")
        # Cerramos conexion FTP y la apertura del archivo
        ftp_server.quit()
        file.close()

# Funcion para comprimir en formato zip
def compressInZip(filePath, fileName, originExt, fileConverterExt):
    registry_log("INFO", f"==> Inicia conversion en ZIP")
    # Comprimimos el archivo
    registry_log("INFO", f"==> Archivo origen [{filePath}{SEPARATOR_SO}{fileName}{originExt}]")
    registry_log("INFO", f"==> Archivo a crear [{filePath}{SEPARATOR_SO}{fileName}{fileConverterExt}]")
    with ZipFile(file=f"{filePath}{SEPARATOR_SO}{fileName}{fileConverterExt}", mode="w", compression=ZIP_DEFLATED) as file:
        file.write(f"{filePath}{SEPARATOR_SO}{fileName}{originExt}", f"{fileName}{originExt}")
    registry_log("INFO", f"==> Finaliza conversion en ZIP")
    return True

# Funcion para comprimir en formato 7Zip
def compressIn7Zip(filePath, fileName, originExt, fileConverterExt):
    registry_log("INFO", f"==> Inicia conversion en 7ZIP")
    # Comprimimos el archivo
    registry_log("INFO", f"==> Archivo origen [{filePath}{SEPARATOR_SO}{fileName}{originExt}]")
    registry_log("INFO", f"==> Archivo a crear [{filePath}{SEPARATOR_SO}{fileName}{fileConverterExt}]")
    with py7zr.SevenZipFile(f"{filePath}{SEPARATOR_SO}{fileName}{fileConverterExt}", 'w') as file:
        file.writeall(f"{filePath}{SEPARATOR_SO}{fileName}{originExt}", f"{fileName}{originExt}")
    registry_log("INFO", f"==> Finaliza conversion en 7ZIP")
    return True

# Funcion para comprimir en formato TGZ
def compressInTgz(filePath, fileName, originExt, fileConverterExt):
    registry_log("INFO", f"==> Inicia conversion en TAR.GZ")
    # Comprimimos el archivo
    registry_log("INFO", f"==> Archivo origen [{filePath}{SEPARATOR_SO}{fileName}{originExt}]")
    registry_log("INFO", f"==> Archivo a crear [{filePath}{SEPARATOR_SO}{fileName}{fileConverterExt}]")
    with tarfile.open(f"{filePath}{SEPARATOR_SO}{fileName}{fileConverterExt}", 'w:gz') as file:
        file.add(f"{filePath}{SEPARATOR_SO}{fileName}{originExt}", f"{fileName}{originExt}")
    registry_log("INFO", f"==> Finaliza conversion en TAR.GZ")
    return True

# Funcion para comprimir en formato BZ2
def compressInTbz(filePath, fileName, originExt, fileConverterExt):
    registry_log("INFO", f"==> Inicia conversion en TAR.BZ2")
    # Comprimimos el archivo
    registry_log("INFO", f"==> Archivo origen [{filePath}{SEPARATOR_SO}{fileName}{originExt}]")
    registry_log("INFO", f"==> Archivo a crear [{filePath}{SEPARATOR_SO}{fileName}{fileConverterExt}]")
    with tarfile.open(f"{filePath}{SEPARATOR_SO}{fileName}{fileConverterExt}", 'w:bz2') as file:
        file.add(f"{filePath}{SEPARATOR_SO}{fileName}{originExt}", f"{fileName}{originExt}")
    registry_log("INFO", f"==> Finaliza conversion en TAR.BZ2")
    return True
