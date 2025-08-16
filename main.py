import os
import secrets
from flask import Flask, request, jsonify
from telegram.ext import Updater, CommandHandler

# Flask app
app = Flask(__name__)

# Generate API Key once (stable until restart / deployment)
API_KEY = os.getenv("API_KEY") or secrets.token_hex(16)

@app.route("/api/stream", methods=["GET"])
def stream():
    key = request.args.get("key")
    url = request.args.get("url")
    if key != API_KEY:
        return jsonify({"error": "Invalid API Key"}), 403
    # Yaha yt-dlp se stream URL nikalne ka code hoga
    return jsonify({"stream_url": f"processed:{url}"})


# Telegram Bot part
BOT_TOKEN = os.getenv("BOT_TOKEN")

def start(update, context):
    update.message.reply_text("👋 Welcome! Use /getapi to receive your API details.")

def getapi(update, context):
    base_url = request.host_url.strip("/") if request else "https://your-northflank-domain.app"
    update.message.reply_text(
        f"✅ API Ready!\n\nBase URL: {base_url}/api\nAPI Key: {API_KEY}"
    )

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("getapi", getapi))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    import threading
    t = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080))))
    t.start()
    main()
