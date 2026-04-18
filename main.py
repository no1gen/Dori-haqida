import os
import io
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("⚠️ .env faylida BOT_TOKEN va GEMINI_API_KEY ko'rsatilmagan!")

# Gemini sozlash
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config={"temperature": 0.3, "top_p": 0.8, "max_output_tokens": 1500},
    safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_MEDICAL: HarmBlockThreshold.BLOCK_NONE,
    }
)

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

DISCLAIMER = "\n⚠️ **TIBBIY OG'OHLANTIRISH:** Bu ma'lumotlar faqat tanishuv uchun. Dori vositalarini qabul qilishdan oldin albatta shifokor yoki farmatsevt bilan maslahatlashing. O'z-o'zingizni davolamang!"

SYSTEM_PROMPT = """Siz "Dori haqida" nomli professional farmatsevtik yordamchi botsiz. Barcha javoblaringiz faqat o'zbek tilida bo'lishi shart.
Quyidagilarni qiling:
1. Dori nomi, tarkibi, qo'llanilishi, dozasi, nojo'ya ta'sirlari, kontrendikatsiyalari, homiladorlik/emasizlik davrida qo'llanilishi, saqlash shartlari va muqobillari haqida batafsil yozing.
2. Agar foydalanuvchi surat yuborsa, dori qutisi, blister yoki tabletkani aniqlang va shunga mos ma'lumot bering.
3. Dori o'zaro ta'siri so'ralsa, kiritilgan dorilarning birgalikda qo'llanilishi haqida ogohlantiring.
4. Belgilar so'ralsa, mumkin bo'lgan kasalliklarni aytib, albatta shifokorga murojaat qilishni tavsiya qiling.
5. Har doim aniq, tushunarli, ilmiy asoslangan va xavfsiz ma'lumot bering.
6. Har bir javob oxirida tibbiy ogohlantirishni qo'shing.
7. Agar ma'lumot yetarli bo'lmasa, "Ma'lumot topilmadi, iltimos, aniqroq nom kiriting yoki shifokorga murojaat qiling" deb javob bering."""

class UserState(StatesGroup):
    waiting_for_drugs_interaction = State()
    waiting_for_symptoms = State()

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💊 Dori nomi bo'yicha qidirish", callback_data="search_name")],
        [InlineKeyboardButton(text="📸 Suratdan dori tahlili", callback_data="search_photo")],
        [InlineKeyboardButton(text="🔄 Dori o'zaro ta'siri", callback_data="check_interaction")],
        [InlineKeyboardButton(text="🤒 Belgilarni tekshirish", callback_data="check_symptoms")],
        [InlineKeyboardButton(text="📞 Shoshilinch yordam raqamlari", callback_data="emergency")]
    ])

async def send_typing(chat_id):
    await bot.send_chat_action(chat_id=chat_id, action="typing")

async def get_gemini_response(prompt: str, image_bytes: bytes = None):
    try:
        parts = []
        if image_bytes:
            parts.append(genai.types.Part.from_bytes(image_bytes, "image/jpeg"))
        parts.append({"text": prompt})

        response = await asyncio.to_thread(
            model.generate_content,
            parts
        )
        if response.text:
            return response.text.strip() + DISCLAIMER
        return "❌ Ma'lumot olinmadi. Iltimos, qayta urinib ko'ring." + DISCLAIMER
    except Exception as e:
        logging.error(f"Gemini xatosi: {e}")
        return "⚠️ Server xatosi. Birozdan so'ng qayta urinib ko'ring." + DISCLAIMER

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Assalomu alaykum! Men **Dori haqida** botman.\n\n"
        "💊 Dori vositalari haqida batafsil ma'lumot olish, suratlardan tahlil qilish, "
        "dori o'zaro ta'sirini tekshirish va belgilarni tahlil qilish uchun quyidagi tugmalardan foydalaning.",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await cmd_start(message)

@dp.callback_query(F.data == "search_name")
async def cb_search_name(callback: types.CallbackQuery):
    await callback.message.answer("💊 Dori nomini yozing (masalan: Paratsetamol, Ibuprofen, Amoksitsillin...)")
    await callback.answer()

