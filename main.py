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

MY_ACCOUNT_URL = "https://t.me/xq_7d"   # حسابك الخاص بالدعم
CHANNEL_URL = "https://t.me/drov70"        # قناة التفعيلات
REQ_CHANNEL_ID = "@drov8"                  # معرف قناة الاشتراك الإجباري
REQ_CHANNEL_URL = "https://t.me/drov8"     # رابط قناة الاشتراك الإجباري

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- تأسيس النواة وقواعد البيانات الشاملة ---
conn = sqlite3.connect('sovereign_store_v9.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY, 
                    username TEXT, 
                    balance REAL DEFAULT 0.0, 
                    referred_by INTEGER,
                    last_gift_date TEXT)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS elements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    parent_id INTEGER DEFAULT 0, 
                    type TEXT, 
                    name TEXT, 
                    content TEXT)''')

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
    wait_new_name = State() 

# --- دالة فحص الاشتراك الإجباري ---
async def is_subscribed(user_id: int) -> bool:
    if user_id == SUPER_ADMIN:
        return True  
    try:
        member = await bot.get_chat_member(chat_id=REQ_CHANNEL_ID, user_id=user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception:
        return True

# --- كيبورد تنبيه الاشتراك الإجباري ---
def get_join_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 اضغط هنا للاشتراك في القناة", url=REQ_CHANNEL_URL)],
        [InlineKeyboardButton(text="🔄 تأكيد الاشتراك والتشغيل", callback_data="check_subscription")]
    ])

# --- محرك القائمة الرئيسية ---
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

# --- محرك توليد أزرار المنتجات ---
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

# --- محرك إدارة الأزرار للمالك ---
def get_manage_keyboard(parent_id=0):
    cursor.execute('SELECT id, name, type FROM elements WHERE parent_id=?', (parent_id,))
    items = cursor.fetchall()
    kb = []
    for item in items:
        item_id, name, item_type = item
        icon = "📁" if item_type == 'folder' else "🔗" if item_type == 'link' else "💎"
        kb.append([InlineKeyboardButton(text=f"{icon} {name} (إدارة)", callback_data=f"manage_item_{item_id}")])
    
    if parent_id != 0:
        cursor.execute('SELECT parent_id FROM elements WHERE id=?', (parent_id,))
        gp_id = cursor.fetchone()[0]
        kb.append([InlineKeyboardButton(text="🔙 رجوع للخلف", callback_data=f"manage_dir_{gp_id}")])
    else:
        kb.append([InlineKeyboardButton(text="🔙 عودة للوحة التحكم", callback_data="super_admin_panel")])
        
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- أمر البداية مع رسالة الترحيب المخصصة ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "بلا معرف"
    
    if not await is_subscribed(user_id):
        return await message.answer(
            f"أهلاً بكم في -  Drov TG   👋\n\n❌ عذراً عزيزي، يجب عليك الاشتراك في قناة البوت الرسمية أولاً لتتمكن من استخدامه!\n\nإشترك هنا: {REQ_CHANNEL_URL}\nثم اضغط على زر التأكيد أدناه👇",
            reply_markup=get_join_keyboard()
        )

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

# --- معالج التحقق من الاشتراك الإجباري ---
@dp.callback_query(F.data == "check_subscription")
async def check_subscription(call: types.CallbackQuery):
    if await is_subscribed(call.from_user.id):
        await call.answer("✅ تم التحقق بنجاح! تم تفعيل البوت لك.", show_alert=True)
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
    else:
        await call.answer("❌ أنت غير مشترك في القناة حالياً! اشترك أولاً ثم اضغط مجدداً.", show_alert=True)

# --- جدار الحماية الرئيسي الشامل لجميع ضغطات الأزرار (Callback Queries) ---
@dp.callback_query()
async def global_callback_guard(call: types.CallbackQuery, state: FSMContext):
    if call.data == "check_subscription":
        return
        
    if not await is_subscribed(call.from_user.id):
        await call.answer("❌ عذراً! تم تقييد حسابك، يرجى الاشتراك في القناة أولاً لاستخدام أزرار البوت.", show_alert=True)
        try:
            await call.message.answer(
                f"❌ يجب عليك الاشتراك في قناة البوت الرسمية أولاً لتتمكن من استخدام الأزرار:\n\nإشترك هنا: {REQ_CHANNEL_URL}",
                reply_markup=get_join_keyboard()
            )
        except: pass
        return

    data = call.data
    
    if data == "back_to_main":
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

    elif data == "main_buy":
        await call.message.edit_text("🛒 أقسام المتجر والمنتجات المتوفرة الديناميكية:", reply_markup=get_store_keyboard(0))

    elif data == "main_charge":
        user_id = call.from_user.id
        cursor.execute('SELECT balance FROM users WHERE user_id=?', (user_id,))
        balance = cursor.fetchone()[0]
        text = f"💰 **قسم شحن الرصيد والنقاط**\n\n💳 رصيدك الحالي: `{balance}` نقطة.\n\nيمكنك تجميع النقاط مجاناً عبر الهدية اليومية، أو التواصل معي مباشرة لشحن الرصيد عبر حسابي."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎁 استلام الهدية اليومية الفورية", callback_data="get_daily_gift")],
            [InlineKeyboardButton(text="📥 تواصل معي للشراء والشحن", url=MY_ACCOUNT_URL)],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")]
        ])
        await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

    elif data == "get_daily_gift":
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

    elif data == "main_purchases":
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

    elif data == "main_referral":
        bot_info = await bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={call.from_user.id}"
        text = "🔗 **نظام الإحالة وتجميع النقاط مجاناً**\n\n"
        text += "شارك الرابط الخاص بك مع أصدقائك، وكل شخص يدخل للبوت عن طريقك ستحصل فوراً على **5 نقاط مجانية** في رصيدك لشراء المنتجات!\n\n"
        text += f"رابطك الخاص:\n`{ref_link}`"
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")]])
        await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

    elif data.startswith("view_"):
        target_id = int(data.split("_")[1])
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
            cursor.execute('INSERT INTO purchases (user_id, item_name, purchase_date) VALUES (?, ?, ?)', (call.from_user.id, name, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            await call.message.answer(f"📦 **{name}**\n\n{content}\n\n*(تمت إضافة هذا المنتج إلى سجل مشترياتك بنجاح)*")
        elif item_type == 'media':
            await call.answer()
            cursor.execute('INSERT INTO purchases (user_id, item_name, purchase_date) VALUES (?, ?, ?)', (call.from_user.id, name, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            await call.message.answer_photo(photo=content, caption=f"📸 {name}\n\n*(تمت إضافة الملف إلى سجل مشترياتك)*")

    elif data == "super_admin_panel":
        if call.from_user.id != SUPER_ADMIN: return await call.answer("❌ لا تملك هذه الصلاحية السيادية!", show_alert=True)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ إضافة عناصر وأزرار جديدة", callback_data="adm_add_element")],
            [InlineKeyboardButton(text="⚙️ تعديل وحذف الأزرار الحالية", callback_data="manage_dir_0")],
            [InlineKeyboardButton(text="📢 إذاعة رسالة إعلان للكل", callback_data="adm_broadcast"), InlineKeyboardButton(text="📊 إحصائيات البوت كاملة", callback_data="adm_stats")],
            [InlineKeyboardButton(text="🔙 إغلاق اللوحة الإدارية", callback_data="back_to_main")]
        ])
        await call.message.edit_text("⚙️ **لوحة التحكم العليا وإدارة الأزرار:**", reply_markup=kb)

    elif data.startswith("manage_dir_"):
        if call.from_user.id != SUPER_ADMIN: return
        pid = int(data.split("_")[2])
        await call.message.edit_text("⚙️ اختر الزر الذي تريد **تعديله** أو **حذفه** من الشجرة أدناه:", reply_markup=get_manage_keyboard(pid))

    elif data.startswith("manage_item_"):
        if call.from_user.id != SUPER_ADMIN: return
        item_id = int(data.split("_")[2])
        cursor.execute("SELECT name, type, parent_id FROM elements WHERE id=?", (item_id,))
        item = cursor.fetchone()
        if not item: return await call.answer("الزر غير موجود!")
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ تعديل اسم هذا الزر", callback_data=f"editname_{item_id}")],
            [InlineKeyboardButton(text="🗑 حذف هذا الزر نهائياً", callback_data=f"delitem_{item_id}")],
            [InlineKeyboardButton(text="🔙 عودة", callback_data=f"manage_dir_{item[2]}")]
        ])
        await call.message.edit_text(f"🛠 **التحكم بالزر:** [{item[0]}]\nنوعه: `{item[1]}`\n\nاختر الإجراء المطلوب:", reply_markup=kb)

    elif data.startswith("editname_"):
        if call.from_user.id != SUPER_ADMIN: return
        item_id = int(data.split("_")[1])
        await state.update_data(edit_item_id=item_id)
        await call.message.answer("✏️ أرسل الآن الاسم الجديد للزر المختار:")
        await state.set_state(SystemStates.wait_new_name)

    elif data.startswith("delitem_"):
        if call.from_user.id != SUPER_ADMIN: return
        item_id = int(data.split("_")[1])
        cursor.execute("SELECT parent_id, name FROM elements WHERE id=?", (item_id,))
        item = cursor.fetchone()
        if item:
            pid = item[0]
            cursor.execute("DELETE FROM elements WHERE id=?", (item_id,))
            cursor.execute("DELETE FROM elements WHERE parent_id=?", (item_id,)) 
            conn.commit()
            await call.answer(f"🗑 تم حذف زر [{item[1]}] بنجاح!", show_alert=True)
            await call.message.edit_text("⚙️ اختر الزر الذي تريد **تعديله** أو **حذفه** من الشجرة أدناه:", reply_markup=get_manage_keyboard(pid))

    elif data == "adm_add_element":
        if call.from_user.id != SUPER_ADMIN: return
        cursor.execute("SELECT id, name FROM elements WHERE type='folder'")
        folders = cursor.fetchall()
        kb = [[InlineKeyboardButton(text="🔝 في واجهة الشراء الأساسية", callback_data="setparent_0")]]
        for f in folders: kb.append([InlineKeyboardButton(text=f"📁 داخل قسم: {f[1]}", callback_data=f"setparent_{f[0]}")])
        await call.message.edit_text("📍 أين تريد وضع هذا الزر الجديد ضمن شجرة المتجر Reef؟", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

    elif data.startswith("setparent_"):
        if call.from_user.id != SUPER_ADMIN: return
        pid = int(data.split("_")[1])
        await state.update_data(parent_id=pid)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📁 قسم فرعي جديد", callback_data="settype_folder"), InlineKeyboardButton(text="📝 نص أو منتج معروض", callback_data="settype_text")],
            [InlineKeyboardButton(text="🔗 رابط ويب أو قناة", callback_data="settype_link"), InlineKeyboardButton(text="📸 ميديا وصورة منتج", callback_data="settype_media")]
        ])
        await call.message.edit_text("⚙️ اختر نوع هذا الزر المخصص للتثبيت:", reply_markup=kb)

    elif data.startswith("settype_"):
        if call.from_user.id != SUPER_ADMIN: return
        elem_type = data.split("_")[1]
        await state.update_data(type=elem_type)
        await call.message.answer("🔤 أرسل الاسم النصي للزر (الذي سيظهر للزبائن):")
        await state.set_state(SystemStates.wait_name)

    elif data == "adm_stats":
        cursor.execute('SELECT COUNT(*) FROM users'); u_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM elements'); e_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM purchases'); p_count = cursor.fetchone()[0]
        stat_text = f"📊 **إحصائيات متجرك السيادي:**\n\n👥 إجمالي المستخدمين 
