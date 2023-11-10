"""User related endpoints"""
from flask import Blueprint, request, jsonify, url_for
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required

from uniride_sme import app
from uniride_sme.models.bo.user_bo import UserBO
from uniride_sme.utils.exception.exceptions import (
    ApiException,
)
from uniride_sme.utils.exception.user_exceptions import EmailAlreadyVerifiedException
from uniride_sme.utils import email


user = Blueprint("user", __name__)


@user.route("/user/register", methods=["POST"])
def register():
    """Sign up endpoint"""
    response = jsonify(message="USER_CREATED_SUCCESSFULLY"), 200
    form = request.form
    try:
        user_bo = UserBO(
            login=form.get("login", None),
            firstname=form.get("firstname", None),
            lastname=form.get("lastname", None),
            student_email=form.get("student_email", None),
            password=form.get("password", None),
            gender=form.get("gender", None),
            phone_number=form.get("phone_number", None),
            description=form.get("description", None),
        )
        user_bo.add_in_db(form.get("password_confirmation", None), request.files)
        send_verification_email(user_bo.u_student_email, user_bo.u_firstname)
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@user.route("/user/auth", methods=["POST"])
def authentificate():
    """Authenfication endpoint"""
    json_object = request.json
    try:
        user_bo = UserBO(
            login=json_object.get("login", None),
            password=json_object.get("password", None),
        )
        user_bo.authentificate()
        user_bo.get_from_db()
        token = create_access_token(
            user_bo.u_id, expires_delta=app.config["JWT_ACCESS_TOKEN_EXPIRES"]
        )
        response = (
            jsonify(message="AUTHENTIFIED_SUCCESSFULLY", token=token),
            200,
        )
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@user.route("/user/change/password", methods=["POST"])
@jwt_required()
def change_password():
    """Change password endpoint"""
    response = jsonify(message="PASSWORD_CHANGED_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()
    json_object = request.json
    try:
        user_bo = UserBO(user_id=user_id)
        user_bo.change_password(
            json_object.get("old_password", None),
            json_object.get("new_password", None),
            json_object.get("new_password_confirmation", None),
        )
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@user.route("/user/change/login", methods=["POST"])
@jwt_required()
def change_login():
    """Change login endpoint"""
    response = jsonify(message="LOGIN_CHANGED_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()
    json_object = request.json
    try:
        user_bo = UserBO(user_id=user_id)
        user_bo.change_login(json_object.get("login", None))
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@user.route("/user/change/firstname", methods=["POST"])
@jwt_required()
def change_firstname():
    """Change firstname endpoint"""
    response = jsonify(message="FIRSTNAME_CHANGED_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()
    json_object = request.json
    try:
        user_bo = UserBO(user_id=user_id)
        user_bo.change_firstname(json_object.get("firstname", None))
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@user.route("/user/change/lastname", methods=["POST"])
@jwt_required()
def change_lastname():
    """Change lastname endpoint"""
    response = jsonify(message="LASTNAME_CHANGED_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()
    json_object = request.json
    try:
        user_bo = UserBO(user_id=user_id)
        user_bo.change_lastname(json_object.get("lastname", None))
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@user.route("/user/change/student-email", methods=["POST"])
@jwt_required()
def change_student_email():
    """Change student email endpoint"""
    response = jsonify(message="STUDENT_EMAIL_CHANGED_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()
    json_object = request.json
    try:
        user_bo = UserBO(user_id=user_id)
        user_bo.change_student_email(json_object.get("student_email", None))
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@user.route("/user/change/phone-number", methods=["POST"])
@jwt_required()
def change_phone_number():
    """Change phone number endpoint"""
    response = jsonify(message="PHONE_NUMBER_CHANGED_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()
    json_object = request.json
    try:
        user_bo = UserBO(user_id=user_id)
        user_bo.change_phone_number(json_object.get("phone_number", None))
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@user.route("/user/change/gender", methods=["POST"])
@jwt_required()
def change_gender():
    """Change gender endpoint"""
    response = jsonify(message="GENDER_CHANGED_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()
    json_object = request.json
    try:
        user_bo = UserBO(user_id=user_id)
        user_bo.change_gender(json_object.get("gender", None))
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@user.route("/user/save/pfp", methods=["POST"])
@jwt_required()
def save_pfp():
    """Save profil picture endpoint"""
    response = jsonify(message="PROFIL_PICTURE_SAVED_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()
    try:
        user_bo = UserBO(user_id=user_id)
        user_bo.save_pfp(request.files)
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@user.route("/user/save/license", methods=["POST"])
@jwt_required()
def save_license():
    """Save profil license endpoint"""
    response = jsonify(message="LICENSE_SAVED_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()
    try:
        user_bo = UserBO(user_id=user_id)
        user_bo.save_license(request.files)
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@user.route("/user/save/id-card", methods=["POST"])
@jwt_required()
def save_id_card():
    """Save profil id_card endpoint"""
    response = jsonify(message="ID_CARD_SAVED_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()
    try:
        user_bo = UserBO(user_id=user_id)
        user_bo.save_id_card(request.files)
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@user.route("/user/save/school-certificate", methods=["POST"])
@jwt_required()
def save_school_certificate():
    """Save profil school_certificate endpoint"""
    response = jsonify(message="SCHOOL_CERTIFICATE_SAVED_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()
    try:
        user_bo = UserBO(user_id=user_id)
        user_bo.save_school_certificate(request.files)
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@user.route("/user/email-confirmation", methods=["GET"])
@jwt_required()
def send_email_confirmation():
    """Send email verification endpoint"""
    response = jsonify(message="EMAIL_SEND_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()
    try:
        user_bo = UserBO(user_id=user_id)
        if user_bo.u_email_verified:
            raise EmailAlreadyVerifiedException()
        send_verification_email(user_bo.u_student_email, user_bo.u_firstname)
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


def send_verification_email(student_email, firstname):
    """Send verification email"""
    with open(
        f"{app.config['PATH']}\\resource\\email\\email_verification_template.html",
        "r",
        encoding="UTF-8",
    ) as html:
        url = url_for(
            "user.verify_email",
            token=email.generate_token(student_email),
            _external=False,
        )
        url = app.config["FRONT_END_URL"] + url
        email.send_email(
            student_email,
            "Vérifier votre email",
            html.read().replace("{firstname}", firstname).replace("{link}", url),
        )


@user.route("/user/verify/email/<token>", methods=["GET"])
def verify_email(token):
    """Sign up endpoint"""
    response = jsonify(message="EMAIL_VERIFIED_SUCCESSFULLY"), 200
    try:
        UserBO.verify_student_email(email.confirm_token(token))
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response
