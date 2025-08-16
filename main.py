import os
import re
from typing import Optional, List

import yt_dlp
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Telegram bot (optional; runs only if env set)
from pyrogram import Client, filters

APP_NAME = os.getenv("APP_NAME", "YouTube API Bot")
PORT = int(os.getenv("PORT", "8080"))

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ---------------- yt-dlp helpers ----------------

def _best_audio_info(url: str) -> dict:
    opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "nocheckcertificate": True,
        "ignoreerrors": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        raise ValueError("Failed to fetch info")
    if "entries" in info and isinstance(info["entries"], list):
        info = next((e for e in info["entries"] if e), None)
        if not info:
            raise ValueError("No entries found")
    return info

def _shape_info(info: dict) -> dict:
    thumb = info.get("thumbnail")
    if not thumb and isinstance(info.get("thumbnails"), list) and info["thumbnails"]:
        thumb = info["thumbnails"][-1].get("url")
    return {
        "id": info.get("id"),
        "title": info.get("title"),
        "duration": info.get("duration"),
        "thumbnail": thumb,
        "webpage_url": info.get("webpage_url") or info.get("original_url"),
        "direct_url": info.get("url"),
        "uploader": info.get("uploader"),
        "channel_id": info.get("channel_id"),
        "view_count": info.get("view_count"),
        "live_status": info.get("live_status"),
    }

def fetch_info(url: str) -> dict:
    return _shape_info(_best_audio_info(url))

def search_youtube(query: str, limit: int = 5) -> List[dict]:
    search_url = f"ytsearch{limit}:{query}"
    opts = {"quiet": True, "nocheckcertificate": True, "ignoreerrors": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        result = ydl.extract_info(search_url, download=False)
    entries = result.get("entries", []) if result else []
    out = []
    for e in entries:
        if not e:
            continue
        thumb = e.get("thumbnail")
        if not thumb and e.get("thumbnails"):
            thumb = e["thumbnails"][-1].get("url")
        out.append({
            "id": e.get("id"),
            "title": e.get("title"),
            "duration": e.get("duration"),
            "webpage_url": e.get("webpage_url"),
            "thumbnail": thumb,
        })
    return out

# ---------------- FastAPI app ----------------

app = FastAPI(title=APP_NAME, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InfoResponse(BaseModel):
    id: Optional[str]
    title: Optional[str]
    duration: Optional[int]
    thumbnail: Optional[str]
    webpage_url: Optional[str]
    direct_url: Optional[str]
    uploader: Optional[str] = None
    channel_id: Optional[str] = None
    view_count: Optional[int] = None
    live_status: Optional[str] = None

@app.get("/")
def root():
    return {
        "message": f"✅ {APP_NAME} is running",
        "http_endpoints": ["/api/info?url=...", "/api/search?q=...&limit=5"],
        "telegram_bot": bool(API_ID and API_HASH and BOT_TOKEN),
    }

@app.get("/api/info", response_model=InfoResponse)
async def api_info(url: str = Query(..., description="YouTube video URL")):
    try:
        return fetch_info(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search")
async def api_search(q: str = Query(..., description="Search text"), limit: int = 5):
    try:
        limit = max(1, min(int(limit), 25))
        return {"count": limit, "results": search_youtube(q, limit)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- Telegram Bot (Pyrogram) ----------------

tg_app: Optional[Client] = None
if API_ID and API_HASH and BOT_TOKEN:
    tg_app = Client(
        "yt_api_bot",
        api_id=int(API_ID),
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        workdir="./.tg",
        in_memory=True,
    )

    async def _send_chunked_text(m, text: str, chunk=3500):
        # Telegram text limit ~4096; keep margin
        for i in range(0, len(text), chunk):
            await m.reply_text(text[i:i+chunk])

    @tg_app.on_message(filters.command(["start", "help"]))
    async def _start(_, m):
        await m.reply_text(
            "👋 **YouTube API Bot**\n\n"
            "Commands:\n"
            "• `/getapi <YouTube URL or search text>` — Direct audio link + info\n"
            "• `/search <query>` — Top 5 results\n"
            "• `/ping` — Check status\n\n"
            "HTTP API: `/api/info?url=...`  `/api/search?q=...`"
        )

    @tg_app.on_message(filters.command("ping"))
    async def _ping(_, m):
        await m.reply_text("🏓 Pong!")

    @tg_app.on_message(filters.command("search"))
    async def _search(_, m):
        if len(m.command) < 2:
            return await m.reply_text("Usage: `/search <query>`", quote=True)
        query = " ".join(m.command[1:])
        results = search_youtube(query, limit=5)
        if not results:
            return await m.reply_text("No results found.")
        lines = [f"**{i+1}.** [{r['title']}]({r['webpage_url']})" for i, r in enumerate(results)]
        await _send_chunked_text(m, "\n".join(lines))

    @tg_app.on_message(filters.command("getapi"))
    async def _getapi(_, m):
        if len(m.command) < 2:
            return await m.reply_text("Usage: `/getapi <YouTube URL or search text>`")
        arg = " ".join(m.command[1:])
        is_url = bool(re.match(r"^https?://", arg))
        try:
            url = arg
            if not is_url:
                results = search_youtube(arg, limit=1)
                if not results:
                    return await m.reply_text("No results found.")
                url = results[0]["webpage_url"]
            data = fetch_info(url)
            # Keep caption very small; send details as text to avoid MEDIA_CAPTION_TOO_LONG
            small_caption = "🎵 Stream info"
            text = (
                f"**Title:** {data.get('title')}\n"
                f"**Duration:** {data.get('duration')} sec\n"
                f"**Direct Link:** {data.get('direct_url')}\n"
                f"**Watch:** {data.get('webpage_url')}"
            )
            thumb = data.get("thumbnail")
            if thumb:
                await m.reply_photo(thumb, caption=small_caption)
                await _send_chunked_text(m, text)
            else:
                await _send_chunked_text(m, text)
        except Exception as e:
            await m.reply_text(f"❌ Error: {e}")

# FastAPI lifecycle hooks to manage bot
@app.on_event("startup")
async def on_startup():
    if tg_app:
        await tg_app.start()

@app.on_event("shutdown")
async def on_shutdown():
    if tg_app:
        try:
            await tg_app.stop()
        except Exception:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
