import os
from dotenv import load_dotenv

load_dotenv()

SITE_URL = os.environ.get("SITE_URL")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
DEBUG = os.environ.get("DEBUG", False)
API_TOKEN = os.environ.get("API_TOKEN")
RUN_TESTNET_BOT = os.environ.get("RUN_TESTNET_BOT", True)
ENVIRONMENT = os.environ.get("ENVIRONMENT")
