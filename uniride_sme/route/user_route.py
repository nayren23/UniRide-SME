"""User related endpoints"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from uniride_sme import app
from uniride_sme.service import user_service, documents_service
from uniride_sme.model.dto.user_dto import UserInfosDTO, InformationsVerifiedDTO, DriverInfosDTO,InformationsStatUsers
from uniride_sme.utils.exception.exceptions import ApiException
from uniride_sme.utils.exception.user_exceptions import EmailAlreadyVerifiedException
from uniride_sme.utils import email
from uniride_sme.utils.jwt_token import revoke_token

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
        documents_service.add_documents(user_bo.u_id, request.files)
        email.send_verification_email(user_bo.u_student_email, user_bo.u_firstname, True)
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@user.route("/auth", methods=["POST"])
def authenticate():
    """Authenfication endpoint"""
    json_object = request.json
    try:
        user_bo = user_service.authenticate(json_object.get("login", None), json_object.get("password", None))
        documents_bo = documents_service.get_documents_by_user_id(user_bo.u_id)
        informations_verified_dto = InformationsVerifiedDTO(
            email_verified=user_bo.u_email_verified,
            license_verified=documents_bo.v_license_verified,
            id_card_verified=documents_bo.v_id_card_verified,
            school_certificate_verified=documents_bo.v_school_certificate_verified,
        )
        token = create_access_token(user_bo.u_id)
        response = (
            jsonify(message="AUTHENTIFIED_SUCCESSFULLY", token=token, informations_verified=informations_verified_dto),
            200,
        )
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@user.route("/logout", methods=["DELETE"])
@jwt_required()
def logout():
    """Logout endpoint"""
    revoke_token()
    return jsonify(message="ACCESS_TOKEN_REVOKED"), 200


@user.route("/infos", methods=["GET"])
@jwt_required()
def get_infos():
    """Get user infos endpoint"""
    user_id = get_jwt_identity()
    try:
        user_bo = user_service.get_user_by_id(user_id)
        user_infos_dto = UserInfosDTO(
            login=user_bo.u_login,
            student_email=user_bo.u_student_email,
            firstname=user_bo.u_firstname,
            lastname=user_bo.u_lastname,
            gender=user_bo.u_gender,
            phone_number=user_bo.u_phone_number,
            description=user_bo.u_description,
        )
        response = jsonify(user_infos_dto), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@user.route("/change/password", methods=["POST"])
@jwt_required()
def change_password():
    """Change password endpoint"""
    response = jsonify(message="PASSWORD_CHANGED_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()
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
    user_id = get_jwt_identity()
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
    user_id = get_jwt_identity()
    try:
        user_bo = user_service.get_user_by_id(user_id)
        user_service.save_pfp(user_id, request.files.get("pfp", None), user_bo.u_profile_picture)
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


def save_document(document_type):
    """Generalized endpoint for saving a user document."""
    response = jsonify(message=f"{document_type.upper()}_SAVED_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()
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




@user.route("/email-confirmation", methods=["GET"])
@jwt_required()
def send_email_confirmation():
    """Send email verification endpoint"""
    response = jsonify(message="EMAIL_SEND_SUCCESSFULLY"), 200
    user_id = get_jwt_identity()
    try:
        user_bo = user_service.get_user_by_id(user_id)
        if user_bo.u_email_verified:
            raise EmailAlreadyVerifiedException()
        email.send_verification_email(user_bo.u_student_email, user_bo.u_firstname)
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


@user.route("/verify/document", methods=["GET"])
def verify_document():
    """Get documents to verify"""
    try:
        doc_bo_list = documents_service.document_to_verify()
        response = jsonify({"message": "DOCUMENT_VERIFIED_SUCCESSFULLY", "request": doc_bo_list}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@user.route("/check", methods=["PUT"])
def check_document():
    """Check document"""
    try:
        data = request.json
        result = documents_service.document_check(data)
        response = jsonify(result), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@user.route("/document_user/<int:id_user>", methods=["GET"])
def document_user_verif(id_user):
    """Get documents to verify"""
    try:
        doc_bo_list = documents_service.document_user(id_user)
        response = jsonify({"message": "DOCUMENT_VERIFIED_SUCCESSFULLY", **doc_bo_list}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@user.route("/user_number", methods=["GET"])
def user_count():
    """User count"""
    try:
        stats_user_infos_dto = InformationsStatUsers(
            user_count_value=user_service.count_users(),
            drivers_count_value=user_service.count_role_user(1),
            passenger_count_value=user_service.count_role_user(2),
            pending_count_value =user_service.count_role_user(3),       
        )

        response = jsonify({"message": "USER_NUMBER_SUCCESSFULLY", "user_infos": stats_user_infos_dto}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@user.route("/driver/infos/<user_id>", methods=["GET"])
@jwt_required()
def get_driver_infos(user_id):
    """Get user infos endpoint"""
    try:
        user_bo = user_service.get_user_by_id(user_id)
        user_infos_dto = DriverInfosDTO(
            id=user_bo.u_id,
            firstname=user_bo.u_firstname,
            lastname=user_bo.u_lastname,
            description=user_bo.u_description,
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
    

@user.route("/users_informations", methods=["GET"])
def users_informations():
    """Get users information"""
    try:
        informations_user = user_service.users_information()
        response = jsonify({"message": "USER_DISPLAYED_SUCESSFULLY", "users": informations_user}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response

@user.route("/user_management/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    """delete user """
    try:
        user_deleted = user_service.delete_user(user_id)
        response = jsonify({"message": "USER_DELETED_SUCESSFULLY", "user_id : ": user_deleted}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@user.route("/infos/<user_id>", methods=["GET"])
def user_information_token(user_id):
    """Informations user by token """
    try:
        user_information = user_service.user_information_id(user_id)
        response = jsonify({"message": "USER_INFORMATIONS_DISPLAYED_SUCESSFULLY", "user_information : ": user_information}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response
