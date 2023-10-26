"""User related routes"""
from flask import Blueprint, request, jsonify

from models.bo.user_bo import UserBO
from models.exception.exceptions import ApiException

user = Blueprint("user", __name__)


@user.route("/user/register", methods=["POST"])
def register():
    """Sign up endpoint"""
    response = jsonify({"message": "USER_CREATED_SUCCESSFULLY"}), 200

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
        user_bo.add_in_db()
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code

    return response


@user.route("/user/validate_email", methods=["POST"])
def validate_email():
    """Email validation endpoint"""
    response = jsonify({"message": "EMAIL_VALID"}), 200

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
    """Login validation endpoint"""
    response = jsonify({"message": "LOGIN_VALID"}), 200

    try:
        json_object = request.json
        user_bo = UserBO(
            login=json_object.get("login", None),
        )
        user_bo.validate_login()
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code

    return response


@user.route("/user/validate_firstname", methods=["POST"])
def validate_firstname():
    """Firstname validation endpoint"""
    response = jsonify({"message": "FIRSTNAME_VALID"}), 200

    try:
        json_object = request.json
        user_bo = UserBO(
            firstname=json_object.get("firstname", None),
        )
        user_bo.validate_firstname()
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code

    return response


@user.route("/user/validate_lastname", methods=["POST"])
def validate_lastname():
    """Lastname validation endpoint"""
    response = jsonify({"message": "LASTNAME_VALID"}), 200

    try:
        json_object = request.json
        user_bo = UserBO(
            lastname=json_object.get("lastname", None),
        )
        user_bo.validate_lastname()
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code

    return response


@user.route("/user/validate_gender/<gender>", methods=["GET"])
def validate_gender(gender):
    """Lastname validation endpoint"""
    response = jsonify({"message": "GENDER_VALID"}), 200

    try:
        user_bo = UserBO(
            gender=gender,
        )
        user_bo.validate_gender()
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code

    return response


@user.route("/user/validate_phone_number", methods=["POST"])
def validate_phone_number():
    """Phone number validation endpoint"""
    response = jsonify({"message": "PHONE_NUMBER_VALID"}), 200

    try:
        json_object = request.json
        user_bo = UserBO(
            phone_number=json_object.get("phone_number", None),
        )
        user_bo.validate_phone_number()
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code

    return response
