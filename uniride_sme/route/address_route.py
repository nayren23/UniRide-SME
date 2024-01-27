"""Adress related routes"""

from flask import Blueprint, request, jsonify
from uniride_sme import app
from uniride_sme.model.bo.address_bo import AddressBO
from uniride_sme.service import address_service
from uniride_sme.utils.exception.exceptions import ApiException
from uniride_sme.utils.field import validate_fields

address = Blueprint("address", __name__, url_prefix="/address")


@address.route("/add", methods=["POST"])
def add_address():
    """Add an address endpoint"""
    try:
        json_object = request.json
        validate_fields(json_object, {"street_number": str, "street_name": str, "city": str, "postal_code": str})
        address_bo = AddressBO(
            street_number=json_object.get("street_number").strip(),
            street_name=json_object.get("street_name").strip(),
            city=json_object.get("city").strip(),
            postal_code=json_object.get("postal_code").strip(),
        )
        address_service.add_address(address_bo)
        response = jsonify({"message": "ADDRESS_CREATED_SUCCESSFULLY", "id_address": address_bo.id}), 200
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code
    return response


@address.route("/university", methods=["GET"])
def get_university_address():
    """Returns the university address"""
    street_number = app.config["UNIVERSITY_STREET_NUMBER"]
    street_name = app.config["UNIVERSITY_STREET_NAME"]
    city = app.config["UNIVERSITY_CITY"]
    postal_code = app.config["UNIVERSITY_POSTAL_CODE"]
    response = jsonify({"address": f"{street_number} {street_name} {city} {postal_code}"})
    return response
