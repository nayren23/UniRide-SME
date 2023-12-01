"""Car related routes"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity


from uniride_sme.model.bo.car_bo import CarBO

from uniride_sme.utils.exception.exceptions import ApiException
from uniride_sme.utils.field import validate_fields
from uniride_sme.service.car_service import add_in_db
from uniride_sme.service.car_service import get_car_info_by_user_id
from uniride_sme.service.car_service import format_get_information_car
from uniride_sme.service.car_service import update_car_information_in_db

car = Blueprint("car", __name__)


@car.route("/car/add", methods=["POST"])
@jwt_required()
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
            user_id=get_jwt_identity(),
        )
        add_in_db(car_bo)
        response = jsonify({"message": "CAR_CREATED_SUCCESSFULLY", "id_car": car_bo.id}), 200
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code
    return response


@car.route("/car/info", methods=["GET"])
@jwt_required()
def get_car_information():
    """Get information about the user's car endpoint"""
    try:
        user_id = get_jwt_identity()
        car_info = get_car_info_by_user_id(user_id)
        if car_info:
            available_car = format_get_information_car(car_info)
            response = jsonify(available_car), 200
        else:
            response = jsonify({"message": "CAR_NOT_FOUND"}), 404
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code
    return response


@car.route("/car/update", methods=["PUT"])
@jwt_required()
def update_car_information():
    """Update information about the user's car endpoint"""
    try:
        user_id = get_jwt_identity()
        json_object = request.json

        # Valider les champs JSON
        validate_fields(
            json_object, {"model": str, "license_plate": str, "country_license_plate": str, "color": str, "brand": str}
        )

        # Récupérer l'objet CarBO existant depuis la base de données
        existing_car_data_list = get_car_info_by_user_id(user_id)

        if existing_car_data_list:
            existing_car_data = existing_car_data_list[0]
            existing_car_model = existing_car_data.get("v_model", "").strip()
            existing_car_license_plate = existing_car_data.get("v_license_plate", "").strip()
            existing_car_country_license_plate = existing_car_data.get("v_country_license_plate", "").strip()
            existing_car_color = existing_car_data.get("v_color", "").strip()
            existing_car_brand = existing_car_data.get("v_brand", "").strip()
            existing_car_total_places = existing_car_data.get("v_total_places", "")

            # Créez un nouvel objet CarBO avec les informations existantes
            existing_car = CarBO(
                model=existing_car_model,
                license_plate=existing_car_license_plate,
                country_license_plate=existing_car_country_license_plate,
                color=existing_car_color,
                brand=existing_car_brand,
                user_id=existing_car_data.get("u_id"),
                total_places=existing_car_total_places,
            )

            # Mettre à jour les propriétés modifiables
            existing_car.model = json_object.get("model", existing_car.model).strip()
            existing_car.license_plate = json_object.get("license_plate", existing_car.license_plate).strip()
            existing_car.country_license_plate = json_object.get(
                "country_license_plate", existing_car.country_license_plate
            ).strip()
            existing_car.color = json_object.get("color", existing_car.color).strip()
            existing_car.brand = json_object.get("brand", existing_car.brand).strip()
            existing_car.total_places = json_object.get("total_places", existing_car.total_places)
            # Mettre à jour la base de données
            update_car_information_in_db(existing_car)

            response = jsonify({"message": "CAR_UPDATED_SUCCESSFULLY"}), 200
        else:
            response = jsonify({"message": "CAR_NOT_FOUND"}), 404
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code
    return response
