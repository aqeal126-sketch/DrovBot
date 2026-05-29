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
ADMIN_ID = 8333784255  # الآيدي الخاص بك
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- قاعدة البيانات ---
conn = sqlite3.connect('bot_data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS buttons 
                  (id INTEGER PRIMARY KEY, name TEXT, content TEXT, parent_id INTEGER)''')
conn.commit()

# --- الحالات ---
class AdminStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_content = State()

# --- دالة جلب الأزرار ---
def get_keyboard(parent_id=0, is_admin=False):
    cursor.execute('SELECT id, name FROM buttons WHERE parent_id=?', (parent_id,))
    buttons = cursor.fetchall()
    keyboard = []
    for btn_id, name in buttons:
        keyboard.append([InlineKeyboardButton(text=name, callback_data=f"btn_{btn_id}")])
    
    if is_admin:
        keyboard.append([InlineKeyboardButton(text="➕ إضافة زر هنا", callback_data=f"add_{parent_id}")])
    
    if parent_id != 0:
        keyboard.append([InlineKeyboardButton(text="🔙 عودة للقائمة الرئيسية", callback_data="back_0")])
        
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# --- دالة البداية المحدثة ---
@dp.message(Command("start"))
async def start(message: types.Message):
    # طباعة الآيدي في الـ Logs للتحقق
    print(f"DEBUG: User ID attempting to start: {message.from_user.id}")

    is_admin = (message.from_user.id == ADMIN_ID)
    await message.answer("أهلاً بك، اختر من القائمة:", reply_markup=get_keyboard(0, is_admin))

# --- التنقل ---
@dp.callback_query(F.data.startswith("btn_"))
async def navigate(call: types.CallbackQuery):
    btn_id = int(call.data.split("_")[1])
    cursor.execute('SELECT content FROM buttons WHERE id=?', (btn_id,))
    content = cursor.fetchone()[0]
    
    if content == "folder":
        is_admin = (call.from_user.id == ADMIN_ID)
        await call.message.edit_text("اختر قسماً:", reply_markup=get_keyboard(btn_id, is_admin))
    else:
        await call.answer(content, show_alert=True)

@dp.callback_query(F.data == "back_0")
async def back_main(call: types.CallbackQuery):
    is_admin = (call.from_user.id == ADMIN_ID)
    await call.message.edit_text("القائمة الرئيسية:", reply_markup=get_keyboard(0, is_admin))

# --- الإضافة (للمدير فقط) ---
@dp.callback_query(F.data.startswith("add_"))
async def add_btn_start(call: types.CallbackQuery, state: FSMContext):
    parent_id = int(call.data.split("_")[1])
    await state.update_data(parent_id=parent_id)
    await call.message.answer("أرسل اسم الزر الجديد:")
    await state.set_state(AdminStates.waiting_for_name)

@dp.message(AdminStates.waiting_for_name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("أرسل محتوى الزر (اكتب 'folder' إذا كان مجلداً للأزرار، أو أي نص/رابط):")
    await state.set_state(AdminStates.waiting_for_content)

@dp.message(AdminStates.waiting_for_content)
async def save_btn(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cursor.execute('INSERT INTO buttons (name, content, parent_id) VALUES (?, ?, ?)', 
                   (data['name'], message.text, data['parent_id']))
    conn.commit()
    await message.answer("✅ تم إضافة الزر بنجاح!")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
  
