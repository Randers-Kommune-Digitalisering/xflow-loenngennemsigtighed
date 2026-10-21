import logging
import os
import requests
from datetime import datetime
from flask import Blueprint, Response, current_app, request
from utils.excel_report import filter_monthly_paid_sheets
from rkdigi.email_handling import EmailSender
from utils.api_requests import APIClient
from utils.config import (
    KRL_API_KEY,
    KRL_API_URL,
    SMTP_SENDER,
    SMTP_SERVER,
    TEST_CPR,
    TEST_EMAIL,
    SMTP_PORT,
    SMTP_PASSWORD,
    REPLY_TO_EMAIL
)

api = Blueprint("api", __name__, url_prefix="/api")
krl_client = APIClient(base_url=KRL_API_URL)
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

    user_cpr = payload.get('cpr')  # The CPR number of the user from MITID xflow
    dato = payload.get('dato')  # The date for which the report is requested
    email_recipients = payload.get('email')  # The email address to send the report to
    if not isinstance(user_cpr, str) or not user_cpr:
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

    try:
        excel_bytes = krl_client.make_request(
            params={
                "currentYear": current_year,
                "currentMonth": current_month,
                "cpr": user_cpr,
                "apiKey": KRL_API_KEY,
                "excel": "true",
            },
            timeout=30,
        )
    except requests.RequestException:
        logger.error("Excel download failed")
        return Response("Excel download failed.", status=400)

    if not isinstance(excel_bytes, bytes):
        logger.error("Excel download returned an unexpected response type")
        return Response("Excel download failed.", status=400)

    try:
        monthly_report = filter_monthly_paid_sheets(excel_bytes)
    except (ValueError) as exc:
        logger.error(f"Excel report is invalid or missing employee numbers ({exc})")
        return Response("Excel report could not be processed.", status=400)

    report_month = f"{current_year}-{current_month}"
    if monthly_report is None:
        body = (
            "Løngennemsigtighed er ikke egnet til timelønnede medarbejdere.\n"
            "Den er kun beregnet til månedslønnede."
        )
        attachments = []
    else:
        body = (
            f"Løngennemsigtighed for {report_month} er vedhæftet.\n"
            "Læs mere omkring løngennemsigtighed her: https://www.krl.dk/"
        )
        attachments = [(f"Loenngennemsigtighed_{report_month}.xlsx", monthly_report)]

    EmailSender(smtp_server=SMTP_SERVER, smtp_port=SMTP_PORT, sender_email=SMTP_SENDER, sender_password=SMTP_PASSWORD, reply_to_email=REPLY_TO_EMAIL).send_email(
        recipients=email_recipients,
        subject=f"Løngennemsigtighed {report_month}",
        body=body,
        attachments=attachments,
    )

    logger.info(f"Løngennemsigtighed email sent for report month: {report_month}")

    return Response("Løngennemsigtighed Excel report successfully sent", status=200)
