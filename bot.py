#!/usr/bin/env python3
"""
💊 DORI HAQIDA BOT
Dori nomi yoki rasmini yuboring — to'liq ma'lumot oling.
Qariyalar uchun oddiy va qulay interfeys.
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
BOT_TOKEN     = os.getenv("BOT_TOKEN", "")
CLAUDE_API    = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL  = "claude-opus-4-5"
# ──────────────────────────────────────────────

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

# ─── KLAVIATURA ───────────────────────────────
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("💊 Dori haqida ma'lumot")],
        [KeyboardButton("📋 Qisqacha ma'lumot"), KeyboardButton("⚠️ Nojo'ya ta'sirlar")],
        [KeyboardButton("💰 Narxi va muqobillari"), KeyboardButton("🕐 Qabul qilish vaqti")],
        [KeyboardButton("ℹ️ Yordam"), KeyboardButton("🏠 Bosh menu")],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)

# ─── CLAUDE API ───────────────────────────────

async def ask_claude(prompt: str, image_b64: str = None, image_mime: str = "image/jpeg") -> str:
    headers = {
        "x-api-key": CLAUDE_API,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    if image_b64:
        content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image_mime,
                    "data": image_b64,
                },
            },
            {"type": "text", "text": prompt},
        ]
    else:
        content = [{"type": "text", "text": prompt}]

    body = {
        "model": CLAUDE_MODEL,
        "max_tokens": 1500,
        "system": (
            "Siz o'zbek tilidagi dori vositalar bo'yicha mutaxassississiz. "
            "Foydalanuvchilar asosan qariyalar bo'lgani uchun:\n"
            "- Oddiy va tushunarli til ishlating\n"
            "- Qisqa, aniq jumlalar yozing\n"
            "- Muhim ma'lumotlarni ✅ ❌ ⚠️ emoji bilan belgilang\n"
            "- Har doim oxirida: 'Doktoringiz bilan maslahatlashing' deb yozing\n"
            "- Faqat o'zbek tilida javob bering"
        ),
        "messages": [{"role": "user", "content": content}],
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
        return data["content"][0]["text"]


# ─── PROMPTS ──────────────────────────────────

def prompt_full(dori: str) -> str:
    return f"""
"{dori}" dori haqida quyidagi ma'lumotlarni bering:

