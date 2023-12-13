"""Email related functions"""
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
    file_path = f"{app.config['PATH']}/resource/email/email_verification_template.html"
    if first_mail:
        file_path = f"{app.config['PATH']}/resource/email/email_welcome_template.html"

    with open(
        file_path,
        "r",
        encoding="UTF-8",
    ) as html:
        url = app.config["FRONT_END_URL"] + "email-verification/" + generate_token(student_email)
        send_email(
            student_email,
            "Vérifier votre email",
            html.read().replace("{firstname}", firstname).replace("{link}", url),
        )


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
