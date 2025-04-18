import qrcode as qr
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask, request
import os

app = Flask(__name__)
TELEGRAM_TOKEN = os.getenv("API_KEY")

# Initialize the bot application
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please Send Your Text. It generates QR codes from text.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Simply send your text, and I'll create a QR code for you!")

async def handel_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    qr_code = qr.make(user_text)
    qr_code.save("qrcode.png")
    with open("qrcode.png", "rb") as photo:
        await update.message.reply_photo(photo)

# Add handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("help", help_command))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handel_text))

# Flask route to handle Telegram webhook
@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), bot_app.bot)
    bot_app.update_queue.put(update)
    return "OK", 200
