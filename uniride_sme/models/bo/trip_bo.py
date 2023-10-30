import os
import connect_pg


class TripBO:
    
    def __init__(
    self ,
    trip_id ,
    total_passenger_count,
    date_proposed,
    creation  ,
    occurrence  ,
    status ,
    price ,
    q_id ,
    u_id ,
    a_id  ,
    a_id_1  
    ):
        self.rip_id  = rip_id,
        self.total_passenger_count = total_passenger_count,
        self.date_proposed =date_proposed ,
        self.creation  = creation,
        self.occurrence  = occurrence,
        self.status  = status,
        self.price =price,
        self.q_id = q_id,
        self.u_id = u_id,
        self.a_id  = a_id,
        self.a_id_1 = a_id_1 