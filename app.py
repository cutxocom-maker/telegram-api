from flask import Flask, request, jsonify
from telethon import TelegramClient, events
import asyncio
import os
import threading
from collections import deque

app = Flask(__name__)

api_id = 39685669
api_hash = "924290ea28ac71b6c0242c8515a09ebf"
bot_username = "tipusultanTg"

client = TelegramClient("session", api_id, api_hash)

messages = deque(maxlen=100)


# ---------------- TELEGRAM BACKGROUND LOOP ----------------
def start_telegram():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def main():
        await client.start()

        @client.on(events.NewMessage(from_users=bot_username))
        async def handler(event):
            messages.append(event.message.text)

        print("Telegram listener started")
        await client.run_until_disconnected()

    loop.run_until_complete(main())


threading.Thread(target=start_telegram, daemon=True).start()


# ---------------- SEND MESSAGE (FAST, NO BLOCK) ----------------
@app.route("/send", methods=["POST"])
def send():
    try:
        data = request.json
        msg = data.get("message")

        if not msg:
            return jsonify({"error": "message required"}), 400

        asyncio.run(client.send_message(bot_username, msg))

        return jsonify({"ok": True, "status": "sent"})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ---------------- GET RESPONSES (FAST) ----------------
@app.route("/get", methods=["GET"])
def get():
    return jsonify({
        "ok": True,
        "replies": list(messages)
    })


# ---------------- HEALTH CHECK ----------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})


# ---------------- START SERVER ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
