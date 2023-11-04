"""Email related functions"""
from flask_mail import Message

from uniride_sme import app, mail
from uniride_sme.utils.exception.exceptions import InvalidInputException
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature


def send_email(to, subject, template):
    """Send email"""
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config["MAIL_USERNAME"],
    )
    mail.send(msg)


def generate_token(email):
    """Generate a token for email verification"""
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    return serializer.dumps(email, salt=app.config["SECURITY_PASSWORD_SALT"])


def confirm_token(token, expiration=600):
    """Verify the token for email verification is valid"""
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    try:
        email = serializer.loads(
            token, salt=app.config["SECURITY_PASSWORD_SALT"], max_age=expiration
        )
        return email
    except SignatureExpired as e:
        raise InvalidInputException("LINK_EXPIRED") from e
    except BadTimeSignature as e:
        raise InvalidInputException("LINK_INVALID") from e
