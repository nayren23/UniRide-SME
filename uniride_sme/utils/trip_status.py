from enum import Enum

class TripStatus(Enum):
        PENDING = 1  # En attente
        CANCELED = 2  # Annulé
        COMPLETED = 3  # Terminé
        ONCOURSE = 4  # En cours
        
