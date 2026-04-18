import logging
import random
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- CONFIGURATION ---
API_TOKEN = '8721694709:AAFV48QMKlq0No2a6xz10fcSyUawHRjwg-I'
CHANNEL_ID = '-1003713449715' 
ADMIN_ID = 7371738152 

BRAND_NAME = 'CoinFlow'
BRAND_WEBSITE = 'example.com' 

# Рандомайзеры
SUPPORTS = ["Rachel", "Alex", "Jordan", "Sarah", "Mike", "Linda", "Kevin", "Emma"]
WAIT_TIMES = ["24 hours", "48 hours", "2 days", "3 days", "36 hours", "over 24h"]

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)

# --- DATABASE ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, task_type TEXT, support_name TEXT, wait_time TEXT, tp_nick TEXT, status TEXT)''')
conn.commit()

class ReportState(StatesGroup):
    waiting_for_nick = State()
    waiting_for_photo = State()

# --- LOGIC ---

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
        # Рандомим тип задачи (50/50 или как захочешь)
        task_type = random.choice(['5_star', '1_star'])
        agent = random.choice(SUPPORTS)
        wait_time = random.choice(WAIT_TIMES)
        
        cursor.execute("INSERT OR REPLACE INTO users (user_id, task_type, support_name, wait_time, status) VALUES (?, ?, ?, ?, ?)", 
                       (call.from_user.id, task_type, agent, wait_time, 'started'))
        conn.commit()

        if task_type == '5_star':
            # ИНСТРУКЦИЯ ДЛЯ 5 ЗВЕЗД
            mission_text = (
                f"🌟 **YOUR EASY MISSION** 🌟\n\n"
                f"**Step 1:** Go to our site 👉 **{BRAND_WEBSITE}**\n"
                f"**Step 2:** Find the **Trustpilot icon** and click it! 🖱\n"
                f"**Step 3:** Give us **5 STARS** ⭐⭐⭐⭐⭐\n"
                f"**Step 4:** Write 2-4 lines of nice text.\n\n"
                f"❗ **IMPORTANT RULE:**\n"
                f"You MUST say 'Thank you' to our agent **{agent}** in your review.\n\n"
                f"💡 *Example (DON'T COPY): {agent} was very helpful with my deposit! Thanks!* \n"
                f"❌ **DO NOT COPY** the example! Write your own words.\n\n"
                f"**Step 5:** Take a **SCREENSHOT** of your review and send it here! 📸"
            )
        else:
            # ИНСТРУКЦИЯ ДЛЯ 1 ЗВЕЗДЫ
            mission_text = (
                f"🌟 **YOUR EASY MISSION** 🌟\n\n"
                f"**Step 1:** Go to our site 👉 **{BRAND_WEBSITE}**\n"
                f"**Step 2:** Find the **Trustpilot icon** and click it! 🖱\n"
                f"**Step 3:** Give us **1 STAR** ⭐\n"
                f"**Step 4:** Write a short angry text (2-3 lines).\n\n"
                f"❗ **IMPORTANT RULE:**\n"
                f"Write that you are still waiting for your money for **{wait_time}**.\n\n"
                f"⚠️ **DO NOT mention any agent names!** Just talk about the waiting time.\n\n"
                f"**Step 5:** Take a **SCREENSHOT** of your review and send it here! 📸"
            )
        
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("📤 SUBMIT PROOF", callback_data="start_report"))
        await call.message.edit_text(mission_text, reply_markup=kb, parse_mode="Markdown", disable_web_page_preview=True)
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
    await message.answer("📸 Upload your **Screenshot** (from 'My Reviews' section):")

@dp.message_handler(content_types=['photo'], state=ReportState.waiting_for_photo)
async def process_photo(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    
    # Достаем данные юзера из БД для отчета
    db_data = cursor.execute("SELECT task_type, support_name, wait_time FROM users WHERE user_id = ?", (message.from_user.id,)).fetchone()
    task_type, agent, wait_time = db_data if db_data else ("Unknown", "Unknown", "Unknown")

    cursor.execute("UPDATE users SET tp_nick = ?, status = ? WHERE user_id = ?",
                   (user_data['nick'], 'pending', message.from_user.id))
    conn.commit()

    # Отчет тебе в личку
    admin_text = (
        f"📩 **NEW REVIEW REPORT!**\n\n"
        f"👤 **User:** @{message.from_user.username}\n"
        f"🆔 **TP Nick:** {user_data['nick']}\n"
        f"📊 **Type:** {task_type}\n"
        f"👩‍💼 **Agent:** {agent if task_type == '5_star' else 'N/A'}\n"
        f"⏳ **Wait Time:** {wait_time if task_type == '1_star' else 'N/A'}\n"
    )
    
    try:
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=admin_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error sending to admin: {e}")

    await state.finish()
    await message.answer("🎯 **Submitted!** Your review is being checked. Results will be in the channel! 🌊")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
