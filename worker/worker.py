from datetime import datetime
from flask import Flask, request
from flask_cors import CORS
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
from celery import Celery
import os
import shutil
import tarfile
from zipfile import ZipFile
import py7zr
from datetime import datetime


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://dbuser:dbpass@postgres:5432/dbconvert"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PROPAGATE_EXCEPTIONS"] = True
app.config['broker_url'] = 'amqp://ConverterUser:ConverterPass@rabbitmq_broker:5672/vhost_converter'
app_context = app.app_context()
app_context.push()
db = SQLAlchemy()
cors = CORS(app)
api = Api(app)

# Initialize Celery
celery = Celery('converter_app', broker=app.config['broker_url'])
celery.conf.update(app.config)
celery.conf.accept_content = ["json", "pickle", "yaml"]


# Configuracion rutas de archivos
PATH_FILES_COMPRESSED = os.getcwd() + "/compressed_files/"

# Clase que define el modelo de bd de la tabla TASK
class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(100), nullable=False)
    file_format = db.Column(db.String(50), nullable=False)
    file_new_format = db.Column(db.String(50), nullable=False)
    file_origin_path = db.Column(db.String(300), nullable=False)
    file_convert_path = db.Column(db.String(300), nullable=True)
    status = db.Column(db.String(50), nullable=False)
    updated = db.Column(DateTime, nullable=True)
    timestamp = db.Column(DateTime, default=datetime.utcnow)

class TaskSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Task
        id = fields.String()

task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)

db.init_app(app)
db.create_all()

# Funcion para el procesamiento de los archivos
@celery.task(name="celery")
def process_file(args):
    print('Inicio tarea ===========================================>')
    message = args
    # Convertimos archivo
    fileNewExt = compressFile(
        message["file_origin_path"], message["file_name"], message["file_format"], message["file_new_format"])
    # Consultamos archivo y actualizamos
    queriedFile = Task.query.get_or_404(message["id"])
    queriedFile.updated = datetime.now()
    queriedFile.file_convert_path = PATH_FILES_COMPRESSED + \
        message["file_name"] + fileNewExt
    queriedFile.status = 'processed'
    db.session.commit()
    print(f'Transaccion procesada [{str(args)}] ================>')
    print('Fin tarea ===========================================>')


# Funciones para comprimir archivos
# Funcion para comprimir archivos
def compressFile(filePath, fileName, originExt, fileConvertedExt):
    convertedExt = ''
    # Validamos si existe el directorio compressed files
    isExistDirectory = os.path.exists(PATH_FILES_COMPRESSED)
    if not isExistDirectory:
        os.makedirs(PATH_FILES_COMPRESSED)

    # Comprimimos el archivos
    if fileConvertedExt.lower() == 'zip':
        convertedExt = compressInZip(filePath, fileName, originExt)
    if fileConvertedExt.lower() == '7z':
        convertedExt = compressIn7Zip(filePath, fileName, originExt)
    if fileConvertedExt.lower() == 'tgz':
        convertedExt = compressInTgz(filePath, fileName, originExt)
    if fileConvertedExt.lower() == 'tbz':
        convertedExt = compressInTbz(filePath, fileName, originExt)

    # Movemos el archivo comprimido
    shutil.move(fileName+convertedExt,
                os.path.join(PATH_FILES_COMPRESSED, fileName+convertedExt))
    return convertedExt

# Funcion para comprimir en formato zip
def compressInZip(filePath, fileName, originExt):
    EXTENSION = '.zip'
    # Comprimimos el archivos
    myzip = ZipFile(fileName+EXTENSION, 'w')
    myzip.write(filePath, fileName+'.'+originExt)
    myzip.close()
    return EXTENSION

# Funcion para comprimir en formato 7Zip
def compressIn7Zip(filePath, fileName, originExt):
    EXTENSION = '.7z'
    # Comprimimos el archivos
    with py7zr.SevenZipFile(fileName+EXTENSION, 'w') as z:
        z.writeall(filePath, fileName+'.'+originExt)
    return EXTENSION

# Funcion para comprimir en formato TGZ
def compressInTgz(filePath, fileName, originExt):
    EXTENSION = '.tar.gz'
    # Comprimimos el archivos
    with tarfile.open(fileName+EXTENSION, 'w:gz') as tar:
        tar.add(filePath, fileName+'.'+originExt)
    return EXTENSION

# Funcion para comprimir en formato BZ2
def compressInTbz(filePath, fileName, originExt):
    EXTENSION = '.tar.bz2'
    # Comprimimos el archivos
    with tarfile.open(fileName+EXTENSION, 'w:bz2') as tar:
        tar.add(filePath, fileName+'.'+originExt)
    return EXTENSION
