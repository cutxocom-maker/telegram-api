from flask import Flask, request, jsonify
from telethon import TelegramClient, events
import asyncio
import os
import threading
from collections import deque

app = Flask(__name__)

api_id = 39685669
api_hash = "e2d1fa04-8308-4e38-bed4-68f99a618d21"
bot_username = "tipusultanTg"

client = TelegramClient("session", api_id, api_hash)

messages = deque(maxlen=100)


# ---------------- TELEGRAM LOOP ----------------
async def telegram_main():
    await client.start()

    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
        messages.append(event.raw_text)

    print("Telegram connected")
    await client.run_until_disconnected()


def start_telegram():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_main())


# START TELEGRAM BEFORE FLASK
threading.Thread(target=start_telegram, daemon=True).start()


# ---------------- API ----------------
@app.route("/send", methods=["POST"])
def send():
    try:
        data = request.json
        msg = data.get("message")

        if not msg:
            return jsonify({"error": "message required"}), 400

        asyncio.run(client.send_message(bot_username, msg))

        return jsonify({"ok": True})

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/get", methods=["GET"])
def get():
    return jsonify({
        "ok": True,
        "replies": list(messages)
    })


@app.route("/health")
def health():
    return "OK"


# ---------------- START SERVER ----------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        use_reloader=False
    )
