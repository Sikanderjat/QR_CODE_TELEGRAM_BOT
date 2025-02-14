


import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import qrcode
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Welcome! Send me any text, and I will generate a QR code for you.')

def generate_qr(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    bio.name = 'qr_code.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    update.message.reply_photo(photo=bio)

def handle_message(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Please use the /generate command to create a QR code.')

def main() -> None:
    token = os.getenv("bot_api")
    updater = Updater(token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("generate", generate_qr))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
