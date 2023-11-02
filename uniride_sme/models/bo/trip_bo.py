import os
import connect_pg
from datetime import datetime

from models.exception.trip_exceptions import (
    InvalidInputException,
    MissingInputException,
)
import requests

#from googlemaps import DirectionsService


class TripBO:
    
    def __init__(
    self ,
    trip_id = None ,
    total_passenger_count = None,
    timestamp_creation = None ,
    timestamp_proposed = None ,
    status = None , #En cours, en attente, annulé, terminé
    price = None,
    daily_id = None,
    user_id = None,
    address_depart_id  = None,
    address_arrival_id = None,
    ):
        self.trip_id  = trip_id
        self.total_passenger_count = total_passenger_count
        self.timestamp_creation  = timestamp_creation
        self.timestamp_proposed  = timestamp_proposed
        self.status  = status 
        self.price =price
        self.user_id = user_id
        self.address_depart_id  = address_depart_id
        self.address_arrival_id = address_arrival_id 
    
    def add_in_db(self):
        """Insert the trip in the database"""
        
        existing_trip_id = self.trip_exists()

        # Check if the address already exists
        if existing_trip_id :
            self.trip_id = existing_trip_id[0][0]
        else:
                        
            # validate values
            self.validate_total_passenger_count()
            self.validate_timestamp_proposed()
            self.validate_status()
            self.validate_price()
            self.validate_user_id()
            self.validate_address_depart_id()
            self.validate_address_arrival_id()
            self.validate_address_depart_id_equals_address_arrival_id() #i need this function to check if the trip is viable

            # retrieve not None values
            attr_dict = {}
            for attr, value in self.__dict__.items():
                if value:
                    attr_dict["t_" + attr] = value
            
            # format for sql query
            fields = ", ".join(attr_dict.keys())
            
            placeholders = ", ".join(["%s"] * len(attr_dict))
            values = tuple(attr_dict.values())

            query = f"INSERT INTO uniride.ur_trip ({fields}) VALUES ({placeholders}) RETURNING t_id"
            #changer le nom de la table dans la BDD
            
            conn = connect_pg.connect()
            trip_id = connect_pg.execute_command(conn, query, values)
            self.trip_id = trip_id

    def validate_total_passenger_count(self):
        if self.total_passenger_count is None:
            raise MissingInputException("total_passenger_count cannot be null")
        if self.total_passenger_count < 0:
            raise InvalidInputException("total_passenger_count cannot be negative")
        if self.total_passenger_count > 10: #change with the number of seats in the car DB
            raise InvalidInputException("total_passenger_count cannot be greater than 10")

    def validate_timestamp_proposed(self):
        return isinstance(self.timestamp_proposed, datetime)
        
    def validate_status(self):
        if self.status is None:
            raise MissingInputException("status cannot be null")
        if self.status < 0:
            raise InvalidInputException("status cannot be negative")
        
    def validate_price(self):
        if self.price is None:
            raise MissingInputException("price cannot be null")
        if self.price < 0:
            raise InvalidInputException("price cannot be negative")
        
    def validate_daily_id(self):
        if self.daily_id is None:
            raise MissingInputException("daily_id cannot be null")
        if self.daily_id < 0:
            raise InvalidInputException("daily_id cannot be negative")
        
    def validate_user_id(self):
        if self.user_id is None:
            raise MissingInputException("user_id cannot be null")
        if self.user_id < 0:
            raise InvalidInputException("user_id cannot be negative")

    def validate_address_depart_id(self):
        if self.address_depart_id is None:
            raise MissingInputException("address_depart_id cannot be null")
        if self.address_depart_id < 0:
            raise InvalidInputException("address_depart_id cannot be negative")
        
    def validate_address_arrival_id(self):
        if self.address_arrival_id is None:
            raise MissingInputException("address_arrival_id cannot be null")
        if self.address_arrival_id < 0:
            raise InvalidInputException("address_arrival_id cannot be negative")
        
    def validate_address_depart_id_equals_address_arrival_id(self):
        if self.address_depart_id == self.address_arrival_id:
            raise InvalidInputException("address_depart_id is equal to address_arrival_id")

        
    def calculate_price(self):
        #TODO
        return 0

    def trip_exists(self):
        """Check if the address already exists in the database"""

        query = """
        SELECT t_id
        FROM uniride.ur_trip
        WHERE  t_address_depart_id = %s AND t_address_arrival_id = %s AND t_timestamp_proposed = %s AND t_total_passenger_count = %s
        """
    
        conn = connect_pg.connect()
        trip_id = connect_pg.get_query(conn, query, (self.address_depart_id, self.address_arrival_id, self.timestamp_proposed, self.total_passenger_count))
        connect_pg.disconnect(conn)
        
        return trip_id
    
    def check_if_route_is_viable(self, departure_latitude, departure_longitude, arrival_latitude,  arrival_longitude, intermediate_point_latitude, intermediate_point_longitude):
        # Calculez le trajet initial
        directions_service = DirectionsService(key="YOUR_API_KEY")
        directions_result = directions_service.directions(
            departure_latitude, departure_longitude, arrival_latitude, arrival_longitude
        )

        # Calculez le trajet modifié
        directions_result_modified = directions_service.directions(
            departure_latitude, departure_longitude, arrival_latitude, arrival_longitude, waypoints=[
                intermediate_point_latitude, intermediate_point_longitude
            ]
        )

        # Comparez la durée des deux trajets
        original_duration = directions_result["routes"][0]["legs"][0]["duration"]["value"]
        modified_duration = directions_result_modified["routes"][0]["legs"][0]["duration"]["value"]
        
        # Obtenez le temps de trajet du trajet modifié
        modified_duration = directions_result_modified["routes"][0]["legs"][0]["duration"]["value"]

        # Obtenez la distance du trajet modifié
        modified_distance = directions_result_modified["routes"][0]["legs"][0]["distance"]["value"]

        # Vérifiez que le trajet modifié ne rajoute pas plus de 10 minutes supplémentaires
        if modified_duration <= original_duration + 600:
            print("Le trajet passe par l'endroit où vous vous trouvez et ne rajoute pas plus de 10 minutes supplémentaires.")
            return True
        else:
            print("Le trajet ne passe pas par l'endroit où vous vous trouvez ou rajoute plus de 10 minutes supplémentaires.")
            return False