import os
import uniride_sme.connect_pg as connect_pg
from datetime import datetime
from decimal import Decimal

from uniride_sme.models.exception.trip_exceptions import (
    InvalidInputException,
    MissingInputException,
)

from uniride_sme.models.dto.trips_get_dto import TripsGetDto
from uniride_sme.models.dto.trip_dto import TripDto
from uniride_sme.models.dto.address_dto import AddressDto
from uniride_sme.utils.trip_status import TripStatus


from dotenv import load_dotenv
import googlemaps

def check_if_route_is_viable(origin, destination, intermediate_point):
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

    time_difference = new_duration - initial_duration  # Différence de temps en secondes
    time_difference_minutes = time_difference / 60  # Différence de temps en minutes

    if time_difference_minutes <= accept_time_difference_minutes:
        intermediate_destination_distance = route_with_intermediate[0]['legs'][0]['distance']['value']  / 1000 
        return [True, new_duration, intermediate_destination_distance]
    else:
        return [False]

class TripBO:
    
    def __init__(
    self ,
    trip_id : int = None ,
    total_passenger_count : int = None,
    timestamp_creation = None ,
    timestamp_proposed = None ,
    status : int = None , #En cours, en attente, annulé, terminé
    price : float = None,
    user_id :int = None,
    address_depart_id :int  = None,
    address_arrival_id :int = None,
    ):
        self.id  = trip_id
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
            self.id = existing_trip_id[0][0]
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
            self.id = trip_id

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

        
    def calculate_price(self, distance, base_rate, total_passenger_count):
        load_dotenv()
    
        rate_per_km = Decimal(os.getenv("RATE_PER_KM"))
        cost_per_km  = Decimal(os.getenv("COST_PER_KM"))
        
         # Calculating the total cost of the trip
        total_cost = (Decimal(distance) * cost_per_km ) + (Decimal(distance) * rate_per_km)
        
        # Calculate the recommended fare to be paid by each passenger
        recommended_price = total_cost / Decimal(total_passenger_count)
        
        # The recommended fare is capped at 1.5 times the base fare
        recommended_price = min(recommended_price, base_rate * Decimal("1.5"))
        
        # Reduce the price by 20%.
        final_price = recommended_price * Decimal("0.8")
        
        # Format price with two decimal places
        formatted_price = '{:.2f}'.format(final_price)  
          
        return formatted_price
   

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
                t.t_initial_price AS t_initial_price,
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
            LEFT JOIN
                uniride.ur_join j ON t.t_id = j.j_trip_id
            WHERE
                {condition_where}
                AND t.t_timestamp_proposed BETWEEN 
                (TIMESTAMP %s - INTERVAL '1 hour') 
                AND 
                (TIMESTAMP %s + INTERVAL '1 hour')
                AND t.t_total_passenger_count >= %s
                AND t.t_status = %s
                ;
        """
    
        conn = connect_pg.connect()
        trips = connect_pg.get_query(conn, query, (departure_or_arrived_latitude, departure__or_arrived_longitude, self.timestamp_proposed, self.timestamp_proposed, self.total_passenger_count, TripStatus.PENDING.value))
        connect_pg.disconnect(conn)
        
        return trips
    
    def get_trips_for_university_address(self, depart_address_bo, address_arrival_bo,university_address_bo):
        
            # Get the intermediate address from the request
            intermediate_departure_latitude = depart_address_bo.latitude
            intermediate_departure_longitude = depart_address_bo.longitude
            intermediate_arrival_latitude = address_arrival_bo.latitude
            intermediate_arrival_longitude = address_arrival_bo.longitude
        
            #We need to round the latitude and longitude to 10 decimal places
            university_latitude = university_address_bo.latitude
            university_longitude = university_address_bo.longitude
                    
            point_universite = (university_latitude, university_longitude)
            
            point_intermediaire_depart = (intermediate_departure_latitude, intermediate_departure_longitude)
            point_intermediaire_arrivee = (intermediate_arrival_latitude, intermediate_arrival_longitude)
            
            if point_intermediaire_depart == point_universite:
                condition_where = "(departure_address.a_latitude = %s AND departure_address.a_longitude = %s)"
                trips = self.get_trips(university_latitude, university_longitude, condition_where)
            elif point_intermediaire_arrivee == point_universite:
                condition_where = "(arrival_address.a_latitude = %s AND arrival_address.a_longitude = %s)"
                trips = self.get_trips(university_latitude, university_longitude, condition_where)
            else:   
                # Si l'adresse intermédiaire n'est pas l'université, lever une exception
                raise Exception("L'adresse intermédiaire ne correspond pas à l'université.")
            
        
            available_trips = []

            for trip in trips:
                trip_id, total_passenger_count, proposed_date, creation_timestamp, trip_status, trip_price, user_id, \
                departure_address_id, arrival_address_id, initial_price, departure_latitude, departure_longitude, arrival_latitude, \
                arrival_longitude = trip

                point_depart = (departure_latitude, departure_longitude)
                point_arrivee = (arrival_latitude, arrival_longitude)
                
                if point_intermediaire_depart == point_universite:
                    # Si le point de départ est l'université, alors l'université est l'adresse d'arrivée du trajet
                    info_route = check_if_route_is_viable(point_depart, point_arrivee, point_intermediaire_depart)
                    is_viable = info_route[0]                
                elif point_intermediaire_arrivee == point_universite:
                    # Si le point d'arrivée est l'université, alors l'université est l'adresse de départ du trajet
                    info_route = check_if_route_is_viable(point_depart, point_arrivee, point_intermediaire_depart)
                    is_viable = info_route[0]
                    
                else:
                    # Sinon, l'université est l'adresse d'arrivée du trajet

                    if((point_intermediaire_depart != point_universite) or (point_intermediaire_arrivee != point_universite)):
                        # Si l'adresse intermédiaire n'est pas l'université, lever une exception
                        raise Exception("L'adresse intermédiaire ne correspond pas à l'université.")
                    info_route = check_if_route_is_viable(point_depart, point_arrivee, point_intermediaire_depart)
                    is_viable = info_route[0]

                if is_viable:
                    price = self.calculate_price(info_route[2], initial_price, total_passenger_count)
                    self.update_trip_price(trip_id, price)
                    formatted_price = '{:.2f}'.format(float(price) * self.total_passenger_count)

                    address_dtos = {
                        "departure": AddressDto(
                            address_id = departure_address_id,
                            latitude = departure_latitude,
                            longitude = departure_longitude,
                            nom_complet = depart_address_bo.concatene_address()
                        ),
                        "arrival": AddressDto(
                            address_id = arrival_address_id,
                            latitude = arrival_latitude,
                            longitude = arrival_longitude,
                            nom_complet = address_arrival_bo.concatene_address()
                        )
                    }
                    trip_dto = TripDto(
                        trip_id=trip_id,
                        address=address_dtos,
                        driver_id = user_id,
                        price = formatted_price,
                    )
                    trips_get_dto = TripsGetDto(
                        trips=trip_dto
                    )
                    available_trips.append(trips_get_dto)

            return available_trips
        
    def update_trip_price(self, trip_id, new_price):
        """Update the price of the trip with the specified ID"""        
        
        conn = connect_pg.connect()
        
        update_query = """
        UPDATE uniride.ur_trip
        SET t_price = %s
        WHERE t_id = %s
        """
        
        connect_pg.execute_command(conn, update_query, (Decimal(new_price), trip_id))
        
        connect_pg.disconnect(conn)