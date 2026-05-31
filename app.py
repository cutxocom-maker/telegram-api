from flask import Flask, request, jsonify
from telethon import TelegramClient, events
import asyncio
import os
from collections import deque

app = Flask(__name__)

# ---------------- CONFIG ----------------
api_id = 39685669
api_hash = "924290ea28ac71b6c0242c8515a09ebf"
bot_username = "tipusultanTg"

client = TelegramClient("session", api_id, api_hash)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# store last messages safely (queue)
messages = deque(maxlen=50)


# ---------------- TELEGRAM EVENT LISTENER ----------------
@client.on(events.NewMessage(from_users=bot_username))
async def handler(event):
    messages.append(event.message.text)


async def start_telegram():
    await client.start()
    print("Telegram client started")


loop.run_until_complete(start_telegram())


# ---------------- API: SEND ----------------
@app.route("/send", methods=["POST"])
def send():
    try:
        data = request.json
        msg = data.get("message")

        if not msg:
            return jsonify({"error": "message required"}), 400

        loop.run_until_complete(client.send_message(bot_username, msg))

        return jsonify({
            "ok": True,
            "status": "sent"
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ---------------- API: GET MESSAGES ----------------
@app.route("/get", methods=["GET"])
def get():
    return jsonify({
        "ok": True,
        "replies": list(messages)
    })


# ---------------- HEALTH CHECK ----------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running"})


# ---------------- START SERVER ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
