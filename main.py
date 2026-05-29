import os
import sqlite3
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- الإعدادات الثابتة مالتنا ---
API_TOKEN = os.getenv('BOT_TOKEN')
SUPER_ADMIN = 8333784255  # معرف المالك المطلق (أنت)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- تأسيس النواة وقواعد البيانات الشاملة ---
conn = sqlite3.connect('sovereign_store_v6.db', check_same_thread=False)
cursor = conn.cursor()

# جدول المستخدمين
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY, 
                    username TEXT, 
                    balance REAL DEFAULT 0.0, 
                    referred_by INTEGER,
                    last_gift_date TEXT)''')

# جدول الأزرار والأقسام الديناميكية
cursor.execute('''CREATE TABLE IF NOT EXISTS elements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    parent_id INTEGER DEFAULT 0, 
                    type TEXT, 
                    name TEXT, 
                    content TEXT)''')

# جدول المشتريات
cursor.execute('''CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    user_id INTEGER, 
                    item_name TEXT, 
                    purchase_date TEXT)''')

# جدول الإعدادات العامة (لحفظ الروابط ديناميكياً بدون كود)
cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY, 
                    value TEXT)''')

# إدخال الروابط الافتراضية إذا لم تكن موجودة
cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('support_url', 'https://t.me/xq_7d')")
cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('channel_url', 'https://t.me/drov70')")
conn.commit()

# --- جلب الروابط ديناميكياً من قاعدة البيانات ---
def get_setting(key):
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    res = cursor.fetchone()
    return res[0] if res else ""

# --- الحالات (FSM) المطورة كاملة ---
class SystemStates(StatesGroup):
    wait_name = State()
    wait_type = State()
    wait_content = State()
    wait_broadcast = State()
    edit_button_name = State()
    edit_button_new_name = State()
    edit_channel_link = State()
    edit_support_link = State()

# --- محرك القائمة الرئيسية المطابق للمخطط 100% ---
def get_main_keyboard(user_id):
    kb = [
        [InlineKeyboardButton(text="🛒 الشراء وتصفح المتجر", callback_data="main_buy")],
        [InlineKeyboardButton(text="💰 شحن رصيد", callback_data="main_charge"), InlineKeyboardButton(text="📦 مشترياتي", callback_data="main_purchases")],
        [InlineKeyboardButton(text="🔗 رابط الإحالة", callback_data="main_referral"), InlineKeyboardButton(text="📢 قناة التفعيلات", url=get_setting('channel_url'))],
        [InlineKeyboardButton(text="👨‍💻 الدعم الفني", url=get_setting('support_url'))]
    ]
    if user_id == SUPER_ADMIN:
        kb.append([InlineKeyboardButton(text="⚙️ لوحة الإعدادات وصلاحيات التحكم الكاملة", callback_data="super_admin_panel")])
        
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- محرك توليد أزرار المنتجات الديناميكية داخل المتجر ---
def get_store_keyboard(parent_id=0):
    cursor.execute('SELECT id, name, type, content FROM elements WHERE parent_id=?', (parent_id,))
    items = cursor.fetchall()
    kb = []
    row = []
    for item in items:
        item_id, name, item_type, content = item
        if item_type == 'link':
            row.append(InlineKeyboardButton(text=f"🔗 {name}", url=content))
        elif item_type == 'folder':
            row.append(InlineKeyboardButton(text=f"📁 {name}", callback_data=f"view_{item_id}"))
        else:
            row.append(InlineKeyboardButton(text=f"💎 {name}", callback_data=f"view_{item_id}"))
            
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
    
    if parent_id != 0:
        cursor.execute('SELECT parent_id FROM elements WHERE id=?', (parent_id,))
        gp = cursor.fetchone()
        gp_id = gp[0] if gp else 0
        kb.append([InlineKeyboardButton(text="🔙 رجوع للخلف", callback_data=f"view_{gp_id}")])
    else:
        kb.append([InlineKeyboardButton(text="🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")])
        
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- أمر البداية مع رسالة الترحيب المخصصة مالتك ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "بلا معرف"
    
    args = message.text.split()
    referred_by = None
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        if referrer_id != user_id:
            referred_by = referrer_id

    cursor.execute('SELECT user_id, balance FROM users WHERE user_id=?', (user_id,))
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute('INSERT INTO users (user_id, username, referred_by) VALUES (?, ?, ?)', (user_id, username, referred_by))
        conn.commit()
        user_balance = 0.0
        if referred_by:
            cursor.execute('UPDATE users SET balance = balance + 5 WHERE user_id=?', (referred_by,))
            conn.commit()
            try:
                await bot.send_message(chat_id=referred_by, text=f"🎉 قام {username} بالدخول للبوت عبر رابطك، وتمت إضافة 5 نقاط لرصيدك!")
            except: pass
    else:
        user_balance = exists[1]
        cursor.execute('UPDATE users SET username=? WHERE user_id=?', (username, user_id))
        conn.commit()
        
    welcome = (
        f"أهلاً بكم في -  Drov TG   👋\n\n"
        f"🚀 أقوى سوق لبيع وشراء حسابات تيليجرام الجاهزة والجديدة لجميع الدول حول العالم 🌐.\n\n"
        f"-  ايديك: `{user_id}` 🆔.\n"
        f"- 👍 رصيدك:  `{user_balance}` نقطة 💵.\n\n"
        f"👍 ابدأ باستخدام البوت الآن بالضغط على الأزرار بالأسفل ⬇️."
    )
    
    if user_id == SUPER_ADMIN:
        welcome = "👑 **مرحباً بك يا سيادة المالك المطلق (لوحة التحكم متوفرة بالأسفل)**\n\n" + welcome
        
    await message.answer(welcome, reply_markup=get_main_keyboard(user_id), parse_mode="Markdown")

