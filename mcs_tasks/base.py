from datetime import datetime
from flask import Flask, request, Response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import traceback
import re
from sqlalchemy import DateTime, LargeBinary, Text
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager, jwt_required
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields, Schema
from celery import Celery
import ftplib
import psycopg2


app = Flask(__name__)
# app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://dbuser:dbpass@postgres:5432/dbconvert"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://dbuser:dbpass@postgres:5555/dbconvert"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PROPAGATE_EXCEPTIONS"] = True
app.config["JWT_SECRET_KEY"] = "JwBGj2B4XFAKhYmn8Pgk0vH2w7UvgYfXAJ32e5rs8vI="
app.config['broker_url'] = 'amqp://ConverterUser:ConverterPass@rabbitmq_broker:5672/vhost_converter'
app_context = app.app_context()
app_context.push()

db = SQLAlchemy()
cors = CORS(app)
api = Api(app)
jwt = JWTManager(app)

# Initialize Celery
celery = Celery('converter_app', broker=app.config['broker_url'])
celery.conf.update(app.config)
celery.conf.accept_content = ["json", "pickle", "yaml"]

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


class TaskSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Task
        id = fields.String()


task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)

db.init_app(app)
db.create_all()
