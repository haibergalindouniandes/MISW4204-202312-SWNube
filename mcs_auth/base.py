import hashlib
import os
from flask import Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager, create_access_token
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields, Schema

# Constantes
POSTGRES_USER = os.getenv("POSTGRES_USER", default="dbuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", default="dbpass")
POSTGRES_DB = os.getenv("POSTGRES_DB", default="dbconvert")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", default=5432)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", default="JwBGj2B4XFAKhYmn8Pgk0vH2w7UvgYfXAJ32e5rs8vI=")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres:{POSTGRES_PORT}/{POSTGRES_DB}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PROPAGATE_EXCEPTIONS"] = True
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app_context = app.app_context()
app_context.push()
db = SQLAlchemy()
cors = CORS(app)
api = Api(app)
jwt = JWTManager(app)

# Clase que cotiene la deficion del modelo de base de datos
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    email = db.Column(db.String(50), unique=True)

# Clase que cotiene la deficion de los esquemas
class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        id = fields.String()

# Definimos los esquemas
user_schema = UserSchema()
users_schema = UserSchema(many=True)
# Iniciamos la configuración de bd
db.init_app(app)
db.create_all()
