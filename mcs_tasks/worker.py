import os
import tempfile
import tarfile
from zipfile import ZipFile
import py7zr
from base import  db, celery
from datetime import datetime
from base import db, Task, celery, ftplib

# Constantes
SHARED_PATH = "shared"
ORIGIN_PATH_FILES = "origin_files"
COMPRESSED_PATH_FILES = "compressed_files"
# SEPARATOR_SO = "\\"
SEPARATOR_SO = "/"
HOME_PATH = os.getcwd()
TMP_PATH = 'tmp'

# Funcion para el procesamiento de los archivos
@celery.task(name="celery")
def process_file(args):
    print(f"<=================== Inicio del procesamiento de la tarea [{datetime.now()}] ===================>")
    print(f"==> Tarea [{str(args)}]")
    message = args
    # Creamos directory temporal si no existe
    createTempDirectory()
    # Convertimos archivo
    compressFileAndUpload(message["file_origin_path"], message["file_name"], message["file_format"], message["file_new_format"])
    # Consultamos archivo y actualizamos
    updateTask = Task.query.get_or_404(message["id"])
    updateTask.updated = datetime.now()
    updateTask.file_convert_path = f"/{SHARED_PATH}/{COMPRESSED_PATH_FILES}/{message['file_name']}{message['file_new_format']}"
    updateTask.status = 'processed'
    db.session.commit()
    print(f"<=================== Fin del procesamiento de la tarea [{datetime.now()}] ===================>")


# Funcion para crear el diretorio temporal
def createTempDirectory():
        isExist = os.path.exists(TMP_PATH)
        if not isExist:
            os.makedirs(TMP_PATH)

# Funcion para comprimir archivos
def compressFileAndUpload(filePath, fileName, originExt, fileConvertedExt):
    # Creamos directorio temporal
    temporaryPath = f"{HOME_PATH}{SEPARATOR_SO}{TMP_PATH}"
    tempDir = tempfile.TemporaryDirectory(dir = temporaryPath)
    print(f"==> Directorio temporal creado [{tempDir.name}]")
    # temporaryPath = tempDir.name
    # Creamos directorio temporal
    fileProcessed = None
    # Validamos si existe el directorio compressed files
    # Conectamos con el servidor FTP
    ftp_server = ftplib.FTP('ftp_server', 'ftp_user', 'ftp_password')
    # force UTF-8 encoding
    ftp_server.encoding = "utf-8"
    ftp_server.cwd(SHARED_PATH)
    # Validamos si existe el directorio file origin si no exite se crea
    if not COMPRESSED_PATH_FILES in ftp_server.nlst():
        # Create a new directory called foo on the server.
        ftp_server.mkd(COMPRESSED_PATH_FILES)
    # Descargamos el archivo original temporalmente
    with open(f"{tempDir.name}{SEPARATOR_SO}{fileName}{originExt}", 'wb') as fileDownloaded:
        ftp_server.retrbinary(f"RETR /{filePath}", fileDownloaded.write)
    # Comprimimos el archivo
    if fileConvertedExt.lower() == '.zip':
        fileProcessed = compressInZip(tempDir.name, fileName, originExt)
    if fileConvertedExt.lower() == '.7z':
        fileProcessed = compressIn7Zip(tempDir.name, fileName, originExt)
    if fileConvertedExt.lower() == '.tar.gz':
        fileProcessed = compressInTgz(tempDir.name, fileName, originExt)
    if fileConvertedExt.lower() == '.tar.bz2':
        fileProcessed = compressInTbz(tempDir.name, fileName, originExt)
    # Subimos el archivo
    if fileProcessed:
        ftp_server.cwd(COMPRESSED_PATH_FILES)
        file = open(f"{tempDir.name}{SEPARATOR_SO}{fileName}{fileConvertedExt}",'rb')
        ftp_server.storbinary(f"STOR {fileName}{fileConvertedExt}", file)
        # Cerramos conexion FTP y la apertura del archivos
        ftp_server.quit()
        file.close()

# Funcion para comprimir en formato zip
def compressInZip(filePath, fileName, originExt):
    print(f"==> Inicia conversion en ZIP [{datetime.now()}]")
    EXTENSION = '.zip'
    # Comprimimos el archivos
    with ZipFile(f"{filePath}{SEPARATOR_SO}{fileName}{EXTENSION}", 'w') as file:
        file.write(f"{filePath}{SEPARATOR_SO}{fileName}{originExt}", f"{fileName}{originExt}")
    print(f"==> Finaliza conversion en ZIP [{datetime.now()}]")
    return True

# Funcion para comprimir en formato 7Zip
def compressIn7Zip(filePath, fileName, originExt):
    print(f"==> Inicia conversion en 7ZIP [{datetime.now()}]")
    EXTENSION = '.7z'
    # Comprimimos el archivos
    with py7zr.SevenZipFile(f"{filePath}{SEPARATOR_SO}{fileName}{EXTENSION}", 'w') as file:
        file.writeall(f"{filePath}{SEPARATOR_SO}{fileName}{originExt}", f"{fileName}{originExt}")
    print(f"==> Finaliza conversion en 7ZIP [{datetime.now()}]")
    return True

# Funcion para comprimir en formato TGZ
def compressInTgz(filePath, fileName, originExt):
    print(f"==> Inicia conversion en TAR.GZ [{datetime.now()}]")
    EXTENSION = '.tar.gz'
    # Comprimimos el archivos
    with tarfile.open(f"{filePath}{SEPARATOR_SO}{fileName}{EXTENSION}", 'w:gz') as file:
        file.add(f"{filePath}{SEPARATOR_SO}{fileName}{originExt}", f"{fileName}{originExt}")
    print(f"==> Finaliza conversion en TAR.GZ [{datetime.now()}]")
    return True

# Funcion para comprimir en formato BZ2
def compressInTbz(filePath, fileName, originExt):
    print(f"==> Inicia conversion en TAR.BZ2 [{datetime.now()}]")
    EXTENSION = '.tar.bz2'
    # Comprimimos el archivos
    with tarfile.open(f"{filePath}{SEPARATOR_SO}{fileName}{EXTENSION}", 'w:bz2') as file:
        file.add(f"{filePath}{SEPARATOR_SO}{fileName}{originExt}", f"{fileName}{originExt}")
    print(f"==> Finaliza conversion en TAR.BZ2 [{datetime.now()}]")
    return True