import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- النواة البرمجية للمالك المطلق ---
API_TOKEN = os.getenv('BOT_TOKEN')
SUPER_ADMIN = 8333784255  # معرفك الثابت لامتلاك البوت بالكامل
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- تأسيس قاعدة البيانات الذكية ---
conn = sqlite3.connect('sovereign_store.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS elements 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, parent_id INTEGER, type TEXT, name TEXT, content TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()

# --- الحالات البرمجية للبناء والإعداد ---
class SystemStates(StatesGroup):
    wait_name = State()
    wait_type = State()
    wait_content = State()
    wait_broadcast = State()

# --- محرك توليد الأزرار الديناميكي ---
def get_menu_keyboard(user_id, parent_id=0):
    cursor.execute('SELECT id, name, type, content FROM elements WHERE parent_id=?', (parent_id,))
    items = cursor.fetchall()
    
    kb = []
    row = []
    for item in items:
        item_id, name, item_type, content = item
        if item_type == 'link':
            row.append(InlineKeyboardButton(text=name, url=content))
        else:
            row.append(InlineKeyboardButton(text=name, callback_data=f"view_{item_id}"))
        
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
    
    # زر العودة الذكي للأقسام
    if parent_id != 0:
        cursor.execute('SELECT parent_id FROM elements WHERE id=?', (parent_id,))
        gp = cursor.fetchone()
        gp_id = gp[0] if gp else 0
        kb.append([InlineKeyboardButton(text="🔙 رجوع للخلف", callback_data=f"view_{gp_id}")])
    
    # 👑 إضافة زر لوحة التحكم غصباً عن البوت إذا كان المستخدم هو المالك المطلق
    if user_id == SUPER_ADMIN and parent_id == 0:
        kb.append([InlineKeyboardButton(text="👑 لوحة تحكم المالك (الملكية الكاملة)", callback_data="super_admin_panel")])
        
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- أمر التشغيل والترحيب ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    username = f"@{message.from_user.username}" if message.from_user.username else "بلا معرف"
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (message.from_user.id, username))
    conn.commit()
    
    welcome_text = "🔥 مرحباً بك في المتجر الذكي الديناميكي!\n\n"
    if message.from_user.id == SUPER_ADMIN:
        welcome_text += "👑 أهلاً بك يا سيادة المالك المطلق. تم تفعيل كامل صلاحيات الإدارة لك."
    else:
        welcome_text += "تصفح الأقسام والمنتجات المتاحة عبر الأزرار أدناه:"
        
    await message.answer(welcome_text, reply_markup=get_menu_keyboard(message.from_user.id, 0))

# --- معالج العرض والتنقل للأقسام والمنتجات ---
@dp.callback_query(F.data.startswith("view_"))
async def navigate_system(call: types.CallbackQuery):
    target_id = int(call.data.split("_")[1])
    
    if target_id == 0:
        await call.message.edit_text("القائمة الرئيسية:", reply_markup=get_menu_keyboard(call.from_user.id, 0))
        return

    cursor.execute('SELECT type, name, content FROM elements WHERE id=?', (target_id,))
    item = cursor.fetchone()
    if not item: return await call.answer("العنصر غير متوفر!")

    item_type, name, content = item
    
    if item_type == 'folder':
        await call.message.edit_text(f"📂 القسم الحالي: {name}", reply_markup=get_menu_keyboard(call.from_user.id, target_id))
    elif item_type == 'text':
        await call.answer()
        await call.message.answer(f"📦 **{name}**\n\n{content}")
    elif item_type == 'media':
        await call.answer()
        await call.message.answer_photo(photo=content, caption=name)

# --- 👑 نظام لوحة الإدارة المطلقة والتحكم الكامل ---
@dp.callback_query(F.data == "super_admin_panel")
async def super_admin_panel(call: types.CallbackQuery):
    if call.from_user.id != SUPER_ADMIN:
        return await call.answer("❌ محاولة اختراق فاشلة! لا تملك صلاحيات المالك.", show_alert=True)
        
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة عنصر جديد (قسم/منتج)", callback_data="adm_add_element")],
        [InlineKeyboardButton(text="📢 إذاعة وإعلان للكل", callback_data="adm_broadcast"), InlineKeyboardButton(text="📊 إحصائيات دقيقة", callback_data="adm_stats")],
        [InlineKeyboardButton(text="🔙 إغلاق اللوحة", callback_data="view_0")]
    ])
    await call.message.edit_text("⚙️ **بوابة التحكم العليا (صلاحيات المالك المطلقة)**:\nيمكنك إضافة أي شيء والتحكم بالبوت من هنا بالكامل:", reply_markup=kb)

