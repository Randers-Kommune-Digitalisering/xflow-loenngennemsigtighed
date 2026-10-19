import os
from dotenv import load_dotenv


# loads .env file, will not overide already set enviroment variables (will do nothing when testing, building and deploying)
load_dotenv()


DEBUG = os.getenv('DEBUG', 'False') in ['True', 'true']
PORT = os.getenv('PORT', '8080')
POD_NAME = os.getenv('POD_NAME', 'pod_name_not_set')

TEST_CPR = os.getenv('TEST_CPR', '').strip()
LOENGENNEMSIGTIGHED_API_URL = os.getenv('LOENGENNEMSIGTIGHED_API_URL', '').strip()
KRL_API_KEY = os.getenv('KRL_API_KEY', '').strip()
SMTP_SERVER = os.getenv('SMTP_SERVER', '').strip()
SMTP_SENDER = os.getenv('SMTP_SENDER', '').strip()

DELTA_URL = os.getenv('DELTA_URL', '').strip()
DELTA_CLIENT_ID = os.getenv('DELTA_CLIENT_ID', '').strip()
DELTA_CLIENT_SECRET = os.getenv('DELTA_CLIENT_SECRET', '').strip()
DELTA_REALM = '730'
DELTA_AUTH_URL = "https://idp.opus-universe.kmd.dk"
