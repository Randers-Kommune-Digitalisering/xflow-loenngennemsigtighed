import logging
import os
from datetime import datetime, timezone
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile
from zoneinfo import ZoneInfo

import requests
from flask import Blueprint, Response, current_app, request
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
from utils.excel_report import filter_monthly_paid_sheets

api = Blueprint("api", __name__, url_prefix="/api")
krl_client = APIClient(base_url=KRL_API_URL)
logger = logging.getLogger(__name__)

MONTH_NAMES = (
    "januar", "februar", "marts", "april", "maj", "juni",
    "juli", "august", "september", "oktober", "november", "december",
)


def _send_email(
    recipients: str,
    subject: str,
    body: str,
    attachments: list[tuple[str, bytes]],
) -> None:
    """
    Send an email with optional report attachments.

    :param recipients: Email address of the recipient.
    :param subject: Subject line of the email.
    :param body: Message text.
    :param attachments: Filename and file content for each attachment.
    :return: None.
    """
    EmailSender(smtp_server=SMTP_SERVER, smtp_port=SMTP_PORT, sender_email=SMTP_SENDER, sender_password=SMTP_PASSWORD, reply_to_email=REPLY_TO_EMAIL).send_email(
        recipients=recipients,
        subject=subject,
        body=body,
        attachments=attachments,
    )


@api.route("/xflow", methods=["POST"])
def get_xflow_data() -> Response:
    if current_app.debug and os.getenv("XFLOW_MOCK_PAYLOAD") == "1":
        payload = {
            "cpr": TEST_CPR,
            "dato": "01-10-2026",
            "email": TEST_EMAIL,
        }
        logger.info("Using mock payload")
    else:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return Response("Invalid payload: expected a JSON object.", status=400)

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

    today = datetime.now(timezone.utc).astimezone(ZoneInfo("Europe/Copenhagen"))
    if (parsed_date.year, parsed_date.month) >= (today.year, today.month):
        previous_year = today.year if today.month > 1 else today.year - 1
        previous_month = today.month - 1 if today.month > 1 else 12
        selected = f"{MONTH_NAMES[parsed_date.month - 1]} {parsed_date.year}"
        suggested = f"{MONTH_NAMES[previous_month - 1]} {previous_year}"
        body = (
            "Vælg en måned, hvor data er tilgængelige. "
            f"Hvis du den {today.day}. {MONTH_NAMES[today.month - 1]} "
            f"{today.year} vælger {selected}, kan udtrækket endnu ikke dannes, "
            "fordi data for måneden ikke er klar. "
            f"Vælg i stedet den foregående måned, {suggested}."
        )
        _send_email(
            recipients=email_recipients,
            subject="Løngennemsigtighed - Vælg en anden måned",
            body=body,
            attachments=[],
        )
        logger.info("Guidance email sent for unavailable KRL report month")
        return Response("Guidance email sent for unavailable KRL month.", status=200)

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
    except (BadZipFile, KeyError, ParseError, ValueError):
        logger.error("Excel report is invalid or missing employee numbers")
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

    _send_email(
        recipients=email_recipients,
        subject=f"Løngennemsigtighed {report_month}",
        body=body,
        attachments=attachments,
    )

    logger.info(f"Løngennemsigtighed email sent for report month: {report_month}")

    return Response("Løngennemsigtighed Excel report successfully sent", status=200)
