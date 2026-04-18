import logging
import random
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- КОНФИГУРАЦИЯ ---
API_TOKEN = '8721694709:AAFV48QMKlq0No2a6xz10fcSyUawHRjwg-I'
CHANNEL_ID = '-1003713449715' 
ADMIN_ID = 7371738152  # !!! ВСТАВЬ СВОЙ ID (цифрами, без кавычек) !!!

BRAND_NAME = 'CoinFlow'
TRUSTPILOT_URL = 'https://www.trustpilot.com/review/example.com' # Ссылка на бренд
REQUIRED_STARS = '5 STARS' # Сколько звезд просим
CUSTOM_INSTRUCTION = 'Search for our brand in Google first, then write a review.' # Твоя инструкция

SUPPORTS = ["Rachel", "Alex", "Jordan", "Sarah", "Mike", "Linda", "Kevin", "Emma"]

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)

# --- БАЗА ДАННЫХ ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, support_name TEXT, tp_nick TEXT, status TEXT)''')
conn.commit()

class ReportState(StatesGroup):
    waiting_for_nick = State()
    waiting_for_photo = State()

# --- ЛОГИКА ---

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🌊 Join Channel", url=f"https://t.me/{CHANNEL_ID[1:]}"),
        InlineKeyboardButton("✅ I HAVE JOINED", callback_data="check_sub")
    )
    await message.answer(f"🌊 **Welcome to {BRAND_NAME}!**\nJoin our channel to unlock missions.", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query_handler(text="check_sub")
async def check_sub(call: types.CallbackQuery):
    status = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=call.from_user.id)
    if status.status != 'left':
        agent = random.choice(SUPPORTS)
        cursor.execute("INSERT OR REPLACE INTO users (user_id, support_name, status) VALUES (?, ?, ?)", 
                       (call.from_user.id, agent, 'started'))
        conn.commit()

        text = (
            f"✅ **Mission Unlocked!**\n\n"
            f"🌟 **Target:** Rate us **{REQUIRED_STARS}**\n"
            f"🔗 **Link:** {TRUSTPILOT_URL}\n\n"
            f"📜 **Instruction:** {CUSTOM_INSTRUCTION}\n\n"
            f"👤 **Agent to mention:** `{agent}`\n\n"
            f"Click below to send your proof!"
        )
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("📤 SUBMIT PROOF", callback_data="start_report"))
        await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await call.answer("❌ Join channel first!", show_alert=True)

@dp.callback_query_handler(text="start_report")
async def start_report(call: types.CallbackQuery):
    await ReportState.waiting_for_nick.set()
    await call.message.answer("📝 Enter your **Trustpilot Nickname**:")

@dp.message_handler(state=ReportState.waiting_for_nick)
async def process_nick(message: types.Message, state: FSMContext):
    await state.update_data(nick=message.text)
    await ReportState.next()
    await message.answer("📸 Upload your **Screenshot**:")

@dp.message_handler(content_types=['photo'], state=ReportState.waiting_for_photo)
async def process_photo(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    agent_data = cursor.execute("SELECT support_name FROM users WHERE user_id = ?", (message.from_user.id,)).fetchone()
    agent = agent_data[0] if agent_data else "Unknown"

    # 1. Сохраняем в БД
    cursor.execute("UPDATE users SET tp_nick = ?, status = ? WHERE user_id = ?",
                   (user_data['nick'], 'pending', message.from_user.id))
    conn.commit()

    # 2. ОТПРАВЛЯЕМ ОТЧЕТ ТЕБЕ (АДМИНУ)
    admin_text = (
        f"📩 **NEW REVIEW REPORT!**\n\n"
        f"👤 **User:** @{message.from_user.username} (ID: `{message.from_user.id}`)\n"
        f"🆔 **TP Nick:** {user_data['nick']}\n"
        f"👩‍💼 **Assigned Agent:** {agent}\n"
    )
    
    try:
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=admin_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Failed to send report to admin: {e}")

    await state.finish()
    await message.answer("🎯 **Submitted!** Your review is under moderation. Winners are announced in the channel! 🌊")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
