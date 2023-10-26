"""User related routes"""
from flask import Blueprint, request, jsonify

from models.bo.user_bo import UserBO
from models.exception.exceptions import ApiException

user = Blueprint("user", __name__)


@user.route("/user/register", methods=["POST"])
def register():
    """Sign up route"""
    response = jsonify({"message": "User created successfuly"}), 200

    try:
        json_object = request.json
        user_bo = UserBO(
            id=json_object.get("id", None),
            login=json_object.get("login", None),
            firstname=json_object.get("firstname", None),
            lastname=json_object.get("lastname", None),
            student_email=json_object.get("student_email", None),
            password=json_object.get("password", None),
            gender=json_object.get("gender", None),
            phone_number=json_object.get("phone_number", None),
            description=json_object.get("description", None),
        )
        response = user_bo.add_in_db()
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code

    return response


@user.route("/user/validate_email", methods=["POST"])
def validate_email():
    """Email validation route"""
    response = jsonify({"message": "Email valid"}), 200

    try:
        json_object = request.json
        user_bo = UserBO(
            student_email=json_object.get("student_email", None),
        )
        user_bo.validate_email()
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code

    return response


@user.route("/user/validate_login", methods=["POST"])
def validate_login():
    """Login validation route"""
    response = jsonify({"message": "Login valid"}), 200

    try:
        json_object = request.json
        user_bo = UserBO(
            login=json_object.get("login", None),
        )
        user_bo.validate_login()
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code

    return response
