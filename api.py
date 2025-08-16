# api.py

from flask import Flask, request, jsonify
import yt_dlp
import config

app = Flask(__name__)

@app.route("/api/get", methods=["GET"])
def get_video():
    key = request.args.get("key")
    url = request.args.get("url")

    # Security check
    if key != config.API_SECRET:
        return jsonify({"error": "Invalid API key"}), 403

    if not url:
        return jsonify({"error": "Missing YouTube URL"}), 400

    try:
        ydl_opts = {"format": "bestaudio/best"}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "title": info.get("title"),
                "duration": info.get("duration"),
                "url": info["url"]
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT)
