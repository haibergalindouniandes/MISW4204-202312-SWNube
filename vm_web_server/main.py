import hashlib
import json
import os
import random
import socket
import string
import tempfile
import traceback
from flask.json import jsonify
from flask_cors import CORS
from flask_restful import Api
from flask import Flask, send_file, request
from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from google.cloud import storage, pubsub_v1
from flask_jwt_extended import JWTManager
from datetime import datetime
from sqlalchemy import DateTime
from werkzeug.utils import secure_filename

# Constantes
DB_DRIVER = os.getenv("DB_DRIVER", default="postgresql")
DB_USER = os.getenv("DB_USER", default="postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", default="dbpass")
DB_HOST = os.getenv("DB_HOST", default="34.66.39.220")
DB_NAME = os.getenv("DB_NAME", default="postgres")
DB_PORT = os.getenv("DB_PORT", default=5432)
JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", default="JwBGj2B4XFAKhYmn8Pgk0vH2w7UvgYfXAJ32e5rs8vI=")
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", default="zip,7z,tgz,tbz")
LOG_FILE = os.getenv("LOG_FILE", default="log_services.txt")
SEPARATOR_SO = os.getenv("SEPARATOR_SO", default="/")
MAX_LETTERS = os.getenv("MAX_LETTERS", default=6)
BUCKET_GOOGLE = os.getenv("BUCKET_GOOGLE", default="bucket-converter-web-app")
ORIGIN_PATH_FILES = os.getenv("ORIGIN_PATH_FILES", default="origin_files")
FILES_PATH = f"files{SEPARATOR_SO}"
PATH_BUCKET_KEY = os.getenv(
    "PATH_BUCKET_KEY", default="misw4204-202312-swnube-bucket.json")
PATH_PUBSUB_KEY = os.getenv(
    "PATH_PUBSUB_KEY", default="misw4204-202312-swnube-pub-sub.json")
PATH_TOPIC = os.getenv(
    "PATH_TOPIC", default="projects/misw4204-202312-swnube/topics/tasks-topic")
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = PATH_PUBSUB_KEY

# Configuracion app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PROPAGATE_EXCEPTIONS"] = True
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app_context = app.app_context()
app_context.push()
cors = CORS(app)
jwt = JWTManager(app)
db = SQLAlchemy()

# Definimos los modelos
# Clase que cotiene la deficion del modelo de base de datos
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    email = db.Column(db.String(50), unique=True)

# Clase que cotiene la deficion de los esquemas
class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        id = fields.String()

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(100), nullable=True)
    file_format = db.Column(db.String(50), nullable=True)
    file_new_format = db.Column(db.String(50), nullable=True)
    file_origin_path = db.Column(db.String(300), nullable=True)
    file_convert_path = db.Column(db.String(300), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    updated = db.Column(DateTime, nullable=True)
    timestamp = db.Column(DateTime, default=datetime.utcnow)
    mimetype = db.Column(db.String(300), nullable=True)
    id_user = db.Column(db.Integer, nullable=True)

class TaskSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Task
        id = fields.String()


# Definimos los esquemas
user_schema = UserSchema()
users_schema = UserSchema(many=True)
task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)

# Ejecutamos la configuracion de sqlachemy
db.init_app(app)
db.create_all()
api = Api(app)

# Funcions utilitarias
# Funcion para envio de mensaje via pubsub
def publish_message(args):
    # Creamos el ciente publihser
    publisher = pubsub_v1.PublisherClient()
    args = json.dumps(args).encode('utf-8')
    messege_published = publisher.publish(PATH_TOPIC, args)
    registry_log(
        "INFO", f"==> Se publico el mensaje exitosamente, [id = {messege_published.result()}]")

# Funcion que permite conectarnos a google storage
def connect_storage():
    # Nos Autenticamos con el service account private key
    return storage.Client.from_service_account_json(PATH_BUCKET_KEY)

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

# Recursos
# Recurso que permite realizar el loggueo
@app.route("/api/auth/login", methods=['POST'])
def login():
    if request.method == 'POST':
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
            return jsonify({
                "msg": "Inicio de sesión exitoso",
                "username": usuario.username,
                "token": token_de_acceso
            })
        except Exception as e:
            traceback.print_stack()
            return {"msg": str(e)}, 500

# # Recurso que permite registrar un usuario nuevo
# @app.route("/api/auth/signup", methods=['GET', 'POST'])
# def signup():
#     if request.method == 'POST':
#         usuario = User.query.filter(
#             User.username == request.json["username"]).first()
#         if usuario is None:
#             email = User.query.filter(
#                 User.email == request.json["email"]).first()
#             if email is None:
#                 if request.json["password1"] == request.json["password2"]:
#                     password_encriptada = hashlib.md5(
#                         request.json["password1"].encode("utf-8")
#                     ).hexdigest()
#                     new_user = User(
#                         username=request.json["username"],
#                         password=password_encriptada,
#                         email=request.json["email"],
#                     )
#                     db.session.add(new_user)
#                     db.session.commit()
#                     return user_schema.dump(new_user)
#                 else:
#                     return {"msg": "El password no coincide"}, 409
#             else:
#                 return {"msg": "El email ya existe"}, 409
#         else:
#             return {"msg": "El usuario ya existe"}, 409


