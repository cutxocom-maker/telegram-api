import os
import asyncio
import threading
from flask import Flask, request, jsonify
from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetHistoryRequest
from collections import deque

app = Flask(__name__)

# ================= ENV VARIABLES =================
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")

# Example: "@telegram" or "@durov" or any channel you want
channel_username = os.environ.get("CHANNEL_USERNAME", "@telegram")

client = TelegramClient("session", api_id, api_hash)
messages = deque(maxlen=100)

# ================= EVENT LOOP =================
loop = asyncio.new_event_loop()

def start_telegram():
    asyncio.set_event_loop(loop)

    async def main():
        await client.start()

        # ✅ Listen to NEW messages from the channel (live)
        @client.on(events.NewMessage(chats=channel_username))
        async def handler(event):
            messages.append({
                "id": event.id,
                "text": event.raw_text,
                "date": str(event.date)
            })
            print(f"New message: {event.raw_text}")

        print(f"Listening to channel: {channel_username}")
        await client.run_until_disconnected()

    loop.run_until_complete(main())

threading.Thread(target=start_telegram, daemon=True).start()

# ================= SAFE RUN =================
def run_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, loop).result()

# ================= API =================
@app.route("/")
def home():
    return "Telegram Channel Reader Running"

# ✅ Get live messages (collected since server started)
@app.route("/get")
def get():
    return jsonify({
        "ok": True,
        "channel": channel_username,
        "replies": list(messages)
    })

# ✅ NEW: Fetch last N messages from channel history
@app.route("/history")
def history():
    try:
        limit = int(request.args.get("limit", 10))  # ?limit=20

        async def fetch():
            channel = await client.get_entity(channel_username)
            result = await client(GetHistoryRequest(
                peer=channel,
                limit=limit,
                offset_date=None,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0
            ))
            msgs = []
            for m in result.messages:
                msgs.append({
                    "id": m.id,
                    "text": m.message or "",
                    "date": str(m.date)
                })
            return msgs

        data = run_async(fetch())
        return jsonify({"ok": True, "messages": data})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ✅ NEW: Search messages in channel
@app.route("/search")
def search():
    try:
        query = request.args.get("q", "")
        limit = int(request.args.get("limit", 10))

        async def fetch():
            results = await client.get_messages(
                channel_username,
                search=query,
                limit=limit
            )
            return [{"id": m.id, "text": m.message, "date": str(m.date)} for m in results]

        data = run_async(fetch())
        return jsonify({"ok": True, "query": query, "messages": data})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/health")
def health():
    return {"status": "ok"}

# ================= START =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
