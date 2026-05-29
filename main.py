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

MY_ACCOUNT_URL = "https://t.me/xq_7d"  # حسابك الخاص بالدعم
CHANNEL_URL = "https://t.me/drov70"       # قناة التفعيلات

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- تأسيس النواة وقواعد البيانات الشاملة ---
conn = sqlite3.connect('sovereign_store_v6.db', check_same_thread=False)
cursor = conn.cursor()

# جدول المستخدمين مع الرصيد والإحالات والهدية اليومية
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

# جدول المشتريات لحفظ سجل كل مستخدم
cursor.execute('''CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    user_id INTEGER, 
                    item_name TEXT, 
                    purchase_date TEXT)''')
conn.commit()

# --- الحالات (FSM) ---
class SystemStates(StatesGroup):
    wait_name = State()
    wait_type = State()
    wait_content = State()
    wait_broadcast = State()

# --- محرك القائمة الرئيسية المطابق للمخطط 100% ---
def get_main_keyboard(user_id):
    kb = [
        [InlineKeyboardButton(text="🛒 الشراء وتصفح المتجر", callback_data="main_buy")],
        [InlineKeyboardButton(text="💰 شحن رصيد", callback_data="main_charge"), InlineKeyboardButton(text="📦 مشترياتي", callback_data="main_purchases")],
        [InlineKeyboardButton(text="🔗 رابط الإحالة", callback_data="main_referral"), InlineKeyboardButton(text="📢 قناة التفعيلات", url=CHANNEL_URL)],
        [InlineKeyboardButton(text="👨‍💻 الدعم الفني", url=MY_ACCOUNT_URL)]
    ]
    if user_id == SUPER_ADMIN:
        kb.append([InlineKeyboardButton(text="⚙️ الإعدادات وصلاحيات التحكم الكاملة", callback_data="super_admin_panel")])
        
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

    # تسجيل المستخدم أو تحديث بياناته
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
        
    # رسالة الترحيب الرسمية مالتك بعد التعديل وجلب البيانات تلقائياً
    welcome = (
        f"أهلاً بكم في -  Drov TG   👋\n\n"
        f"🚀 أقوى سوق لبيع وشراء حسابات تيليجرام الجاهزة والجديدة لجميع الدول حول العالم 🌐.\n\n"
        f"-  ايديك: `{user_id}` 🆔.\n"
        f"- 👍 رصيدك:  `{user_balance}` نقطة 💵.\n\n"
        f"👍 ابدأ باستخدام البوت الآن بالضغط على الأزرار بالأسفل ⬇️."
    )
    
    # رسالة تنبيه للمالك تظهر بشكل مخفي ومرتب فوق النص الأساسي
    if user_id == SUPER_ADMIN:
        welcome = "👑 **مرحباً بك يا سيادة المالك المطلق (لوحة التحكم متوفرة بالأسفل)**\n\n" + welcome
        
    await message.answer(welcome, reply_markup=get_main_keyboard(user_id), parse_mode="Markdown")

# --- معالجة الأزرار الثابتة حسب المخطط مالتك ---

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

# 1. زر الشراء (عرض الأقسام)
@dp.callback_query(F.data == "main_buy")
async def main_buy(call: types.CallbackQuery):
    await call.message.edit_text("🛒 أقسام المتجر والمنتجات المتوفرة الديناميكية:", reply_markup=get_store_keyboard(0))

# 2. زر شحن الرصيد ونظام الهدية اليومية
@dp.callback_query(F.data == "main_charge")
async def main_charge(call: types.CallbackQuery):
    user_id = call.from_user.id
    cursor.execute('SELECT balance FROM users WHERE user_id=?', (user_id,))
    balance = cursor.fetchone()[0]
    
    text = f"💰 **قسم شحن الرصيد والنقاط**\n\n"
    text += f"💳 رصيدك الحالي: `{balance}` نقطة.\n\n"
    text += "يمكنك تجميع النقاط مجاناً عبر الهدية اليومية، أو التواصل معي مباشرة لشحن الرصيد عبر حسابي."
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 استلام الهدية اليومية الفورية", callback_data="get_daily_gift")],
        [InlineKeyboardButton(text="📥 تواصل معي للشراء والشحن", url=MY_ACCOUNT_URL)],
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
        
        cursor.execute('SELECT balance FROM users WHERE user_id=?', (user_id,))
        balance = cursor.fetchone()[0]
        text = f"💰 **قسم شحن الرصيد والنقاط**\n\n💳 رصيدك الحالي: `{balance}` نقطة.\n\nتم تحديث الرصيد بنجاح!"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎁 استلام الهدية اليومية الفورية", callback_data="get_daily_gift")],
            [InlineKeyboardButton(text="📥 تواصل معي للشراء والشحن", url=MY_ACCOUNT_URL)],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")]
        ])
        try: await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        except: pass

