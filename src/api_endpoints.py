import logging
import os
import requests
from datetime import datetime
from flask import Blueprint, Response, current_app, jsonify, request
from rkdigi.email_handling import EmailSender
from utils.api_requests import APIClient
from utils.config import (
    KRL_API_KEY,
    LOENGENNEMSIGTIGHED_API_URL,
    SMTP_SENDER,
    SMTP_SERVER,
    TEST_CPR,
    TEST_EMAIL,
)

api = Blueprint("api", __name__, url_prefix="/api")
report_client = APIClient(base_url=LOENGENNEMSIGTIGHED_API_URL)
logger = logging.getLogger(__name__)


@api.route("/xflow", methods=["POST"])
def get_xflow_data() -> Response:
    if current_app.debug and os.getenv("XFLOW_MOCK_PAYLOAD") == "1":
        payload = {
            "cpr": TEST_CPR,
            "dato": "01-09-2026",
            "email": TEST_EMAIL,
        }
        logger.info("Using mock payload")
    else:
        payload = request.get_json(silent=True) or {}

    user_cpr = payload.get('cpr')
    dato = payload.get('dato')
    email_recipients = payload.get('email')
    # if not isinstance(user_cpr, str) or not user_cpr:
    if not user_cpr:
        logger.error("Invalid 'cpr' in payload")
        return Response("Invalid payload: 'cpr' must be a string.", status=400)
    if not isinstance(dato, str) or not dato:
        logger.error("Invalid 'dato' in payload")
        return Response("Invalid payload: 'dato' must be a string.", status=400)
    if not isinstance(email_recipients, str) or not email_recipients.strip():
        logger.error("Invalid 'email' in payload")
        return Response("Invalid payload: 'email' must be a string.", status=400)

    try:
        parsed_date = datetime.strptime(dato, "%d-%m-%Y")
        if parsed_date.strftime("%d-%m-%Y") != dato:
            raise ValueError("Invalid date format")
    except ValueError:
        return Response("Invalid payload: 'dato' must be DD-MM-YYYY.", status=400)

    current_year = str(parsed_date.year)
    current_month = f"{parsed_date.month:02d}"
    logger.info(f"Parsed date: {current_year}-{current_month} from input dato: {dato}")

    # try:
    #     excel_bytes = report_client.make_request(
    #         params={
    #             "currentYear": current_year,
    #             "currentMonth": current_month,
    #             "cpr": user_cpr,
    #             "apiKey": KRL_API_KEY,
    #             "excel": "true",
    #         },
    #         timeout=30,
    #     )
    # except requests.RequestException:
    #     logger.error("Excel download failed")
    #     return Response("Excel download failed.", status=502)

    # if not isinstance(excel_bytes, bytes):
    #     logger.error("Excel download returned an unexpected response type")
    #     return Response("Excel download failed.", status=502)

    report_month = f"{current_year}-{current_month}"
    # filename = f"Loenngennemsigtighed_{report_month}.xlsx"

    EmailSender(smtp_server=SMTP_SERVER).send_email(
        sender=SMTP_SENDER,
        recipients=email_recipients,
        subject=f"Løngennemsigtighed {report_month}",
        body=f"Løngennemsigtighed for {report_month} er vedhæftet.\n Læs mere omkring løngennemsigtighed her: https://www.krl.dk/",
        attachments=[],
        # attachments=[(filename, excel_bytes)],
    )

    logger.info(f"Løngennemsigtighed email sent for report month: {report_month} to {email_recipients}")

    return Response("Løngennemsigtighed Excel report successfully sent", status=200)
