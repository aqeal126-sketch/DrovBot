import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatMember

# --- الإعدادات ---
API_TOKEN = os.getenv('BOT_TOKEN')
SUPER_ADMIN = 8333784255
REQ_CHANNEL = "@drov8"
MY_ACCOUNT_URL = "https://t.me/xq_7d"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- قاعدة البيانات ---
conn = sqlite3.connect('store_db.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
cursor.execute('CREATE TABLE IF NOT EXISTS elements (id INTEGER PRIMARY KEY AUTOINCREMENT, parent_id INTEGER, type TEXT, name TEXT, content TEXT)')
conn.commit()

# --- فحص الاشتراك ---
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(chat_id=REQ_CHANNEL, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

# --- الحالات ---
class AdminStates(StatesGroup):
    wait_name = State()
    wait_content = State()
    wait_edit_name = State()

# --- الأزرار ---
def get_main_kb(user_id):
    kb = [[InlineKeyboardButton(text="🛒 المتجر", callback_data="buy")], [InlineKeyboardButton(text="👨‍💻 الدعم", url=MY_ACCOUNT_URL)]]
    if user_id == SUPER_ADMIN: kb.append([InlineKeyboardButton(text="⚙️ الإدارة", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- البداية ---
@dp.message(CommandStart())
async def start(message: types.Message):
    if not await check_sub(message.from_user.id):
        return await message.answer(f"❌ يجب الاشتراك في القناة أولاً: {REQ_CHANNEL}")
    await message.answer("أهلاً بك في متجرنا:", reply_markup=get_main_kb(message.from_user.id))

# --- لوحة الإدارة ---
@dp.callback_query(F.data == "admin")
async def admin_panel(call: types.CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="➕ إضافة عنصر", callback_data="add_el")],
        [InlineKeyboardButton(text="🗑 حذف عنصر", callback_data="del_el")]
    ]
    await call.message.edit_text("⚙️ لوحة التحكم:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data == "add_el")
async def add_el(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("أرسل اسم الزر الجديد:")
    await state.set_state(AdminStates.wait_name)

@dp.message(AdminStates.wait_name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("أرسل المحتوى (رابط أو نص):")
    await state.set_state(AdminStates.wait_content)

@dp.message(AdminStates.wait_content)
async def get_content(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cursor.execute('INSERT INTO elements (name, content) VALUES (?, ?)', (data['name'], message.text))
    conn.commit()
    await message.answer("✅ تم الإضافة!")
    await state.clear()

# --- تشغيل البوت ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
  
