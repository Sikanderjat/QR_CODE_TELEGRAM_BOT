import os
from threading import Thread

import qrcode as qr
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from telegram.utils.request import Request

import hmac
import hashlib
from flask import Flask, request, jsonify


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

# Set these as environment variables on Render (preferred)
EXPECTED_SECRET = os.environ.get("OTHER_BOT_SECRET", "himynameisikander")  # REPLACE_ME or set env var
USE_HMAC = os.environ.get("USE_HMAC", "0") == "1"  # set to "1" on Render to enable HMAC verify

def verify_hmac(raw_body: bytes, header_signature: str, secret: str) -> bool:
    # header expected: "sha256=<hex>"
    if not header_signature or not header_signature.startswith("sha256="):
        return False
    sig_hex = header_signature.split("=", 1)[1]
    computed = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig_hex, computed)

@app.route("/receive_link", methods=["POST"])
def receive_link():
    raw = request.get_data() or b""
    header = request.headers.get("X-Webhook-Secret", "")

    # verify either HMAC or plain header match
    if USE_HMAC and EXPECTED_SECRET:
        if not verify_hmac(raw, header, EXPECTED_SECRET):
            return jsonify({"error":"invalid signature"}), 403
    else:
        if header != (EXPECTED_SECRET or ""):
            return jsonify({"error":"invalid secret"}), 403

    # parse JSON body
    data = request.get_json(force=True, silent=True) or {}
    url = data.get("url")
    caption = data.get("caption", "")
    fetched_at = data.get("fetched_at", "")

    # quick sanity check
    if not url:
        return jsonify({"error":"missing url"}), 400

    # For now just log and acknowledge (expand this to generate QR or forward to Telegram)
    print("RECEIVED LINK:", url, "caption:", caption, "fetched_at:", fetched_at)

    # TODO: generate QR / forward to telegram here
    return jsonify({"ok": True, "received_url": url}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


# --------------- RUN SERVER ---------------

if __name__ == "__main__":
    # Render will pass PORT env var; fallback for local run
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

