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

COMMUNITY_NAME = 'CoinFlow' 

# Сайты для поиска
TARGET_DOMAINS = ['byjanil.com', 'recoup.dk', 'domain3.com'] 
domain_counter = 0 # Счетчик для чередования

# Рандомайзеры
SUPPORTS = ["Rachel", "Alex", "Jordan", "Sarah", "Mike", "Linda", "Kevin", "Emma"]
WAIT_TIMES = ["24 hours", "48 hours", "2 days", "3 days", "36 hours", "over 24h", "about 30 hours"]

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)

# --- DATABASE ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, task_type TEXT, target_domain TEXT, wait_time TEXT, tp_nick TEXT, status TEXT)''')
conn.commit()

class ReportState(StatesGroup):
    waiting_for_nick = State()
    waiting_for_photo = State()

# --- LOGIC ---

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🌊 Join Channel", url=f"https://t.me/CoinFlowRewards"),
        InlineKeyboardButton("✅ I HAVE JOINED", callback_data="check_sub")
    )
    await message.answer(f"🌊 **Welcome to the {COMMUNITY_NAME} Reward Hub!**\nJoin our channel to get your mission.", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query_handler(text="check_sub")
async def check_sub(call: types.CallbackQuery):
    # ПРОВЕРКА: не нажимал ли он уже кнопку?
    user_data = cursor.execute("SELECT status FROM users WHERE user_id = ?", (call.from_user.id,)).fetchone()
    
    if user_data:
        if user_data[0] == 'started':
            await call.answer("⚠️ You already have an active mission! Please complete it.", show_alert=True)
            return
        elif user_data[0] == 'pending':
            await call.answer("⏳ Please wait! Your review is already being checked. 🌊", show_alert=True)
            return

    # Если всё ок, проверяем подписку
if user_status.status in ['member', 'administrator', 'creator']:
        global domain_counter
        # Берем домен по очереди
        current_domain = TARGET_DOMAINS[domain_counter % len(TARGET_DOMAINS)]
        domain_counter += 1
        
        wait_time = random.choice(WAIT_TIMES)
        
        # Записываем в базу (task_type теперь всегда 1_star)
        cursor.execute("INSERT OR REPLACE INTO users (user_id, task_type, target_domain, wait_time, status) VALUES (?, ?, ?, ?, ?)", 
                       (call.from_user.id, '1_star', current_domain, wait_time, 'started'))
        conn.commit()
        
        cursor.execute("INSERT OR REPLACE INTO users (user_id, task_type, support_name, wait_time, status) VALUES (?, ?, ?, ?, ?)", 
                       (call.from_user.id, task_type, agent, wait_time, 'started'))
        conn.commit()

   mission_text = (
            f"🎰 **YOUR LOTTERY MISSION** 🎰\n\n"
            f"1️⃣ **Go to Google.com**\n"
            f"2️⃣ Search for: `{current_domain}`\n"
            f"3️⃣ Find and click on the **{current_domain}** TrustPilot Page result.\n\n"
            f"4️⃣ Give **1 STAR** ⭐\n"
            f"5️⃣ Write 2-3 lines of negative text.\n\n"
            f"⚠️ **REQUIRED RULE:**\n"
            f"Mention that you are still waiting for your withdrawal for **{wait_time}**.\n"
            f"🚫 **DO NOT COPY EXAMPLES!** Use your own words.\n\n"
            f"6️⃣ Send a **SCREENSHOT** of your review! 📸"
        )
        
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("📤 SUBMIT PROOF", callback_data="start_report"))
        await call.message.edit_text(mission_text, reply_markup=kb, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await call.answer("❌ Please join our channel first!", show_alert=True)

@dp.callback_query_handler(text="start_report")
async def start_report(call: types.CallbackQuery):
    await ReportState.waiting_for_nick.set()
    await call.message.answer("📝 Enter your **Trustpilot Nickname**:")

@dp.message_handler(state=ReportState.waiting_for_nick)
async def process_nick(message: types.Message, state: FSMContext):
    await state.update_data(nick=message.text)
    await ReportState.next()
    await message.answer("📸 Upload a **Screenshot** of your review (Go to 'My Reviews' section):")

@dp.message_handler(content_types=['photo'], state=ReportState.waiting_for_photo)
async def process_photo(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    db_data = cursor.execute("SELECT target_domain, wait_time FROM users WHERE user_id = ?", (message.from_user.id,)).fetchone()
    target_domain, wait_time = db_data if db_data else ("Unknown", "Unknown")

    # Обновляем статус на pending (проверка)
    cursor.execute("UPDATE users SET tp_nick = ?, status = ? WHERE user_id = ?",
                   (user_data['nick'], 'pending', message.from_user.id))
    conn.commit()

  admin_text = (
        f"📩 <b>NEW REVIEW SUBMITTED!</b>\n\n"
        f"👤 <b>User:</b> @{message.from_user.username if message.from_user.username else 'NoUsername'} (ID: <code>{message.from_user.id}</code>)\n"
        f"🆔 <b>TP Nick:</b> {user_data['nick']}\n"
        f"👩‍💼 <b>Agent:</b> {agent if task_type == '5_star' else 'N/A'}\n"
        f"⏳ <b>Wait Time:</b> {wait_time if task_type == '1_star' else 'N/A'}\n"
        f"🌐 <b>Target Site:</b> {TARGET_SITE_DOMAIN}"
    )
    
    try:
        # Пытаемся отправить фото
        await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=admin_text, parse_mode="HTML")
    except Exception as e:
        # Если не вышло, бот напишет в консоль ПОЛНУЮ причину
        logging.error(f"FULL ERROR INFO: {e}")
        # И попробует отправить тебе хотя бы текст, чтобы ты знал о проблеме
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ Photo error, but here is info:\n\n{admin_text}", parse_mode="HTML")
        except:
            pass

    await state.finish()
    await message.answer("🎯 **Submitted!** We are checking your review. Please wait for the announcement! 🌊")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
