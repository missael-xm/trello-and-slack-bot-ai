# src/utils/config.py
import os

# OpenAI
model_name = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
openai_api_key_env = os.environ.get("OPENAI_API_KEY")
base_temperature = 0.3

# Slack
slack_app_bot_key = os.environ.get("SLACK_APP_BOT_KEY")
slack_app_user_key = os.environ.get("SLACK_APP_USER_KEY")
slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
slack_bot_channel = os.environ.get("SLACK_BOT_CHANNEL")
slack_bot_channel_id = os.environ.get("SLACK_BOT_CHANNEL_ID")

# Trello
trello_api_key = os.environ.get("TRELLO_API_KEY")
trello_api_token = os.environ.get("TRELLO_API_TOKEN")
trello_api_url = "https://api.trello.com"

# MongoDB
mongodb_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")