"""Trip related routes"""
from flask import Blueprint, request, jsonify

from models.bo.trip_bo import TripBO
from models.exception.exceptions import ApiException
from datetime import datetime

from models.exception.trip_exceptions import (
    InvalidInputException,
    MissingInputException,
)

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
            price = 1,
        )
        #trip_bo.price =  10 #appeller la fonction de calcul du prix,

        trip_bo.add_in_db()
        response = jsonify({"message": "TRIP_CREATED_SUCCESSFULLY" , "trip_id": trip_bo.trip_id}), 200

    except (MissingInputException, InvalidInputException, ApiException) as e:
        response = jsonify({"message": e.message}), e.status_code

    return response