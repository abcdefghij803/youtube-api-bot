# main.py

from pyrogram import Client, filters
from pyrogram.types import Message
import config

app = Client(
    "YouTubeAPI_Bot",
    bot_token=config.BOT_TOKEN,
    api_id=12345,   # my.telegram.org se API_ID
    api_hash="your_api_hash"
)

# Command: Start
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "👋 **Welcome to YouTube API Bot!**\n\n"
        "👉 Sirf Owner `/getapi` se API le sakta hai.\n"
        "🎵 Deploy karke Music Bot ke liye use karo!"
    )

# Command: Get API (Owner-only)
@app.on_message(filters.command("getapi"))
async def getapi(client, message: Message):
    if message.from_user.id != config.OWNER_ID:
        return await message.reply_text("❌ You are not authorized to use this command!")

    base_url = f"https://{message.from_user.username}.northflank.app/api"
    api_key = config.API_SECRET

    text = (
        "✅ **Your Self-Hosted API Details** ✅\n\n"
        f"🌍 Base URL: `{base_url}`\n"
        f"🔑 API Key: `{api_key}`\n\n"
        "⚡ Paste this into your Music Bot repo to play unlimited music 🎶"
    )

    await message.reply_text(text)

if __name__ == "__main__":
    app.run()
