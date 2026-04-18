#!/usr/bin/env python3
"""
💊 DORI HAQIDA BOT
Google Gemini AI bilan ishlaydi — bepul!
Dori nomi yoki rasmini yuboring — to'liq ma'lumot oling.
"""

import os
import logging
import base64
import httpx
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ─── SOZLAMALAR ───────────────────────────────
BOT_TOKEN   = os.getenv("BOT_TOKEN", "")
GEMINI_KEY  = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL  = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)
# ──────────────────────────────────────────────

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)


# ─── KLAVIATURA ───────────────────────────────
MENU = ReplyKeyboardMarkup(
    [
        [KeyboardButton("💊 To'liq ma'lumot")],
        [KeyboardButton("📋 Qisqacha"),        KeyboardButton("⚠️ Nojo'ya ta'sirlar")],
        [KeyboardButton("💰 Narxi"),            KeyboardButton("🕐 Qabul vaqti")],
        [KeyboardButton("ℹ️ Yordam"),           KeyboardButton("🏠 Bosh menu")],
    ],
    resize_keyboard=True,
)


# ─── GEMINI API ───────────────────────────────

SYSTEM = (
    "Siz o'zbek tilidagi dori vositalar bo'yicha mutaxassississiz. "
    "Foydalanuvchilar asosan qariyalar. Shuning uchun:\n"
    "- Oddiy va tushunarli til ishlating\n"
    "- Qisqa, aniq jumlalar yozing\n"
    "- Muhim joylarni emoji bilan belgilang\n"
    "- FAQAT o'zbek tilida javob bering\n"
    "- Oxirida doim: '⚕️ Doktoringiz bilan maslahatlashing!' deb yozing"
)

async def ask_gemini(prompt: str, image_b64: str = None) -> str:
    parts = []

    if image_b64:
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": image_b64,
            }
        })

    parts.append({"text": SYSTEM + "\n\n" + prompt})

    body = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1500,
        }
    }

    url = f"{GEMINI_URL}?key={GEMINI_KEY}"

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, json=body)
        r.raise_for_status()
        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


# ─── PROMPTS ──────────────────────────────────

def p_full(dori):
    return f"""
"{dori}" dori haqida to'liq ma'lumot bering:

💊 DORI NOMI: (rasmiy nomi)
📌 NIMA UCHUN: (qanday kasalliklarda ishlatiladi)
📏 DOZASI: (kattalar va qariyalar uchun)
🕐 QACHON ICHILADI: (ovqatdan oldin/keyin/bilan)
⚠️ EHTIYOT BO'LING: (kimlar ichmasligi kerak)
❌ NOJO'YA TA'SIRLAR: (eng ko'p uchraydigan 3-4 ta)
🚫 QARSHI KO'RSATMALAR: (qanday holatlarda mumkin emas)
💡 MASLAHAT: (muhim eslatma)
"""

def p_short(dori):
    return f'"{dori}" dorini qisqacha tushuntiring. Faqat 5-6 qator. Oddiy tilda.'

def p_side(dori):
    return f'"{dori}" dorining nojo\'ya ta\'sirlari ro\'yxatini bering. Qachon darhol doktorga borish kerakligini ham ayting.'

def p_price(dori):
    return f'"{dori}" dorining O\'zbekistondagi taxminiy narxi va arzonroq muqobil doriylarini ayting.'

def p_schedule(dori):
    return f'"{dori}" dorini qanday ichish kerak: kuniga necha marta, qaysi vaqtda, ovqatdan oldin yoki keyin. Jadval ko\'rinishida yozing.'

def p_photo():
    return (
        "Bu rasmda qanday dori ko'rinayapti? "
        "Dori nomi, nima uchun ishlatilishi, "
        "asosiy ma'lumotlar va ehtiyot choralarini ayting. "
        "Agar nomi ko'rinmasa, rasmdan taxmin qiling."
    )


# ─── HANDLERS ────────────────────────────────

async def cmd_start(u: Update, _):
    name = u.effective_user.first_name
    await u.message.reply_html(
        f"👋 Salom, <b>{name}</b>!\n\n"
        "💊 <b>DORI HAQIDA BOT</b>\n\n"
        "Bu bot har qanday dori haqida\n"
        "to'liq ma'lumot beradi.\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✏️ <b>Dori nomini yozing</b>\n"
        "   Misol: <i>Paracetamol</i>\n\n"
        "📸 <b>Yoki rasmini yuboring</b>\n"
        "   (quticha yoki blister rasmi)\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "👇 Keyin tugma bosing:",
        reply_markup=MENU,
    )


