import os
import sqlite3
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- الإعدادات الثابتة ---
API_TOKEN = os.getenv('BOT_TOKEN')
SUPER_ADMIN = 8333784255  # معرفك

MY_ACCOUNT_URL = "https://t.me/xq_7d"  
CHANNEL_URL = "https://t.me/drov70"       

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
DB_NAME = 'sovereign_store_v8.db'

# --- دوال قاعدة البيانات الآمنة (لمنع الأخطاء وعدم الحفظ) ---
def db_write(query, args=()):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(query, args)
    conn.commit()
    conn.close()

def db_read(query, args=()):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(query, args)
    res = cursor.fetchall()
    conn.close()
    return res

def init_db():
    db_write('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, balance REAL DEFAULT 0.0, 
        referred_by INTEGER, last_gift_date TEXT)''')
    db_write('''CREATE TABLE IF NOT EXISTS elements (
        id INTEGER PRIMARY KEY AUTOINCREMENT, parent_id INTEGER DEFAULT 0, 
        type TEXT, name TEXT, content TEXT, price REAL DEFAULT 0.0)''')
    db_write('''CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, 
        item_name TEXT, purchase_date TEXT)''')
init_db()

# --- الحالات (FSM) ---
class SystemStates(StatesGroup):
    wait_name = State()
    wait_price = State()
    wait_content = State()
    wait_broadcast = State()
    wait_delete_id = State()
    wait_add_balance_id = State()
    wait_add_balance_amount = State()

# --- الكيبوردات (لوحات المفاتيح) ---
def get_main_keyboard(user_id):
    kb = [
        [InlineKeyboardButton(text="🛒 الشراء وتصفح المتجر", callback_data="main_buy")],
        [InlineKeyboardButton(text="💰 شحن رصيد", callback_data="main_charge"), InlineKeyboardButton(text="📦 مشترياتي", callback_data="main_purchases")],
        [InlineKeyboardButton(text="🔗 رابط الإحالة", callback_data="main_referral"), InlineKeyboardButton(text="📢 قناة التفعيلات", url=CHANNEL_URL)],
        [InlineKeyboardButton(text="👨‍💻 الدعم الفني", url=MY_ACCOUNT_URL)]
    ]
    if user_id == SUPER_ADMIN:
        kb.append([InlineKeyboardButton(text="⚙️ لوحة الإدارة الشاملة (God Mode)", callback_data="super_admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_store_keyboard(parent_id=0):
    items = db_read('SELECT id, name, type, content, price FROM elements WHERE parent_id=?', (parent_id,))
    kb = []
    row = []
    for item in items:
        item_id, name, item_type, content, price = item
        price_text = int(price) if price.is_integer() else price
        
        # إذا كان رابط يفتح مباشرة، وإذا مجلد يفتح القسم، وإذا منتج يعرض سعره
        if item_type == 'link':
            row.append(InlineKeyboardButton(text=f"🔗 {name}", url=content))
        elif item_type == 'folder':
            row.append(InlineKeyboardButton(text=f"📁 {name}", callback_data=f"view_{item_id}"))
        else:
            row.append(InlineKeyboardButton(text=f"💎 {name} | {price_text} نقطة", callback_data=f"view_{item_id}"))

        if len(row) == 2:  
            kb.append(row)  
            row = []  
    if row: kb.append(row)  
      
    if parent_id != 0:  
        gp = db_read('SELECT parent_id FROM elements WHERE id=?', (parent_id,))
        gp_id = gp[0][0] if gp else 0  
        kb.append([InlineKeyboardButton(text="🔙 رجوع للخلف", callback_data=f"view_{gp_id}")])  
    else:  
        kb.append([InlineKeyboardButton(text="🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")])  
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- الواجهة والتنقل ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "بلا معرف"
    args = message.text.split()  
    referred_by = int(args[1]) if len(args) > 1 and args[1].isdigit() and int(args[1]) != user_id else None  

    exists = db_read('SELECT balance FROM users WHERE user_id=?', (user_id,))
    if not exists:  
        db_write('INSERT INTO users (user_id, username, referred_by) VALUES (?, ?, ?)', (user_id, username, referred_by))
        user_balance = 0.0  
        if referred_by:  
            db_write('UPDATE users SET balance = balance + 5 WHERE user_id=?', (referred_by,))
            try: await bot.send_message(chat_id=referred_by, text=f"🎉 قام {username} بالدخول عبر رابطك، ربحت 5 نقاط!")  
            except: pass  
    else:  
        user_balance = exists[0][0]  
        db_write('UPDATE users SET username=? WHERE user_id=?', (username, user_id))
          
    bal = int(user_balance) if float(user_balance).is_integer() else user_balance
    welcome = (f"أهلاً بكم في -  Drov TG   👋\n\n🚀 أقوى سوق لبيع وشراء حسابات تيليجرام 🌐.\n\n"
               f"-  ايديك: `{user_id}` 🆔.\n- 👍 رصيدك:  `{bal}` نقطة 💵.\n\n👍 ابدأ الاستخدام من الأسفل ⬇️.")  
    if user_id == SUPER_ADMIN: welcome = "👑 **مرحباً بك يا سيادة المالك المطلق**\n\n" + welcome  
    await message.answer(welcome, reply_markup=get_main_keyboard(user_id), parse_mode="Markdown")

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(call: types.CallbackQuery):
    user_id = call.from_user.id
    bal_data = db_read('SELECT balance FROM users WHERE user_id=?', (user_id,))
    bal = bal_data[0][0] if bal_data else 0
    bal_disp = int(bal) if float(bal).is_integer() else bal
    welcome = (f"أهلاً بكم في -  Drov TG   👋\n\n🚀 أقوى سوق لبيع وشراء حسابات تيليجرام 🌐.\n\n"
               f"-  ايديك: `{user_id}` 🆔.\n- 👍 رصيدك:  `{bal_disp}` نقطة 💵.\n\n👍 ابدأ الاستخدام من الأسفل ⬇️.")  
    await call.message.edit_text(welcome, reply_markup=get_main_keyboard(user_id), parse_mode="Markdown")

@dp.callback_query(F.data == "main_buy")
async def main_buy(call: types.CallbackQuery):
    await call.message.edit_text("🛒 **أقسام المتجر والمنتجات المتوفرة:**\n(اضغط على السلعة لشرائها)", reply_markup=get_store_keyboard(0), parse_mode="Markdown")

# --- نظام الشراء الفعلي ---
@dp.callback_query(F.data.startswith("view_"))
async def navigate_system(call: types.CallbackQuery):
    target_id = int(call.data.split("_")[1])
    if target_id == 0:  
        return await call.message.edit_text("🛒 أقسام المتجر:", reply_markup=get_store_keyboard(0))  

    item = db_read('SELECT type, name, content, price FROM elements WHERE id=?', (target_id,))
    if not item: return await call.answer("العنصر المطلوب محذوف أو غير متوفر!", show_alert=True)  

    item_type, name, content, price = item[0]  
    user_id = call.from_user.id
      
    if item_type == 'folder':  
        await call.message.edit_text(f"📂 قسم: **{name}**\nاختر المنتج الذي تود شراءه:", reply_markup=get_store_keyboard(target_id), parse_mode="Markdown")  
    elif item_type in ['text', 'media']:
        user_bal = db_read('SELECT balance FROM users WHERE user_id=?', (user_id,))[0][0]
        
        if user_bal < price:
            return await call.answer(f"❌ رصيدك غير كافٍ!\nسعر المنتج: {price} نقطة\nرصيدك: {user_bal} نقطة", show_alert=True)
            
        db_write('UPDATE users SET balance = balance - ? WHERE user_id=?', (price, user_id))
        db_write('INSERT INTO purchases (user_id, item_name, purchase_date) VALUES (?, ?, ?)', (user_id, name, datetime.now().strftime("%Y-%m-%d %H:%M")))  
        
        await call.answer("✅ تمت عملية الشراء بنجاح! تم خصم الرصيد.", show_alert=True)
        
        if item_type == 'text':  
            await call.message.answer(f"📦 **مشترياتك:** {name}\n\n{content}\n\n*(شكراً لتسوقك من Drov)*", parse_mode="Markdown")  
        elif item_type == 'media':  
            await call.message.answer_photo(photo=content, caption=f"📸 {name}\n\n*(شكراً لتسوقك من Drov)*", parse_mode="Markdown")

# --- ⚙️ الإعدادات (لوحة المالك الشاملة) ---
@dp.callback_query(F.data == "super_admin_panel")
async def super_admin_panel(call: types.CallbackQuery):
    if call.from_user.id != SUPER_ADMIN: return await call.answer("❌ للـ VIP فقط!", show_alert=True)
    kb = InlineKeyboardMarkup(inline_keyboard=[  
        [InlineKeyboardButton(text="➕ إضافة (قسم / سلعة / رابط)", callback_data="adm_add_element")],  
        [InlineKeyboardButton(text="🗑 حذف سلعة أو قسم", callback_data="adm_delete_element"), InlineKeyboardButton(text="💰 إضافة رصيد لشخص", callback_data="adm_add_balance")],
        [InlineKeyboardButton(text="📢 إذاعة رسالة للكل", callback_data="adm_broadcast"), InlineKeyboardButton(text="📊 إحصائيات", callback_data="adm_stats")],  
        [InlineKeyboardButton(text="🔙 إغلاق اللوحة", callback_data="back_to_main")]  
    ])  
    await call.message.edit_text("⚙️ **إعدادات Drov الشاملة (God Mode):**\nاختر النظام الذي تريد إدارته:", reply_markup=kb, parse_mode="Markdown")

# 1. إضافة الأقسام والسلع
@dp.callback_query(F.data == "adm_add_element")
async def build_step1(call: types.CallbackQuery):
    folders = db_read("SELECT id, name FROM elements WHERE type='folder'")
    kb = [[InlineKeyboardButton(text="🔝 في الواجهة الأساسية للمتجر", callback_data="setparent_0")]]  
    for f in folders:  
        kb.append([InlineKeyboardButton(text=f"📁 داخل قسم: {f[1]}", callback_data=f"setparent_{f[0]}")])  
    await call.message.edit_text("📍 **أين تريد وضع الزر الجديد؟**", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("setparent_"))
async def build_step2(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(parent_id=int(call.data.split("_")[1]))
    kb = InlineKeyboardMarkup(inline_keyboard=[  
        [InlineKeyboardButton(text="📁 مجلد (قسم)", callback_data="settype_folder"), InlineKeyboardButton(text="🔗 رابط قناة/موقع", callback_data="settype_link")],  
        [InlineKeyboardButton(text="📝 سلعة (نصية)", callback_data="settype_text"), InlineKeyboardButton(text="📸 سلعة (صورة)", callback_data="settype_media")]  
    ])  
    await call.message.edit_text("⚙️ **اختر نوع العنصر المراد إضافته:**", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("settype_"))
async def build_step3(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(type=call.data.split("_")[1])
    await call.message.answer("🔤 **أرسل اسم الزر الآن:**\n(مثال: حسابات ببجي، أو قناة التحديثات)", parse_mode="Markdown")
    await state.set_state(SystemStates.wait_name)

@dp.message(SystemStates.wait_name)
async def build_step4(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    data = await state.get_data()
    if data['type'] in ['folder', 'link']:  
        await state.update_data(price=0.0)
        if data['type'] == 'folder':
            db_write('INSERT INTO elements (parent_id, type, name, content, price) VALUES (?, ?, ?, ?, ?)', (data['parent_id'], 'folder', data['name'], 'none', 0.0))  
            await message.answer("✅ **تم إنشاء القسم بنجاح!**", parse_mode="Markdown")  
            await state.clear()  
        else:
            await message.answer("🔗 **أرسل الرابط الآن:**\n(يجب أن يبدأ بـ http:// أو https://)", parse_mode="Markdown")
            await state.set_state(SystemStates.wait_content)
    else:  
        await message.answer("💰 **أرسل سعر السلعة (أرقام فقط):**\n(مثال: 15 أو 2.5)", parse_mode="Markdown")  
        await state.set_state(SystemStates.wait_price)

@dp.message(SystemStates.wait_price)
async def build_step_price(message: types.Message, state: FSMContext):
    try:
        await state.update_data(price=float(message.text))
        await message.answer("📥 **أرسل محتوى السلعة الآن:**\n(إذا اخترت نص: أرسل الإيميل/الباسورد. وإذا صورة: أرسل الصورة)", parse_mode="Markdown")  
        await state.set_state(SystemStates.wait_content)
    except ValueError:
        await message.answer("❌ السعر يجب أن يكون رقماً فقط! حاول مجدداً:")

@dp.message(SystemStates.wait_content)
async def build_step5(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # الفحص الآمن للمحتوى بدون الفلاتر المزعجة
    if data['type'] == 'media':
        if not message.photo: return await message.answer("❌ يرجى إرسال صورة!")
        content = message.photo[-1].file_id
    else:
        if not message.text: return await message.answer("❌ يرجى إرسال نص/رابط!")
        content = message.text

    db_write('INSERT INTO elements (parent_id, type, name, content, price) VALUES (?, ?, ?, ?, ?)', 
             (data['parent_id'], data['type'], data['name'], content, data.get('price', 0.0)))  
    await message.answer(f"🎯 **تم إضافة ({data['name']}) بنجاح إلى المتجر!**", parse_mode="Markdown")  
    await state.clear()

# 2. حذف العناصر
@dp.callback_query(F.data == "adm_delete_element")
async def delete_element_start(call: types.CallbackQuery, state: FSMContext):
    items = db_read("SELECT id, name, type FROM elements")
    if not items: return await call.answer("لا يوجد شيء لحذفه!", show_alert=True)
    text = "🗑 **لحذف أي عنصر (سلعة أو قسم):**\nأرسل الـ ID الخاص به من القائمة أدناه:\n\n"
    for i in items:
        icon = "📁" if i[2] == 'folder' else "🔗" if i[2] == 'link' else "💎"
        text += f"ID: `{i[0]}` | {icon} {i[1]}\n"
    await call.message.answer(text, parse_mode="Markdown")
    await state.set_state(SystemStates.wait_delete_id)

@dp.message(SystemStates.wait_delete_id)
async def delete_element_execute(message: types.Message, state: FSMContext):
    try:
        elem_id = int(message.text)
        db_write("DELETE FROM elements WHERE id=?", (elem_id,))
        await message.answer("✅ **تم الحذف بنجاح!**", parse_mode="Markdown")
    except:
        await message.answer("❌ خطأ بالرقم!")
    await state.clear()

# 3. إضافة رصيد
@dp.callback_query(F.data == "adm_add_balance")
async def add_bal_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("أرسل **ايدي (ID)** المستخدم الذي تريد إضافة رصيد له:", parse_mode="Markdown")
    await state.set_state(SystemStates.wait_add_balance_id)

@dp.message(SystemStates.wait_add_balance_id)
async def add_bal_id(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("❌ الايدي أرقام فقط!")
    await state.update_data(target_user=int(message.text))
    await message.answer("كم نقطة تريد إضافتها لرصيده؟", parse_mode="Markdown")
    await state.set_state(SystemStates.wait_add_balance_amount)

@dp.message(SystemStates.wait_add_balance_amount)
async def add_bal_execute(message: types.Message, state: FSMContext):
    try:
        amt = float(message.text)
        data = await state.get_data()
        db_write("UPDATE users SET balance = balance + ? WHERE user_id=?", (amt, data['target_user']))
        await message.answer(f"✅ **تمت إضافة {amt} نقطة للمستخدم بنجاح!**", parse_mode="Markdown")
        try: await bot.send_message(chat_id=data['target_user'], text=f"🎁 الإدارة أضافت لرصيدك {amt} نقطة!")
        except: pass
    except:
        await message.answer("❌ خطأ بقيمة الرصيد!")
    await state.clear()

# --- التشغيل ---
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
