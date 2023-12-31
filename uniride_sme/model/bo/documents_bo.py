"""User business owner"""
from datetime import datetime
import dataclasses


@dataclasses.dataclass
class DocumentsBO:  # pylint: disable=too-many-instance-attributes
    """Documents business owner class"""

    def __init__(  # pylint: disable=too-many-arguments, too-many-locals
        self,
        u_id: int,
        d_id: int,
        d_license: str,
        d_id_card: str,
        d_school_certificate: str,
        d_insurance: str,
        d_timestamp_addition: datetime,
        d_timestamp_modification: datetime,
        v_id: int,
        v_license_verified: bool,
        v_id_card_verified: bool,
        v_school_certificate_verified: bool,
        v_timestamp_modification: datetime,
    ):
        self.u_id = u_id
        self.d_id = d_id
        self.d_license = d_license
        self.d_id_card = d_id_card
        self.d_insurance = d_insurance
        self.d_school_certificate = d_school_certificate
        self.d_timestamp_addition = d_timestamp_addition
        self.d_timestamp_modification = d_timestamp_modification

        self.v_id = v_id
        self.v_license_verified = v_license_verified
        self.v_id_card_verified = v_id_card_verified
        self.v_school_certificate_verified = v_school_certificate_verified
        self.v_timestamp_modification = v_timestamp_modification
