"""Trip related routes"""
from flask import Blueprint, request, jsonify

from uniride_sme.models.bo.trip_bo import TripBO

from models.exception.exceptions import ApiException
from datetime import datetime
from uniride_sme.models.bo.address_bo import AddressBO
from uniride_sme.models.dto.trips_get_dto import TripsGetDto
from uniride_sme.models.dto.trip_dto import TripDto
from uniride_sme.models.dto.address_dto import AddressDto
from uniride_sme.models.bo.trip_bo import check_if_route_is_viable

from uniride_sme.models.exception.trip_exceptions import (
    InvalidInputException,
    MissingInputException,
)

import os
from dotenv import load_dotenv


trip = Blueprint("trip", __name__)

@trip.route("/trip/test", methods=["GET"])
def register():
    """Sign up endpoint"""
    response = jsonify({"message": "Test trip OK"}), 200

    return response


@trip.route("/trip/propose", methods=["POST"])
def propose_trip():
    """Propose a trip endpoint"""
    response = jsonify({"message": "TRIP_CREATED_SUCCESSFULLY"}), 200
    
        #verify the fileds
    necessary_fields = ['total_passenger_count', 'timestamp_proposed', 'user_id', 'address_depart_id', 'address_arrival_id']
    json_object = request.json
    
    for field in necessary_fields:
        if field not in json_object:
            return jsonify({"error": f"The '{field}' field is required"}), 400

    try:
        json_object = request.json
        trip_bo = TripBO(
            total_passenger_count = json_object.get("total_passenger_count", None),
            timestamp_proposed = json_object.get("timestamp_proposed", None),
            user_id = json_object.get("user_id", None),
            address_depart_id = json_object.get("address_depart_id", None),
            address_arrival_id = json_object.get("address_arrival_id", None),
            
            status = 1,     #proposé, En cours, annulé, terminé, 
            timestamp_creation = datetime.now(),
        )
        trip_bo.add_in_db()
        response = jsonify({"message": "TRIP_CREATED_SUCCESSFULLY" , "trip_id": trip_bo.trip_id}), 200

    except (MissingInputException, InvalidInputException, ApiException) as e:
        response = jsonify({"message": e.message}), e.status_code

    return response


@trip.route("/trips", methods=["POST"])
def get_available_trips():
    try:

        json_object = request.json
        
        depart_address_bo = AddressBO(
            street_number = json_object.get("depart").get("street_number", None),
            street_name =  json_object.get("depart").get("street_name" , None),
            city = json_object.get("depart").get("city" , None),
            postal_code = json_object.get("depart").get("postal_code", None),
        )
        
        depart_address_bo.get_latitude_longitude_from_address()

        address_arrival_bo = AddressBO(
            street_number = json_object.get("arrival").get("street_number", None),
            street_name = json_object.get("arrival").get("street_name", None),
            city = json_object.get("arrival").get("city", None),
            postal_code = json_object.get("arrival").get("postal_code", None),
        )
        
        address_arrival_bo.get_latitude_longitude_from_address()
        
        #We use the environment variables to get the university address
        university_address_bo = AddressBO(
            street_number = str(os.getenv("UNIVERSITY_STREET_NUMBER")),
            street_name = str(os.getenv("UNIVERSITY_STREET_NAME")),
            city = str(os.getenv("UNIVERSITY_CITY")),
            postal_code = str(os.getenv("UNIVERSITY_POSTAL_CODE")),
        )
        university_address_bo.get_latitude_longitude_from_address()
        
        trip_bo = TripBO(
            total_passenger_count = json_object.get("trip").get("passenger_count", 1),
            timestamp_proposed = json_object.get("trip").get("departure_date", None),
        )
        
        available_trips = trip_bo.get_trips_for_university_address(depart_address_bo, address_arrival_bo,university_address_bo)
        
        response = available_trips
        return jsonify(response), 200


    except ApiException as e:
        response = jsonify({"message": e.message}), 400
        return response