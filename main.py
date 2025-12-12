import os
import hmac
import hashlib
import tempfile
import qrcode as qr
from threading import Thread
from flask import Flask, request, jsonify

from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from telegram.utils.request import Request

# --------------- CONFIG ---------------
BOT_TOKEN = os.environ.get("API_KEY")
if not BOT_TOKEN:
    raise SystemExit("❌ API_KEY env var missing (Telegram bot token).")

RECEIVER_TARGET_CHAT_ID = os.environ.get("RECEIVER_TARGET_CHAT_ID")  # where to forward generated QR
EXPECTED_SECRET = os.environ.get("OTHER_BOT_SECRET", "himynameisikander")
USE_HMAC = os.environ.get("USE_HMAC", "0") == "1"

# Telegram bot with timeout settings
req = Request(connect_timeout=10, read_timeout=30)
bot = Bot(token=BOT_TOKEN, request=req)

# Flask
app = Flask(__name__)

# Dispatcher for Telegram-updates (webhook)
dispatcher = Dispatcher(bot, None, workers=4, use_context=True)


# --------------- TELEGRAM HANDLERS ---------------
def start(update, context):
    update.message.reply_text("Please send your text. I’ll generate a QR code from it!")

def help_command(update, context):
    update.message.reply_text("Send any text and I'll return a QR code image.")

def about_command(update, context):
    update.message.reply_text("Simple QR code generator bot.")

def handle_text(update, context):
    user_text = update.message.text.strip()
    if not user_text:
        update.message.reply_text("Send some text, not empty message.")
        return
    # Generate QR and send back to the user
    img = qr.make(user_text)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
        img.save(tf.name)
        tf.flush()
        with open(tf.name, "rb") as photo:
            bot.send_photo(chat_id=update.effective_chat.id, photo=photo)

# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(CommandHandler("about", about_command))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))


# --------------- HMAC / SECRET VERIFY ---------------
def verify_hmac(raw_body: bytes, header_signature: str, secret: str) -> bool:
    if not header_signature or not header_signature.startswith("sha256="):
        return False
    sig_hex = header_signature.split("=", 1)[1]
    computed = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig_hex, computed)


# --------------- RECEIVER ENDPOINT ---------------
@app.route("/receive_link", methods=["POST"])
def receive_link():
    raw = request.get_data() or b""
    header = request.headers.get("X-Webhook-Secret", "")

    # verify signature
    if USE_HMAC and EXPECTED_SECRET:
        if not verify_hmac(raw, header, EXPECTED_SECRET):
            return jsonify({"error": "invalid signature"}), 403
    else:
        if header != (EXPECTED_SECRET or ""):
            return jsonify({"error": "invalid secret"}), 403

    data = request.get_json(force=True, silent=True) or {}
    url = data.get("url")
    caption = data.get("caption", "")

    if not url:
        return jsonify({"error": "missing url"}), 400

    # create a QR image (the payload we will send to telegram)
    try:
        img = qr.make(url)
        # save to a temp file and send
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            img.save(tf.name)
            tf.flush()
            # If RECEIVER_TARGET_CHAT_ID is set, forward there. Otherwise return file as bytes in response (for testing)
            if RECEIVER_TARGET_CHAT_ID:
                try:
                    with open(tf.name, "rb") as photo:
                        bot.send_photo(chat_id=RECEIVER_TARGET_CHAT_ID, photo=photo, caption=caption or None)
                except Exception as e:
                    app.logger.exception("Failed to send photo to Telegram")
                    return jsonify({"error": "telegram send failed", "detail": str(e)}), 500
            else:
                # no chat configured: return success but include base message (good for testing)
                app.logger.info("No RECEIVER_TARGET_CHAT_ID set; generated QR but did not forward.")
    except Exception as e:
        app.logger.exception("QR generation failed")
        return jsonify({"error": "qr_generation_failed", "detail": str(e)}), 500

    app.logger.info("Received and processed URL: %s", url)
    return jsonify({"ok": True, "received_url": url}), 200


# --------------- TELEGRAM WEBHOOK ENDPOINT ---------------
@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    # process async
    Thread(target=dispatcher.process_update, args=(update,)).start()
    return "OK", 200


@app.route("/", methods=["GET"])
def home():
    return "✅ QR Code Bot (Webhook Active)"


# --------------- RUN ---------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
