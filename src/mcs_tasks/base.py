import hashlib
from flask import Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields, Schema

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dbapp.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PROPAGATE_EXCEPTIONS"] = True
app.config["JWT_SECRET_KEY"] = "JwBGj2B4XFAKhYmn8Pgk0vH2w7UvgYfXAJ32e5rs8vI="

app_context = app.app_context()
app_context.push()

db = SQLAlchemy()
cors = CORS(app)
api = Api(app)
jwt = JWTManager(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    originalFile = db.Column(db.String(50), unique=True)
    state = db.Column(db.String(9))
    convertedlFile = db.Column(db.String(50), unique=True)


class TaskSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Task
        id = fields.String()


task_schema = TaskSchema()
task_schema = TaskSchema(many=True)

db.init_app(app)
db.create_all()
