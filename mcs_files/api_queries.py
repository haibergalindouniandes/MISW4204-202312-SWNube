from base import request, Resource, api, app, Task, jwt_required, tempfile, send_file, ftplib, os, traceback, socket, datetime

# Constantes
PRINT_PROPERTIES = os.getenv("PRINT_PROPERTIES", default=False)
FTP_SERVER = os.getenv("FTP_SERVER", default="172.168.0.12")
FTP_PORT = os.getenv("FTP_PORT", default=21)
FTP_USER = os.getenv("FTP_USER", default="converteruser")
FTP_PASSWORD = os.getenv("FTP_PASSWORD", default="Converter2023")
LOG_FILE = os.getenv("LOG_FILE", default="log_files.txt")
SHARED_PATH = os.getenv("SHARED_PATH", default="shared")
ORIGIN_PATH_FILES = os.getenv("ORIGIN_PATH_FILES", default="origin_files")
COMPRESSED_PATH_FILES = os.getenv("COMPRESSED_PATH_FILES", default="compressed_files")
SEPARATOR_SO = os.getenv("SEPARATOR_SO", default="/")
TMP_PATH = os.getenv("TMP_PATH", default="tmp")
HOME_PATH = os.getcwd()

# Clase que contiene la logica para descargar los archivos
class FileDownloadResource(Resource):
    @jwt_required()
    def get(id_file, id_task):
        registry_log("INFO", f"<=================== Inicio de la descarga de archivos ===================>")
        try:
            # Se valida si viene fileType
            queryParams = request.args
            if not 'fileType' in queryParams:
                registry_log("ERROR", f"==> El parámetros fileType es obligatorio")
                registry_log("ERROR", f"<=================== Fin de la descarga de archivos ===================>")
                return {"msg": f"El parámetros fileType es obligatorio"}, 400
            
            # Se valida el tipo de archivo a retornar
            fileType = queryParams["fileType"]
            if fileType != 'original' and fileType != 'compressed':
                registry_log("ERROR", f"==> Solo se permiten los siguiente formatos [original, compressed]")
                registry_log("ERROR", f"<=================== Fin de la descarga de archivos ===================>")
                return {"msg": f"Solo se permiten los siguiente formatos [original, compressed]"}, 400
            
            # Se consulta la tarea con base al id
            registry_log("INFO", f"==> Se consultara la tarea [{id_task}]")
            task = Task.query.filter(Task.id == id_task).first()
            # Se valida si no existe la tarea
            registry_log("INFO", f"==> Resultado de la consulta [{str(task)}]")
            if task is None:
                registry_log("ERROR", f"==> La tarea con el id [{id_task}] no se encuentra registrada")
                registry_log("ERROR", f"<=================== Fin de la descarga de archivos ===================>")
                return {"msg": f"La tarea con el id [{id_task}] no se encuentra registrada"}, 400
            # Creamos directory temporal si no existe
            createTempDirectory()
            # Creamos directorio temporal
            temporaryPath = f"{HOME_PATH}{SEPARATOR_SO}{TMP_PATH}"
            tempDir = tempfile.TemporaryDirectory(dir=temporaryPath)
            registry_log("INFO", f"==> Directorio temporal creado [{tempDir.name}]")
            pathFileDownloaded = None
            # Descargamos el archivo
            if fileType == 'original':
                pathFileDownloaded = downloadFileFromServer(tempDir, task.file_name, task.file_format, task.file_origin_path)
            else:
                pathFileDownloaded = downloadFileFromServer(tempDir, task.file_name, task.file_new_format, task.file_convert_path)    
            registry_log("INFO", f"==> La a descarga de archivos fue realizada correctamente")
            registry_log("INFO", f"<=================== Fin de la descarga de archivos ===================>")
            # return {"msg": f"La tarea con el id [{id_task}] fue eliminada correctamente"}
            return send_file(pathFileDownloaded, as_attachment=True)
        except Exception as e:
            traceback.print_stack()
            registry_log("ERROR", f"==> Se produjo el siguiente [{str(e)}]")
            registry_log("ERROR", f"<=================== Fin de la descarga de archivos ===================>")
            return {"msg": str(e)}, 500


# Funcion para crear el diretorio temporal
def createTempDirectory():
    isExist = os.path.exists(TMP_PATH)
    if not isExist:
        os.makedirs(TMP_PATH)
        registry_log("INFO",f"==> Se crea directorio [{TMP_PATH}]")

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

# Funcion que permite realizar el cierre de conexiones del servidor FTP
def closeConnectionServer(ftp_server):
    ftp_server.quit()
    ftp_server.close()
    registry_log("INFO", f"==> Se cierra la conexion con el servidor FTP")

# Funcion quer permite realizar la descarga de archivos del servidor FTP
def downloadFileFromServer(tempDir, fileName, extension, filePath):
    ftp_server = connectFtp()
    # Descargamos el archivo original temporalmente
    with open(f"{tempDir.name}{SEPARATOR_SO}{fileName}{extension}", 'wb') as fileDownloaded:
        ftp_server.retrbinary(f"RETR {filePath}", fileDownloaded.write)
    closeConnectionServer(ftp_server)
    registry_log("INFO", f"==> Se descarga temporalmente el archivo [{tempDir.name}{SEPARATOR_SO}{fileName}{extension}]")
    return f"{tempDir.name}{SEPARATOR_SO}{fileName}{extension}"

# Funcion para resgitrar logs
def registry_log(severity, message):
    with open(LOG_FILE, 'a') as file:
        file.write(
            f"[{severity}]-[{datetime.now()}]-[{message}]\n")

# Agregamos los recursos
api.add_resource(FileDownloadResource, "/api/files/<int:id_task>")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
