import environ
import os

# Путь к .env
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# TWIN
TWIN_EMAIL = env("TWIN_EMAIL")
TWIN_PASSWORD = env("TWIN_PASSWORD")
TWIN_SCENARIO_ID = env("TWIN_SCENARIO_ID")
TWIN_CALLER_ID = env("TWIN_CALLER_ID")
TWIN_WEBHOOK_URL = env("TWIN_WEBHOOK_URL")

# TELEGRAM
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = env("TELEGRAM_CHAT_ID")