# # Recursos que permite gestionar las tareas de conversion
# @app.route("/api/tasks/<int:id_task>", methods=['GET', 'DELETE'])
# @jwt_required()
# def taskById(id_task):
#     if request.method == 'DELETE':
#         try:
#             registry_log(
#                 "INFO", f"<=================== Inicio de la eliminación de tareas ===================>")
#             # Se consulta la tarea con base al id
#             registry_log("INFO", f"==> Se consultara la tarea [{id_task}]")
#             task = Task.query.filter(Task.id == id_task).first()
#             # Se valida si no existe la tarea
#             registry_log("INFO", f"==> Resultado de la consulta [{str(task)}]")
#             if task is None:
#                 registry_log(
#                     "ERROR", f"==> La tarea con el id [{id_task}] no se encuentra registrada")
#                 registry_log(
#                     "ERROR", f"<=================== Fin de la eliminación de tareas ===================>")
#                 return {"msg": f"La tarea con el id [{id_task}] no se encuentra registrada"}, 400
#             # Se elimina la tarea
#             db.session.delete(task)
#             db.session.commit()
#             registry_log(
#                 "INFO", f"==> La tarea con el id [{id_task}] fue eliminada correctamente")
#             registry_log(
#                 "INFO", f"<=================== Fin de la eliminación de tareas ===================>")
#             return {"msg": f"La tarea con el id [{id_task}] fue eliminada correctamente"}
#         except Exception as e:
#             traceback.print_stack()
#             registry_log(
#                 "ERROR", f"==> Se produjo el siguiente error  [{str(e)}]")
#             registry_log(
#                 "ERROR", f"<=================== Fin de la eliminación de tareas ===================>")
#             return {"msg": str(e)}, 500
#     else:
#         return jsonify(task_schema.dump(Task.query.get_or_404(id_task)))

# # Recursos que permite gestionar las tareas de conversion
# @app.route("/api/files/<int:id_task>", methods=['GET'])
# def downloadFiles(id_task):
#     try:
#         registry_log(
#             "INFO", f"<=================== Inicio de la descarga de archivos ===================>")
#         # Se valida si viene fileType
#         queryParams = request.args
#         if not 'fileType' in queryParams:
#             registry_log("ERROR", f"==> El parámetros fileType es obligatorio")
#             registry_log(
#                 "ERROR", f"<=================== Fin de la descarga de archivos ===================>")
#             return {"msg": f"El parámetros fileType es obligatorio"}, 400
#         # Se valida el tipo de archivo a retornar
#         fileType = queryParams.get("fileType")
#         if fileType != 'original' and fileType != 'compressed':
#             registry_log(
#                 "ERROR", f"==> Solo se permiten los siguiente formatos [original, compressed]")
#             registry_log(
#                 "ERROR", f"<=================== Fin de la descarga de archivos ===================>")
#             return {"msg": f"Solo se permiten los siguiente formatos [original, compressed]"}, 400
#         # Se consulta la tarea con base al id
#         registry_log("INFO", f"==> Se consultara la tarea [{id_task}]")
#         task = Task.query.filter(Task.id == id_task).first()
#         # Se valida si no existe la tarea
#         registry_log("INFO", f"==> Resultado de la consulta [{str(task)}]")
#         if task is None:
#             registry_log(
#                 "ERROR", f"==> La tarea con el id [{id_task}] no se encuentra registrada")
#             registry_log(
#                 "ERROR", f"<=================== Fin de la descarga de archivos ===================>")
#             return {"msg": f"La tarea con el id [{id_task}] no se encuentra registrada"}, 400
#         pathFileToDownload = None
#         extensionFileToDownload = None
#         # Descargamos el archivo
#         if fileType == 'original':
#             pathFileToDownload = task.file_origin_path
#             extensionFileToDownload = task.file_format
#         else:
#             pathFileToDownload = task.file_convert_path
#             extensionFileToDownload = task.file_new_format
#         # Descargamos el archivo temporalmente
#         # Nos conectamos al bucket
#         client = connect_storage()
#         bucket = storage.Bucket(client, BUCKET_GOOGLE)
#         blob = bucket.blob(pathFileToDownload)
#         # Descargamos temporalmente el archivo
#         with tempfile.NamedTemporaryFile() as temp:
#             blob.download_to_filename(temp.name)
#             registry_log(
#                 "INFO", f"==> La a descarga de archivos fue realizada correctamente")
#             registry_log(
#                 "INFO", f"<=================== Fin de la descarga de archivos ===================>")
#             return send_file(temp.name, attachment_filename=f"{task.file_name}{extensionFileToDownload}")
#     except Exception as e:
#         traceback.print_stack()
#         registry_log("ERROR", f"==> Se produjo el siguiente error  [{str(e)}]")
#         registry_log(
#             "ERROR", f"<=================== Fin de la descarga de archivos ===================>")
#         return {"msg": str(e)}, 500


