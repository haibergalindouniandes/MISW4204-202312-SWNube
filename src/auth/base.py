import enum
import hashlib
from flask import Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields, Schema
from flask_jwt_extended import jwt_required, create_access_token

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


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    email = db.Column(db.String(50), unique=True)


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        id = fields.String()


user_schema = UserSchema()
users_schema = UserSchema(many=True)

db.init_app(app)
db.create_all()

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
api.add_resource(AuthLogInResource, "/api/auth/login")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=6600)
