import os
import asyncio
import threading
from flask import Flask, request, jsonify
from telethon import TelegramClient, events
from collections import deque

app = Flask(__name__)

# ================= CONFIG =================
api_id = 39685669
api_hash = "924290ea28ac71b6c0242c8515a09ebf"
bot_username = "tipusultanTg"

client = TelegramClient("session", api_id, api_hash)

# store last replies
messages = deque(maxlen=100)

# ================= TELEGRAM WORKER =================
def telegram_worker():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def main():
        await client.start()

        @client.on(events.NewMessage(from_users=bot_username))
        async def handler(event):
            messages.append(event.raw_text)

        print("Telegram connected")
        await client.run_until_disconnected()

    loop.run_until_complete(main())

threading.Thread(target=telegram_worker, daemon=True).start()

# ================= API =================

@app.route("/")
def home():
    return "Telegram API Running"

@app.route("/send", methods=["POST"])
def send():
    try:
        data = request.json
        msg = data.get("message")

        if not msg:
            return jsonify({"error": "message required"}), 400

        asyncio.run(client.send_message(bot_username, msg))

        return jsonify({
            "ok": True,
            "status": "sent"
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        })


@app.route("/get", methods=["GET"])
def get():
    return jsonify({
        "ok": True,
        "replies": list(messages)
    })


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}

# ================= START SERVER =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
