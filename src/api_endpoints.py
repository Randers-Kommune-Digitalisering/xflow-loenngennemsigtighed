"""
API endpoints for the Flask application.
"""
import logging
from flask import Blueprint, Response, jsonify

api = Blueprint("api", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)


@api.route("/example", methods=["GET"])
def example() -> tuple[Response, int]:
    """
    Return a simple JSON response. Only allows GET requests.
    """
    logger.info("Example endpoint was called.")
    return jsonify({"status": "ok"}), 200
