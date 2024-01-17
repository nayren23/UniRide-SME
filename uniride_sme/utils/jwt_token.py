"""JWT token utilities"""
from datetime import datetime
from flask_jwt_extended import get_jwt
from uniride_sme import cache, jwt


@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload: dict):  # pylint: disable=unused-argument
    """Check if token is revoked"""
    jti = jwt_payload["jti"]
    token_in_redis = cache.get(jti)
    return token_in_redis is not None


def revoke_token():
    """Revoke token"""
    token = get_jwt()
    expiration_datetime = datetime.utcfromtimestamp(token["exp"])
    current_time = datetime.utcnow()
    time_remaining = expiration_datetime - current_time
    timeout = int(time_remaining.total_seconds()) + 1
    cache.set(token["jti"], "", timeout=timeout)
