import os
from threading import Thread

import qrcode as qr
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from telegram.utils.request import Request

# --------------- CONFIG ---------------

# Use env var for security; or replace with a hardcoded string if you really want
BOT_TOKEN = os.environ.get("API_KEY")

if not BOT_TOKEN:
    raise SystemExit("❌ API_KEY env var missing (Telegram bot token).")

# Telegram bot with timeout settings
req = Request(connect_timeout=10, read_timeout=30)
bot = Bot(token=BOT_TOKEN, request=req)

# Flask app for webhook
app = Flask(__name__)

# Dispatcher handles updates (workers = number of threads)
dispatcher = Dispatcher(bot, None, workers=4, use_context=True)


# --------------- HANDLERS ---------------

def start(update: Update, context):
    update.message.reply_text("Please send your text. I’ll generate a QR code from it!")


def help_command(update: Update, context):
    update.message.reply_text("Just send me any text, and I’ll convert it into a QR code.")

def about_command(update: Update, context):
    update.message.reply_text("This is a simple QR code generator bot made by SIKANDER." \
    "More features looding soon")


def handle_text(update: Update, context):
    user_text = update.message.text.strip()
    if not user_text:
        update.message.reply_text("Send some text, not empty message.")
        return

    # Generate QR
    qr_code = qr.make(user_text)
    file_path = "qrcode.png"
    qr_code.save(file_path)

    with open(file_path, "rb") as photo:
        bot.send_photo(chat_id=update.effective_chat.id, photo=photo)


# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(CommandHandler("about", about_command))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))


# --------------- FLASK WEBHOOK ENDPOINTS ---------------

@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    """Telegram sends updates here."""
    update = Update.de_json(request.get_json(force=True), bot)

    # Process the update in a separate thread to respond to Telegram quickly
    Thread(target=dispatcher.process_update, args=(update,)).start()

    return "OK", 200


@app.route("/", methods=["GET"])
def home():
    return "✅ QR Code Bot (Webhook Active)"


# --------------- RUN SERVER ---------------

if __name__ == "__main__":
    # Render will pass PORT env var; fallback for local run
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
