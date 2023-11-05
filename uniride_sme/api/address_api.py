"""Adress related routes"""
from flask import Blueprint, request, jsonify

from uniride_sme.models.bo.address_bo import AddressBO
from uniride_sme.models.exception.exceptions import ApiException
from datetime import datetime

address = Blueprint("address", __name__)

@address.route("/address/add", methods=["POST"])
def add_address():
    """Add an address endpoint"""
    try:
        json_object = request.json
        #verify the fileds
        necessary_fields = ['street_number', 'street_name', 'city', 'postal_code', 'description']
        for field in necessary_fields:
            if field not in json_object:
                return jsonify({"error": f"The '{field}' field is required"}), 400
            
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
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code
    return response