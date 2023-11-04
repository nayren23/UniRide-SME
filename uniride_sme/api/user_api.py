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

    try:
        form = request.form
        print(form)
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
    try:
        json_object = request.json
        user_bo = UserBO(
            login=json_object.get("login", None),
            password=json_object.get("password", None),
        )
        user_bo.authentificate()
        user_bo.get_from_db()
        token = create_access_token(user_bo.u_id, expires_delta=False)
        response = (
            jsonify(message="AUTHENTIFIED_SUCCESSFULLY", token=token),
            200,
        )
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
        # TODO remplacer l'url par l'url du front
        url = url_for(
            "user.verify_email",
            token=email.generate_token(student_email),
            _external=True,
        )
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
        user_bo = UserBO(
            student_email=email.confirm_token(token),
        )
        user_bo.verify_student_email()
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response
