import hashlib
import os
import random
import string
import socket
import traceback
import tempfile
from datetime import datetime
from celery import Celery
from flask import request, send_file
from models import db, User, UserSchema, Task, TaskSchema
from flask_restful import Resource
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.utils import secure_filename
from google.cloud import storage

# Constantes
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", default="zip,7z,tgz,tbz")
RABBIT_USER = os.getenv("RABBIT_USER", default="ConverterUser")
RABBIT_PASSWORD = os.getenv("RABBIT_PASSWORD", default="ConverterPass")
RABBIT_HOST = os.getenv("RABBIT_HOST", default="rabbitmq_broker")
RABBIT_PORT = os.getenv("RABBIT_PORT", default=15672)
CELERY_TASK_NAME = os.getenv("CELERY_TASK_NAME", default="celery")
BROKER_URL = f"pyamqp://{RABBIT_USER}:{RABBIT_PASSWORD}@{RABBIT_HOST}//"
LOG_FILE = os.getenv("LOG_FILE", default="log_services.txt")
SEPARATOR_SO = os.getenv("SEPARATOR_SO", default="/")
MAX_LETTERS = os.getenv("MAX_LETTERS", default=6)
BUCKET_GOOGLE = os.getenv("BUCKET_GOOGLE", default="bucket-converter-app")
ORIGIN_PATH_FILES = os.getenv("ORIGIN_PATH_FILES", default="origin_files")
FILES_PATH = f"files{SEPARATOR_SO}"

# Configuramos Celery
celery = Celery(CELERY_TASK_NAME, broker=BROKER_URL)
# Definimos los esquemas
user_schema = UserSchema()
users_schema = UserSchema(many=True)
task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)

# Clase que retorna el estado del servicio
class HealthCheckResource(Resource):
    def get(self):
        hostIp = socket.gethostbyname(socket.gethostname())
        hostName = socket.gethostname()
        timestamp = datetime.now()
        remoteIp = None
        if request.remote_addr:
            remoteIp = request.remote_addr
        elif request.environ['REMOTE_ADDR']:
            remoteIp = request.remote_addr
        else:
            remoteIp = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        return {"host_name": hostName, "host_ip": hostIp, "remote_ip": remoteIp, "timestamp": str(timestamp)}

# Clase que contiene la logica para solicitar el token
class AuthLogInResource(Resource):
    def post(self):
        try:
            password_encriptada = hashlib.md5(
                request.json["password"].encode("utf-8")
            ).hexdigest()
            usuario = User.query.filter(
                User.username == request.json["username"],
                User.password == password_encriptada,
            ).first()

            if usuario is None:
                return {"msg": "Usuario o contraseña invalida"}, 409

            token_de_acceso = create_access_token(identity=usuario.id)
            return {
                "msg": "Inicio de sesión exitoso",
                "username": usuario.username,
                "token": token_de_acceso,
            }
        except Exception as e:
            traceback.print_stack()
            return {"msg": str(e)}, 500
        
# Clase que contiene la logica para registrar un usuario nuevo
class AuthSignUpResource(Resource):
    def post(self):
        usuario = User.query.filter(User.username == request.json["username"]).first()
        if usuario is None:
            email = User.query.filter(User.email == request.json["email"]).first()
            if email is None:
                if request.json["password1"] == request.json["password2"]:
                    password_encriptada = hashlib.md5(
                        request.json["password1"].encode("utf-8")
                    ).hexdigest()
                    new_user = User(
                        username=request.json["username"],
                        password=password_encriptada,
                        email=request.json["email"],
                    )
                    db.session.add(new_user)
                    db.session.commit()
                    return user_schema.dump(new_user)
                else:
                    return {"msg": "El password no coincide"}, 409
            else:
                return {"msg": "El email ya existe"}, 409
        else:
            return {"msg": "El usuario ya existe"}, 409


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
            fileNameSanitized = secure_filename(file.filename)
            registry_log("INFO", f"==> Nombre sanitizado del archivo recibido [{fileNameSanitized}]")
            idUser = get_jwt_identity()
            
            # Generamos el path del archivo
            userFilesPath = f"{FILES_PATH}{idUser}{SEPARATOR_SO}{ORIGIN_PATH_FILES}{SEPARATOR_SO}"
            
            # Generamos el prefijo para el archivo
            prefix = f"{random_letters(MAX_LETTERS)}_"
            fileNameSanitized = f"{prefix}{fileNameSanitized}"
            
            # Subimos el archivo 
            upload_file(file, userFilesPath, fileNameSanitized)
            
            # Obtenemos información del archivo
            fileName = fileNameSanitized.rsplit('.', 1)[0]
            dataFile = dataFile.split('.')
            fileFormat = dataFile[-1]
            
            # Guardamos la informacion del archivo en DB
            newTask = registry_task_to_db(fileName, fileFormat, fileNewFormat, userFilesPath, fileNameSanitized, file.mimetype, idUser)
            
            registry_log("INFO", f"==> Se registra tarea en BD [{task_schema.dump(newTask)}]")
            # Enviamos de tarea asincrona
            args = (task_schema.dump(newTask))
            registry_log("INFO", f"==> Se envia tarea al Broker RabbitMQ [{BROKER_URL}] el siguiente mensaje [{str(args)}]")
            send_async_task.delay(args)
            # Retornamos respuesta exitosa
            registry_log("INFO", f"<=================== Fin de la creación de la tarea ===================>")
            return {"msg": "El archivo sera procesado", "task": task_schema.dump(newTask)}
        except Exception as e:
            traceback.print_stack()
            registry_log("ERROR", f"==> {str(e)}")
            registry_log("ERROR", f"<=================== Fin de la creación de la tarea ===================>")
            return {"msg": str(e)}, 500

    @jwt_required()
    def get(self):
        queryParams = request.args
        tasks = tasks_schema.dump(Task.query.all())
        try:
            if int(queryParams['order']) == 1:
                tasks = sorted(tasks, key=lambda d: d["id"], reverse=True)
            else:
                tasks = sorted(tasks, key=lambda d: d["id"], reverse=False)
            
            if 'max' in queryParams:
                tasks = tasks[: int(queryParams["max"])]
            
            return tasks                    
        except Exception as e:
            return {"msg": str(e)}, 500
    
    # @jwt_required()
    def put(self):
        registry_log("INFO", f"<=================== Inicio de la actualización de tareas ===================>")
        try:
            data = request.json
            # Validamos la tarea
            updateTask = Task.query.filter(Task.id == int(data['id_task'])).first()
            if updateTask is None:
                raise Exception(f"La tarea [{data['id_task']}] no se encuentra registrada")
            
            # Actualizamos tarea en BD
            updateTask.updated = datetime.now()
            updateTask.file_convert_path = data["file_convert_path"]
            updateTask.status = 'processed'
            db.session.commit()
            registry_log("INFO", f"==> Se actualiza la tarea en BD [{task_schema.dump(updateTask)}]")
            return {"msg": f"La tarea con el id [{data['id_task']}] fue actualizada correctamente"}
        except Exception as e:
            traceback.print_stack()
            registry_log("ERROR", f"==> Se produjo el siguiente [{str(e)}]")
            registry_log("ERROR", f"<=================== Fin de la actualización de tareas ===================>")
            return {"msg": str(e)}, 500
    
    