# # Recursos que permite gestionar las tareas de conversion
# @app.route("/api/tasks", methods=['GET', 'POST'])
# @jwt_required()
# def tasks():
#     if request.method == 'POST':
#         try:
#             registry_log(
#                 "INFO", f"<=================== Inicio de la consulta de todas las tareas ===================>")
#             queryParams = request.args
#             tasks = tasks_schema.dump(Task.query.all())
#             registry_log(
#                 "INFO", f"==> Tareas retornadas [{str(tasks)}]")
#             if queryParams.get('order') != None:
#                 if int(queryParams.get('order')) == 1:
#                     tasks = sorted(tasks, key=lambda d: d["id"], reverse=True)
#                 else:
#                     tasks = sorted(tasks, key=lambda d: d["id"], reverse=False)
#             if 'max' in queryParams:
#                 tasks = tasks[: int(queryParams.get("max"))]
#             registry_log(
#                 "INFO", f"==> Tareas filtradas [{str(tasks)}]")
#             registry_log(
#                 "INFO", f"<=================== Fin de la consulta de todas las tareas ===================>")
#             return jsonify(tasks)
#         except Exception as e:
#             registry_log(
#                 "ERROR", f"==> Se produjo el siguiente error  [{str(e)}]")
#             return {"msg": str(e)}, 500
#     elif request.method == 'GET':
#         try:
#             registry_log(
#                 "INFO", f"<=================== Inicio de la creación de la tarea ===================>")
#             # Validacion de parametros de entrada
#             if not 'fileName' in request.files:
#                 return {"msg": "Parámetros de entrada invalidos. El parámetro 'fileName' es obligatorio."}, 400

#             if not 'newFormat' in request.form:
#                 return {"msg": "Parámetros de entrada invalidos. El parámetro 'newFormat' es obligatorio."}, 400

#             fileNewFormat = request.form['newFormat']

#             if not fileNewFormat in ALLOWED_EXTENSIONS:
#                 return {"msg": f"Solo se permiten los siguiente formatos [{ALLOWED_EXTENSIONS}]"}, 400

#             # Obtenemos el archivo
#             file = request.files['fileName']
#             dataFile = file.filename
#             registry_log(
#                 "INFO", f"==> Nombre original del archivo recibido [{dataFile}]")
#             fileNameSanitized = secure_filename(file.filename)
#             registry_log(
#                 "INFO", f"==> Nombre sanitizado del archivo recibido [{fileNameSanitized}]")
#             idUser = get_jwt_identity()

#             # Generamos el path del archivo
#             userFilesPath = f"{FILES_PATH}{idUser}{SEPARATOR_SO}{ORIGIN_PATH_FILES}{SEPARATOR_SO}"

#             # Generamos el prefijo para el archivo
#             prefix = f"{random_letters(MAX_LETTERS)}_"
#             fileNameSanitized = f"{prefix}{fileNameSanitized}"

#             # Subimos el archivo
#             upload_file(file, userFilesPath, fileNameSanitized)

#             # Obtenemos información del archivo
#             fileName = fileNameSanitized.rsplit('.', 1)[0]
#             dataFile = dataFile.split('.')
#             fileFormat = dataFile[-1]

#             # Guardamos la informacion del archivo en DB
#             newTask = registry_task_to_db(
#                 fileName, fileFormat, fileNewFormat, userFilesPath, fileNameSanitized, file.mimetype, idUser)

#             registry_log(
#                 "INFO", f"==> Se registra tarea en BD [{task_schema.dump(newTask)}]")
#             # Enviamos de tarea asincrona
#             args = (task_schema.dump(newTask))
#             registry_log(
#                 "INFO", f"==> Se envia al Topic [{PATH_TOPIC}] el siguiente mensaje [{str(args)}]")
#             publish_message(args)
#             # Retornamos respuesta exitosa
#             registry_log(
#                 "INFO", f"<=================== Fin de la creación de la tarea ===================>")
#             return {"msg": "El archivo sera procesado", "task": task_schema.dump(newTask)}
#         except Exception as e:
#             registry_log("ERROR", f"==> {str(e)}")
#             registry_log(
#                 "ERROR", f"<=================== Fin de la creación de la tarea ===================>")
#             return {"msg": str(e)}, 500

# Recurso que retorna el estado del sistema
@app.route("/", methods=['GET'])
def get_health():
    hostIp = socket.gethostbyname(socket.gethostname())
    hostName = socket.gethostname()
    timestamp = datetime.now()
    remoteIp = None
    if request.remote_addr:
        remoteIp = request.remote_addr
    elif request.environ['REMOTE_ADDR']:
        remoteIp = request.remote_addr
    else:
        remoteIp = request.environ.get(
            'HTTP_X_FORWARDED_FOR', request.remote_addr)
    return {"host_name": hostName, "host_ip": hostIp, "remote_ip": remoteIp, "timestamp": str(timestamp)}



# Inicializamos la aplicacion con Flask
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(
        os.getenv("PORT", default="80")))
