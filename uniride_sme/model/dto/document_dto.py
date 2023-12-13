"""DTO for Car BO"""

from typing import TypedDict


class DocumentVerificationDTO(TypedDict):
    """DocumentVerificationDTO (Data Transfer Object)"""
    id_user: int
    request_number: int
    documents_to_verify:int
    full_name:str
    profile_picture: str
    last_modified_date: str