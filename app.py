import os
import asyncio
import threading
from flask import Flask, request, jsonify
from telethon import TelegramClient, events
from collections import deque

app = Flask(__name__)

# ================= ENV CONFIG =================
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
bot_username = os.environ.get("BOT_USERNAME")

client = TelegramClient("session", api_id, api_hash)

messages = deque(maxlen=100)

# ================= EVENT LOOP =================
loop = asyncio.new_event_loop()

def telegram_worker():
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


# ================= SAFE ASYNC RUNNER =================
def run_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, loop).result()


# ================= API =================

@app.route("/")
def home():
    return "Cloud Telegram API Running"

@app.route("/send", methods=["POST"])
def send():
    try:
        msg = request.json.get("message")

        if not msg:
            return jsonify({"error": "message required"}), 400

        run_async(client.send_message(bot_username, msg))

        return jsonify({"ok": True, "status": "sent"})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/get", methods=["GET"])
def get():
    return jsonify({
        "ok": True,
        "replies": list(messages)
    })


@app.route("/health")
def health():
    return {"status": "ok"}


# ================= START SERVER =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # cloud safe
    app.run(host="0.0.0.0", port=port)
