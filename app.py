from flask import Flask, request, jsonify
from telethon import TelegramClient
import asyncio
import time

app = Flask(__name__)

api_id = 39685669
api_hash = "924290ea28ac71b6c0242c8515a09ebf"
bot_username = "tipusultanTg"

client = TelegramClient("session", api_id, api_hash)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


async def get_all_replies(message):
    await client.start()

    # send message
    await client.send_message(bot_username, message)

    # wait for bot to respond
    await asyncio.sleep(2)

    # get last messages from bot
    messages = await client.get_messages(bot_username, limit=10)

    replies = []

    for msg in messages:
        if msg.out == False:   # incoming messages (bot replies)
            replies.append(msg.text)

    return replies[::-1]  # oldest → newest


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        message = data.get("message")

        replies = loop.run_until_complete(get_all_replies(message))

        return jsonify({
            "ok": True,
            "message": message,
            "replies": replies
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/")
def home():
    return "Multi Reply API Running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