💊 **DORI NOMI:** (to'liq nomi)
📌 **NIMA UCHUN ISHLATILADI:** (asosiy maqsad, 2-3 jumla)
📏 **QANCHA MIQDORDA:** (odatiy doza, yoshlar va qariyalar uchun)
🕐 **QACHON ICHILADI:** (ovqatdan oldin/keyin/bilan)
⚠️ **EHTIYOT BO'LING:** (asosiy cheklovlar)
❌ **NOJO'YA TA'SIRLAR:** (eng ko'p uchraydigan 3-4 ta)
🚫 **KIM ICHMAYDI:** (qarshi ko'rsatmalar)
💡 **MUHIM ESLATMA:** (qisqa maslahat)

Oxirida: ⚕️ Doktoringiz bilan albatta maslahatlashing!
"""

def prompt_short(dori: str) -> str:
    return f"""
"{dori}" dori haqida QISQACHA (5-6 qator) ma'lumot bering:
- Nima uchun ishlatiladi
- Qanday ichiladi
- Asosiy ogohlantirish
Oddiy, tushunarli tilda yozing.
"""

def prompt_side_effects(dori: str) -> str:
    return f"""
"{dori}" dorining nojo'ya ta'sirlari haqida batafsil yozing.
Eng ko'p uchraydiganlarini ro'yxat qiling.
Qachon darhol doktorga borish kerakligini ham ayting.
"""

def prompt_price(dori: str) -> str:
    return f"""
"{dori}" dori haqida:
- O'zbekistondagi taxminiy narxi
- Muqobil (analog) dorilar nomi
- Arzonroq muqobillari bormi?
Taxminiy ma'lumot ekanini eslatib qo'ying.
"""

def prompt_schedule(dori: str) -> str:
    return f"""
"{dori}" dorini qabul qilish jadvali haqida yozing:
- Kuniga necha marta
- Qaysi vaqtda (ertalab/kechqurun)
- Ovqatdan oldin yoki keyin
- Qancha kun ichish kerak (odatda)
Jadval ko'rinishida yozing.
"""

def prompt_photo() -> str:
    return """
Bu rasmda ko'ringan dori haqida quyidagini ayting:
1. Dori nomi (agar ko'rinsa)
2. Nima uchun ishlatiladi
3. Asosiy ma'lumotlar
4. Ehtiyot bo'lish kerak bo'lgan holatlar

Agar dori nomi ko'rinmasa — rasmdan taxmin qiling.
"""


# ─── HANDLERS ────────────────────────────────

async def cmd_start(u: Update, _):
    await u.message.reply_html(
        "👋 Salom!\n\n"
        "💊 <b>DORI HAQIDA BOT</b>\n\n"
        "Bu bot sizga har qanday dori haqida\n"
        "to'liq ma'lumot beradi.\n\n"
        "📸 <b>Rasmini yuboring</b>\n"
        "✏️ <b>Yoki nomini yozing</b>\n\n"
        "👇 Quyidagi tugmalardan foydalaning:",
        reply_markup=MAIN_KEYBOARD,
    )


async def cmd_help(u: Update, _):
    await u.message.reply_html(
        "ℹ️ <b>QANDAY ISHLATILADI?</b>\n\n"
        "1️⃣ Dori nomini yozing\n"
        "   Misol: <i>Paracetamol</i>\n\n"
        "2️⃣ Yoki dorining rasmini yuboring\n"
        "   (quticha, blister, shisha rasmi)\n\n"
        "3️⃣ Keyin tugma tanlang:\n"
        "   💊 To'liq ma'lumot\n"
        "   📋 Qisqacha\n"
        "   ⚠️ Nojo'ya ta'sirlar\n"
        "   💰 Narxi\n"
        "   🕐 Qabul vaqti\n\n"
        "⚕️ <b>Eslatma:</b> Bu bot ma'lumot beradi,\n"
        "davolanish uchun doktorga boring!",
        reply_markup=MAIN_KEYBOARD,
    )


async def handle_text(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = u.message.text.strip()

    # Menu tugmalari
    if text in ("🏠 Bosh menu", "/start"):
        await cmd_start(u, ctx)
        return
    if text in ("ℹ️ Yordam", "/help"):
        await cmd_help(u, ctx)
        return

    # Tugma bosildi — oldingi dori nomini tekshiramiz
    dori = ctx.user_data.get("last_dori")

    button_map = {
        "💊 Dori haqida ma'lumot": ("full",    "💊 To'liq ma'lumot tayyorlanmoqda..."),
        "📋 Qisqacha ma'lumot":    ("short",   "📋 Qisqacha ma'lumot tayyorlanmoqda..."),
        "⚠️ Nojo'ya ta'sirlar":    ("side",    "⚠️ Nojo'ya ta'sirlar tekshirilmoqda..."),
        "💰 Narxi va muqobillari": ("price",   "💰 Narx ma'lumotlari izlanmoqda..."),
        "🕐 Qabul qilish vaqti":   ("schedule","🕐 Qabul jadvali tayyorlanmoqda..."),
    }

    if text in button_map:
        if not dori:
            await u.message.reply_text(
                "✏️ Avval dori nomini yozing!\nMisol: Paracetamol",
                reply_markup=MAIN_KEYBOARD,
            )
            return
        mode, wait_text = button_map[text]
        await send_dori_info(u, dori, mode, wait_text)
        return

    # Yangi dori nomi kiritildi
    ctx.user_data["last_dori"] = text
    await u.message.reply_html(
        f"✅ <b>{text}</b> dori tanlandi!\n\n"
        "👇 Qanday ma'lumot kerak?",
        reply_markup=MAIN_KEYBOARD,
    )


async def handle_photo(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    wait = await u.message.reply_text("🔍 Rasm tahlil qilinmoqda... Kuting...")

    try:
        photo = u.message.photo[-1]
        file = await photo.get_file()
        data = await file.download_as_bytearray()
        b64 = base64.b64encode(data).decode()

        answer = await ask_claude(prompt_photo(), image_b64=b64)
        await wait.delete()
        await u.message.reply_html(
            f"📸 <b>RASM TAHLILI</b>\n\n{answer}",
            reply_markup=MAIN_KEYBOARD,
        )

        # Agar rasm matnida dori nomi topilsa — saqlash
        ctx.user_data["last_dori"] = "rasmdan topilgan dori"

    except Exception as e:
        log.exception(e)
        await wait.edit_text("❌ Rasm o'qishda xatolik. Qayta yuboring.")


async def send_dori_info(u: Update, dori: str, mode: str, wait_text: str):
    wait = await u.message.reply_text(f"⏳ {wait_text}")

    try:
        if mode == "full":
            prompt = prompt_full(dori)
        elif mode == "short":
            prompt = prompt_short(dori)
        elif mode == "side":
            prompt = prompt_side_effects(dori)
        elif mode == "price":
            prompt = prompt_price(dori)
        else:
            prompt = prompt_schedule(dori)

        answer = await ask_claude(prompt)
        await wait.delete()
        await u.message.reply_html(
            f"💊 <b>{dori.upper()}</b>\n\n{answer}",
            reply_markup=MAIN_KEYBOARD,
        )

    except httpx.HTTPStatusError as e:
        log.error(f"Claude API error: {e}")
        await wait.edit_text("❌ Xizmat vaqtincha ishlamaydi. Qayta urinib ko'ring.")
    except Exception as e:
        log.exception(e)
        await wait.edit_text("❌ Xatolik yuz berdi. Qayta urinib ko'ring.")


# ─── MAIN ────────────────────────────────────

def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN yo'q!")
        return
    if not CLAUDE_API:
        print("❌ CLAUDE_API_KEY yo'q!")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🚀 Dori haqida Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()