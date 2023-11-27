"""Car related routes"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required


from uniride_sme.model.bo.car_bo import CarBO

from uniride_sme.utils.exception.exceptions import ApiException
from uniride_sme.utils.field import validate_fields
from uniride_sme.service.car_service import add_in_db

car = Blueprint("car", __name__)

@car.route("/car/add", methods=["POST"])
@jwt_required()
def information_car():
    """Add information car endpoint"""
    try:
        json_object = request.json
        validate_fields(json_object, {"model": str, "licence_plate": str, "country_licence_plate": str, "color": str, "brand": str})
        car_bo = CarBO(
            model=json_object.get("model").strip(),
            licence_plate=json_object.get("licence_plate").strip(),
            country_licence_plate=json_object.get("country_licence_plate").strip(),
            color=json_object.get("color").strip(),
            brand=json_object.get("brand").strip()
        )
        add_in_db()
        response = jsonify({"message": "CAR_CREATED_SUCCESSFULLY", "id_car": car_bo.id}), 200
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code
    return response