class ConvertTaskFileByIdResource(Resource):
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
    
    # @jwt_required()    
    def get(self, id_task):
        return task_schema.dump(Task.query.get_or_404(id_task))

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
            
            pathFileToDownload = None
            extensionFileToDownload = None
            # Descargamos el archivo
            if fileType == 'original':
                pathFileToDownload = task.file_origin_path
                extensionFileToDownload = task.file_format
            else:
                pathFileToDownload = task.file_convert_path
                extensionFileToDownload = task.file_new_format
            
            client = connect_storage()
            # Nos conectamos al bucket
            bucket = storage.Bucket(client, BUCKET_GOOGLE)
            blob = bucket.blob(pathFileToDownload)
            with tempfile.NamedTemporaryFile() as temp:
                blob.download_to_filename(temp.name)
                registry_log("INFO", f"==> La a descarga de archivos fue realizada correctamente")
                registry_log("INFO", f"<=================== Fin de la descarga de archivos ===================>")
                return send_file(temp.name, attachment_filename=f"{task.file_name}{extensionFileToDownload}")
                # return send_file(temp.name, as_attachment=True)
        except Exception as e:
            traceback.print_stack()
            registry_log("ERROR", f"==> Se produjo el siguiente [{str(e)}]")
            registry_log("ERROR", f"<=================== Fin de la descarga de archivos ===================>")
            return {"msg": str(e)}, 500

# Funcion para envio de tareas asincronas
@celery.task(name=CELERY_TASK_NAME)
def send_async_task(args):
    registry_log("INFO", f"==> Se envia tarea al Broker RabbitMQ el siguiente mensaje [{str(args)}]")

# Funcion que permite conectarnos a google storage
def connect_storage():
    # Nos Autenticamos con el service account private key
    path_to_private_key = './dauntless-bay-384421-56876ce150d4.json'
    return storage.Client.from_service_account_json(json_credentials_path=path_to_private_key)

# Funcion que permite subir un archivo al bucket
def upload_file(file, userFilesPath, fileNameSanitized):
    client = connect_storage()
    # Nos conectamos al bucket
    bucket = storage.Bucket(client, BUCKET_GOOGLE)
    blob = bucket.blob(f"{userFilesPath}{fileNameSanitized}")
    blob.upload_from_string(file.read(), content_type=file.content_type)

# Funcion que permite registrar tarea en BD
def registry_task_to_db(fileName, fileFormat, fileNewFormat, userFilesPath, fileNameSanitized, fileMimetype, idUser):
    # Registramos tarea en BD
    newTask = Task(file_name=fileName, file_format=f".{fileFormat}",
                    file_new_format=formatHomologation(fileNewFormat),
                    file_origin_path=f"{userFilesPath}{fileNameSanitized}", status='uploaded',
                    mimetype=fileMimetype, id_user=idUser)
    db.session.add(newTask)
    db.session.commit()
    return newTask    

# Funcion que permite generar letras aleatorias
def random_letters(max):
       return ''.join(random.choice(string.ascii_letters) for x in range(max))

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



