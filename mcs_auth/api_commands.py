from base import User, request, Resource, db, api, app, hashlib, create_access_token

class AuthLogInResource(Resource):
    def post(self):
        password_encriptada = hashlib.md5(
            request.json["password"].encode("utf-8")
        ).hexdigest()
        usuario = User.query.filter(
            User.username == request.json["username"],
            User.password == password_encriptada,
        ).first()
        db.session.commit()
        token_de_acceso = create_access_token(identity=usuario.id)
        return {
            "mensaje": "Inicio de sesión exitoso",
            "username": usuario.username,
            "token": token_de_acceso,
        }

api.add_resource(AuthLogInResource, "/api/auth/login")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)