import qrcode as qr
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os

# Load token from environment variable
TELEGRAM_TOKEN = os.environ.get("API_KEY")

# Initialize the bot application
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please send your text. I’ll generate a QR code from it!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Just send me any text, and I’ll convert it into a QR code.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    qr_code = qr.make(user_text)
    qr_code.save("qrcode.png")
    with open("qrcode.png", "rb") as photo:
        await update.message.reply_photo(photo)

# Add handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("help", help_command))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

# Start the bot with polling
if __name__ == "__main__":
    bot_app.run_polling()
