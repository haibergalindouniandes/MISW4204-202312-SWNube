import random
import string
from base import request, Resource, db, api, app, Task, jwt_required, task_schema, celery, ftplib, datetime, re, traceback, os, socket

# Constantes
PRINT_PROPERTIES = os.getenv("PRINT_PROPERTIES", default=False)
SHARED_PATH = os.getenv("SHARED_PATH", default="shared")
ORIGIN_PATH_FILES = os.getenv("ORIGIN_PATH_FILES", default="origin_files")
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", default="zip,7z,tgz,tbz")
EXP_REG_SANITIZATE = os.getenv("EXP_REG_SANITIZATE", default="[^-a-zA-Z0-9_.]+")
FTP_SERVER = os.getenv("FTP_SERVER", default="172.168.0.12")
FTP_PORT = os.getenv("FTP_PORT", default=21)
FTP_USER = os.getenv("FTP_USER", default="converteruser")
FTP_PASSWORD = os.getenv("FTP_PASSWORD", default="Converter2023")
LOG_FILE = os.getenv("LOG_FILE", default="log_tasks.txt")
MAX_LETTERS = os.getenv("MAX_LETTERS", default=6)
CELERY_TASK_NAME = os.getenv("CELERY_TASK_NAME", default="celery")


# Clase que contiene la logica para registrar tareas de conversión
class ConvertTaskFileResource(Resource):
    @jwt_required()
    def post(self):
        try:
            registry_log("INFO", f"<=================== Inicio de la creación de la tarea ===================>")
            # Validamos si se debe imprimir las propiedades
            if PRINT_PROPERTIES:
                registry_properties()
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
            # Generamos el prefijo para el archivo
            prefix = f"{random_letters(MAX_LETTERS)}_"
            fileNameSanitized = f"{prefix}{fileNameSanitized}"
            # Subimos el archivo 
            updaloadFileToServer(file, fileNameSanitized)    
            fileOriginPath = f"/{SHARED_PATH}/{ORIGIN_PATH_FILES}/{fileNameSanitized}"
            registry_log("INFO", f"==> Path sanitizado [{fileOriginPath}]")
            # Guardamos la informacion del archivo
            fileName = fileNameSanitized.rsplit('.', 1)[0]
            dataFile = dataFile.split('.')
            fileFormat = dataFile[-1]
            # Registramos tarea en BD
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
            registry_log("ERROR", f"==> {str(e)}")
            registry_log("ERROR", f"<=================== Fin de la creación de la tarea ===================>")
            return {"msg": str(e)}, 500


class ConvertTaskFileDelResource(Resource):
    @jwt_required()
    def delete(self, id_task):
        registry_log("INFO", f"<=================== Inicio de la eliminación de tareas ===================>")
        try:
            # Se consulta la tarea con base al id
            registry_log("INFO", f"==> Se consultara la tarea [{id_task}]")
            task = Task.query.filter(Task.id == id_task).first()
            # Se valida si no existe la tarea
            registry_log("INFO", f"==> Resultado de la consulta [{str(task)}]")
            if task is None:
                registry_log("ERROR", f"==> La tarea con el id [{id_task}] no se encuentra registrada")
                registry_log("ERROR", f"<=================== Fin de la eliminación de tareas ===================>")
                return {"msg": f"La tarea con el id [{id_task}] no se encuentra registrada"}, 400
            # Se elimina la tarea             
            db.session.delete(task)
            db.session.commit()
            registry_log("INFO", f"==> La tarea con el id [{id_task}] fue eliminada correctamente")
            registry_log("INFO", f"<=================== Fin de la eliminación de tareas ===================>")
            return {"msg": f"La tarea con el id [{id_task}] fue eliminada correctamente"}
        except Exception as e:
            traceback.print_stack()
            registry_log("ERROR", f"==> Se produjo el siguiente [{str(e)}]")
            registry_log("ERROR", f"<=================== Fin de la eliminación de tareas ===================>")
            return {"msg": str(e)}, 500


# Funcion que permite generar letras aleatorias
def random_letters(max):
       return ''.join(random.choice(string.ascii_letters) for x in range(max))

# Funcion que permite realizar la conexion con el servidor FTP
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

# Funcion que permite realizar la descarga de archivos del servidor FTP
def updaloadFileToServer(file, fileNameSanitized):
    ftp_server = connectFtp()
    # Validamos si no existe el directorio shared
    if not SHARED_PATH in ftp_server.nlst():
        # Creamos el directorio file origin
        ftp_server.mkd(SHARED_PATH)
        registry_log("INFO", f"==> Se crea directorio [{SHARED_PATH}]")
    ftp_server.cwd(SHARED_PATH)
    # Validamos si existe el directorio file origin si no exite se crea
    if not ORIGIN_PATH_FILES in ftp_server.nlst():
        # Create a new directory called foo on the server.
        ftp_server.mkd(ORIGIN_PATH_FILES)
        registry_log("INFO", f"==> Se crea directorio [{ORIGIN_PATH_FILES}]")
    ftp_server.cwd(ORIGIN_PATH_FILES)
    # Subimos el archivo
    ftp_server.storbinary(f"STOR {fileNameSanitized}", file)
    # Cerramos conexion FTP y la apertura del archivo
    closeConnectionServer(ftp_server)
    file.close()

# Funcion que permite realizar el cierre de conexiones del servidor FTP
def closeConnectionServer(ftp_server):
    ftp_server.quit()
    ftp_server.close()
    registry_log("INFO", f"==> Se cierra la conexion con el servidor FTP")

# Funcion para registrar propiedades
def registry_properties():
    registry_log("INFO", f"==> Propiedades del sistema:")
    registry_log("INFO", f"==> SHARED_PATH={SHARED_PATH}")
    registry_log("INFO", f"==> ORIGIN_PATH_FILES={ORIGIN_PATH_FILES}")
    registry_log("INFO", f"==> ALLOWED_EXTENSIONS={ALLOWED_EXTENSIONS}")
    registry_log("INFO", f"==> EXP_REG_SANITIZATE={EXP_REG_SANITIZATE}")
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
@celery.task(name=CELERY_TASK_NAME)
def send_async_task(args):
    registry_log("INFO", f"==> Se envia tarea al Broker RabbitMQ [{str(args)}]")


# Agregamos los recursos
api.add_resource(ConvertTaskFileResource, "/api/tasks")
api.add_resource(ConvertTaskFileDelResource, "/api/tasks/<int:id_task>")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