# 3. زر مشترياتي
@dp.callback_query(F.data == "main_purchases")
async def main_purchases(call: types.CallbackQuery):
    user_id = call.from_user.id
    cursor.execute('SELECT item_name, purchase_date FROM purchases WHERE user_id=? ORDER BY id DESC', (user_id,))
    rows = cursor.fetchall()
    
    text = "📦 **سجل مشترياتك من البوت:**\n\n"
    if not rows:
        text += "أنت لم تقم بشراء أي شيء بعد. تصفح قسم الشراء لتسوق منتجاتنا!"
    else:
        for idx, item in enumerate(rows, start=1):
            text += f"{idx}. 🛍 `{item[0]}` - بتاريخ: {item[1]}\n"
            
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")]])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# 4. زر الإحالة
@dp.callback_query(F.data == "main_referral")
async def main_referral(call: types.CallbackQuery):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={call.from_user.id}"
    
    text = "🔗 **نظام الإحالة وتجميع النقاط مجاناً**\n\n"
    text += "شارك الرابط الخاص بك مع أصدقائك، وكل شخص يدخل للبوت عن طريقك ستحصل فوراً على **5 نقاط مجانية** في رصيدك لشراء المنتجات!\n\n"
    text += f"رابطك الخاص:\n`{ref_link}`"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")]])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# --- معالجة الأزرار الديناميكية للتنقل والتصفح الشجري ---
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
    elif item_type == 'text':
        await call.answer()
        cursor.execute('INSERT INTO purchases (user_id, item_name, purchase_date) VALUES (?, ?, ?)', 
                       (call.from_user.id, name, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        await call.message.answer(f"📦 **{name}**\n\n{content}\n\n*(تمت إضافة هذا المنتج إلى سجل مشترياتك بنجاح)*")
    elif item_type == 'media':
        await call.answer()
        cursor.execute('INSERT INTO purchases (user_id, item_name, purchase_date) VALUES (?, ?, ?)', 
                       (call.from_user.id, name, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        await call.message.answer_photo(photo=content, caption=f"📸 {name}\n\n*(تمت إضافة الملف إلى سجل مشترياتك)*")

# --- ⚙️ لوحة الإعدادات والتحكم للمالك فقط ---
@dp.callback_query(F.data == "super_admin_panel")
async def super_admin_panel(call: types.CallbackQuery):
    if call.from_user.id != SUPER_ADMIN:
        return await call.answer("❌ لا تملك هذه الصلاحية السيادية!", show_alert=True)
        
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة عناصر وأزرار جديدة", callback_data="adm_add_element")],
        [InlineKeyboardButton(text="📢 إذاعة رسالة إعلان للكل", callback_data="adm_broadcast"), InlineKeyboardButton(text="📊 إحصائيات البوت كاملة", callback_data="adm_stats")],
        [InlineKeyboardButton(text="🔙 إغلاق اللوحة الإدارية", callback_data="back_to_main")]
    ])
    await call.message.edit_text("⚙️ **لوحة المالك العليا والتحكم المطلق (God Mode)**:\nيمكنك التحكم بمحتوى البوت الشجري بالكامل وإضافة الأزرار من هنا:", reply_markup=kb)

# --- نظام البناء الديناميكي لإضافة أزرار تحت القائمة الشجرية للشراء ---
@dp.callback_query(F.data == "adm_add_element")
async def build_step1(call: types.CallbackQuery, state: FSMContext):
    cursor.execute("SELECT id, name FROM elements WHERE type='folder'")
    folders = cursor.fetchall()
    
    kb = [[InlineKeyboardButton(text="🔝 في واجهة الشراء الأساسية", callback_data="setparent_0")]]
    for f in folders:
        kb.append([InlineKeyboardButton(text=f"📁 داخل قسم: {f[1]}", callback_data=f"setparent_{f[0]}")])
        
    await call.message.edit_text("📍 أين تريد وضع هذا الزر الجديد ضمن شجرة المتجر؟", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("setparent_"))
async def build_step2(call: types.CallbackQuery, state: FSMContext):
    pid = int(call.data.split("_")[1])
    await state.update_data(parent_id=pid)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📁 قسم فرعي جديد", callback_data="settype_folder"), InlineKeyboardButton(text="📝 نص أو منتج معروض", callback_data="settype_text")],
        [InlineKeyboardButton(text="🔗 رابط ويب خارجي", callback_data="settype_link"), InlineKeyboardButton(text="📸 ميديا وصورة منتج", callback_data="settype_media")]
    ])
    await call.message.edit_text("⚙️ اختر نوع هذا الزر المخصص للتثبيت:", reply_markup=kb)