async def cmd_help(u: Update, _):
    await u.message.reply_html(
        "ℹ️ <b>QANDAY ISHLATILADI?</b>\n\n"
        "1️⃣ Dori nomini yozing\n"
        "   Misol: <i>Analgin, Ibuprofen</i>\n\n"
        "2️⃣ Yoki dori rasmini yuboring\n\n"
        "3️⃣ Tugma bosing:\n\n"
        "💊 <b>To'liq ma'lumot</b>\n"
        "   Hamma narsa batafsil\n\n"
        "📋 <b>Qisqacha</b>\n"
        "   5-6 qatorda asosiy narsa\n\n"
        "⚠️ <b>Nojo'ya ta'sirlar</b>\n"
        "   Yon ta'sirlar ro'yxati\n\n"
        "💰 <b>Narxi</b>\n"
        "   Narx va arzon muqobillari\n\n"
        "🕐 <b>Qabul vaqti</b>\n"
        "   Qachon, qancha ichish\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "⚕️ Bu bot ma'lumot beradi.\n"
        "Davolanish uchun doktorga boring!",
        reply_markup=MENU,
    )


async def handle_photo(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    wait = await u.message.reply_text("🔍 Rasm o'qilmoqda... Kuting...")
    try:
        photo = u.message.photo[-1]
        file  = await photo.get_file()
        data  = await file.download_as_bytearray()
        b64   = base64.b64encode(data).decode()

        answer = await ask_gemini(p_photo(), image_b64=b64)
        await wait.delete()
        await u.message.reply_html(
            f"📸 <b>RASM TAHLILI</b>\n\n{answer}",
            reply_markup=MENU,
        )
        ctx.user_data["last_dori"] = "rasmdan topilgan dori"

    except Exception as e:
        log.exception(e)
        await wait.edit_text("❌ Rasm o'qishda xatolik. Qayta yuboring.")


async def handle_text(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (u.message.text or "").strip()

    # Menu tugmalari
    if text in ("🏠 Bosh menu", "/start"):
        return await cmd_start(u, ctx)
    if text in ("ℹ️ Yordam", "/help"):
        return await cmd_help(u, ctx)

    dori = ctx.user_data.get("last_dori")

    buttons = {
        "💊 To'liq ma'lumot":    ("full",     "💊 To'liq ma'lumot tayyorlanmoqda..."),
        "📋 Qisqacha":           ("short",    "📋 Qisqacha ma'lumot tayyorlanmoqda..."),
        "⚠️ Nojo'ya ta'sirlar":  ("side",     "⚠️ Nojo'ya ta'sirlar tekshirilmoqda..."),
        "💰 Narxi":              ("price",    "💰 Narx ma'lumotlari izlanmoqda..."),
        "🕐 Qabul vaqti":        ("schedule", "🕐 Qabul jadvali tayyorlanmoqda..."),
    }

    if text in buttons:
        if not dori:
            await u.message.reply_text(
                "✏️ Avval dori nomini yozing!\n\nMisol: Paracetamol",
                reply_markup=MENU,
            )
            return
        mode, wait_text = buttons[text]
        await send_info(u, dori, mode, wait_text)
        return

    # Yangi dori nomi
    ctx.user_data["last_dori"] = text
    await u.message.reply_html(
        f"✅ <b>{text}</b> tanlandi!\n\n"
        "👇 Qanday ma'lumot kerak?",
        reply_markup=MENU,
    )


async def send_info(u: Update, dori: str, mode: str, wait_text: str):
    wait = await u.message.reply_text(f"⏳ {wait_text}")
    try:
        prompt_fn = {
            "full":     p_full,
            "short":    p_short,
            "side":     p_side,
            "price":    p_price,
            "schedule": p_schedule,
        }[mode]

        answer = await ask_gemini(prompt_fn(dori))
        await wait.delete()
        await u.message.reply_html(
            f"💊 <b>{dori.upper()}</b>\n\n{answer}",
            reply_markup=MENU,
        )
    except httpx.HTTPStatusError as e:
        log.error(f"Gemini API xato: {e.response.text}")
        await wait.edit_text("❌ AI xizmat vaqtincha ishlamaydi. Qayta urinib ko'ring.")
    except Exception as e:
        log.exception(e)
        await wait.edit_text("❌ Xatolik yuz berdi. Qayta urinib ko'ring.")


# ─── MAIN ────────────────────────────────────

def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN yo'q!")
        return
    if not GEMINI_KEY:
        print("❌ GEMINI_API_KEY yo'q!")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(MessageHandler(filters.PHOTO,                    handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,  handle_text))

    print("🚀 Dori haqida Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
