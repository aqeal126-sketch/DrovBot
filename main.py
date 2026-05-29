import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- الإعدادات ---
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 8333784255 # تأكد أن هذا هو رقمك
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- قاعدة البيانات ---
conn = sqlite3.connect('store_bot.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS store (id INTEGER PRIMARY KEY, name TEXT, content TEXT, parent_id INTEGER)')
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
conn.commit()

class AdminStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_content = State()
    broadcast_msg = State()

# --- دالة الواجهة الرئيسية ---
def get_main_kb(is_admin):
    # جلب الأزرار الرئيسية
    cursor.execute('SELECT id, name FROM store WHERE parent_id=0')
    items = cursor.fetchall()
    kb = []
    for item_id, name in items:
        kb.append([InlineKeyboardButton(text=name, callback_data=f"open_{item_id}")])
    
    if is_admin:
        kb.append([InlineKeyboardButton(text="⚙️ لوحة التحكم", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- البداية ---
@dp.message(Command("start"))
async def start(message: types.Message):
    # تسجيل دخول المستخدم
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (message.from_user.id,))
    conn.commit()
    
    print(f"DEBUG: User ID: {message.from_user.id}") # ستظهر في logs السيرفر
    is_admin = (message.from_user.id == ADMIN_ID)
    await message.answer("مرحباً بك في متجرنا!", reply_markup=get_main_kb(is_admin))

# --- لوحة التحكم ---
@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 إدارة المنتجات", callback_data="manage_store")],
        [InlineKeyboardButton(text="📢 إذاعة", callback_data="broadcast")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_main")]
    ])
    await call.message.edit_text("⚙️ لوحة التحكم:", reply_markup=kb)

# --- الإذاعة ---
@dp.callback_query(F.data == "broadcast")
async def broadcast_step1(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("أرسل نص الإذاعة:")
    await state.set_state(AdminStates.broadcast_msg)

@dp.message(AdminStates.broadcast_msg)
async def broadcast_execute(message: types.Message, state: FSMContext):
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    count = 0
    for u in users:
        try:
            await bot.send_message(u[0], message.text)
            count += 1
        except: pass
    await message.answer(f"✅ تم الإرسال لـ {count} مستخدم.")
    await state.clear()

# --- معالجة الأزرار (العودة) ---
@dp.callback_query(F.data == "back_main")
async def back_main(call: types.CallbackQuery):
    is_admin = (call.from_user.id == ADMIN_ID)
    await call.message.edit_text("القائمة الرئيسية:", reply_markup=get_main_kb(is_admin))

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
  
