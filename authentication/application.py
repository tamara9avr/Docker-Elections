import re
from email.utils import parseaddr

from flask import Flask, request, Response, jsonify
from sqlalchemy import and_

from adminDecorator import roleCheck
from configuration import Configuration
from models import database, User, UserRole
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity
from email_validator import validate_email, EmailNotValidError

application = Flask(__name__)
application.config.from_object(Configuration)


@application.route("/register", methods=["POST"])
def register():
    jmbg = request.json.get("jmbg", "")
    email = request.json.get("email", "")
    password = request.json.get("password", "")
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")

    jmbgEmpty = len(jmbg) == 0
    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0
    forenameEmpty = len(forename) == 0
    surnameEmpty = len(surname) == 0

    if jmbgEmpty:
        message = "Field jmbg is missing."
        return jsonify(message=message), 400

    if forenameEmpty:
        message = "Field forename is missing."
        return jsonify(message=message), 400

    if surnameEmpty:
        message = "Field surname is missing."
        return jsonify(message=message), 400

    if emailEmpty:
        message = "Field email is missing."
        return jsonify(message=message), 400

    if passwordEmpty:
        message = "Field password is missing."
        return jsonify(message=message), 400


    reg = re.compile(r"[0-3][0-9][0-1][0-9][0-9][0-9][0-9][7-9][0-9][0-9][0-9][0-9](\d)")
    jmbgOK = reg.search(jmbg)

    if not jmbgOK:
        message = "Invalid jmbg."
        return jsonify(message=message), 400

    k = int(jmbgOK.group(1))

    l = 0
    i = 7

    for j in range(6):
        l = l + i * (int(jmbg[j]) + int(jmbg[j + 6]))
        i = i - 1

    m = 11 - (l % 11)
    if m >= 10:
        m = 0

    if m != k:
        message = "Invalid jmbg."
        return jsonify(message=message), 400

    try:
        validate_email(email)
    except EmailNotValidError:
        message = "Invalid email."
        return jsonify(message=message), 400

    user = User.query.filter(User.email == email).first()

    status = any(char.isdigit() for char in password) \
             and any(char.isupper() for char in password) \
             and any(char.isalpha() for char in password)

    if not status or len(password) < 8:
        message = "Invalid password."
        return jsonify(message=message), 400

    if user:
        message = "Email already exists."
        return jsonify(message=message), 400

    user = User(jmbg=jmbg, email=email, password=password, forename=forename, surname=surname)
    database.session.add(user)
    database.session.commit()

    userRole = UserRole(userId=user.id, roleId=2)
    database.session.add(userRole)
    database.session.commit()

    return Response(status=200)


jwt = JWTManager(application)


@application.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0

    if emailEmpty:
        message = "Field email is missing."
        return jsonify(message=message), 400
    if passwordEmpty:
        message = "Field password is missing."
        return jsonify(message=message), 400

    try:
        validate_email(email)
    except EmailNotValidError:
        message = "Invalid email."
        return jsonify(message=message), 400

    user = User.query.filter(and_(User.email == email, User.password == password)).first()

    if not user:
        message = "Invalid credentials."
        return jsonify(message=message), 400

    additionalClaims = {
        "forename": user.forename,
        "surname": user.surname,
        "jmbg": user.jmbg,
        "roles": [str(role) for role in user.roles]
    }

    accessToken = create_access_token(identity=user.email, additional_claims=additionalClaims)
    refreshToken = create_refresh_token(identity=user.email, additional_claims=additionalClaims)

    return jsonify(accessToken=accessToken, refreshToken=refreshToken)


@application.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    refreshClaims = get_jwt()

    additionalClaims = {
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "jmbg": refreshClaims["jmbg"],
        "roles": refreshClaims["roles"]
    }

    return jsonify(accessToken=create_access_token(identity=identity, additional_claims=additionalClaims)), 200


@application.route("/delete", methods=["POST"])
@jwt_required()
@roleCheck(role="admin")
def delete():
    email = request.json.get("email", "")

    if len(email) == 0:
        message = "Field email is missing."
        return jsonify(message=message), 400

    try:
        validate_email(email)
    except EmailNotValidError:
        message = "Invalid email."
        return jsonify(message=message), 400

    user = User.query.filter(User.email == email).first()

    if not user:
        message = "Unknown user."
        return jsonify(message=message), 400

    database.session.delete(user)
    database.session.commit()

    return Response(status=200)


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5002)
