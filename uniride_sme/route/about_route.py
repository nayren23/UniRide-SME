"""About route module."""

from flask import Blueprint, jsonify
from uniride_sme.utils.exception.exceptions import ApiException
from uniride_sme.utils import about as about_utils

about = Blueprint("about", __name__, url_prefix="/about")


@about.route("/conditions", methods=["GET"])
def get_conditions():
    """Get conditions of use"""
    try:
        conditions = about_utils.get_conditions()
        response = jsonify(conditions=conditions), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response


@about.route("/privacy", methods=["GET"])
def get_privacy():
    """Get privacy policy"""
    try:
        privacy = about_utils.get_privacy()
        response = jsonify(privacy=privacy), 200
    except ApiException as e:
        response = jsonify(message=e.message), e.status_code
    return response
