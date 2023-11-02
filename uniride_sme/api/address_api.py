"""Adress related routes"""
from flask import Blueprint, request, jsonify

from models.bo.address_bo import AddressBO
from models.exception.exceptions import ApiException
from datetime import datetime


address = Blueprint("address", __name__)

@address.route("/address/test", methods=["GET"])
def register():
    """Sign up endpoint"""
    response = jsonify({"message": "Test address OK"}), 200

    
    return response

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
            
        address_bo = create_address_from_json(json_object)
        address_bo.add_in_db()
        response = jsonify({"message": "ADDRESS_CREATED_SUCCESSFULLY!", "id_address": address_bo.address_id}), 200
    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code
    return response

@address.route("/address/add_trip_addresses", methods=["POST"])
def add_trip_addresses():
    """Add departure and arrival addresses for a trip"""
    try:
        json_object = request.json

        #verify the fileds
        necessary_fields = ['departure_street_number', 'departure_street_name', 'departure_city', 'departure_postal_code', 'departure_description',
                            'arrival_street_number', 'arrival_street_name', 'arrival_city', 'arrival_postal_code', 'arrival_description'
                            ]
        
        for field in necessary_fields:
            if field not in json_object:
                return jsonify({"error": f"The '{field}' field is required"}), 400
        
        # Create departure and arrival addresses using helper function
        departure_address_bo = create_address_from_json(json_object, "departure_")
        
        print(departure_address_bo)
        arrival_address_bo = create_address_from_json(json_object, "arrival_")

        # Add addresses to the database
        departure_address_bo.add_in_db()
        arrival_address_bo.add_in_db()

        response = jsonify({"message": "ADDRESSES_CREATED_SUCCESSFULLY!",
                            "departure_address_id": departure_address_bo.address_id,
                            "arrival_address_id": arrival_address_bo.address_id}), 200

    except ApiException as e:
        response = jsonify({"message": e.message}), e.status_code

    return response

def create_address_from_json(json_object, prefix=""):


    """Create an AddressBO object from JSON data with the given prefix (departure or arrival)"""
    return AddressBO(
        street_number=json_object.get(f"{prefix}street_number", None),
        street_name=json_object.get(f"{prefix}street_name", None),
        city=json_object.get(f"{prefix}city", None),
        postal_code=json_object.get(f"{prefix}postal_code", None),
        description=json_object.get(f"{prefix}description", None),
        timestamp_modification=datetime.now()
    )