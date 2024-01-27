"""Car related routes"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity

from uniride_sme.model.bo.car_bo import CarBO
from uniride_sme.service.car_service import (
    add_car,
    get_car_info_by_user_id,
    format_get_information_car,
    update_car_information_in_db,
)

from uniride_sme.utils.exception.exceptions import ApiException
from uniride_sme.utils.field import validate_fields
from uniride_sme.utils.role_user import RoleUser, role_required

car = Blueprint("car", __name__, url_prefix="/car")


@car.route("/add", methods=["POST"])
@role_required(RoleUser.DRIVER)
def add_car_information():
    """Add information car endpoint"""
    try:
        json_object = request.json
        validate_fields(
            json_object,
            {
                "model": str,
                "license_plate": str,
                "country_license_plate": str,
                "color": str,
                "brand": str,
                "total_places": int,
            },
        )
        car_bo = CarBO(
            model=json_object.get("model").strip(),
            license_plate=json_object.get("license_plate").strip(),
            country_license_plate=json_object.get("country_license_plate").strip(),
            color=json_object.get("color").strip(),
            brand=json_object.get("brand").strip(),
            total_places=json_object.get("total_places"),
            user_id=get_jwt_identity()["id"],
        )
        add_car(car_bo)
        response = jsonify({"message": "CAR_CREATED_SUCCESSFULLY", "id_car": car_bo.id}), 200
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code
    return response


@car.route("/info", methods=["GET"])
@role_required(RoleUser.DRIVER)
def get_car_information():
    """Get information about the user's car endpoint"""
    try:
        user_id = get_jwt_identity()["id"]
        car_info = get_car_info_by_user_id(user_id)
        available_car = format_get_information_car(car_info)
        response = jsonify(available_car), 200
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code
    return response


@car.route("/update", methods=["PUT"])
@role_required(RoleUser.DRIVER)
def update_car_information():
    """Update information about the user's car endpoint"""
    try:
        user_id = get_jwt_identity()["id"]
        json_object = request.json

        # Valider les champs JSON
        validate_fields(
            json_object, {"model": str, "license_plate": str, "country_license_plate": str, "color": str, "brand": str}
        )

        # Récupérer l'objet CarBO existant depuis la base de données
        existing_car_data_list = get_car_info_by_user_id(user_id)

        # Mettre à jour les propriétés modifiables
        existing_car_data_list.model = json_object.get("model", existing_car_data_list.model).strip()
        existing_car_data_list.license_plate = json_object.get(
            "license_plate", existing_car_data_list.license_plate
        ).strip()
        existing_car_data_list.country_license_plate = json_object.get(
            "country_license_plate", existing_car_data_list.country_license_plate
        ).strip()
        existing_car_data_list.color = json_object.get("color", existing_car_data_list.color).strip()
        existing_car_data_list.brand = json_object.get("brand", existing_car_data_list.brand).strip()
        existing_car_data_list.total_places = json_object.get("total_places", existing_car_data_list.total_places)
        # Mettre à jour la base de données
        update_car_information_in_db(existing_car_data_list)

        response = jsonify({"message": "CAR_UPDATED_SUCCESSFULLY"}), 200
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code
    return response
