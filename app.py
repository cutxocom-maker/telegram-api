import os
import asyncio
import threading
from collections import deque
from flask import Flask, request, jsonify
from telethon import TelegramClient, events

app = Flask(__name__)

# ================= ENV =================

api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
bot_username = os.environ["BOT_USERNAME"]

client = TelegramClient("session", api_id, api_hash)

# Recent live messages
messages = deque(maxlen=1000)

# ================= TELEGRAM LOOP =================

loop = asyncio.new_event_loop()


def run_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, loop).result()


def telegram_worker():
    asyncio.set_event_loop(loop)

    async def main():
        await client.start()

        print("Telegram connected")

        # Capture messages accessible to your account
        @client.on(events.NewMessage)
        async def handler(event):
            try:
                messages.append({
                    "chat_id": event.chat_id,
                    "sender_id": event.sender_id,
                    "message_id": event.id,
                    "text": event.raw_text
                })
            except Exception as e:
                print(e)

        await client.run_until_disconnected()

    loop.run_until_complete(main())


threading.Thread(target=telegram_worker, daemon=True).start()

# ================= ROUTES =================

@app.route("/")
def home():
    return "Telegram API Running"


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/send", methods=["POST"])
def send():
    try:
        data = request.get_json(force=True)

        msg = data.get("message")

        if not msg:
            return jsonify({
                "ok": False,
                "error": "message required"
            }), 400

        run_async(client.send_message(bot_username, msg))

        return jsonify({
            "ok": True,
            "status": "sent"
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        })


@app.route("/get")
def get_live_messages():
    return jsonify({
        "ok": True,
        "count": len(messages),
        "messages": list(messages)
    })


@app.route("/chats")
def chats():
    try:
        async def get_chats():
            dialogs = await client.get_dialogs()

            result = []

            for d in dialogs:
                result.append({
                    "id": d.id,
                    "name": d.name,
                    "unread_count": d.unread_count
                })

            return result

        data = run_async(get_chats())

        return jsonify({
            "ok": True,
            "count": len(data),
            "chats": data
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        })


@app.route("/messages/<int:chat_id>")
def get_messages(chat_id):
    try:
        async def load_messages():
            result = []

            async for msg in client.iter_messages(chat_id, limit=100):
                result.append({
                    "id": msg.id,
                    "text": msg.raw_text,
                    "date": str(msg.date)
                })

            return result

        data = run_async(load_messages())

        return jsonify({
            "ok": True,
            "count": len(data),
            "messages": data
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        })


# ================= START =================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
