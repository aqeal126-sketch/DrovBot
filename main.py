import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- الإعدادات الثابتة الوحيدة ---
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 8333784255 
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- قاعدة البيانات الديناميكية الشاملة ---
conn = sqlite3.connect('ultimate_store.db', check_same_thread=False)
cursor = conn.cursor()
# نوع المحتوى (folder, text, link, media)
cursor.execute('''CREATE TABLE IF NOT EXISTS elements 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, parent_id INTEGER, type TEXT, name TEXT, content TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()

# --- FSM (حالات البناء الديناميكي) ---
class Builder(StatesGroup):
    wait_name = State()
    wait_type = State()
    wait_content = State()
    wait_broadcast = State()

# --- المحرك الديناميكي لجلب القوائم ---
def get_dynamic_kb(parent_id=0):
    cursor.execute('SELECT id, name, type, content FROM elements WHERE parent_id=?', (parent_id,))
    items = cursor.fetchall()
    
    kb = []
    row = []
    for item in items:
        item_id, name, item_type, content = item
        if item_type == 'link':
            row.append(InlineKeyboardButton(text=name, url=content))
        else:
            row.append(InlineKeyboardButton(text=name, callback_data=f"go_{item_id}"))
        
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
    
    if parent_id != 0:
        cursor.execute('SELECT parent_id FROM elements WHERE id=?', (parent_id,))
        grand_parent = cursor.fetchone()
        gp_id = grand_parent[0] if grand_parent else 0
        kb.append([InlineKeyboardButton(text="🔙 رجوع", callback_data=f"go_{gp_id}")])
    else:
        # زر لوحة التحكم يظهر دائماً في القائمة الرئيسية
        kb.append([InlineKeyboardButton(text="⚙️ لوحة التحكم", callback_data="admin_panel")])
        
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- البداية ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (message.from_user.id,))
    conn.commit()
    await message.answer("أهلاً بك في نظامنا المتطور:", reply_markup=get_dynamic_kb(0))

# --- معالج التنقل الديناميكي (قلب البوت) ---
@dp.callback_query(F.data.startswith("go_"))
async def navigate_system(call: types.CallbackQuery):
    target_id = int(call.data.split("_")[1])
    
    if target_id == 0:
        await call.message.edit_text("القائمة الرئيسية:", reply_markup=get_dynamic_kb(0))
        return

    cursor.execute('SELECT type, name, content FROM elements WHERE id=?', (target_id,))
    item = cursor.fetchone()
    if not item: return await call.answer("غير متوفر!")

    item_type, name, content = item
    
    if item_type == 'folder':
        await call.message.edit_text(f"📂 قسم: {name}", reply_markup=get_dynamic_kb(target_id))
    elif item_type == 'text':
        await call.answer()
        await call.message.answer(f"📝 **{name}**\n\n{content}")
    elif item_type == 'media':
        await call.answer()
        await call.message.answer_photo(photo=content, caption=name)

# --- جدار حماية الإدارة ---
@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("❌ دخول غير مصرح به!", show_alert=True)
        
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ بناء عنصر جديد", callback_data="build_select_parent")],
        [InlineKeyboardButton(text="📢 إذاعة", callback_data="admin_cast"), InlineKeyboardButton(text="📊 إحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔙 إغلاق", callback_data="go_0")]
    ])
    await call.message.edit_text("⚙️ **وضع المُنشئ (God Mode)**:", reply_markup=kb)

# --- نظام البناء الديناميكي (إضافة كل شيء من البوت) ---
@dp.callback_query(F.data == "build_select_parent")
async def build_step1(call: types.CallbackQuery, state: FSMContext):
    cursor.execute("SELECT id, name FROM elements WHERE type='folder'")
    folders = cursor.fetchall()
    
    kb = [[InlineKeyboardButton(text="🔝 في القائمة الرئيسية", callback_data="build_p_0")]]
    for f in folders:
        kb.append([InlineKeyboardButton(text=f"📁 داخل: {f[1]}", callback_data=f"build_p_{f[0]}")])
        
    await call.message.edit_text("📍 أين تريد إضافة العنصر الجديد؟", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("build_p_"))
async def build_step2(call: types.CallbackQuery, state: FSMContext):
    pid = int(call.data.split("_")[2])
    await state.update_data(parent_id=pid)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📁 قسم فرعي", callback_data="btype_folder"), InlineKeyboardButton(text="📝 نص/منتج", callback_data="btype_text")],
        [InlineKeyboardButton(text="🔗 رابط خارجي", callback_data="btype_link"), InlineKeyboardButton(text="📸 صورة/ملف", callback_data="btype_media")]
    ])
    await call.message.edit_text("⚙️ ما هو نوع العنصر الذي تريد إنشاءه؟", reply_markup=kb)

@dp.callback_query(F.data.startswith("btype_"))
async def build_step3(call: types.CallbackQuery, state: FSMContext):
    elem_type = call.data.split("_")[1]
    await state.update_data(type=elem_type)
    await call.message.answer("🔤 أرسل اسم الزر (ما سيراه المستخدم):")
    await state.set_state(Builder.wait_name)

@dp.message(Builder.wait_name)
async def build_step4(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    data = await state.get_data()
    
    if data['type'] == 'folder':
        cursor.execute('INSERT INTO elements (parent_id, type, name, content) VALUES (?, ?, ?, ?)', (data['parent_id'], 'folder', data['name'], 'none'))
        conn.commit()
        await message.answer("✅ تم إنشاء القسم بنجاح!")
        await state.clear()
    else:
        msg = "أرسل محتوى الزر:\n- للنص: اكتب التفاصيل\n- للرابط: أرسل الرابط يبدأ بـ http\n- للصورة: أرسل الصورة هنا مباشرة"
        await message.answer(msg)
        await state.set_state(Builder.wait_content)

@dp.message(Builder.wait_content, F.any)
async def build_step5(message: types.Message, state: FSMContext):
    data = await state.get_data()
    content = ""
    
    if data['type'] == 'media' and message.photo:
        content = message.photo[-1].file_id # جلب آيدي الصورة من سيرفر تليجرام
    else:
        content = message.text
        
    cursor.execute('INSERT INTO elements (parent_id, type, name, content) VALUES (?, ?, ?, ?)', (data['parent_id'], data['type'], data['name'], content))
    conn.commit()
    await message.answer("✅ تم دمج العنصر في النظام بنجاح!")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
  
