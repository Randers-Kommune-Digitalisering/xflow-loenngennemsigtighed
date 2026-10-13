"""
API endpoints for the Flask application.
"""
import base64
import binascii
import logging

from flask import Blueprint, Response, jsonify, request

api = Blueprint("api", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)


@api.route("/example", methods=["GET"])
def example() -> tuple[Response, int]:
    """
    Return a simple JSON response. Only allows GET requests.
    """
    logger.info("Example endpoint was called.")
    return jsonify({"status": "ok"}), 200


@api.route("/xflow", methods=["POST"])
def get_xflow_data() -> Response:
    payload = request.get_json(silent=True) or {}

    user = payload.get("user")
    data = payload.get("data")
    if not user or not data:
        return Response("Invalid payload: 'user' and 'data' fields are required.", status=400)
    if not isinstance(user, str):
        return Response("Invalid payload: 'user' must be a string.", status=400)
    if not isinstance(data, str):
        return Response("Invalid payload: 'data' must be a base64-encoded string.", status=400)

    user_dq = user.split(" - ")[-1].strip()
    if not user_dq.lower().startswith(("dq", "ap", "aa")):
        return Response("Invalid payload: 'user' must contain a DQ, AP or AA identifier.", status=400)
    logger.info(f"Processing Xflow request for user: {user_dq}")

    try:
        pdf_bytes = base64.b64decode(data.strip(), validate=True)
    except (binascii.Error, ValueError):
        logger.warning("Invalid base64 PDF data received")
        return Response("Invalid PDF data: expected base64-encoded PDF.", status=400)

    if not pdf_bytes.startswith(b"%PDF"):
        logger.warning("Base64 decoded data is not a PDF")
        return Response("Invalid PDF data.", status=400)

    logger.info(f"Successfully validated PDF for user: {user_dq}")

    return jsonify({"status": "ok"})
