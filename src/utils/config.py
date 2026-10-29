"""Load application configuration from environment variables."""

import os
from dotenv import load_dotenv


# loads .env file, will not overide already set enviroment variables (will do nothing when testing, building and deploying)
load_dotenv()


DEBUG = os.getenv("DEBUG", "False") in ["True", "true"]
PORT = os.getenv("PORT", "8080")
POD_NAME = os.getenv("POD_NAME", "pod_name_not_set")

TEST_CPR = os.getenv("TEST_CPR", "").strip()
TEST_EMAIL = os.getenv("TEST_EMAIL", "").strip()
KRL_API_URL = os.getenv("KRL_API_URL", "").strip()
KRL_API_KEY = os.getenv("KRL_API_KEY", "").strip()
SMTP_SERVER = os.getenv("SMTP_SERVER", "").strip()
SMTP_SENDER = os.getenv("SMTP_SENDER", "").strip()
SMTP_PORT = 587
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
REPLY_TO_EMAIL = os.getenv("REPLY_TO_EMAIL", "").strip()
