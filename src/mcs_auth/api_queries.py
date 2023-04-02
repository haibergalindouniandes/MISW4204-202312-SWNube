from base import User, request, Resource, db, api, app, hashlib, user_schema

class AuthSignUpResource(Resource):
    def post(self):
        usuario = User.query.filter(User.username == request.json["username"]).first()
        if usuario is None:
            email = User.query.filter(User.email == request.json["email"]).first()
            if email is None:
                if request.json["password1"] == request.json["password2"]:
                    password_encriptada = hashlib.md5(
                        request.json["password1"].encode("utf-8")
                    ).hexdigest()
                    new_user = User(
                        username=request.json["username"],
                        password=password_encriptada,
                        email=request.json["email"],
                    )
                    db.session.add(new_user)
                    db.session.commit()
                    return user_schema.dump(new_user)
                else:
                    return "El password no coincide", 409
            else:
                return "El email ya existe", 409
        else:
            return "El usuario ya existe", 409


api.add_resource(AuthSignUpResource, "/api/auth/signup")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=6600)