# --- معالجة الأزرار الثابتة ---
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(call: types.CallbackQuery):
    user_id = call.from_user.id
    cursor.execute('SELECT balance FROM users WHERE user_id=?', (user_id,))
    user_balance = cursor.fetchone()[0]
    
    welcome = (
        f"أهلاً بكم في -  Drov TG   👋\n\n"
        f"🚀 أقوى سوق لبيع وشراء حسابات تيليجرام الجاهزة والجديدة لجميع الدول حول العالم 🌐.\n\n"
        f"-  ايديك: `{user_id}` 🆔.\n"
        f"- 👍 رصيدك:  `{user_balance}` نقطة 💵.\n\n"
        f"👍 ابدأ باستخدام البوت الآن بالضغط على الأزرار بالأسفل ⬇️."
    )
    await call.message.edit_text(welcome, reply_markup=get_main_keyboard(user_id), parse_mode="Markdown")

@dp.callback_query(F.data == "main_buy")
async def main_buy(call: types.CallbackQuery):
    await call.message.edit_text("🛒 أقسام المتجر والمنتجات المتوفرة الديناميكية:", reply_markup=get_store_keyboard(0))

@dp.callback_query(F.data == "main_charge")
async def main_charge(call: types.CallbackQuery):
    user_id = call.from_user.id
    cursor.execute('SELECT balance FROM users WHERE user_id=?', (user_id,))
    balance = cursor.fetchone()[0]
    
    text = f"💰 **قسم شحن الرصيد والنقاط**\n\n💳 رصيدك الحالي: `{balance}` نقطة.\n\nيمكنك تجميع النقاط مجاناً عبر الهدية اليومية، أو التواصل معي مباشرة لشحن الرصيد عبر حسابي."
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 استلام الهدية اليومية الفورية", callback_data="get_daily_gift")],
        [InlineKeyboardButton(text="📥 تواصل معي للشراء والشحن", url=get_setting('support_url'))],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "get_daily_gift")
