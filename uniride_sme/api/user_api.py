"""User related endpoints"""
from flask import Blueprint, request, jsonify, url_for

from uniride_sme.models.bo.user_bo import UserBO
from uniride_sme.utils.exception.exceptions import ApiException
import uniride_sme.utils.email as email

user = Blueprint("user", __name__)


@user.route("/user/register", methods=["POST"])
def register():
    """Sign up endpoint"""
    response = jsonify({"message": "USER_CREATED_SUCCESSFULLY"}), 200

    try:
        json_object = request.json
        user_bo = UserBO(
            user_id=json_object.get("id", None),
            login=json_object.get("login", None),
            firstname=json_object.get("firstname", None),
            lastname=json_object.get("lastname", None),
            student_email=json_object.get("student_email", None),
            password=json_object.get("password", None),
            gender=json_object.get("gender", None),
            phone_number=json_object.get("phone_number", None),
            description=json_object.get("description", None),
        )
        user_bo.add_in_db(json_object.get("password_confirmation", None))
        email.send_email(
            user_bo.u_student_email,
            "Validate email",
            None,
            f"{url_for("user.verify_email", token=email.generate_token(user_bo.u_student_email), _external=True)}",
        )
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code

    return response


@user.route("/user/verify/email/<token>", methods=["GET"])
def verify_email(token):
    """Sign up endpoint"""
    response = jsonify({"message": "EMAIL_VERIFIED_SUCCESSFULLY"}), 200
    try:
        user_bo = UserBO(
            student_email=email.confirm_token(token),
        )
        user_bo.verify_student_email()
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code

    return response


@user.route("/user/validate/email", methods=["POST"])
def validate_email():
    """Email validation endpoint"""
    response = jsonify({"message": "EMAIL_VALID"}), 200

    try:
        json_object = request.json
        user_bo = UserBO(
            student_email=json_object.get("student_email", None),
        )
        user_bo.validate_student_email()
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code

    return response


@user.route("/user/validate/login", methods=["POST"])
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


@user.route("/user/validate/firstname", methods=["POST"])
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


@user.route("/user/validate/lastname", methods=["POST"])
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


@user.route("/user/validate/gender/<gender>", methods=["GET"])
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


@user.route("/user/validate/phone_number", methods=["POST"])
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


@user.route("/user/validate/password", methods=["POST"])
def validate_password():
    """Password validation endpoint"""
    response = jsonify({"message": "PASSWORD_VALID"}), 200

    try:
        json_object = request.json
        user_bo = UserBO(
            password=json_object.get("password", None),
        )
        user_bo.validate_password(json_object.get("password_confirmation", None))
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code

    return response


@user.route("/user/validate/description", methods=["POST"])
def validate_description():
    """Description validation endpoint"""
    response = jsonify({"message": "DESCRIPTION_VALID"}), 200

    try:
        json_object = request.json
        user_bo = UserBO(
            description=json_object.get("description", None),
        )
        user_bo.validate_description()
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code

    return response
