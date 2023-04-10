from base import request, Resource, db, api, app, Task, jwt_required, task_schema, celery, ftplib, datetime, re, traceback, os

# Constantes
SHARED_PATH = os.getenv("SHARED_PATH", default="shared")
ORIGIN_PATH_FILES = os.getenv("ORIGIN_PATH_FILES", default="origin_files")
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", default="zip,7z,tgz,tbz")
EXP_REG_SANITIZATE = os.getenv("EXP_REG_SANITIZATE", default="[^-a-zA-Z0-9_.]+")
FTP_SERVER = os.getenv("FTP_SERVER", default="ftp_server")
FTP_PORT = os.getenv("FTP_PORT", default=21)
FTP_USER = os.getenv("FTP_USER", default="ftp_user")
FTP_PASSWORD = os.getenv("FTP_PASSWORD", default="ftp_password")
FTP_ENCODING = os.getenv("FTP_ENCODING", default="utf-8")
LOG_FILE = os.getenv("LOG_FILE", default="log_tasks.txt")


# Clase que contiene la logica para registrar tareas de conversión
class ConvertTaskFileResource(Resource):
    @jwt_required()
    def post(self):
        try:
            registry_log("INFO", f"<=================== Inicio de la creación de la tarea ===================>")
            # Validacion de parametros de entrada
            if not 'fileName' in request.files:
                return {"msg": "Parámetros de entrada invalidos. El parámetro 'fileName' es obligatorio."}, 400

            if not 'newFormat' in request.form:
                return {"msg": "Parámetros de entrada invalidos. El parámetro 'newFormat' es obligatorio."}, 400

            fileNewFormat = request.form['newFormat']

            if not fileNewFormat in ALLOWED_EXTENSIONS:
                return {"msg": f"Solo se permiten los siguiente formatos [{ALLOWED_EXTENSIONS}]"}, 400

            # Obtenemos el archivo
            file = request.files['fileName']
            dataFile = file.filename
            registry_log("INFO", f"==> Nombre original del archivo recibido [{dataFile}]")
            fileNameSanitized = re.sub(EXP_REG_SANITIZATE, '', dataFile)
            registry_log("INFO", f"==> Nombre sanitizado del archivo recibido [{fileNameSanitized}]")
            # Conectamos con el servidor FTP
            ftp_server = ftplib.FTP()
            ftp_server.connect(FTP_SERVER, FTP_PORT)
            ftp_server.login(FTP_USER, FTP_PASSWORD)
            # force UTF-8 encoding
            ftp_server.encoding = FTP_ENCODING
            ftp_server.cwd(SHARED_PATH)
            registry_log("INFO", f"==> Se crea conexion con el servidor FTP y se accede a [{SHARED_PATH}]")
            # Validamos si no existe el directorio file origin
            if not ORIGIN_PATH_FILES in ftp_server.nlst():
                # Creamos el directorio file origin
                ftp_server.mkd(ORIGIN_PATH_FILES)
                registry_log("INFO", f"==> Se crea directorio [{ORIGIN_PATH_FILES}]")
            ftp_server.cwd(ORIGIN_PATH_FILES)
            # Subimos el archivo
            ftp_server.storbinary(f"STOR {fileNameSanitized}", file)
            # Cerramos conexion
            ftp_server.quit()

            fileOriginPath = f"/{SHARED_PATH}/{ORIGIN_PATH_FILES}/{fileNameSanitized}"
            registry_log("INFO", f"==> Path sanitizado [{fileOriginPath}]")
            # Guardamos la informacion del archivo
            fileName = fileNameSanitized.rsplit('.', 1)[0]
            dataFile = dataFile.split('.')
            fileFormat = dataFile[-1]
            # Guardamos en base de datos la tarea
            newTask = Task(file_name=fileName, file_format=f".{fileFormat}",
                           file_new_format=formatHomologation(fileNewFormat),
                           file_origin_path=fileOriginPath, status='uploaded',
                           mimetype=file.mimetype)
            db.session.add(newTask)
            db.session.commit()
            registry_log("INFO", f"==> Se registra tarea en BD [{task_schema.dump(newTask)}]")
            # Enviamos de tarea asincrona
            args = (task_schema.dump(newTask))
            send_async_task.delay(args)
            # Retornamos respuesta exitosa
            registry_log("INFO", f"<=================== Fin de la creación de la tarea ===================>")
            return {"msg": "El archivo sera procesado", "task": task_schema.dump(newTask)}
        except Exception as e:
            traceback.print_stack()
            registry_log("INFO", f"<=================== Fin de la creación de la tarea ===================>")
            return {"msg": str(e)}, 500


# Funcion para resgitrar logs
def registry_log(severity, message):
    with open(LOG_FILE, 'a') as file:
        file.write(
            f"[{severity}]-[{datetime.now()}]-[{message}]\n")

# Funcion para homologar formatos de conversion
def formatHomologation(format):
    formatHomologated = ''
    if format == 'zip':
        formatHomologated = '.zip'
    if format == '7z':
        formatHomologated = '.7z'
    if format == 'tgz':
        formatHomologated = '.tar.gz'
    if format == 'tbz':
        formatHomologated = '.tar.bz2'
    return formatHomologated

# Funcion para envio de tareas asincronas
@celery.task(name="celery")
def send_async_task(args):
    registry_log("INFO", f"==> Se envia tarea con celery [{str(args)}]")


# Agregamos los recursos
api.add_resource(ConvertTaskFileResource, "/api/tasks")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
