"""Adress related routes"""
from datetime import datetime
from flask import Blueprint, request, jsonify

from uniride_sme.models.bo.address_bo import AddressBO
from uniride_sme.utils.exception.exceptions import ApiException
from uniride_sme.utils.exception.exceptions import InvalidInputException
from uniride_sme.utils.field import validate_fields

address = Blueprint("address", __name__)


@address.route("/address/add", methods=["POST"])
def add_address():
    """Add an address endpoint"""
    try:
        json_object = request.json
        validate_fields(json_object, {"street_number": str, "street_name": str, "city": str, "postal_code": str, "description": str})
        address_bo = AddressBO(
            street_number=json_object.get("street_number", None).strip(),
            street_name=json_object.get("street_name", None).strip(),
            city=json_object.get("city", None).strip(),
            postal_code=json_object.get("postal_code", None).strip(),
            description=json_object.get("description", None).strip(),
            timestamp_modification=datetime.now(),
        )
        address_bo.add_in_db()
        response = jsonify({"message": "ADDRESS_CREATED_SUCCESSFULLY", "id_address": address_bo.id}), 200
    except (ApiException, InvalidInputException) as e:
        response = jsonify({"message": e.message}), e.status_code
    return response
