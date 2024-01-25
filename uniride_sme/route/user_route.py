"""User related endpoints"""
from flask import Blueprint, request, jsonify, send_file, make_response
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
    create_access_token,
    set_access_cookies,
    create_refresh_token,
    set_refresh_cookies,
    unset_jwt_cookies,
    verify_jwt_in_request,
)
from flask_jwt_extended.exceptions import NoAuthorizationError
from jwt import ExpiredSignatureError

from uniride_sme import app
from uniride_sme.service import user_service, documents_service
from uniride_sme.model.dto.user_dto import UserInfosDTO, DriverInfosDTO
from uniride_sme.utils.exception.exceptions import ApiException
from uniride_sme.utils.exception.user_exceptions import EmailAlreadyVerifiedException
from uniride_sme.utils import email
from uniride_sme.utils.file import get_encoded_file
from uniride_sme.utils.jwt_token import revoke_token
from uniride_sme.utils.role_user import RoleUser, role_required

user = Blueprint("user", __name__, url_prefix="/user")


@user.route("/register", methods=["POST"])
def register():
    """Sign up endpoint"""
    response = jsonify(message="USER_CREATED_SUCCESSFULLY"), 200
    form = request.form
    try:
        user_bo = user_service.add_user(
            form.get("login", None),
            form.get("firstname", None),
            form.get("lastname", None),
            form.get("student_email", None),
            form.get("password", None),
            form.get("password_confirmation", None),
            form.get("gender", None),
            form.get("phone_number", None),
            form.get("description", None),
            request.files.get("pfp", None),
        )
        documents_service.add_documents(user_bo.id, request.files)
        email.send_verification_email(user_bo.student_email, user_bo.firstname, True)
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@user.route("/auth", methods=["POST"])
def authenticate():
    """Authenfication endpoint"""
    json_object = request.json
    try:
        user_bo = user_service.authenticate(json_object.get("login", None), json_object.get("password", None))
        response = make_response(jsonify(message="AUTHENTIFIED_SUCCESSFULLY"))

        access_token = create_access_token({"id": user_bo.id, "role": user_bo.r_id})
        set_access_cookies(response, access_token)
        if json_object.get("keepLoggedIn", False):
            refresh_token = create_refresh_token({"id": user_bo.id, "role": user_bo.r_id})
            set_refresh_cookies(response, refresh_token)
        response.status_code = 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@user.route("/refresh", methods=["GET"])
@jwt_required(refresh=True)
def refresh():
    """Refresh token endpoint"""
    response = jsonify(message="REFRESHED_SUCCESSFULLY")
    access_token = create_access_token(get_jwt_identity())
    set_access_cookies(response, access_token)
    return response, 200


@user.route("/logout", methods=["DELETE"])
def logout():
    """Logout endpoint"""
    response = jsonify(message="LOGOUT_SUCCESSFULY")
    try:
        verify_jwt_in_request()
        revoke_token()
    except (ExpiredSignatureError, NoAuthorizationError):
        pass

    try:
        verify_jwt_in_request(refresh=True)
        revoke_token()
    except (ExpiredSignatureError, NoAuthorizationError):
        pass

    unset_jwt_cookies(response)
    return response, 200


@user.route("/infos", methods=["GET"])
@jwt_required()
def get_infos():
    """Get user infos endpoint"""
    user_id = get_jwt_identity()["id"]
    try:
        user_bo = user_service.get_user_by_id(user_id)
        user_infos_dto = UserInfosDTO(
            id=user_id,
            login=user_bo.login,
            student_email=user_bo.student_email,
            firstname=user_bo.firstname,
            lastname=user_bo.lastname,
            gender=user_bo.gender,
            phone_number=user_bo.phone_number,
            description=user_bo.description,
            role=user_bo.r_id,
            profile_picture=get_encoded_file(user_bo.profile_picture, "PFP_UPLOAD_FOLDER"),
        )
        response = jsonify(user_infos_dto), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@user.route("/role", methods=["GET"])
@jwt_required()
def get_user_id():
    """Get user ID and his role ID"""
    user_id = get_jwt_identity()["id"]
    try:
        user_role = user_service.get_user_role(user_id)
        response = jsonify(user_role), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@user.route("/change/password", methods=["POST"])
