import os
import connect_pg
from datetime import datetime

from models.exception.trip_exceptions import (
    InvalidInputException,
    MissingInputException,
)

from dotenv import load_dotenv

import googlemaps


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
    
    def check_if_route_is_viable(self, origin, destination, intermediate_point):
        accept_time_difference_minutes = 10
        """Check if the route is viable"""
    
        now = datetime.now()
        
        load_dotenv()
        google_api_key = os.getenv("GOOGLE_API_KEY")

        # Calculez le trajet initial
        gmaps = googlemaps.Client(key=google_api_key)
        
        # Calcule l'itinéraire initial sans le point intermédiaire
        mode = "driving"
        
        initial_route = gmaps.directions(origin, destination, mode , departure_time=now)

        # Calcule l'itinéraire avec le point intermédiaire
        route_initial_intermediate = gmaps.directions(origin, intermediate_point, mode,  departure_time=now)

        route_with_intermediate = gmaps.directions(intermediate_point, destination, mode,  departure_time=now)
        
        #Vérifie si l'ajout du point intermédiaire augmente la durée de trajet de plus de 10 minutes
        initial_duration = initial_route[0]['legs'][0]['duration']['value']  # Durée en secondes
        intermediate_duration = route_initial_intermediate[0]['legs'][0]['duration']['value']  # Durée en secondes
        intermediate_destination_duration = route_with_intermediate[0]['legs'][0]['duration']['value'] # Durée en secondes
        
        new_duration = intermediate_duration + intermediate_destination_duration

        print("initial_duration", initial_duration)
        print("intermediate_duration", intermediate_duration)
        print("intermediate_destination_duration", intermediate_destination_duration)
        print("new_duration", new_duration)

        time_difference = new_duration - initial_duration  # Différence de temps en secondes
        time_difference_minutes = time_difference / 60  # Différence de temps en minutes

        print("time_difference_minutes", time_difference_minutes)
        if time_difference_minutes <= accept_time_difference_minutes:
            return True
        else:
            return False
    
       
        
    def get_trips(self, departure_or_arrived_latitude, departure__or_arrived_longitude, condition_where):
        """Get the trips from the database"""
        
        query = f"""
            SELECT
                t.t_id AS trip_id,
                t.t_total_passenger_count AS total_passenger_count,
                t.t_timestamp_proposed AS proposed_date,
                t.t_timestamp_creation AS creation_timestamp,
                t.t_status AS trip_status,
                t.t_price AS trip_price,
                t.t_user_id AS user_id,
                t.t_address_depart_id AS departure_address_id,
                t.t_address_arrival_id AS arrival_address_id,
                departure_address.a_latitude AS departure_latitude,
                departure_address.a_longitude AS departure_longitude,
                arrival_address.a_latitude AS arrival_latitude,
                arrival_address.a_longitude AS arrival_longitude
            FROM
                uniride.ur_trip t
            JOIN
                uniride.ur_address departure_address ON t.t_address_depart_id = departure_address.a_id
            JOIN
                uniride.ur_address arrival_address ON t.t_address_arrival_id = arrival_address.a_id
            WHERE
                {condition_where}
                AND t.t_timestamp_proposed BETWEEN 
                (TIMESTAMP %s - INTERVAL '1 hour') 
                AND 
                (TIMESTAMP %s + INTERVAL '1 hour')
                AND t.t_total_passenger_count >= %s;
        """
    
        conn = connect_pg.connect()
        trips = connect_pg.get_query(conn, query, (departure_or_arrived_latitude, departure__or_arrived_longitude, self.timestamp_proposed, self.timestamp_proposed, self.total_passenger_count))
        connect_pg.disconnect(conn)
        
        return trips