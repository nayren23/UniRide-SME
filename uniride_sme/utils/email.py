"""Email related functions"""
import os
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature

from uniride_sme import app, mail, rq
from uniride_sme.utils.exception.exceptions import InvalidInputException
from uniride_sme.utils.decorator import with_app_context


@rq.job
@with_app_context
def send_email(to, subject, template):
    """Send email"""
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config["MAIL_USERNAME"],
    )
    mail.send(msg)
    print("Email sent")


def send_verification_email(student_email, firstname, first_mail=False):
    """Send verification email"""
    if first_mail:
        file_path = os.path.join(app.config["PATH"], "resource/email/email_welcome_template.html")
    else:
        file_path = os.path.join(app.config["PATH"], "resource/email/email_verification_template.html")

    url = app.config["FRONT_END_URL"] + "email-verification/" + generate_token(student_email)
    with open(file_path, "r", encoding="UTF-8") as html:
        content = html.read().replace("{firstname}", firstname).replace("{url}", url)
    send_email(student_email, "Vérifier votre adresse e-mail", content)


def send_reservation_response_email(student_email, firstname, trip_id):
    """Send reservation response email"""
    print("path : " + app.config["PATH"])
    file_path = os.path.join(app.config["PATH"], "resource/email/email_reservation_response_template.html")
    print("file path : " + file_path)
    url = f"{app.config['FRONT_END_URL']}trip-info/{trip_id}"
    with open(file_path, "r", encoding="UTF-8") as html:
        content = html.read().replace("{firstname}", firstname).replace("{url}", url)
    send_email(student_email, "Votre demande de réservation a reçu une réponse", content)


def generate_token(email):
    """Generate a token for email verification"""
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    return serializer.dumps(email, salt=app.config["SECURITY_PASSWORD_SALT"])


def confirm_token(token):
    """Verify the token for email verification is valid"""
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    try:
        email = serializer.loads(
            token, salt=app.config["SECURITY_PASSWORD_SALT"], max_age=app.config["MAIL_EXPIRATION"]
        )
        return email
    except SignatureExpired as e:
        raise InvalidInputException("LINK_EXPIRED") from e
    except BadTimeSignature as e:
        raise InvalidInputException("LINK_INVALID") from e
