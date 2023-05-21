
# Constantes
import os
import socket
from flask import Flask
from flask import request
from flask_cors import CORS
from flask_restful import Api
from flask_restful import Resource
from datetime import datetime

# Constantes
DB_USER = os.getenv("DB_USER", default="postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", default="dbpass")
DB_HOST = os.getenv("DB_HOST", default="postgres")
DB_NAME = os.getenv("DB_NAME", default="postgres")
DB_PORT = os.getenv("DB_PORT", default=5432)
SEPARATOR_SO = os.getenv("SEPARATOR_SO", default="/")
TMP_PATH = os.getenv("TMP_PATH", default="tmp")
FILES_PATH = f"files{SEPARATOR_SO}"
COMPRESSED_PATH_FILES = os.getenv(
    "COMPRESSED_PATH_FILES", default="compressed_files")
LOG_FILE = os.getenv("LOG_FILE", default="log_worker.txt")
BUCKET_GOOGLE = os.getenv("BUCKET_GOOGLE", default="bucket-converter-web-app")
PATH_PRIVATE_KEY = os.getenv(
    "PATH_PRIVATE_KEY", default="misw4204-202312-swnube-bucket.json")

# Configuracion app
app = Flask(__name__)
app_context = app.app_context()
app_context.push()
cors = CORS(app)

api = Api(app)


# Funciones utilitarias
# Funcion para resgitrar logs
def registry_log(severity, message):
    with open(LOG_FILE, 'a') as file:
        file.write(
            f"[{severity}]-[{datetime.now()}]-[{message}]\n")

# Clases
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
            remoteIp = request.environ.get(
                'HTTP_X_FORWARDED_FOR', request.remote_addr)

        return {"host_name": hostName, "host_ip": hostIp, "remote_ip": remoteIp, "timestamp": str(timestamp)}


# Agregamos los recursos
api.add_resource(HealthCheckResource, "/api")

# Inicializamos la aplicacion con Flask
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(
        os.getenv("PORT", default="8080")))
