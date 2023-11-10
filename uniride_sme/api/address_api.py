"""Adress related routes"""
from flask import Blueprint, request, jsonify
from datetime import datetime

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
        if validate_fields(json_object, {"street_number": str, "street_name": str, "city": str, "postal_code": str, "description": str}):
                
            address_bo = AddressBO(
                                    street_number=json_object.get("street_number", None),
                                    street_name=json_object.get("street_name", None),
                                    city=json_object.get("city", None),
                                    postal_code=json_object.get("postal_code", None),
                                    description=json_object.get("description", None),
                                    timestamp_modification=datetime.now()
                                )
            address_bo.add_in_db()
            response = jsonify({"message": "ADDRESS_CREATED_SUCCESSFULLY!", "id_address": address_bo.id}), 200
    except (ApiException, InvalidInputException) as e:
        response = jsonify({"message": e.message}), e.status_code
    return response