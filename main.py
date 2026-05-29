import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- الإعدادات ---
API_TOKEN = os.getenv('BOT_TOKEN')
SUPER_ADMIN = 8333784255

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- قاعدة البيانات ---
conn = sqlite3.connect('store_db.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS elements (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, content TEXT)')
conn.commit()

# --- الحالات ---
class AdminStates(StatesGroup):
    wait_name = State()
    wait_content = State()
    wait_edit_name = State()
    wait_edit_content = State()

# --- توليد الأزرار ---
def get_main_kb(user_id):
    cursor.execute('SELECT id, name FROM elements')
    items = cursor.fetchall()
    kb = []
    for item in items:
        kb.append([InlineKeyboardButton(text=f"💎 {item[1]}", callback_data=f"show_{item[0]}")])
    
    if user_id == SUPER_ADMIN:
        kb.append([InlineKeyboardButton(text="⚙️ لوحة الإدارة", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- البداية ---
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("أهلاً بك في المتجر، اختر ما يناسبك:", reply_markup=get_main_kb(message.from_user.id))

# --- عرض المحتوى ---
@dp.callback_query(F.data.startswith("show_"))
async def show_item(call: types.CallbackQuery):
    item_id = call.data.split("_")[1]
    cursor.execute('SELECT name, content FROM elements WHERE id=?', (item_id,))
    item = cursor.fetchone()
    await call.message.answer(f"📦 {item[0]}:\n\n{item[1]}")

# --- لوحة الإدارة ---
@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: types.CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="➕ إضافة زر", callback_data="add_el")],
        [InlineKeyboardButton(text="✏️ تعديل/حذف", callback_data="manage_el")]
    ]
    await call.message.edit_text("⚙️ تحكم بالمتجر:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- إضافة ---
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
    await message.answer("✅ تم إضافة الزر بنجاح!")
    await state.clear()

# --- تعديل وحذف ---
@dp.callback_query(F.data == "manage_el")
async def manage_el(call: types.CallbackQuery):
    cursor.execute('SELECT id, name FROM elements')
    items = cursor.fetchall()
    kb = [[InlineKeyboardButton(text=f"🗑 {item[1]}", callback_data=f"del_{item[0]}")] for item in items]
    kb.append([InlineKeyboardButton(text="🔙 عودة", callback_data="admin_panel")])
    await call.message.edit_text("اختر لحذف العنصر:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("del_"))
async def del_el(call: types.CallbackQuery):
    item_id = call.data.split("_")[1]
    cursor.execute('DELETE FROM elements WHERE id=?', (item_id,))
    conn.commit()
    await call.answer("✅ تم الحذف!", show_alert=True)
    await admin_panel(call)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