@dp.callback_query(F.data == "search_photo")
async def cb_search_photo(callback: types.CallbackQuery):
    await callback.message.answer("📸 Dori qutisi, blister yoki tabletkasining aniq suratini yuboring.")
    await callback.answer()

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    await send_typing(message.chat.id)
    try:
        photo = message.photo[-1]
        file = await bot.download(photo.file_id)
        image_bytes = file.read()
        prompt = "Bu suratdagi dori vositasini aniqla va batafsil ma'lumot ber: nomi, tarkibi, qo'llanilishi, dozasi, nojo'ya ta'sirlari, kontrendikatsiyalari va muqobillari."
        response = await get_gemini_response(prompt, image_bytes)
        await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Photo error: {e}")
        await message.answer("❌ Suratni tahlil qilishda xatolik yuz berdi. Iltimos, aniqroq surat yuboring." + DISCLAIMER)

@dp.message(F.text & ~F.photo)
async def handle_text(message: types.Message):
    if message.text.startswith("/"):
        return
    await send_typing(message.chat.id)
    prompt = f"Foydalanuvchi '{message.text}' haqida so'ramoqda. Iltimos, dori vositasi sifatida tahlil qiling va batafsil ma'lumot bering."
    response = await get_gemini_response(prompt)
    await message.answer(response, parse_mode="Markdown")

@dp.callback_query(F.data == "check_interaction")
async def cb_interaction(callback: types.CallbackQuery):
    await callback.message.answer("🔄 2 yoki undan ortiq dori nomini vergul bilan ajratib yozing.\nMasalan: `Aspirin, Ibuprofen, Metformin`")
    await callback.answer()

@dp.message(UserState.waiting_for_drugs_interaction)
async def process_interaction(message: types.Message, state: FSMContext):
    await send_typing(message.chat.id)
    prompt = f"Quyidagi dorilar birgalikda qo'llanilganda o'zaro ta'siri qanday bo'ladi? Xavf darajasi, qanday nojo'ya ta'sirlar bo'lishi mumkin va qanday ehtiyot choralarini ko'rish kerakligini tushuntiring: {message.text}"
    response = await get_gemini_response(prompt)
    await message.answer(response, parse_mode="Markdown")
    await state.clear()

@dp.callback_query(F.data == "check_symptoms")
async def cb_symptoms(callback: types.CallbackQuery):
    await callback.message.answer("🤒 Qanday belgilaringiz bor? Yash, yosh, jinsingiz va boshqa kasalliklaringizni yozing.\nMasalan: `32 yosh, erkak, bosh og'rig'i, harorat 38, yo'tal`")
    await callback.answer()

@dp.message(UserState.waiting_for_symptoms)
async def process_symptoms(message: types.Message, state: FSMContext):
    await send_typing(message.chat.id)
    prompt = f"Foydalanuvchi quyidagi belgilarni ko'rsatmoqda: {message.text}. Mumkin bo'lgan holatlarni tahlil qiling, qachon shifokorga borish kerakligini ayting va o'z-o'zini davolashdan ogohlantiring."
    response = await get_gemini_response(prompt)
    await message.answer(response, parse_mode="Markdown")
    await state.clear()

@dp.callback_query(F.data == "emergency")
async def cb_emergency(callback: types.CallbackQuery):
    text = (
        "🚑 **Shoshilinch tibbiy yordam raqamlari (O'zbekiston):**\n\n"
        "📞 103 – Tez tibbiy yordam\n"
        "📞 105 – Favqulodda vaziyatlar\n"
        "📞 112 – Yagona qutqaruv xizmati\n\n"
        "💡 Agar holat og'ir bo'lsa, darhol shifokorga murojaat qiling yoki yaqin shifoxonaga boring."
    )
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@dp.errors()
async def error_handler(event: types.ErrorEvent):
    logging.exception(f"Bot xatosi: {event.exception}")
    if event.update.message:
        await event.update.message.answer("❌ Kutilmagan xatolik yuz berdi. Iltimos, qayta urinib ko'ring." + DISCLAIMER)

async def main():
    logging.info("🚀 Dori haqida bot ishga tushirildi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
