import os
from flask_cors import CORS
from celery import Celery
from flask_restful import Api
from flask import Flask, send_from_directory, jsonify
from views import AuthLogInResource, AuthSignUpResource, ConvertTaskFileResource, ConvertTaskFileByIdResource, FileDownloadResource, HealthCheckResource
from models import db
from flask_jwt_extended import JWTManager

# Constantes
DB_DRIVER = os.getenv("DB_DRIVER", default="postgresql")
DB_USER = os.getenv("DB_USER", default="postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", default="dbpass")
DB_HOST = os.getenv("DB_HOST", default="postgres")
DB_NAME = os.getenv("DB_NAME", default="postgres")
DB_PORT = os.getenv("DB_PORT", default=5432)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", default="JwBGj2B4XFAKhYmn8Pgk0vH2w7UvgYfXAJ32e5rs8vI=")


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

db.init_app(app)
db.create_all()
api = Api(app)

# Agregamos los recursos
api.add_resource(HealthCheckResource, "/")
api.add_resource(AuthSignUpResource, "/api/auth/signup")
api.add_resource(AuthLogInResource, "/api/auth/login")
api.add_resource(ConvertTaskFileResource, "/api/tasks")
api.add_resource(ConvertTaskFileByIdResource, "/api/tasks/<int:id_task>")
api.add_resource(FileDownloadResource, "/api/files/<int:id_task>")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")