@jwt_required()
def change_password():
    """Change password endpoint"""
    response = jsonify(message="PASSWORD_CHANGED_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()["id"]
    json_object = request.json
    try:
        user_service.change_password(
            user_id,
            json_object.get("old_password", None),
            json_object.get("new_password", None),
            json_object.get("new_password_confirmation", None),
        )
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


def change_user_attribute(attribute_name):
    """Generalized endpoint for changing a user attribute."""
    response = jsonify(message=f"{attribute_name.upper()}_CHANGED_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()["id"]
    try:
        getattr(user_service, f"change_{attribute_name}")(user_id, request.json.get(attribute_name, None))
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@user.route("/change/login", methods=["POST"])
@jwt_required()
def change_login():
    """Change login endpoint."""
    return change_user_attribute("login")


@user.route("/change/firstname", methods=["POST"])
@jwt_required()
def change_firstname():
    """Change firstname endpoint."""
    return change_user_attribute("firstname")


@user.route("/change/lastname", methods=["POST"])
@jwt_required()
def change_lastname():
    """Change lastname endpoint."""
    return change_user_attribute("lastname")


@user.route("/change/student-email", methods=["POST"])
@jwt_required()
def change_student_email():
    """Change student email endpoint."""
    return change_user_attribute("student_email")


@user.route("/change/phone-number", methods=["POST"])
@jwt_required()
def change_phone_number():
    """Change phone number endpoint."""
    return change_user_attribute("phone_number")


@user.route("/change/gender", methods=["POST"])
@jwt_required()
def change_gender():
    """Change gender endpoint."""
    return change_user_attribute("gender")


@user.route("/change/description", methods=["POST"])
@jwt_required()
def change_description():
    """Change description endpoint."""
    return change_user_attribute("description")


@user.route("/save/pfp", methods=["POST"])
@jwt_required()
def save_pfp():
    """Save profil picture endpoint"""
    response = jsonify(message="PROFIL_PICTURE_SAVED_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()["id"]
    try:
        user_bo = user_service.get_user_by_id(user_id)
        user_service.save_pfp(user_id, request.files.get("pfp", None), user_bo.profile_picture)
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@user.route("documents/infos", methods=["GET"])
@jwt_required()
def get_user_documents_infos():
    """Get user infos endpoint"""
    user_id = get_jwt_identity()["id"]
    try:
        doc_bo_list = documents_service.document_user(user_id)
        response = jsonify({"message": "DOCUMENT_VERIFIED_SUCCESSFULLY", **doc_bo_list}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


def save_document(document_type):
    """Generalized endpoint for saving a user document."""
    response = jsonify(message=f"{document_type.upper()}_SAVED_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()["id"]
    document_file = request.files.get(document_type, None)
    try:
        document_bo = documents_service.get_documents_by_user_id(user_id)
        getattr(documents_service, f"save_{document_type}")(
            user_id, document_file, getattr(document_bo, f"d_{document_type}")
        )
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@user.route("/save/license", methods=["POST"])
@jwt_required()
def save_license():
    """Save profile license endpoint."""
    return save_document("license")


@user.route("/save/id-card", methods=["POST"])
@jwt_required()
def save_id_card():
    """Save profile ID card endpoint."""
    return save_document("id_card")


@user.route("/save/school-certificate", methods=["POST"])
@jwt_required()
def save_school_certificate():
    """Save profile school certificate endpoint."""
    return save_document("school_certificate")


@user.route("/save/insurance", methods=["POST"])
@jwt_required()
def insurance():
    """Save profile insurance endpoint."""
    return save_document("insurance")


@user.route("/email-confirmation", methods=["GET"])
@jwt_required()
def send_email_confirmation():
    """Send email verification endpoint"""
    response = jsonify(message="EMAIL_SEND_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()["id"]
    try:
        user_bo = user_service.get_user_by_id(user_id)
        if user_bo.email_verified:
            raise EmailAlreadyVerifiedException()
        email.send_verification_email(user_bo.student_email, user_bo.firstname)
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@user.route("/verify/email/<token>", methods=["GET"])
def verify_email(token):
    """Sign up endpoint"""
    response = jsonify(message="EMAIL_VERIFIED_SUCCESSFULLY"), 200
    try:
        student_email = email.confirm_token(token)
        user_service.verify_student_email(student_email)
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@user.route("/change/password/<token>", methods=["POST"])
def change_forgotten_password(token):
    """Change password endpoint"""
    response = jsonify(message="PASSWORD_CHANGED_SUCCESSFULLY"), 200
    json_object = request.json
    try:
        user_id = email.confirm_token(token)
        user_service.change_forgotten_password(
            user_id,
            json_object.get("new_password", None),
            json_object.get("new_password_confirmation", None),
        )
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@user.route("/request-password-change", methods=["POST"])
def send_password_change():
    """Send email password change endpoint"""
    response = jsonify(message="EMAIL_SEND_SUCCESSFULLY"), 200
    try:
        user_bo = user_service.get_user_by_email(request.json.get("student_email", None))
        email.send_password_change_email(user_bo.student_email, user_bo.firstname)
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@user.route("/driver/infos/<user_id>", methods=["GET"])
@role_required(RoleUser.PASSENGER)
def get_driver_infos(user_id):
    """Get user infos endpoint"""
    try:
        user_bo = user_service.get_user_by_id(user_id)
        user_infos_dto = DriverInfosDTO(
            id=user_bo.id,
            firstname=user_bo.firstname,
            lastname=user_bo.lastname,
            description=user_bo.description,
        )
        response = jsonify(user_infos_dto), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@user.route("/default-profile-picture", methods=["GET"])
def get_default_profile_picture():
    """Get default profile picture""" ""
    return send_file(
        f"{app.config['PATH']}/resource/default_profile_picture.png",
        download_name="default_profile_picture.png",
    )


@user.route("/label/info/<trip_id>", methods=["GET"])
@jwt_required()
def get_label(trip_id):
    """Get label"""
    try:
        user_id = get_jwt_identity()["id"]
        data = user_service.get_label(trip_id, user_id)
        response = jsonify({"label": data}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response
