import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

# --- الإعدادات ---
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 8333784255  # آيديك هنا
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- قاعدة البيانات ---
conn = sqlite3.connect('buttons.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS custom_buttons (id INTEGER PRIMARY KEY, name TEXT, action TEXT)')
conn.commit()

# --- الحالات (States) ---
class AdminStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_action = State()

# --- دالة الأزرار الديناميكية ---
def get_dynamic_menu(is_admin):
    cursor.execute('SELECT name, action FROM custom_buttons')
    buttons = cursor.fetchall()
    inline_kb = []
    for name, action in buttons:
        inline_kb.append([InlineKeyboardButton(text=name, callback_data=f"btn_{name}")])
    
    if is_admin:
        inline_kb.append([InlineKeyboardButton(text="⚙️ لوحة الإعدادات", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=inline_kb)

# --- أوامر البوت ---
@dp.message(Command("start"))
async def start(message: types.Message):
    is_admin = (message.from_user.id == ADMIN_ID)
    await message.answer("أهلاً بك في البوت، اختر من القائمة:", reply_markup=get_dynamic_menu(is_admin))

# --- لوحة التحكم ---
@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة زر جديد", callback_data="add_new_btn")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_main")]
    ])
    await call.message.edit_text("لوحة تحكم المدير:", reply_markup=kb)

@dp.callback_query(F.data == "add_new_btn")
async def start_add_btn(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("أرسل اسم الزر الجديد:")
    await state.set_state(AdminStates.waiting_for_name)

@dp.message(AdminStates.waiting_for_name)
async def get_btn_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("الآن أرسل المحتوى (رابط أو نص) للزر:")
    await state.set_state(AdminStates.waiting_for_action)

@dp.message(AdminStates.waiting_for_action)
async def get_btn_action(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cursor.execute('INSERT INTO custom_buttons (name, action) VALUES (?, ?)', (data['name'], message.text))
    conn.commit()
    await message.answer("تم إضافة الزر بنجاح!")
    await state.clear()

# --- معالجة الأزرار الديناميكية ---
@dp.callback_query(F.data.startswith("btn_"))
async def handle_dynamic_btns(call: types.CallbackQuery):
    btn_name = call.data.split("_")[1]
    cursor.execute('SELECT action FROM custom_buttons WHERE name=?', (btn_name,))
    result = cursor.fetchone()
    if result:
        await call.message.answer(f"محتوى الزر {btn_name}:\n{result[0]}")
    await call.answer()

@dp.callback_query(F.data == "back_main")
async def back_main(call: types.CallbackQuery):
    is_admin = (call.from_user.id == ADMIN_ID)
    await call.message.edit_text("القائمة الرئيسية:", reply_markup=get_dynamic_menu(is_admin))

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
