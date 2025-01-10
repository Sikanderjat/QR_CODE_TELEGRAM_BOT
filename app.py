import qrcode as qr
from telegram import Update
from telegram.ext import Updater, Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import os
from flask import Flask, request
import requests

logging.basicConfig(level=logging.INFO)

bot_api = "7681906379:AAGsM-gpLxdt0AKUtjXHrcZ6yeJ6fC4rPnc"

# Flask App setup
app = Flask(__name__)

def qr_code_generator(text):
    try:
        qr_code = qr.make(text)
        qr_code.save("qrcode.png")
        return "qrcode.png"
    except Exception as e:
        logging.error(f"Error generating QR code: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please Send Your Text. It generates QR codes from text.")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("This is a simple QR code generator bot Generated by SIKANDER.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send your text, and the bot will generate a QR code.")

async def handel_text(update: Update, context=ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    qr_code_file = qr_code_generator(user_text)
    if qr_code_file:
        with open(qr_code_file, "rb") as photo:
            await update.message.reply_photo(photo)
    else:
        await update.message.reply_text("Error generating QR code")

# Set up the webhook route
@app.route('/' + bot_api, methods=['POST'])
def webhook():
    json_str = request.get_data(as_text=True)
    update = Update.de_json(json_str, application.bot)
    application.process_update(update)
    return 'OK', 200

# Initialize the bot with the webhook handler
application = Application.builder().token(bot_api).build()

# Register command handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("about", about))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handel_text))

if __name__ == "__main__":
    # Start the Flask app (Vercel needs this to run)
    application.updater = None  # disable polling
    app.run(debug=True)
