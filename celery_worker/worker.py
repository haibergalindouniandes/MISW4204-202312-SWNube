from base import db, Task, celery, ftplib, task_schema, os, tempfile, tarfile, py7zr, datetime, ZipFile, ZIP_DEFLATED, socket

# Constantes
PRINT_PROPERTIES = os.getenv("PRINT_PROPERTIES", default=False)
FTP_SERVER = os.getenv("FTP_SERVER", default="172.168.0.12")
FTP_PORT = os.getenv("FTP_PORT", default=21)
FTP_USER = os.getenv("FTP_USER", default="converteruser")
FTP_PASSWORD = os.getenv("FTP_PASSWORD", default="Converter2023")
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
    message = args
    try:
        registry_log("INFO", f"<=================== Inicio del procesamiento de la tarea ===================>")
        registry_log("INFO", f"==> Tarea [{str(args)}]")
        if PRINT_PROPERTIES:
            registry_properties()
                
        # Validamos la tarea
        updateTask = Task.query.filter(Task.id == int(message["id"])).first()
        if updateTask is None:
            raise Exception(f"==> La tarea [{message['id']}] fue eliminada")
        # Creamos directory temporal si no existe
        createTempDirectory()
        # Convertimos archivo y lo subimos al servidor
        compressFileAndUpload(message["file_origin_path"], message["file_name"],
                              message["file_format"], message["file_new_format"])
        # Actualizamos tarea en BD
        updateTask.updated = datetime.now()
        updateTask.file_convert_path = f"/{SHARED_PATH}/{COMPRESSED_PATH_FILES}/{message['file_name']}{message['file_new_format']}"
        updateTask.status = 'processed'
        db.session.commit()
        registry_log("INFO", f"==> Se actualiza la tarea en BD [{task_schema.dump(updateTask)}]")
    except Exception as e:
        registry_log("ERROR", f"==> {str(e)}")
    finally:
        registry_log("INFO", f"<=================== Fin del procesamiento de la tarea ===================>")


# Funcion para registrar propiedades
def registry_properties():
    registry_log("INFO", f"==> Propiedades del sistema:")
    registry_log("INFO", f"==> SHARED_PATH={SHARED_PATH}")
    registry_log("INFO", f"==> ORIGIN_PATH_FILES={ORIGIN_PATH_FILES}")
    registry_log("INFO", f"==> COMPRESSED_PATH_FILES={COMPRESSED_PATH_FILES}")
    registry_log("INFO", f"==> SEPARATOR_SO={SEPARATOR_SO}")
    registry_log("INFO", f"==> HOME_PATH={HOME_PATH}")
    registry_log("INFO", f"==> TMP_PATH={TMP_PATH}")
    registry_log("INFO", f"==> CELERY_TASK_NAME={CELERY_TASK_NAME}")
    registry_log("INFO", f"==> FTP_SERVER={FTP_SERVER}")
    registry_log("INFO", f"==> FTP_PORT={FTP_PORT}")
    registry_log("INFO", f"==> FTP_USER={FTP_USER}")
    registry_log("INFO", f"==> FTP_PASSWORD={FTP_PASSWORD}")
    registry_log("INFO", f"==> LOG_FILE={LOG_FILE}")
    registry_log("INFO", f"==> Fin Propiedades del sistema")

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
    # Descargamos el archivo
    downloadFileFromServer(tempDir, fileName, originExt, filePath)
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
        updaloadFileToServer(tempDir, fileName, fileConverterExt)


# Funcion quer permite realizar la conexion con el servidor FTP
def connectFtp():
    ftp_server = ftplib.FTP()
    # ftp_server.ssl_version = ssl.PROTOCOL_TLS
    ftp_server.connect(FTP_SERVER, FTP_PORT)
    registry_log("INFO", f"==> Se conecta al puerto [{FTP_PORT}] del servidor FTP [{FTP_SERVER}]")
    ftp_server.login(FTP_USER, FTP_PASSWORD)
    # ftp_server.prot_p()
    ftp_server.af = socket.AF_INET6
    registry_log("INFO", f"==> Se genera el login en el servidor FTP [FTP_USER={FTP_USER}, FTP_PASSWORD={FTP_PASSWORD}]")
    ftp_server.set_debuglevel(2)
    return ftp_server

# Funcion quer permite realizar la descarga de archivos del servidor FTP
def downloadFileFromServer(tempDir, fileName, originExt, filePath):
    ftp_server = connectFtp()
    # Validamos si no existe el directorio shared
    if not SHARED_PATH in ftp_server.nlst():
        # Creamos el directorio file origin
        ftp_server.mkd(SHARED_PATH)
        registry_log("INFO", f"==> Se crea directorio [{SHARED_PATH}]")
    ftp_server.cwd(SHARED_PATH)
    # Descargamos el archivo original temporalmente
    with open(f"{tempDir.name}{SEPARATOR_SO}{fileName}{originExt}", 'wb') as fileDownloaded:
        ftp_server.retrbinary(f"RETR /{filePath}", fileDownloaded.write)
    closeConnectionServer(ftp_server)
    registry_log("INFO", f"==> Se descarga temporalmente el archivo [{tempDir.name}{SEPARATOR_SO}{fileName}{originExt}]")

# Funcion que permite realizar la descarga de archivos del servidor FTP
def updaloadFileToServer(tempDir, fileName, fileConverterExt):
    ftp_server = connectFtp()
    # Validamos si no existe el directorio shared
    if not SHARED_PATH in ftp_server.nlst():
        # Creamos el directorio file origin
        ftp_server.mkd(SHARED_PATH)
        registry_log("INFO", f"==> Se crea directorio [{SHARED_PATH}]")
    ftp_server.cwd(SHARED_PATH)
    # Validamos si existe el directorio file origin si no exite se crea
    if not COMPRESSED_PATH_FILES in ftp_server.nlst():
        # Create a new directory called foo on the server.
        ftp_server.mkd(COMPRESSED_PATH_FILES)
        registry_log("INFO", f"==> Se crea directorio [{COMPRESSED_PATH_FILES}]")
    
    ftp_server.cwd(COMPRESSED_PATH_FILES)
    file = open(f"{tempDir.name}{SEPARATOR_SO}{fileName}{fileConverterExt}", 'rb')
    ftp_server.storbinary(f"STOR {fileName}{fileConverterExt}", file)
    registry_log("INFO", f"==> Se sube archivo [{tempDir.name}{SEPARATOR_SO}{fileName}{fileConverterExt}]")
    # Cerramos conexion FTP y la apertura del archivo
    closeConnectionServer(ftp_server)
    file.close()
 
# Funcion que permite realizar el cierre de conexiones del servidor FTP
def closeConnectionServer(ftp_server):
    ftp_server.quit()
    ftp_server.close()
    registry_log("INFO", f"==> Se cierra la conexion con el servidor FTP")
    
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
