import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- الإعدادات الأساسية ---
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 8333784255 
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- بناء النواة (قاعدة البيانات) ---
conn = sqlite3.connect('pro_god_mode.db', check_same_thread=False)
cursor = conn.cursor()

# جداول النظام الشامل
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, is_blocked BOOLEAN DEFAULT 0)')
cursor.execute('CREATE TABLE IF NOT EXISTS store (id INTEGER PRIMARY KEY AUTOINCREMENT, parent_id INTEGER, type TEXT, name TEXT, content TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS pages (slug TEXT PRIMARY KEY, title TEXT, content TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')

# إعداد الإعدادات الافتراضية
cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES ("captcha", "off"), ("spam_filter", "on"), ("stats_enabled", "on")')
conn.commit()

class AdminStates(StatesGroup):
    waiting_input = State()
    broadcast_msg = State()

# --- محرك الأزرار الشجرية ---
def get_main_keyboard():
    cursor.execute('SELECT id, name FROM store WHERE parent_id=0')
    items = cursor.fetchall()
    kb = []
    for i in range(0, len(items), 2):
        row = [InlineKeyboardButton(text=items[i][1], callback_data=f"go_{items[i][0]}")]
        if i+1 < len(items): row.append(InlineKeyboardButton(text=items[i+1][1], callback_data=f"go_{items[i+1][0]}"))
        kb.append(row)
    
    # زر لوحة التحكم يظهر للجميع (الوصول محمي برمجياً)
    kb.append([InlineKeyboardButton(text="⚙️ لوحة التحكم", callback_data="admin_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- أوامر البداية ---
@dp.message(Command("start"))
async def start(message: types.Message):
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (message.from_user.id, f"@{message.from_user.username}"))
    conn.commit()
    await message.answer("🔥 أهلاً بك في البوت الأقوى على الإطلاق!\nاستخدم القائمة أدناه للتنقل:", reply_markup=get_main_keyboard())

# --- لوحة التحكم المركزية (The Command Center) ---
@dp.callback_query(F.data == "admin_main")
async def admin_main(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("❌ عذراً، هذه اللوحة للمطور فقط!", show_alert=True)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 المستخدمون", callback_data="adm_users"), InlineKeyboardButton(text="🛒 المنتجات", callback_data="adm_products")],
        [InlineKeyboardButton(text="🎨 إدارة الأزرار", callback_data="adm_btns"), InlineKeyboardButton(text="📑 الصفحات", callback_data="adm_pages")],
        [InlineKeyboardButton(text="📢 الإعلانات", callback_data="adm_cast"), InlineKeyboardButton(text="🛡 الحماية", callback_data="adm_sec")],
        [InlineKeyboardButton(text="⚙️ الإعدادات المتقدمة", callback_data="adm_adv")],
        [InlineKeyboardButton(text="🔙 إغلاق", callback_data="close")]
    ])
    await call.message.edit_text("⚙️ **لوحة التحكم المركزية**\nاختر القسم الذي تريد إدارته:", reply_markup=kb, parse_mode="Markdown")

# --- 1. قسم المستخدمين ---
@dp.callback_query(F.data == "adm_users")
async def adm_users(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 بحث عن مستخدم", callback_data="u_search"), InlineKeyboardButton(text="🚫 الحظر", callback_data="u_ban")],
        [InlineKeyboardButton(text="✅ فك الحظر", callback_data="u_unban"), InlineKeyboardButton(text="📋 القائمة", callback_data="u_list")],
        [InlineKeyboardButton(text="🔙 عودة", callback_data="admin_main")]
    ])
    await call.message.edit_text("👥 **إدارة المستخدمين**:", reply_markup=kb)

# --- 2. قسم المنتجات والأقسام ---
@dp.callback_query(F.data == "adm_products")
async def adm_products(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 الأقسام (ألعاب، بوتات...)", callback_data="p_cats")],
        [InlineKeyboardButton(text="➕ إضافة قسم", callback_data="p_add_cat"), InlineKeyboardButton(text="📦 إدارة المنتجات", callback_data="p_manage")],
        [InlineKeyboardButton(text="🔙 عودة", callback_data="admin_main")]
    ])
    await call.message.edit_text("🛒 **إدارة المتجر والمنتجات**:", reply_markup=kb)

# --- 3. قسم الإعلانات ---
@dp.callback_query(F.data == "adm_cast")
async def adm_cast(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 إذاعة للجميع", callback_data="c_all"), InlineKeyboardButton(text="🎯 إذاعة لفئة", callback_data="c_seg")],
        [InlineKeyboardButton(text="📸 إذاعة صورة", callback_data="c_img"), InlineKeyboardButton(text="🎥 إذاعة فيديو", callback_data="c_vid")],
        [InlineKeyboardButton(text="🔙 عودة", callback_data="admin_main")]
    ])
    await call.message.edit_text("📢 **محرك الإعلانات والإذاعة**:", reply_markup=kb)

# --- 4. قسم الإعدادات المتقدمة ---
@dp.callback_query(F.data == "adm_adv")
async def adm_adv(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 إعادة تشغيل", callback_data="adv_restart"), InlineKeyboardButton(text="🧹 تنظيف السجلات", callback_data="adv_clear")],
        [InlineKeyboardButton(text="📤 نسخة احتياطية", callback_data="adv_back"), InlineKeyboardButton(text="📊 الإحصائيات", callback_data="adv_stats")],
        [InlineKeyboardButton(text="🔙 عودة", callback_data="admin_main")]
    ])
    await call.message.edit_text("⚙️ **الإعدادات المتقدمة للنظام**:", reply_markup=kb)

# --- نظام التنقل والعودة ---
@dp.callback_query(F.data == "close")
async def close(call: types.CallbackQuery):
    await call.message.edit_text("تم إغلاق اللوحة الإدارية.", reply_markup=get_main_keyboard())

async def main():
    print("🚀 THE ULTIMATE BOT IS LIVE...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
  
