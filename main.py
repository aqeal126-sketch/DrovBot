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
ADMIN_ID = 8333784255  # معرف المطور الخاص بك
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- إنشاء وتحديث قاعدة البيانات الاحترافية ---
conn = sqlite3.connect('pro_store.db', check_same_thread=False)
cursor = conn.cursor()

# جدول الأزرار والمنتجات (الشجرية)
cursor.execute('''CREATE TABLE IF NOT EXISTS store 
                  (id INTEGER PRIMARY KEY AUTO_INCREMENT, name TEXT, content TEXT, parent_id INTEGER)''')

# جدول المستخدمين والحماية
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, username TEXT, is_blocked BOOLEAN DEFAULT 0)''')

# جدول الصفحات الثابتة
cursor.execute('''CREATE TABLE IF NOT EXISTS pages 
                  (slug TEXT PRIMARY KEY, title TEXT, content TEXT)''')

# إدخال الصفحات الافتراضية إذا لم تكن موجودة
cursor.executemany('INSERT OR IGNORE INTO pages (slug, title, content) VALUES (?, ?, ?)', [
    ('about', '📜 من نحن', 'مرحباً بك في متجرنا الرقمي الاحترافي.'),
    ('terms', '📋 الشروط', 'شروط الاستخدام: يرجى احترام سياسات المتجر.'),
    ('privacy', '🔒 سياسة الخصوصية', 'بياناتك آمنة ومشفرة لدينا بالكامل.')
])
conn.commit()

# --- حالات لوحة التحكم (FSM) ---
class AdminStates(StatesGroup):
    waiting_for_btn_name = State()
    waiting_for_btn_content = State()
    waiting_for_broadcast = State()
    waiting_for_page_content = State()

# --- دالة الواجهة الرئيسية (تظهر للجميع) ---
def get_main_keyboard():
    # جلب الأزرار الرئيسية من المجلد الرئيسي (parent_id = 0)
    cursor.execute('SELECT id, name FROM store WHERE parent_id=0')
    items = cursor.fetchall()
    
    keyboard = []
    # ترتيب الأزرار بشكل ثنائي
    row = []
    for item_id, name in items:
        row.append(InlineKeyboardButton(text=name, callback_data=f"open_{item_id}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    # إضافة الصفحات الثابتة أسفل المنتجات
    keyboard.append([
        InlineKeyboardButton(text="📜 من نحن", callback_data="page_about"),
        InlineKeyboardButton(text="📋 الشروط", callback_data="page_terms")
    ])
    
    # زر لوحة التحكم يظهر للجميع "غصباً عن البوت" لإظهار الاحترافية
    keyboard.append([InlineKeyboardButton(text="⚙️ لوحة التحكم", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# --- أمر التشغيل البداية ---
@dp.message(Command("start"))
async def start_command(message: types.Message):
    # حفظ المستخدم تلقائياً في قاعدة البيانات
    username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد"
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (message.from_user.id, username))
    conn.commit()
    
    # طباعة في الـ Logs للتأكد التام
    print(f"PRO_DEBUG: User {message.from_user.id} started the bot.")
    
    await message.answer("🔥 أهلاً بك في المتجر الرقمي المتكامل!\nاختر ما تريده من الأزرار أدناه:", reply_markup=get_main_keyboard())

# --- حماية لوحة التحكم والتنقل بين أقسام الملحقات ---
@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: types.CallbackQuery):
    # جدار الحماية: إذا لم يكن الآيدي مطابقاً لك
    if call.from_user.id != ADMIN_ID:
        await call.answer("❌ عذراً عزيزي، هذه اللوحة مخصصة لمالك البوت فقط!", show_alert=True)
        return
        
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 المستخدمون", callback_data="admin_users"), InlineKeyboardButton(text="🛒 المنتجات والأقسام", callback_data="admin_products")],
        [InlineKeyboardButton(text="🎨 إدارة الأزرار", callback_data="admin_buttons"), InlineKeyboardButton(text="📢 الإعلانات والإذاعة", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📑 الصفحات", callback_data="admin_pages"), InlineKeyboardButton(text="🛡 حماية النظام", callback_data="admin_security")],
        [InlineKeyboardButton(text="🔙 العودة للمتجر", callback_data="to_main")]
    ])
    await call.message.edit_text("⚙️ **أهلاً بك يا مطور في لوحة التحكم الشاملة**\nإليك صلاحيات النظام الكاملة:", reply_markup=kb, parse_mode="Markdown")

# --- 1) قسم المستخدمين ---
@dp.callback_query(F.data == "admin_users")
async def admin_users(call: types.CallbackQuery):
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 قائمة الأعضاء", callback_data="list_users")],
        [InlineKeyboardButton(text="🔙 عودة للوحة", callback_data="admin_panel")]
    ])
    await call.message.edit_text(f"👥 **إدارة المستخدمين**\n\n📊 إجمالي المشتركين في البوت: {total_users}", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "list_users")
async def list_users(call: types.CallbackQuery):
    cursor.execute('SELECT user_id, username FROM users LIMIT 10')
    users = cursor.fetchall()
    text = "📋 **أخر 10 مستخدمين تفاعلوا مع البوت:**\n\n"
    for uid, uname in users:
        text += f"👤 ID: `{uid}` -> {uname}\n"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 عودة", callback_data="admin_users")]])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# --- 2) قسم الإعلانات والإذاعة ---
@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 إذاعة نصية للجميع", callback_data="start_broadcast")],
        [InlineKeyboardButton(text="🔙 عودة", callback_data="admin_panel")]
    ])
    await call.message.edit_text("📢 **قسم الإعلانات والإذاعة الذكية**", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "start_broadcast")
async def start_broadcast(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📝 أرسل الآن نص الإعلان الذي تريد توجيهه لجميع المشتركين:")
    await state.set_state(AdminStates.waiting_for_broadcast)

@dp.message(AdminStates.waiting_for_broadcast)
async def run_broadcast(message: types.Message, state: FSMContext):
    await message.answer("🔄 جاري بدء البث والنشر...")
    cursor.execute('SELECT user_id FROM users')
    all_users = cursor.fetchall()
    
    success = 0
    for user in all_users:
        try:
            await bot.send_message(chat_id=user[0], text=message.text)
            success += 1
        except:
            continue
            
    await message.answer(f"✅ **تمت الإذاعة بنجاح!**\nوصلت الرسالة إلى {success} مستخدم بنجاح.")
    await state.clear()

# --- 3) قسم الأزرار والمنتجات الشجرية (إضافة زر داخل زر) ---
@dp.callback_query(F.data == "admin_buttons")
@dp.callback_query(F.data == "admin_products")
async def admin_buttons_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة زر (رئيسي أو فرعي)", callback_data="add_btn_select")],
        [InlineKeyboardButton(text="🔙 عودة", callback_data="admin_panel")]
    ])
    await call.message.edit_text("🎨 **إدارة المنتجات والأزرار الديناميكية**\nيمكنك التحكم بشجرة الأزرار هنا.", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "add_btn_select")
async def add_btn_select(call: types.CallbackQuery, state: FSMContext):
    # جلب المجلدات الحالية ليتسنى له الإضافة داخلها كزر فرعي
    cursor.execute("SELECT id, name FROM store WHERE content = 'folder'")
    folders = cursor.fetchall()
    
    kb = [[InlineKeyboardButton(text="🔝 جعله زر رئيسي (قائمة أولى)", callback_data="set_parent_0")]]
    for fid, fname in folders:
        kb.append([InlineKeyboardButton(text=f"📁 داخل قسم: {fname}", callback_data=f"set_parent_{fid}")])
    kb.append([InlineKeyboardButton(text="🔙 إلغاء", callback_data="admin_buttons")])
    
    await call.message.edit_text("📍 حدد أين تريد وضع هذا الزر الجديد:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("set_parent_"))
async def set_parent_id(call: types.CallbackQuery, state: FSMContext):
    pid = int(call.data.split("_")[2])
    await state.update_data(parent_id=pid)
    await call.message.answer("🔤 أرسل الآن **اسم الزر الجديد** (الذي سيظهر للمستخدم):")
    await state.set_state(AdminStates.waiting_for_btn_name)

@dp.message(AdminStates.waiting_for_btn_name)
async def get_btn_name(message: types.Message, state: FSMContext):
    await state.update_data(btn_name=message.text)
    await message.answer("📥 أرسل **محتوى الزر**:\n\n💡 *ملاحظة:* إذا كنت تريد جعل هذا الزر عبارة عن (قسم) يفتح أزراراً فرعية بداخله، أكتب كلمة `folder` فقط.")
    await state.set_state(AdminStates.waiting_for_btn_content)

@dp.message(AdminStates.waiting_for_btn_content)
async def save_pro_btn(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cursor.execute('INSERT INTO store (name, content, parent_id) VALUES (?, ?, ?)', 
                   (data['btn_name'], message.text, data['parent_id']))
    conn.commit()
    await message.answer("🎯 **عاش يا بطل! تم إنشاء وتثبيت الزر بنجاح في قاعدة البيانات.**")
    await state.clear()

# --- تصفح الأزرار والمنتجات من قبل المستخدمين ---
@dp.callback_query(F.data.startswith("open_"))
async def open_store_item(call: types.CallbackQuery):
    item_id = int(call.data.split("_")[1])
    cursor.execute('SELECT name, content FROM store WHERE id=?', (item_id,))
    item = cursor.fetchone()
    
    if not item:
        await call.answer("❌ هذا المنتج غير متوفر حالياً.")
        return
        
    name, content = item[0], item[1]
    
    if content == "folder":
        # إذا كان مجلداً، نجلب الأزرار التابعة له (الأزرار الفرعية)
        cursor.execute('SELECT id, name FROM store WHERE parent_id=?', (item_id,))
        sub_items = cursor.fetchall()
        
        kb = []
        for sid, sname in sub_items:
            kb.append([InlineKeyboardButton(text=sname, callback_data=f"open_{sid}")])
        kb.append([InlineKeyboardButton(text="🔙 العودة للقائمة الرئيسية", callback_data="to_main")])
        
        await call.message.edit_text(f"📁 القسم: {name}\nاختر من الأفرع المتاحة المضافة من المطور:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    else:
        # إذا كان منتجاً، يعرض محتواه (ملف، رابط، نص) في تنبيه ذكي
        await call.message.answer(f"📦 **تفاصيل المنتج ({name}):**\n\n{content}", parse_mode="Markdown")
        await call.answer()

# --- عرض الصفحات الثابتة ---
@dp.callback_query(F.data.startswith("page_"))
async def show_page(call: types.CallbackQuery):
    slug = call.data.split("_")[1]
    cursor.execute('SELECT title, content FROM pages WHERE slug=?', (slug,))
    page = cursor.fetchone()
    if page:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 عودة للمتجر", callback_data="to_main")]])
        await call.message.edit_text(f"✨ **{page[0]}**\n\n{page[1]}", reply_markup=kb, parse_mode="Markdown")

# --- العودة للرئيسية ---
@dp.callback_query(F.data == "to_main")
async def back_to_main_menu(call: types.CallbackQuery):
    await call.message.edit_text("🔥 أهلاً بك في المتجر الرقمي المتكامل!\nاختر ما تريده من الأزرار أدناه:", reply_markup=get_main_keyboard())

# --- تشغيل البوت الاحترافي ---
async def main():
    print("🚀 PRO BOT IS ALIVE AND RUNNING...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