async def get_daily_gift(call: types.CallbackQuery):
    user_id = call.from_user.id
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute('SELECT last_gift_date FROM users WHERE user_id=?', (user_id,))
    last_date = cursor.fetchone()[0]
    
    if last_date == today_str:
        await call.answer("❌ لقد قمت باستلام هديتك اليومية بالفعل! عد غداً يا بطل.", show_alert=True)
    else:
        cursor.execute('UPDATE users SET balance = balance + 1, last_gift_date=? WHERE user_id=?', (today_str, user_id))
        conn.commit()
        await call.answer("🎉 مبروك! حصلت على 1 نقطة مجانية كهدية يومية.", show_alert=True)
        await main_charge(call)

@dp.callback_query(F.data == "main_purchases")
async def main_purchases(call: types.CallbackQuery):
    user_id = call.from_user.id
    cursor.execute('SELECT item_name, purchase_date FROM purchases WHERE user_id=? ORDER BY id DESC', (user_id,))
    rows = cursor.fetchall()
    text = "📦 **سجل مشترياتك من البوت:**\n\n"
    if not rows:
        text += "أنت لم تقم بشراء أي شيء بعد."
    else:
        for idx, item in enumerate(rows, start=1):
            text += f"{idx}. 🛍 `{item[0]}` - بتاريخ: {item[1]}\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")]])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "main_referral")
async def main_referral(call: types.CallbackQuery):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={call.from_user.id}"
    text = f"🔗 **نظام الإحالة وتجميع النقاط مجاناً**\n\nشارك رابطك وخذ **5 نقاط مجانية** لكل صديق يسجل!\n\nرابطك الخاص:\n`{ref_link}`"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")]])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("view_"))
