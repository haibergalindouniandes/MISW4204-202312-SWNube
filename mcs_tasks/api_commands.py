from base import request, Resource, db, api, app, Task, jwt_required, task_schema, celery, ftplib, datetime, re, traceback

# Constantes
SHARED_PATH = "shared"
ORIGIN_PATH_FILES = "origin_files"
ALLOWED_EXTENSIONS = "zip,7z,tgz,tbz"

class ConvertTaskFileResource(Resource):
    # @jwt_required()
    def post(self):
        try:
            print(f"<=================== Inicio del procesamiento de la tarea [{datetime.now()}] ===================>")
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
            print(f"==> Nombre original del archivo recibido [{dataFile}]")
            fileNameSanitized = re.sub('[^-a-zA-Z0-9_.]+', '', dataFile)
            print(f"==> Nombre sanitizado del archivo recibido [{fileNameSanitized}]")
            # Conectamos con el servidor FTP
            ftp_server = ftplib.FTP('ftp_server', 'ftp_user', 'ftp_password')
            # Forzamos la codificacion a UTF-8
            ftp_server.encoding = "utf-8"
            ftp_server.cwd(SHARED_PATH)
            # Validamos si no existe el directorio file origin
            if not ORIGIN_PATH_FILES in ftp_server.nlst():
                # Creamos el directorio file origin
                ftp_server.mkd(ORIGIN_PATH_FILES)
            ftp_server.cwd(ORIGIN_PATH_FILES)
            # Subimos el archivo
            ftp_server.storbinary(f"STOR {fileNameSanitized}", file)
            # Cerramos conexion
            ftp_server.quit()
            
            fileOriginPath = f"/{SHARED_PATH}/{ORIGIN_PATH_FILES}/{fileNameSanitized}"
            print(f"==> Path sanitizado [{fileOriginPath}]")
            # Guardamos la informacion del archivo
            fileName = fileNameSanitized.rsplit('.', 1)[0]
            
            dataFile = dataFile.split('.')
            fileFormat = dataFile[-1]
            # Guardamos en base de datos la tarea
            newFile = Task(file_name=fileName, file_format=f".{fileFormat}",
                           file_new_format=formatHomologation(fileNewFormat),
                           file_origin_path=fileOriginPath, status='uploaded',
                           mimetype=file.mimetype)
            db.session.add(newFile)
            db.session.commit()
            # Enviamos de tarea asincrona
            args = (task_schema.dump(newFile))
            send_async_task.delay(args)
            # Retornamos respuesta exitosa
            print(f"<=================== Fin del procesamiento de la tarea [{datetime.now()}] ===================>")
            return {"msg": "El archivo sera procesado", "task": task_schema.dump(newFile)}
        except Exception as e:
            traceback.print_stack()
            return {"msg": str(e)}, 500


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


# Funcion para envio de tareas asincronas
@celery.task(name="celery")
def send_async_task(args):
    pass

# Agregamos los recursos
api.add_resource(ConvertTaskFileResource, "/api/tasks")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
