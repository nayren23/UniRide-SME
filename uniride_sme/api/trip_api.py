"""Trip related routes"""
from flask import Blueprint, request, jsonify

from models.bo.trip_bo import TripBO

from models.exception.exceptions import ApiException
from datetime import datetime
from models.bo.address_bo import AddressBO

from models.exception.trip_exceptions import (
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
            price = 1,
        )
        #trip_bo.price =  10 #appeller la fonction de calcul du prix,

        trip_bo.add_in_db()
        response = jsonify({"message": "TRIP_CREATED_SUCCESSFULLY" , "trip_id": trip_bo.trip_id}), 200

    except (MissingInputException, InvalidInputException, ApiException) as e:
        response = jsonify({"message": e.message}), e.status_code

    return response


@trip.route("/trips", methods=["GET"])
def get_available_trips():
    try:
        # Get the intermediate address from the request
        intermediate_departure_latitude = str(request.args.get("departure_latitude"))
        intermediate_departure_longitude = str(request.args.get("departure_longitude"))
        intermediate_arrival_latitude = str(request.args.get("arrival_latitude"))
        intermediate_arrival_longitude = str(request.args.get("arrival_longitude"))

        #We use the environment variables to get the university address
        address_bo = AddressBO(
            street_number = str(os.getenv("UNIVERSITY_STREET_NUMBER")),
            street_name = str(os.getenv("UNIVERSITY_STREET_NAME")),
            city = str(os.getenv("UNIVERSITY_CITY")),
            postal_code = str(os.getenv("UNIVERSITY_POSTAL_CODE")),
        )
        address_bo.get_latitude_longitude_from_address()
        
        #We need to round the latitude and longitude to 10 decimal places
        university_latitude = "{:.10f}".format(address_bo.latitude)
        university_longitude = "{:.10f}".format(address_bo.longitude)
                
        point_universite = (university_latitude, university_longitude)
        
        point_intermediaire_depart = (intermediate_departure_latitude, intermediate_departure_longitude)
        point_intermediaire_arrivee = (intermediate_arrival_latitude, intermediate_arrival_longitude)

        trip_bo = TripBO(
            total_passenger_count= str(request.args.get("passenger_count", 1)),
            timestamp_proposed= request.args.get("departure_date"),
        )
                
        if(point_intermediaire_depart == point_universite):
            print("intermediaire_depart == universite")
            condition_where = "(departure_address.a_latitude = %s AND departure_address.a_longitude = %s)"
            trips = trip_bo.get_trips(university_latitude, university_longitude, condition_where)
        elif(point_intermediaire_arrivee == point_universite):
            print("intermediaire_arrivee == universite")
            condition_where = "(arrival_address.a_latitude = %s AND arrival_address.a_longitude = %s)"
            trips = trip_bo.get_trips(university_latitude, university_longitude, condition_where)
        else:   
            # If the intermediate address is not the university, raise an exception
            raise Exception("L'adresse intermédiaire ne correspond pas à l'université.")
        

        print("trips", trips)

    
        available_trips = []

        for trip in trips:
            trip_id, total_passenger_count, proposed_date, creation_timestamp, trip_status, trip_price, user_id, \
            departure_address_id, arrival_address_id, departure_latitude, departure_longitude, arrival_latitude, \
            arrival_longitude = trip

            point_depart = (departure_latitude, departure_longitude)
            point_arrivee = (arrival_latitude, arrival_longitude)
            
            if point_intermediaire_depart == point_universite:
                # Si le point de départ est l'université, alors l'université est l'adresse d'arrivée du trajet
                print("QUOIIII!!!!!!!!!!!!!!!!!!!!")
                is_viable = trip_bo.check_if_route_is_viable(point_depart, point_arrivee, point_intermediaire_arrivee)
            
            elif point_intermediaire_arrivee == point_universite:
                # Si le point d'arrivée est l'université, alors l'université est l'adresse de départ du trajet
                print("OUIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII")
                is_viable = trip_bo.check_if_route_is_viable(point_depart, point_arrivee, point_intermediaire_depart)
                
            else:
                # Sinon, l'université est l'adresse d'arrivée du trajet
                print("CHELOUUUU?????????????")

                if((point_intermediaire_depart != point_universite) or (point_intermediaire_arrivee != point_universite)):
                    # Si l'adresse intermédiaire n'est pas l'université, lever une exception
                    raise Exception("L'adresse intermédiaire ne correspond pas à l'université.")
                is_viable = trip_bo.check_if_route_is_viable(point_depart, (university_latitude, university_longitude),
                                                            point_arrivee)

            if is_viable:
                available_trips.append(trip)
                print("Trip viable", trip_id)

        response = jsonify(available_trips)
        return response, 200

    except ApiException as e:
        response = jsonify({"message": e.message}), 400
        return response