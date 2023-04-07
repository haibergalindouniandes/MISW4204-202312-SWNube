from datetime import datetime
from flask import Flask, request, Response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, LargeBinary, Text
from zipfile import ZipFile, ZIP_DEFLATED
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager, jwt_required
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields, Schema
from celery import Celery
import tempfile
import ftplib
import psycopg2
import tarfile
import traceback
import py7zr
import zlib
import re
import os

# Constantes
POSTGRES_USER = os.getenv("POSTGRES_USER", default="dbuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", default="dbpass")
POSTGRES_DB = os.getenv("POSTGRES_DB", default="dbconvert")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", default=5432)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", default="JwBGj2B4XFAKhYmn8Pgk0vH2w7UvgYfXAJ32e5rs8vI=")
RABBIT_USER = os.getenv("RABBIT_USER", default="ConverterUser")
RABBIT_PASSWORD = os.getenv("RABBIT_PASSWORD", default="ConverterPass")
RABBIT_HOST = os.getenv("RABBIT_HOST", default="rabbitmq_broker")
RABBIT_PORT = os.getenv("RABBIT_PORT", default=5672)
RABBIT_VHOST = os.getenv("RABBIT_VHOST", default="vhost_converter")
CELERY_NAME_APP = os.getenv("CELERY_NAME_APP", default="converter_app")
ACCEPT_CONTENT = os.getenv("ACEPT_CONTENT", default=["json", "pickle", "yaml"])


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres:{POSTGRES_PORT}/{POSTGRES_DB}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PROPAGATE_EXCEPTIONS"] = True
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config['broker_url'] = f"amqp://{RABBIT_USER}:{RABBIT_PASSWORD}@{RABBIT_HOST}:{RABBIT_PORT}/{RABBIT_VHOST}"
app_context = app.app_context()
app_context.push()
db = SQLAlchemy()
cors = CORS(app)
api = Api(app)
jwt = JWTManager(app)

# Configuramos Celery
celery = Celery(CELERY_NAME_APP, broker=app.config['broker_url'])
celery.conf.update(app.config)
celery.conf.accept_content = ACCEPT_CONTENT

# Clase que cotiene la deficion del modelo de base de datos
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

# Clase que cotiene la deficion de los esquemas
class TaskSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Task
        id = fields.String()

# Definimos los esquemas
task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)
# Iniciamos la configuración de bd
db.init_app(app)
db.create_all()
