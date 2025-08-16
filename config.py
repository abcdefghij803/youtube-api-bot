# config.py

import os

# Telegram Bot Token (BotFather se lo)
BOT_TOKEN = os.getenv("BOT_TOKEN", "your-telegram-bot-token")

# Owner ka Telegram user ID (sirf wahi /getapi use kar payega)
OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))

# API secret key (extra security for API requests)
API_SECRET = os.getenv("API_SECRET", "super-secret-key")

# Flask server port
PORT = int(os.getenv("PORT", 8080))
