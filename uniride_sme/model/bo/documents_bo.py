"""User business owner"""
from datetime import datetime
import dataclasses


@dataclasses.dataclass
class DocumentsBO:  # pylint: disable=too-many-instance-attributes
    """Documents business owner class"""

    u_id: int
    d_id: int
    d_license: str
    d_id_card: str
    d_school_certificate: str
    d_insurance: str
    d_timestamp_addition: datetime
    d_timestamp_modification: datetime
    v_id: int
    v_license_verified: bool
    v_id_card_verified: bool
    v_insurance_verified: bool
    v_school_certificate_verified: bool
    v_timestamp_modification: datetime
    v_license_description: str
    v_card_description: str
    v_insurance_description: str
    v_school_certificate_description: str
