"""Trip related routes"""
from flask import Blueprint, request, jsonify
from datetime import datetime

from uniride_sme.models.bo.trip_bo import TripBO
from uniride_sme.models.bo.address_bo import AddressBO
from uniride_sme.models.dto.trips_get_dto import TripsGetDto
from uniride_sme.models.dto.trip_dto import TripDto
from uniride_sme.models.dto.address_dto import AddressDto
from uniride_sme.models.bo.trip_bo import check_if_route_is_viable
from uniride_sme.models.bo.trip_bo import get_distance
from uniride_sme.models.dto.address_simple_dto import AddressSimpleDto

from uniride_sme.utils.exception.exceptions import ApiException
from uniride_sme.utils.trip_status import TripStatus

from uniride_sme.utils.exception.trip_exceptions import (
    InvalidInputException,
    MissingInputException,
    TripAlreadyExistsException
)

from uniride_sme.utils.exception.address_exceptions import (
    AddressNotFoundException,
    InvalidAddressException,
    MissingInputException,
    InvalidIntermediateAddressException
)

import os
from dotenv import load_dotenv


trip = Blueprint("trip", __name__)


@trip.route("/trip/propose", methods=["POST"])
def propose_trip():
    """Propose a trip endpoint"""
    """We define the  price of the trip and the status of the trip as pending"""
    
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
            
            status = TripStatus.PENDING.value, 
            timestamp_creation = datetime.now(),
        )
        #Verify the trip is viable
        trip_bo.validate_total_passenger_count()
        trip_bo.validate_timestamp_proposed()
        
        #We need to check if user id is valid
        
        departure_address = AddressBO(address_id = trip_bo.address_depart_id)
        arrival_address = AddressBO(address_id = trip_bo.address_arrival_id)
        
        #We check if address is viable
        departure_address.check_address_existence()
        arrival_address.check_address_existence()
        
        origin = (departure_address.latitude, departure_address.longitude)
        destination = (arrival_address.latitude, arrival_address.longitude)
        
        initial_distance = get_distance(origin, destination)
        trip_price = trip_bo.calculate_price(initial_distance, 1)
        
        trip_bo.price = trip_price
        trip_bo.add_in_db()
        
        response = jsonify({"message": "CREATED_SUCCESSFULLY" , "trip_id": trip_bo.id}), 200

    except (MissingInputException, InvalidInputException, ApiException, AddressNotFoundException, TripAlreadyExistsException) as e:
        response = jsonify({"message": e.message}), e.status_code

    return response


@trip.route("/trips", methods=["POST"])
def get_available_trips():
    """Get all the available trips endpoint"""
    
    try:
        necessary_fields = ['depart', 'arrival', 'trip']
        address_fields = ['street_number', 'street_name', 'city', 'postal_code']
        json_object = request.json
        
        for field in necessary_fields:
            if field not in json_object:
                return jsonify({"error": f"The '{field}' field is required"}), 400
        
        for field in address_fields:
            if field not in json_object['depart'] or field not in json_object['arrival']:
                return jsonify({"error": f"The '{field}' field is required in 'depart' and 'arrival'"}), 400

        depart_address_bo = AddressBO(
            street_number = json_object.get("depart").get("street_number", None),
            street_name =  json_object.get("depart").get("street_name" , None),
            city = json_object.get("depart").get("city" , None),
            postal_code = json_object.get("depart").get("postal_code", None),
        )
        
        #We check if the address is valid
        depart_address_bo.check_address_exigeance()
        
        depart_address_bo.get_latitude_longitude_from_address()

        address_arrival_bo = AddressBO(
            street_number = json_object.get("arrival").get("street_number", None),
            street_name = json_object.get("arrival").get("street_name", None),
            city = json_object.get("arrival").get("city", None),
            postal_code = json_object.get("arrival").get("postal_code", None),
        )
                
        #We check if the address is valid
        address_arrival_bo.check_address_exigeance()
        
        address_arrival_bo.get_latitude_longitude_from_address()
        
        #We use the environment variables to get the university address
        university_address_bo = AddressBO(
            street_number = str(os.getenv("UNIVERSITY_STREET_NUMBER")),
            street_name = str(os.getenv("UNIVERSITY_STREET_NAME")),
            city = str(os.getenv("UNIVERSITY_CITY")),
            postal_code = str(os.getenv("UNIVERSITY_POSTAL_CODE")),
        )
        
        #We check if the address is valid
        university_address_bo.check_address_exigeance()
        
        university_address_bo.get_latitude_longitude_from_address()
        
        trip_bo = TripBO(
            total_passenger_count = json_object.get("trip").get("passenger_count", None),
            timestamp_proposed = json_object.get("trip").get("departure_date", None),
        )
        
        trip_bo.validate_total_passenger_count()
        trip_bo.validate_timestamp_proposed()
        
        available_trips = trip_bo.get_trips_for_university_address(depart_address_bo, address_arrival_bo,university_address_bo)
        
        response = available_trips
        return jsonify(response), 200


    except (ApiException, InvalidIntermediateAddressException, InvalidAddressException, InvalidInputException) as e:
        response = jsonify({"message": e.message}), 400
        return response
    
@trip.route('/trips/driver/current/<userId>', methods=['GET'])
def get_current_driver_trips(userId):
    """Get all the current trips of a driver"""
    try:
        
        trip_bo = TripBO(user_id= userId)
        driver_current_trips = trip_bo.get_current_driver_trips()
        
        available_trips = []

        for trip in driver_current_trips:
            t_id, t_address_depart_id, t_address_arrival_id, price = trip
            
            adresse_depart = AddressBO(address_id = t_address_depart_id)
            arival_address = AddressBO(address_id = t_address_arrival_id)
            
            adresse_depart.check_address_existence()
            arival_address.check_address_existence()
            
            address_dtos = {
                            "departure": AddressSimpleDto(
                                id = adresse_depart.id,
                                name = adresse_depart.concatene_address()
                            ),
                            "arrival": AddressSimpleDto(
                                id = arival_address.id,
                                name = arival_address.concatene_address()
                            )
                        }
            trip_dto = TripDto(
                trip_id= t_id,
                address=address_dtos,
                driver_id = userId,
                price = price,
            )
            trips_get_dto = TripsGetDto(
                trips=trip_dto
            )
            available_trips.append(trips_get_dto)

            # Créez une réponse JSON avec la liste des trajets en cours du conducteur
        response = available_trips
        return jsonify(response), 200

    except ApiException as e:
        return jsonify({"error": str(e)}), 500