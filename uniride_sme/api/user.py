"""User related routes"""
from flask import Blueprint, request, jsonify

from models.bo.user_bo import UserBO

user = Blueprint("user", __name__)


@user.route("/user/signup", methods=["POST"])
def sign_up():
    """Sign up route"""
    json_object = request.json
    user_bo = UserBO(
        id=json_object.get("id", None),
        login=json_object.get("login", None),
        firstname=json_object.get("firstname", None),
        lastname=json_object.get("lastname", None),
        student_email=json_object.get("student_email", None),
        password=json_object.get("password", None),
        gender=json_object.get("gender", None),
        phone_number=json_object.get("phone_number", None),
        description=json_object.get("description", None),
    )
    response = user_bo.add_in_db()
    return jsonify({"message": response["message"]}), response["status_code"]
