import os
import sqlite3
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- الإعدادات ---
API_TOKEN = os.getenv('BOT_TOKEN')
SUPER_ADMIN = 8333784255
MY_ACCOUNT_URL = "https://t.me/xq_7d"
CHANNEL_URL = "https://t.me/drov70"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- قاعدة البيانات ---
conn = sqlite3.connect('sovereign_store_v6.db', check_same_thread=False)
cursor = conn.cursor()
# (تم الاحتفاظ بنفس الجداول السابقة لضمان توافق بياناتك)
cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, balance REAL DEFAULT 0.0, referred_by INTEGER, last_gift_date TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS elements (id INTEGER PRIMARY KEY AUTOINCREMENT, parent_id INTEGER DEFAULT 0, type TEXT, name TEXT, content TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS purchases (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, item_name TEXT, purchase_date TEXT)''')
conn.commit()

# --- الحالات (FSM) ---
class SystemStates(StatesGroup):
    wait_name = State()
    wait_content = State()
    wait_edit_name = State()
    wait_broadcast = State()

# --- الدوال المساعدة (الأزرار) ---
def get_main_keyboard(user_id):
    kb = [
        [InlineKeyboardButton(text="🛒 الشراء وتصفح المتجر", callback_data="main_buy")],
        [InlineKeyboardButton(text="💰 شحن رصيد", callback_data="main_charge"), InlineKeyboardButton(text="📦 مشترياتي", callback_data="main_purchases")],
        [InlineKeyboardButton(text="🔗 رابط الإحالة", callback_data="main_referral"), InlineKeyboardButton(text="📢 قناة التفعيلات", url=CHANNEL_URL)],
        [InlineKeyboardButton(text="👨‍💻 الدعم الفني", url=MY_ACCOUNT_URL)]
    ]
    if user_id == SUPER_ADMIN:
        kb.append([InlineKeyboardButton(text="⚙️ لوحة التحكم السيادية", callback_data="super_admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- لوحة الإدارة المطورة ---
@dp.callback_query(F.data == "super_admin_panel")
async def admin_panel(call: types.CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="➕ إضافة عنصر", callback_data="adm_add_element")],
        [InlineKeyboardButton(text="✏️ تعديل اسم زر", callback_data="adm_edit_list"), InlineKeyboardButton(text="🗑 حذف عنصر", callback_data="adm_del_list")],
        [InlineKeyboardButton(text="📢 إذاعة", callback_data="adm_broadcast"), InlineKeyboardButton(text="📊 إحصائيات", callback_data="adm_stats")],
        [InlineKeyboardButton(text="🔙 عودة", callback_data="back_to_main")]
    ]
    await call.message.edit_text("⚙️ **لوحة التحكم الإدارية:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- نظام التعديل ---
@dp.callback_query(F.data == "adm_edit_list")
async def edit_list(call: types.CallbackQuery):
    cursor.execute("SELECT id, name FROM elements")
    items = cursor.fetchall()
    kb = [[InlineKeyboardButton(text=f"✏️ {i[1]}", callback_data=f"edit_el_{i[0]}")] for i in items]
    kb.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="super_admin_panel")])
    await call.message.edit_text("اختر الزر لتعديل اسمه:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("edit_el_"))
async def edit_name_step(call: types.CallbackQuery, state: FSMContext):
    eid = call.data.split("_")[2]
    await state.update_data(edit_id=eid)
    await call.message.answer("أرسل الاسم الجديد للزر:")
    await state.set_state(SystemStates.wait_edit_name)

@dp.message(SystemStates.wait_edit_name)
async def process_edit(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cursor.execute("UPDATE elements SET name=? WHERE id=?", (message.text, data['edit_id']))
    conn.commit()
    await message.answer("✅ تم تحديث اسم الزر بنجاح!")
    await state.clear()

# --- نظام الحذف ---
@dp.callback_query(F.data == "adm_del_list")
async def del_list(call: types.CallbackQuery):
    cursor.execute("SELECT id, name FROM elements")
    items = cursor.fetchall()
    kb = [[InlineKeyboardButton(text=f"❌ {i[1]}", callback_data=f"del_el_{i[0]}")] for i in items]
    kb.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="super_admin_panel")])
    await call.message.edit_text("اختر الزر للحذف (سيتم حذفه نهائياً):", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("del_el_"))
async def perform_del(call: types.CallbackQuery):
    eid = call.data.split("_")[2]
    cursor.execute("DELETE FROM elements WHERE id=?", (eid,))
    conn.commit()
    await call.answer("✅ تم الحذف!", show_alert=True)
    await admin_panel(call)

# ... (باقي الدوال كما هي في كودك الأصلي للإضافة والإحصائيات والتشغيل)
async def main():
    print("🚀 البوت يعمل الآن...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
