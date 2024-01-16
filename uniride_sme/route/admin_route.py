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
from uniride_sme.model.dto.trip_dto import TripStatusDTO
from uniride_sme import app
from uniride_sme.service import admin_service, documents_service, user_service,trip_service
from uniride_sme.model.dto.user_dto import (
    UserInfosDTO,
    InformationsVerifiedDTO,
    DriverInfosDTO,
    InformationsStatUsers,
)
from uniride_sme.utils.exception.exceptions import ApiException
from uniride_sme.utils.exception.user_exceptions import EmailAlreadyVerifiedException, UserNotAUTHORIZED
from uniride_sme.utils import email
from uniride_sme.utils.file import get_encoded_file
from uniride_sme.utils.jwt_token import revoke_token
from uniride_sme.utils.role_user import RoleUser, role_required

admin = Blueprint("admin", __name__, url_prefix="/admin")



@admin.route("/users-informations", methods=["GET"])
@role_required(RoleUser.ADMINISTRATOR)
def users_informations():
    """Get users information"""
    try:
        informations_user = admin_service.users_information()
        response = jsonify({"message": "USER_DISPLAYED_SUCESSFULLY", "users": informations_user}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@admin.route("/user-management/<user_id>", methods=["DELETE"])
@role_required(RoleUser.ADMINISTRATOR)
def delete_user(user_id):
    """delete user"""
    user_id_token = get_jwt_identity()["id"]
    role = user_service.get_user_role(user_id)

    try:
        if user_id_token == user_id or role["role"] == 0:
            raise UserNotAUTHORIZED
        user_deleted = admin_service.delete_user(user_id)
        response = jsonify({"message": "USER_DELETED_SUCESSFULLY", "user_id : ": user_deleted}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@admin.route("/infos/<user_id>", methods=["GET"])
@role_required(RoleUser.ADMINISTRATOR)
def user_information_token(user_id):
    """Informations user by token"""
    try:
        user_information = admin_service.user_information_id(user_id)
        response = (
            jsonify({"message": "USER_INFORMATIONS_DISPLAYED_SUCESSFULLY", "user_information": user_information}),
            200,
        )
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@admin.route("/statistics/<user_id>", methods=["GET"])
@role_required(RoleUser.ADMINISTRATOR)
def user_stat_id(user_id):
    """Informations user by token"""
    try:
        user_stat_passenger = admin_service.user_stat_passenger(user_id)
        user_stat_driver = admin_service.user_stat_driver(user_id)
        average_rating = admin_service.average_rating_user_id(user_id)
        response_data = {
            "statistics": [
                {
                    "driver_trip": user_stat_driver,
                },
                {
                    "passenger_trip": user_stat_passenger,
                },
                {
                    "average_rating": average_rating,
                },
            ]
        }

        response = (
            jsonify({"message": "USER_STATS_DISPLAYED_SUCESSFULLY", **response_data}),
            200,
        )
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response

@admin.route("/trip-number", methods=["GET"])
@role_required(RoleUser.ADMINISTRATOR)
def trip_count():
    """Trip count"""
    try:
        trip_count_status = TripStatusDTO(
            trip_pending=trip_service.trips_status(1),
            trip_canceled=trip_service.trips_status(2),
            trip_completed=trip_service.trips_status(3),
            trip_oncourse=trip_service.trips_status(4),
        )
        response = jsonify({"message": "TRIP_NUMBER_DISPLAYED_SUCCESSFULLY", "trip_infos": trip_count_status}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response

@admin.route("/user-number", methods=["GET"])
@role_required(RoleUser.ADMINISTRATOR)
def user_count():
    """User count"""
    try:
        stats_user_infos_dto = InformationsStatUsers(
            admin_count_value=admin_service.count_role_user(0),
            drivers_count_value=admin_service.count_role_user(1),
            passenger_count_value=admin_service.count_role_user(2),
            pending_count_value=admin_service.count_role_user(3),
        )

        response = jsonify({"message": "USER_NUMBER_SUCCESSFULLY", "user_infos": stats_user_infos_dto}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response

@admin.route("/verify/document", methods=["GET"])
@role_required(RoleUser.ADMINISTRATOR)
def verify_document():
    """Get documents to verify"""
    try:
        doc_bo_list = documents_service.document_to_verify()
        response = jsonify({"message": "DOCUMENT_VERIFIED_SUCCESSFULLY", "request": doc_bo_list}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@admin.route("/check", methods=["PUT"])
@role_required(RoleUser.ADMINISTRATOR)
def check_document():
    """Check document"""
    try:
        data = request.json
        result = documents_service.document_check(data)
        # Utilisez jsonify pour retourner une réponse JSON
        user_bo = user_service.get_user_by_id(data["user_id"])
        email.send_document_validation_email(
            user_bo.student_email,
            user_bo.firstname,
            data["document"]["type"],
            data["document"]["status"],
        )
        response = jsonify(result), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@admin.route("/document-user/<int:id_user>", methods=["GET"])
@role_required(RoleUser.ADMINISTRATOR)
def document_user_verif(id_user):
    """Get documents to verify"""
    try:
        doc_bo_list = documents_service.document_user(id_user)
        response = jsonify({"message": "DOCUMENT_VERIFIED_SUCCESSFULLY", **doc_bo_list}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@admin.route("/document-number", methods=["GET"])
@role_required(RoleUser.ADMINISTRATOR)
def count_documents_status():
    """Get documents to verify"""
    try:
        doc_numbers = documents_service.document_number_status()
        response = (
            jsonify({"message": "DOCUMENT_NUMBER_STATUS_DISPLAYED_SUCESSFULLY", "document_infos": doc_numbers}),
            200,
        )
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response

@admin.route("/label", methods=["GET"])
@role_required(RoleUser.ADMINISTRATOR)
def get_rating_criteria():
    """Get rating criteria"""
    try:
        user_information = admin_service.get_rating_criteria()
        return jsonify({"message": "USER_INFORMATIONS_DISPLAYED_SUCCESSFULLY", "labels": user_information}), 200
    except ApiException as e:
        return jsonify(message=e.message), e.status_code


@admin.route("/label", methods=["POST"])
@role_required(RoleUser.ADMINISTRATOR)
def insert_label():
    """Insert rating criteria"""
    data = request.get_json()
    try:
        user_information = admin_service.insert_rating_criteria(data)
        response = (
            jsonify({"message": "RATING_CRITERIA_INSERTED_SUCCESSFULLY", "user_information": user_information}),
            201,
        )
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code

    return response


@admin.route("/label/<id_criteria>", methods=["DELETE"])
@role_required(RoleUser.ADMINISTRATOR)
def delete_label(id_criteria):
    """Delete rating criteria"""
    try:
        user_information = admin_service.delete_rating_criteria(id_criteria)
        return jsonify({"message": "RATING_CRITERIA_DELETED_SUCCESSFULLY", "id_criteria": user_information}), 200
    except ApiException as e:
        return jsonify(message=e.message), e.status_code


@admin.route("/label", methods=["PUT"])
@role_required(RoleUser.ADMINISTRATOR)
def update_label():
    """Update rating criteria"""
    data = request.get_json()

    try:
        admin_service.update_rating_criteria(data)
        response = jsonify({"message": "RATING_CRITERIA_UPDATED_SUCCESSFULLY"}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@admin.route("/drivers-ranking", methods=["GET"])
@role_required(RoleUser.ADMINISTRATOR)
def get_ranking_drivers():
    """Get ranking drivers"""
    try:
        data = admin_service.users_ranking(1)
        response = jsonify({"message": "DRIVERS_RATING_CRITERIA_DISPLAYED_SUCCESSFULLY", "ranking": data}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@admin.route("/passengers-ranking", methods=["GET"])
@role_required(RoleUser.ADMINISTRATOR)
def get_ranking_passengers():
    """Get ranking passengers"""
    try:
        data = admin_service.users_ranking(2)
        response = jsonify({"message": "PASSENGERS_RATING_CRITERIA_DISPLAYED_SUCCESSFULLY", "ranking": data}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@admin.route("/actif-criterion/<r_id>", methods=["GET"])
@role_required(RoleUser.ADMINISTRATOR)
def get_actif_criterian(r_id):
    """Get ranking passengers"""
    try:
        data = admin_service.actif_criteria(r_id)
        response = jsonify({"message": "ACTIF_CRITERION_DISPLAYED_SUCCESSFULLY", "criterion": data}), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response
