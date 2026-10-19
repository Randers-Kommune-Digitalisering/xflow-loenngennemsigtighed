import logging
import os
import requests
from datetime import datetime
from flask import Blueprint, Response, current_app, jsonify, request
from delta_client import DeltaClient
from rkdigi.email_handling import EmailSender
from utils.config import (
    DELTA_AUTH_URL,
    DELTA_CLIENT_ID,
    DELTA_CLIENT_SECRET,
    DELTA_REALM,
    DELTA_URL,
    KRL_API_KEY,
    LOENGENNEMSIGTIGHED_API_URL,
    SMTP_SENDER,
    SMTP_SERVER,
    TEST_CPR,
)

api = Blueprint("api", __name__, url_prefix="/api")
delta_client = DeltaClient(base_url=DELTA_URL, auth_url=DELTA_AUTH_URL, realm=DELTA_REALM, client_id=DELTA_CLIENT_ID, client_secret=DELTA_CLIENT_SECRET)
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
    if current_app.debug and os.getenv("XFLOW_MOCK_PAYLOAD") == "1":
        payload = {
            "cpr": TEST_CPR,
            "dato": "01-09-2026",
        }
    else:
        payload = request.get_json(silent=True) or {}

    user_cpr = payload.get('cpr')
    dato = payload.get('dato')
    if not isinstance(user_cpr, str) or not user_cpr:
        return Response("Invalid payload: 'cpr' must be a string.", status=400)
    if not isinstance(dato, str) or not dato:
        return Response("Invalid payload: 'dato' must be a string.", status=400)

    try:
        parsed_date = datetime.strptime(dato, "%d-%m-%Y")
        if parsed_date.strftime("%d-%m-%Y") != dato:
            raise ValueError("Invalid date format")
    except ValueError:
        return Response("Invalid payload: 'dato' must be DD-MM-YYYY.", status=400)

    current_year = str(parsed_date.year)
    current_month = f"{parsed_date.month:02d}"

    try:
        email_recipients = delta_client.get_email_by_cpr(cpr=user_cpr)
    except (ValueError):
        return Response("Delta email lookup failed.", status=500)

    if not email_recipients:
        return Response("Email not found in Delta", status=404)

    try:
        excel_response = requests.get(
            LOENGENNEMSIGTIGHED_API_URL,
            params={
                "currentYear": current_year,
                "currentMonth": current_month,
                "cpr": user_cpr,
                "apiKey": KRL_API_KEY,
                "excel": "true",
            },
            timeout=30,
        )
        excel_response.raise_for_status()
    except requests.RequestException:
        logger.error("Excel download failed")
        return Response("Excel download failed.", status=502)

    excel_bytes = excel_response.content

    report_month = f"{current_year}-{current_month}"
    filename = f"Loenngennemsigtighed_{report_month}.xlsx"

    EmailSender(smtp_server=SMTP_SERVER).send_email(
        sender=SMTP_SENDER,
        recipients=email_recipients,
        subject=f"Løngennemsigtighed {report_month}",
        body=f"Løngennemsigtighed for {report_month} er vedhæftet.",
        attachments=[(filename, excel_bytes)],
    )

    logger.info(f"Loenngennemsigtighed email sent to {email_recipients}")

    return Response(f"Løngennemsigtighed Excel report successfully sent to {email_recipients}", status=200)
