import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import google.generativeai as genai

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- ЛОГИ ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- GEMINI ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# --- КОМАНДА /start ---
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Salom! 👋\n\n"
        "Menga dori nomini yoki rasmini yuboring.\n"
        "Men sizga u haqida ma'lumot beraman."
    )

# --- ОБРАБОТКА ТЕКСТА ---
def handle_text(update: Update, context: CallbackContext):
    user_text = update.message.text

    prompt = f"""
    Sen farmatsevt yordamchisan.
    Foydalanuvchiga dorilar haqida tushunarli va xavfsiz ma'lumot ber.

    Dori: {user_text}

    Qisqa qilib tushuntir:
    - Nima uchun ishlatiladi
    - Qanday ichiladi
    - Muhim ogohlantirishlar

    Hech qachon aniq davolash buyurma.
    """

    try:
        response = model.generate_content(prompt)
        update.message.reply_text(response.text)
    except Exception as e:
        update.message.reply_text("Xatolik yuz berdi. Keyinroq urinib ko‘ring.")

# --- ОБРАБОТКА ФОТО ---
def handle_photo(update: Update, context: CallbackContext):
    update.message.reply_text(
        "📷 Rasm qabul qilindi!\n\n"
        "Hozircha faqat dori nomini yozib yuboring.\n"
        "Keyingi versiyada rasm orqali aniqlash qo‘shiladi."
    )

# --- ЗАПУСК ---
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
