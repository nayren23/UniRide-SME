"""DTO for Car BO"""

from typing import TypedDict


class DocumentVerificationDTO(TypedDict):
    """DocumentVerificationDTO (Data Transfer Object)"""

    id_user: int
    request_number: int
    documents_to_verify: int
    full_name: str
    profile_picture: str
    last_modified_date: str

class UserDocumentsInfosDTO(TypedDict):
    """UserDocumentsDTO (Data Transfer Object)"""
    
    id_user: int
    license: str
    id_card: str
    school_certificate: str
    insurance: str
    license_verified: bool
    id_card_verified: bool
    insurance_verified: bool
    school_certificate_verified: bool
    id_card_description: str
    license_description: str
    insurance_description: str
    school_certificate_description: str

    