@dp.callback_query(F.data.startswith("settype_"))
async def build_step3(call: types.CallbackQuery, state: FSMContext):
    elem_type = call.data.split("_")[1]
    await state.update_data(type=elem_type)
    await call.message.answer("🔤 أرسل الاسم النصي للزر (الذي سيظهر للزبائن):")
    await state.set_state(SystemStates.wait_name)

@dp.message(SystemStates.wait_name)
async def build_step4(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    data = await state.get_data()
    
    if data['type'] == 'folder':
        cursor.execute('INSERT INTO elements (parent_id, type, name, content) VALUES (?, ?, ?, ?)', (data['parent_id'], 'folder', data['name'], 'none'))
        conn.commit()
        await message.answer("✅ تم إنشاء القسم البرمجي المجلد بنجاح تام!")
        await state.clear()
    else:
        msg = "📥 أرسل الآن المحتوى المطلوب ربطه بهذا الزر:\n- للنصوص: اكتب الكود أو تفاصيل السلعة.\n- للرابط: أرسل الرابط يبدأ بـ http.\n- للصورة: أرسل الصورة فوراً في الشات."
        await message.answer(msg)
        await state.set_state(SystemStates.wait_content)

@dp.message(SystemStates.wait_content, F.any)
async def build_step5(message: types.Message, state: FSMContext):
    data = await state.get_data()
    content = message.photo[-1].file_id if (data['type'] == 'media' and message.photo) else message.text
        
    cursor.execute('INSERT INTO elements (parent_id, type, name, content) VALUES (?, ?, ?, ?)', (data['parent_id'], data['type'], data['name'], content))
    conn.commit()
    await message.answer("🎯 تم تثبيت الزر الجديد بنجاح مذهل ضمن هيكلية المتجر!")
    await state.clear()

# --- إحصائيات فورية للمالك ---
@dp.callback_query(F.data == "adm_stats")
async def adm_stats(call: types.CallbackQuery):
    cursor.execute('SELECT COUNT(*) FROM users')
    u_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM elements')
    e_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM purchases')
    p_count = cursor.fetchone()[0]
    
    stat_text = f"📊 **إحصائيات متجرك السيادي:**\n\n👥 إجمالي المستخدمين المسجلين: `{u_count}`\n📦 إجمالي أزرار المتجر المخصصة: `{e_count}`\n🛍 إجمالي عمليات الشراء المسجلة: `{p_count}`"
    await call.message.answer(stat_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 عودة للإعدادات", callback_data="super_admin_panel")]]), parse_mode="Markdown")

# --- نظام الإذاعة الشامل للبوت للترويج والإعلانات ---
@dp.callback_query(F.data == "adm_broadcast")
async def adm_broadcast(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📝 أرسل نص الرسالة الإعلانية لتبثها فوراً لكل المشتركين:")
    await state.set_state(SystemStates.wait_broadcast)

@dp.message(SystemStates.wait_broadcast)
async def execute_broadcast(message: types.Message, state: FSMContext):
    await message.answer("🔄 جاري البث والنشر للمشتركين...")
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
  