# --- نظام إضافة المحتوى من داخل البوت (الأقسام، الروابط، الميديا، النصوص) ---
@dp.callback_query(F.data == "adm_add_element")
async def build_step1(call: types.CallbackQuery, state: FSMContext):
    cursor.execute("SELECT id, name FROM elements WHERE type='folder'")
    folders = cursor.fetchall()
    
    kb = [[InlineKeyboardButton(text="🔝 في الواجهة الرئيسية", callback_data="setparent_0")]]
    for f in folders:
        kb.append([InlineKeyboardButton(text=f"📁 داخل قسم: {f[1]}", callback_data=f"setparent_{f[0]}")])
        
    await call.message.edit_text("📍 أين تريد وضع هذا الزر أو العنصر الجديد؟", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("setparent_"))
async def build_step2(call: types.CallbackQuery, state: FSMContext):
    pid = int(call.data.split("_")[1])
    await state.update_data(parent_id=pid)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📁 قسم فرعي/مجلد", callback_data="settype_folder"), InlineKeyboardButton(text="📝 نص أو منتج", callback_data="settype_text")],
        [InlineKeyboardButton(text="🔗 رابط خارجي", callback_data="settype_link"), InlineKeyboardButton(text="📸 ميديا (صورة)", callback_data="settype_media")]
    ])
    await call.message.edit_text("⚙️ اختر نوع هذا الزر البرمجي:", reply_markup=kb)

@dp.callback_query(F.data.startswith("settype_"))
async def build_step3(call: types.CallbackQuery, state: FSMContext):
    elem_type = call.data.split("_")[1]
    await state.update_data(type=elem_type)
    await call.message.answer("🔤 أرسل الآن الاسم الذي سيظهر على الزر للمستخدمين:")
    await state.set_state(SystemStates.wait_name)

@dp.message(SystemStates.wait_name)
async def build_step4(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    data = await state.get_data()
    
    if data['type'] == 'folder':
        cursor.execute('INSERT INTO elements (parent_id, type, name, content) VALUES (?, ?, ?, ?)', (data['parent_id'], 'folder', data['name'], 'none'))
        conn.commit()
        await message.answer("✅ تم إنشاء القسم البرمجي الجديد بنجاح!")
        await state.clear()
    else:
        msg = "📥 أرسل المحتوى المطلوب ربطه بالزر:\n- للنص: اكتب تفاصيل الحسابات أو المنتج.\n- للرابط: أرسل رابطاً يبدأ بـ http.\n- للصورة: أرسل الصورة مباشرة في المحادثة."
        await message.answer(msg)
        await state.set_state(SystemStates.wait_content)

@dp.message(SystemStates.wait_content, F.any)
async def build_step5(message: types.Message, state: FSMContext):
    data = await state.get_data()
    content = message.photo[-1].file_id if (data['type'] == 'media' and message.photo) else message.text
        
    cursor.execute('INSERT INTO elements (parent_id, type, name, content) VALUES (?, ?, ?, ?)', (data['parent_id'], data['type'], data['name'], content))
    conn.commit()
    await message.answer("🎯 تم دمج وتثبيت العنصر الجديد داخل البوت بنجاح تام!")
    await state.clear()

# --- الإحصائيات الفورية للمالك ---
@dp.callback_query(F.data == "adm_stats")
async def adm_stats(call: types.CallbackQuery):
    cursor.execute('SELECT COUNT(*) FROM users')
    u_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM elements')
    e_count = cursor.fetchone()[0]
    await call.answer(f"📊 إحصائياتك السيادية:\n👥 إجمالي المستخدمين: {u_count}\n📦 إجمالي الأزرار والعناصر: {e_count}", show_alert=True)

# --- نظام الإذاعة الشامل للبوت للترويج والإعلانات ---
@dp.callback_query(F.data == "adm_broadcast")
async def adm_broadcast(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📝 أرسل نص الرسالة الإعلانية لتبثها فوراً لكل المشتركين:")
    await state.set_state(SystemStates.wait_broadcast)

@dp.message(SystemStates.wait_broadcast)
async def execute_broadcast(message: types.Message, state: FSMContext):
    await message.answer("🔄 جاري البث والنشر تحت سيادتك...")
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    
    success = 0
    for u in users:
        try:
            await bot.send_message(chat_id=u[0], text=message.text)
            success += 1
        except: continue
        
    await message.answer(f"✅ تمت الإذاعة بنجاح ووصلت إلى {success} مستخدم.")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
