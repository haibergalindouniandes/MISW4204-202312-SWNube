from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
from sqlalchemy import DateTime


db = SQLAlchemy()

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