async def navigate_system(call: types.CallbackQuery):
    target_id = int(call.data.split("_")[1])
    if target_id == 0:
        await call.message.edit_text("🛒 أقسام المتجر الأساسية:", reply_markup=get_store_keyboard(0))
        return
    cursor.execute('SELECT type, name, content FROM elements WHERE id=?', (target_id,))
    item = cursor.fetchone()
    if not item: return await call.answer("العنصر المطلوب غير متوفر حالياً!")
    item_type, name, content = item
    
    if item_type == 'folder':
        await call.message.edit_text(f"📂 قسم: {name}", reply_markup=get_store_keyboard(target_id))
    else:
        await call.answer()
        cursor.execute('INSERT INTO purchases (user_id, item_name, purchase_date) VALUES (?, ?, ?)', (call.from_user.id, name, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        if item_type == 'media':
            await call.message.answer_photo(photo=content, caption=f"📸 {name}\n\n*(تمت إضافة الملف إلى مشترياتك)*")
        else:
            await call.message.answer(f"📦 **{name}**\n\n{content}")

# ================= ⚙️ لوحة الإعدادات الشاملة (مثل z81bot) =================

@dp.callback_query(F.data == "super_admin_panel")
async def super_admin_panel(call: types.CallbackQuery):
    if call.from_user.id != SUPER_ADMIN: return await call.answer("❌ صلاحية مرفوضة", show_alert=True)
    
    kb = [
        [InlineKeyboardButton(text="➕ إضافة عنصر جديد", callback_data="adm_add_element")],
        [InlineKeyboardButton(text="✏️ تعديل اسم زر", callback_data="adm_edit_button"), InlineKeyboardButton(text="🗑 حذف زر", callback_data="adm_delete_button")],
        [InlineKeyboardButton(text="📢 إذاعة رسالة للكل", callback_data="adm_broadcast"), InlineKeyboardButton(text="📊 إحصائيات البوت كاملة", callback_data="adm_stats")],
        [InlineKeyboardButton(text="🔗 تعديل رابط القناة", callback_data="change_channel"), InlineKeyboardButton(text="👨‍💻 تعديل رابط الدعم", callback_data="change_support")],
        [InlineKeyboardButton(text="🔙 إغلاق اللوحة", callback_data="back_to_main")]
    ]
    await call.message.edit_text("👑 **مرحباً بك في لوحة التحكم الإدارية المطلقة**\nالتحكم الآن بالكامل من الأزرار بدون الحاجة لتعديل الكود:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- تكتيك التعديل والحذف الذكي (بدون كتابة ID يدوياً) ---
def get_admin_elements_keyboard(action_prefix):
    cursor.execute("SELECT id, name, type FROM elements")
    items = cursor.fetchall()
    kb = []
    for item_id, name, item_type in items:
        symbol = "📁" if item_type == "folder" else "💎"
        kb.append([InlineKeyboardButton(text=f"{symbol} {name}", callback_data=f"{action_prefix}_{item_id}")])
    kb.append([InlineKeyboardButton(text="🔙 عودة للوحة التحكم", callback_data="super_admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.callback_query(F.data == "adm_edit_button")
async def edit_button_list(call: types.CallbackQuery):
    await call.message.edit_text("✏️ **اختر الزر المراد تعديل اسمه فوراً من القائمة أدناه:**", reply_markup=get_admin_elements_keyboard("click_edit"))

@dp.callback_query(F.data.startswith("click_edit_"))
async def get_button_to_edit(call: types.CallbackQuery, state: FSMContext):
    button_id = int(call.data.split("_")[2])
    cursor.execute("SELECT name FROM elements WHERE id=?", (button_id,))
    res = cursor.fetchone()
    await state.update_data(button_id=button_id)
    await call.message.answer(f"📝 الاسم الحالي للزر هو: **{res[0]}**\n\nأرسل الآن الاسم الجديد الذي تريده:")
    await state.set_state(SystemStates.edit_button_new_name)

@dp.message(SystemStates.edit_button_new_name)
async def save_new_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    button_id = data['button_id']
    new_name = message.text
    cursor.execute("UPDATE elements SET name=? WHERE id=?", (new_name, button_id))
    conn.commit()
    await message.answer(f"✅ تم تغيير اسم الزر بنجاح إلى: **{new_name}**")
    await state.clear()

@dp.callback_query(F.data == "adm_delete_button")
async def delete_button_list(call: types.CallbackQuery):
    await call.message.edit_text("🗑 **اختر الزر المراد حذفه نهائياً بلمسة واحدة:**", reply_markup=get_admin_elements_keyboard("click_delete"))

@dp.callback_query(F.data.startswith("click_delete_"))
async def perform_button_delete(call: types.CallbackQuery):
    button_id = int(call.data.split("_")[2])
    cursor.execute("DELETE FROM elements WHERE id=?", (button_id,))
    conn.commit()
    await call.answer("✅ تم حذف الزر وكل محتوياته من المتجر!", show_alert=True)
    await call.message.edit_text("🗑 **اختر الزر المراد حذفه نهائياً بلمسة واحدة:**", reply_markup=get_admin_elements_keyboard("click_delete"))

# --- تعديل الروابط ديناميكياً من داخل البوت (تعديل القناة والدعم) ---
@dp.callback_query(F.data == "change_channel")
async def change_channel_cmd(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(f"🔗 الرابط الحالي للقناة هو: {get_setting('channel_url')}\n\nأرسل الآن الرابط الجديد بالكامل:")
    await state.set_state(SystemStates.edit_channel_link)

@dp.message(SystemStates.edit_channel_link)
async def save_channel_link(message: types.Message, state: FSMContext):
    if not message.text.startswith("http"):
        return await message.answer("❌ خطأ! يجب أن يبدأ الرابط بـ http أو https. أعد الإرسال:")
    cursor.execute("UPDATE settings SET value=? WHERE key='channel_url'", (message.text,))
    conn.commit()
    await message.answer(f"✅ تم تحديث رابط القناة بنجاح إلى:\n{message.text}")
    await state.clear()

@dp.callback_query(F.data == "change_support")
async def change_support_cmd(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(f"👨‍💻 رابط الدعم الحالي هو: {get_setting('
                                                                     
