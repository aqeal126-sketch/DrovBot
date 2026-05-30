import os
import sqlite3
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramAPIError
from aiohttp import web

# --- الإعدادات الثابتة للمتجر ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
SUPER_ADMIN = 8333784255  # معرف المالك المطلق

MY_ACCOUNT_URL = "https://t.me/xq_7d"  
CHANNEL_URL = "https://t.me/drov70"       

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
DB_NAME = 'sovereign_store_v9.db'

# --- قاموس اللغات الشامل لكل نصوص البوت ---
STRINGS = {
    'ar': {
        'select_lang': "الرجاء اختيار اللغة الخاصة بك للبدء: 🌐",
        'welcome': "أهلاً بكم في -  Drov TG   👋\n\n🚀 أقوى سوق لبيع وشراء حسابات تيليجرام الجاهزة والجديدة لجميع الدول حول العالم 🌐.\n\n- ايديك: `{user_id}` 🆔.\n- 👍 رصيدك: `${balance}` دولار 💵.\n\n👍 ابدأ باستخدام البوت الآن بالضغط على الأزرار بالأسفل ⬇️.",
        'admin_welcome': "👑 **مرحباً بك يا سيادة المالك المطلق (لوحة التحكم متوفرة بالأسفل)**\n\n",
        'btn_buy': "🛒 الشراء وتصفح المتجر",
        'btn_charge': "💰 شحن رصيد",
        'btn_purchases': "📦 مشترياتي",
        'btn_referral': "🔗 رابط الإحالة",
        'btn_channel': "📢 قناة التفعيلات",
        'btn_support': "👨‍💻 الدعم الفني",
        'btn_admin': "⚙️ لوحة الإدارة والتحكم الكاملة",
        'btn_change_lang': "🌐 تغيير اللغة / Change Language",
        'btn_back': "🔙 رجوع للخلف",
        'btn_main_menu': "🔙 العودة للقائمة الرئيسية",
        'store_title': "🛒 أقسام المتجر والمنتجات المتوفرة الاحترافية:",
        'soon_alert': "⚠️ هذا القسم غير متوفر حالياً، سيتم إطلاقه قريباً جداً!",
        'soon_tag': "قريباً",
        'insufficient_balance': "❌ رصيدك غير كافٍ لشراء هذه السلعة!\nسعر المنتج: ${price}\nرصيدك الحالي: ${balance}",
        'purchase_success': "✅ تمت عملية الشراء بنجاح! تم خصم الرصيد وتسليم السلعة.",
        'thanks': "*(شكراً لتسوقك من متجر Drov)*",
        'charge_title': "💰 **قسم شحن الرصيد والحساب**\n\n💳 رصيدك الحالي: `${balance}` دولار.\n\nيمكنك تجميع الرصيد مجاناً عبر نظام الإحالة، أو التواصل مع المالك مباشرة للشحن الفوري.",
        'btn_gift': "🎁 استلام الهدية اليومية",
        'btn_contact_charge': "📥 تواصل معي للشراء والشحن",
        'gift_already': "❌ لقد قمت باستلام هديتك اليومية بالفعل! عد غداً يا بطل.",
        'gift_success': "🎉 مبروك! حصلت على $0.10 دولار مجاناً كهدية يومية.",
        'ref_title': "🔗 **نظام الإحالة وتجميع الرصيد مجاناً**\n\nشارك الرابط الخاص بك مع أصدقائك، وكل شخص يدخل للبوت عن طريقك ستحصل فوراً على **$0.50 دولار مجاناً** في رصيدك لشراء المنتجات!\n\nرابطك الخاص:\n`{ref_link}`",
        'purchases_title': "📦 **سجل مشترياتك من البوت:**\n\n",
        'no_purchases': "أنت لم تقم بشراء أي شيء بعد. تصفح قسم الشراء لتسوق منتجاتنا!",
        'ref_alert': "🎉 قام {username} بالدخول للبوت عبر رابطك، وتمت إضافة $0.50 لرصيدك!"
    },
    'en': {
        'select_lang': "Please select your language to start: 🌐",
        'welcome': "Welcome to - Drov TG 👋\n\n🚀 The most powerful market for buying and selling ready-made and new Telegram accounts worldwide 🌐.\n\n- Your ID: `{user_id}` 🆔.\n- 👍 Balance: `${balance}` USD 💵.\n\n👍 Start using the bot now by clicking the buttons below ⬇️.",
        'admin_welcome': "👑 **Welcome, Supreme Owner! (Admin Panel available below)**\n\n",
        'btn_buy': "🛒 Browse & Buy",
        'btn_charge': "💰 Top-up Balance",
        'btn_purchases': "📦 My Purchases",
        'btn_referral': "🔗 Referral Link",
        'btn_channel': "📢 Activation Channel",
        'btn_support': "👨‍💻 Technical Support",
        'btn_admin': "⚙️ Control & Admin Panel",
        'btn_change_lang': "🌐 Change Language / تغيير اللغة",
        'btn_back': "🔙 Back",
        'btn_main_menu': "🔙 Back to Main Menu",
        'store_title': "🛒 Store Categories and Available Products:",
        'soon_alert': "⚠️ This section is currently unavailable, it will be launched very soon!",
        'soon_tag': "Soon",
        'insufficient_balance': "❌ Insufficient balance to buy this item!\nProduct Price: ${price}\nYour Balance: ${balance}",
        'purchase_success': "✅ Purchase successful! Balance deducted and item delivered.",
        'thanks': "*(Thank you for shopping at Drov Store)*",
        'charge_title': "💰 **Balance & Account Top-up Section**\n\n💳 Current Balance: `${balance}` USD.\n\nYou can collect balance for free via the referral system, or contact the owner directly for instant top-up.",
        'btn_gift': "🎁 Claim Daily Gift",
        'btn_contact_charge': "📥 Contact Me to Buy & Top-up",
        'gift_already': "❌ You have already claimed your daily gift! Come back tomorrow.",
        'gift_success': "🎉 Congratulations! You received $0.10 free USD as a daily gift.",
        'ref_title': "🔗 **Referral System & Free Balance**\n\nShare your link with friends. For every person who joins via your link, you will instantly get **$0.50 free USD** added to your balance!\n\nYour Link:\n`{ref_link}`",
        'purchases_title': "📦 **Your Purchase History:**\n\n",
        'no_purchases': "You haven't bought anything yet. Browse the store to shop our products!",
        'ref_alert': "🎉 {username} joined via your link, $0.50 USD has been added to your balance!"
    },
    'ru': {
        'select_lang': "Пожалуйста, выберите язык для начала: 🌐",
        'welcome': "Добро пожаловать в - Drov TG 👋\n\n🚀 Самый мощный маркетплейс по покупке и продаже готовых и новых аккаунтов Telegram по всему миру 🌐.\n\n- Ваш ID: `{user_id}` 🆔.\n- 👍 Баланс: `${balance}` USD 💵.\n\n👍 Начните использовать бота прямо сейчас, нажимая кнопки ниже ⬇️.",
        'admin_welcome': "👑 **Добро пожаловать, Владелец! (Панель управления доступна ниже)**\n\n",
        'btn_buy': "🛒 Купить и Просмотреть",
        'btn_charge': "💰 Пополнить баланс",
        'btn_purchases': "📦 Мои покупки",
        'btn_referral': "🔗 Реферальная ссылка",
        'btn_channel': "📢 Канал активаций",
        'btn_support': "👨‍💻 Техподдержка",
        'btn_admin': "⚙️ Панель управления",
        'btn_change_lang': "🌐 Изменить язык / Change Language",
        'btn_back': "🔙 Назад",
        'btn_main_menu': "🔙 В главное меню",
        'store_title': "🛒 Категории магазина и доступные товары:",
        'soon_alert': "⚠️ Этот раздел сейчас недоступен, он будет запущен очень скоро!",
        'soon_tag': "Скоро",
        'insufficient_balance': "❌ Недостаточно средств для покупки!\nЦена товара: ${price}\nВаш баланс: ${balance}",
        'purchase_success': "✅ Покупка успешна! Баланс списан, товар доставлен.",
        'thanks': "*(Спасибо за покупку в магазине Drov)*",
        'charge_title': "💰 **Раздел пополнения баланса и аккаунта**\n\n💳 Текущий баланс: `${balance}` USD.\n\nВы можете собирать баланс бесплатно через реферальную систему или связаться с владельцем напрямую для пополнения.",
        'btn_gift': "🎁 Получить ежедневный бонус",
        'btn_contact_charge': "📥 Связаться для пополнения",
        'gift_already': "❌ Вы уже получили свой ежедневный бонус! Возвращайтесь завтра.",
        'gift_success': "🎉 Поздравляем! Вы получили $0.10 USD бесплатно в качестве бонуса.",
        'ref_title': "🔗 **Реферальная система и бесплатный баланс**\n\nПоделитесь своей ссылкой с друзьями. За каждого человека, который зайдет по вашей ссылке, вы мгновенно получите **$0.50 USD** на свой баланс!\n\nВаша ссылка:\n`{ref_link}`",
        'purchases_title': "📦 **История ваших покупок:**\n\n",
        'no_purchases': "Вы еще ничего не купили. Загляните в магазин, чтобы сделать покупки!",
        'ref_alert': "🎉 {username} зарегистрировался по вашей ссылке, $0.50 USD добалены на ваш баланс!"
    }
}

# --- دوال إدارة قاعدة البيانات ---
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
        referred_by INTEGER, last_gift_date TEXT, lang TEXT DEFAULT 'none')''')
    
    db_write('''CREATE TABLE IF NOT EXISTS elements (
        id INTEGER PRIMARY KEY AUTOINCREMENT, parent_id INTEGER DEFAULT 0, 
        type TEXT, name_ar TEXT, name_en TEXT, name_ru TEXT, content TEXT, price REAL DEFAULT 0.0)''')
        
    db_write('''CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, 
        item_name TEXT, purchase_date TEXT)''')
    
    count = db_read("SELECT COUNT(*) FROM elements WHERE parent_id = 0")
    if count[0][0] == 0:
        categories = [
            ('soon', 'قسم الارقام API', 'API Numbers Section', 'Раздел API Номера', 'none', 0.0),
            ('folder', 'قسم الادوات', 'Tools Section', 'Раздел Инструменты', 'none', 0.0),
            ('folder', 'قسم اليوزرات التليغرام', 'Telegram Usernames Section', 'Раздел Юзернеймы Telegram', 'none', 0.0),
            ('folder', 'قسم اليوزرات تيك توك', 'TikTok Usernames Section', 'Раздел Юзернеймы TikTok', 'none', 0.0),
            ('soon', 'قسم يوزرات الديسكورد', 'Discord Usernames Section', 'Раздел Юзернеймы Discord', 'none', 0.0),
            ('folder', 'قسم اليوزرات الانستقرام', 'Instagram Usernames Section', 'Раздел Юзернеймы Instagram', 'none', 0.0),
            ('folder', 'قسم بيع القنوات والمجموعات التليغرام', 'Telegram Channels & Groups Sale', 'Продажа каналов и групп Telegram', 'none', 0.0)
        ]
        for cat in categories:
            db_write("INSERT INTO elements (type, name_ar, name_en, name_ru, content, price) VALUES (?, ?, ?, ?, ?, ?)", cat)

init_db()

# --- حالات FSM ---
class SystemStates(StatesGroup):
    wait_name_ar = State()
    wait_name_en = State()
    wait_name_ru = State()
    wait_price = State()
    wait_content = State()
    wait_broadcast = State()
    wait_delete_id = State()
    wait_add_balance_id = State()
    wait_add_balance_amount = State()

# --- الكيبوردات ---
def get_lang_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇸🇦 العربية", callback_data="setlang_ar")],
        [InlineKeyboardButton(text="🇺🇸 English", callback_data="setlang_en")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru")]
    ])

def get_main_keyboard(user_id, lang):
    s = STRINGS[lang]
    kb = [
        [InlineKeyboardButton(text=s['btn_buy'], callback_data="main_buy")],
        [InlineKeyboardButton(text=s['btn_charge'], callback_data="main_charge"), InlineKeyboardButton(text=s['btn_purchases'], callback_data="main_purchases")],
        [InlineKeyboardButton(text=s['btn_referral'], callback_data="main_referral"), InlineKeyboardButton(text=s['btn_channel'], url=CHANNEL_URL)],
        [InlineKeyboardButton(text=s['btn_support'], url=MY_ACCOUNT_URL)],
        [InlineKeyboardButton(text=s['btn_change_lang'], callback_data="trigger_lang_change")]
    ]
    if user_id == SUPER_ADMIN:
        kb.append([InlineKeyboardButton(text=s['btn_admin'], callback_data="super_admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_store_keyboard(parent_id, lang):
    s = STRINGS[lang]
    items = db_read('SELECT id, name_ar, name_en, name_ru, type, content, price FROM elements WHERE parent_id=?', (parent_id,))
    kb = []
    row = []
    
    name_index = 1 if lang == 'ar' else (2 if lang == 'en' else 3)
    
    for item in items:
        item_id = item[0]
        name = item[name_index]
        item_type = item[4]
        content = item[5]
        price = item[6]
        
        price_disp = f"${int(price) if price.is_integer() else price}"
        
        if item_type == 'soon':
            row.append(InlineKeyboardButton(text=f"🔒 {name} ({s['soon_tag']})", callback_data=f"view_{item_id}"))
        elif item_type == 'link':
            row.append(InlineKeyboardButton(text=f"🔗 {name}", url=content))
        elif item_type == 'folder':
            row.append(InlineKeyboardButton(text=f"📁 {name}", callback_data=f"view_{item_id}"))
        else:
            row.append(InlineKeyboardButton(text=f"💎 {name} | {price_disp}", callback_data=f"view_{item_id}"))

        if len(row) == 2:  
            kb.append(row)  
            row = []  
    if row: kb.append(row)  
      
    if parent_id != 0:  
        gp = db_read('SELECT parent_id FROM elements WHERE id=?', (parent_id,))
        gp_id = gp[0][0] if gp else 0  
        kb.append([InlineKeyboardButton(text=s['btn_back'], callback_data=f"view_{gp_id}")])
    else:  
        kb.append([InlineKeyboardButton(text=s['btn_main_menu'], callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- المعالجات الخاصة بالمستخدم ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "No User"
    args = message.text.split()  
    referred_by = int(args[1]) if len(args) > 1 and args[1].isdigit() and int(args[1]) != user_id else None  

    exists = db_read('SELECT balance, lang FROM users WHERE user_id=?', (user_id,))
    if not exists:  
        db_write('INSERT INTO users (user_id, username, referred_by, lang) VALUES (?, ?, ?, ?)', (user_id, username, referred_by, 'none'))
        if referred_by:  
            db_write('UPDATE users SET balance = balance + 0.50 WHERE user_id=?', (referred_by,))
            try:
                ref_lang_data = db_read('SELECT lang FROM users WHERE user_id=?', (referred_by,))
                ref_lang = ref_lang_data[0][0] if ref_lang_data and ref_lang_data[0][0] != 'none' else 'ar'
                await bot.send_message(chat_id=referred_by, text=STRINGS[ref_lang]['ref_alert'].format(username=username))  
            except: pass  
        lang = 'none'
    else:  
        lang = exists[0][1]
        db_write('UPDATE users SET username=? WHERE user_id=?', (username, user_id))

    if lang == 'none':
        await message.answer("الرجاء اختيار اللغة الخاصة بك للبدء / Please select your language: 🌐", reply_markup=get_lang_keyboard())
    else:
        balance = db_read('SELECT balance FROM users WHERE user_id=?', (user_id,))[0][0]
        bal_disp = int(balance) if float(balance).is_integer() else balance
        welcome_text = STRINGS[lang]['welcome'].format(user_id=user_id, balance=bal_disp)
        if user_id == SUPER_ADMIN:
            welcome_text = STRINGS[lang]['admin_welcome'] + welcome_text
        await message.answer(welcome_text, reply_markup=get_main_keyboard(user_id, lang), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("setlang_"))
async def set_language_callback(call: types.CallbackQuery):
    selected_lang = call.data.split("_")[1]
    user_id = call.from_user.id
    db_write('UPDATE users SET lang=? WHERE user_id=?', (selected_lang, user_id))
    await call.answer()
    
    balance = db_read('SELECT balance FROM users WHERE user_id=?', (user_id,))[0][0]
    bal_disp = int(balance) if float(balance).is_integer() else balance
    welcome_text = STRINGS[selected_lang]['welcome'].format(user_id=user_id, balance=bal_disp)
    if user_id == SUPER_ADMIN:
        welcome_text = STRINGS[selected_lang]['admin_welcome'] + welcome_text
    await call.message.edit_text(welcome_text, reply_markup=get_main_keyboard(user_id, selected_lang), parse_mode="Markdown")

@dp.callback_query(F.data == "trigger_lang_change")
async def trigger_lang_change(call: types.CallbackQuery):
    await call.message.edit_text("Select Language / اختر اللغة:", reply_markup=get_lang_keyboard())

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_data = db_read('SELECT balance, lang FROM users WHERE user_id=?', (user_id,))
    balance, lang = user_data[0] if user_data else (0.0, 'ar')
    if lang == 'none': lang = 'ar'
    bal_disp = int(balance) if float(balance).is_integer() else balance
    welcome_text = STRINGS[lang]['welcome'].format(user_id=user_id, balance=bal_disp)
    if user_id == SUPER_ADMIN:
        welcome_text = STRINGS[lang]['admin_welcome'] + welcome_text
    await call.message.edit_text(welcome_text, reply_markup=get_main_keyboard(user_id, lang), parse_mode="Markdown")

@dp.callback_query(F.data == "main_buy")
async def main_buy(call: types.CallbackQuery):
    user_id = call.from_user.id
    lang = db_read('SELECT lang FROM users WHERE user_id=?', (user_id,))[0][0]
    if lang == 'none': lang = 'ar'
    await call.message.edit_text(STRINGS[lang]['store_title'], reply_markup=get_store_keyboard(0, lang), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("view_"))
async def view_store_element(call: types.CallbackQuery):
    target_id = int(call.data.split("_")[1])
    user_id = call.from_user.id
    lang = db_read('SELECT lang FROM users WHERE user_id=?', (user_id,))[0][0]
    if lang == 'none': lang = 'ar'
    s = STRINGS[lang]

    if target_id == 0:  
        return await call.message.edit_text(s['store_title'], reply_markup=get_store_keyboard(0, lang))  

    item = db_read('SELECT type, name_ar, name_en, name_ru, content, price FROM elements WHERE id=?', (target_id,))
    if not item: return await call.answer(s['soon_alert'], show_alert=True)  

    item_type, name_ar, name_en, name_ru, content, price = item[0]
    name = name_ar if lang == 'ar' else (name_en if lang == 'en' else name_ru)
      
    if item_type == 'soon':
        return await call.answer(s['soon_alert'], show_alert=True)
        
    elif item_type == 'folder':  
        await call.message.edit_text(f"📂 {name}", reply_markup=get_store_keyboard(target_id, lang), parse_mode="Markdown")  
        
    elif item_type in ['text', 'media']:
        user_bal = db_read('SELECT balance FROM users WHERE user_id=?', (user_id,))[0][0]
        if user_bal < price:
            return await call.answer(s['insufficient_balance'].format(price=price, balance=user_bal), show_alert=True)
            
        db_write('UPDATE users SET balance = balance - ? WHERE user_id=?', (price, user_id))
        db_write('INSERT INTO purchases (user_id, item_name, purchase_date) VALUES (?, ?, ?)', (user_id, name, datetime.now().strftime("%Y-%m-%d %H:%M")))  
        
        await call.answer(s['purchase_success'], show_alert=True)
        
        if item_type == 'text':  
            await call.message.answer(f"📦 **{name}**\n\n`{content}`\n\n{s['thanks']}", parse_mode="Markdown")  
        elif item_type == 'media':  
            await call.message.answer_photo(photo=content, caption=f"📸 **{name}**\n\n{s['thanks']}", parse_mode="Markdown")

@dp.callback_query(F.data == "main_charge")
async def main_charge(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_data = db_read('SELECT balance, lang FROM users WHERE user_id=?', (user_id,))
    balance, lang = user_data[0] if user_data else (0.0, 'ar')
    if lang == 'none': lang = 'ar'
    s = STRINGS[lang]
    
    bal_disp = int(balance) if float(balance).is_integer() else balance
    kb = InlineKeyboardMarkup(inline_keyboard=[  
        [InlineKeyboardButton(text=s['btn_gift'], callback_data="get_daily_gift")],  
        [InlineKeyboardButton(text=s['btn_contact_charge'], url=MY_ACCOUNT_URL)],  
        [InlineKeyboardButton(text=s['btn_back'], callback_data="back_to_main")]  
    ])  
    
    await call.message.edit_text(text=s['charge_title'].format(balance=bal_disp), reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "get_daily_gift")
async def get_daily_gift(call: types.CallbackQuery):
    user_id = call.from_user.id
    lang = db_read('SELECT lang FROM users WHERE user_id=?', (user_id,))[0][0]
    if lang == 'none': lang = 'ar'
    s = STRINGS[lang]
    today_str = datetime.now().strftime("%Y-%m-%d")

    last_date_data = db_read('SELECT last_gift_date FROM users WHERE user_id=?', (user_id,))
    last_date = last_date_data[0][0] if last_date_data else None
      
    if last_date == today_str:  
        await call.answer(s['gift_already'], show_alert=True)  
    else:  
        db_write('UPDATE users SET balance = balance + 0.10, last_gift_date=? WHERE user_id=?', (today_str, user_id))  
        await call.answer(s['gift_success'], show_alert=True)  
          
        balance = db_read('SELECT balance FROM users WHERE user_id=?', (user_id,))[0][0]
        bal_disp = int(balance) if float(balance).is_integer() else balance
        kb = InlineKeyboardMarkup(inline_keyboard=[  
            [InlineKeyboardButton(text=s['btn_gift'], callback_data="get_daily_gift")],  
            [InlineKeyboardButton(text=s['btn_contact_charge'], url=MY_ACCOUNT_URL)],  
            [InlineKeyboardButton(text=s['btn_back'], callback_data="back_to_main")]  
        ])  
        try: await call.message.edit_text(text=s['charge_title'].format(balance=bal_disp), reply_markup=kb, parse_mode="Markdown")  
        except: pass

@dp.callback_query(F.data == "main_referral")
async def main_referral(call: types.CallbackQuery):
    user_id = call.from_user.id
    lang = db_read('SELECT lang FROM users WHERE user_id=?', (user_id,))[0][0]
    if lang == 'none': lang = 'ar'
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=STRINGS[lang]['btn_back'], callback_data="back_to_main")]]) 
    await call.message.edit_text(STRINGS[lang]['ref_title'].format(ref_link=ref_link), reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "main_purchases")
async def main_purchases(call: types.CallbackQuery):
    user_id = call.from_user.id
    lang = db_read('SELECT lang FROM users WHERE user_id=?', (user_id,))[0][0]
    if lang == 'none': lang = 'ar'
    s = STRINGS[lang]
    
    rows = db_read('SELECT item_name, purchase_date FROM purchases WHERE user_id=? ORDER BY id DESC', (user_id,))
    text = s['purchases_title']
    if not rows:  
        text += s['no_purchases']
    else:  
        for idx, item in enumerate(rows, start=1):  
            text += f"{idx}. 🛍 `{item[0]}` - 📅: {item[1]}\n"  
              
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=s['btn_back'], callback_data="back_to_main")]]) 
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# --- لوحة تحكم المالك ---
@dp.callback_query(F.data == "super_admin_panel")
async def super_admin_panel(call: types.CallbackQuery):
    if call.from_user.id != SUPER_ADMIN: return await call.answer("❌ صلاحية محظورة!", show_alert=True)
    kb = InlineKeyboardMarkup(inline_keyboard=[  
        [InlineKeyboardButton(text="➕ إضافة (قسم فرعي / سلعة / رابط)", callback_data="adm_add_element")],  
        [InlineKeyboardButton(text="🗑 حذف أي عنصر أو قسم", callback_data="adm_delete_element"), InlineKeyboardButton(text="💰 شحن رصيد مستخدم", callback_data="adm_add_balance")],
        [InlineKeyboardButton(text="📢 إذاعة رسالة جماعية", callback_data="adm_broadcast"), InlineKeyboardButton(text="📊 إحصائيات النظام كاملة", callback_data="adm_stats")],  
        [InlineKeyboardButton(text="🔙 إغلاق لوحة التحكم", callback_data="back_to_main")]  
    ])  
    await call.message.edit_text("⚙️ **أهلاً بك يا سيادة المالك في أنظمة إعدادات Drov العليا:**", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "adm_add_element")
async def adm_add_element(call: types.CallbackQuery):
    folders = db_read("SELECT id, name_ar FROM elements WHERE type='folder'")
    kb = [[InlineKeyboardButton(text="🔝 في الواجهة الأساسية للمتجر", callback_data="setparent_0")]]  
    for f in folders:  
        kb.append([InlineKeyboardButton(text=f"📁 داخل قسم: {f[1]}", callback_data=f"setparent_{f[0]}")]) 
    await call.message.edit_text("📍 **اختر المجلد الذي تود الإضافة بداخله:**", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("setparent_"))
async def setparent_callback(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(parent_id=int(call.data.split("_")[1]))
    kb = InlineKeyboardMarkup(inline_keyboard=[  
        [InlineKeyboardButton(text="📁 مجلد (قسم فرعي جديد)", callback_data="settype_folder"), InlineKeyboardButton(text="🔗 رابط خارجي", callback_data="settype_link")],  
        [InlineKeyboardButton(text="📝 سلعة نصية (كود/حساب)", callback_data="settype_text"), InlineKeyboardButton(text="📸 سلعة صورية (ملف/ميديا)", callback_data="settype_media")]  
    ])  
    await call.message.edit_text("⚙️ **اختر الآن نوع هذا الزر البرمجي الجديد:**", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("settype_"))
async def settype_callback(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(type=call.data.split("_")[1])
    await call.message.answer("🇸🇦 أرسل الاسم بـ **اللغة العربية** (سيظهر للعرب):", parse_mode="Markdown")
    await state.set_state(SystemStates.wait_name_ar)

@dp.message(SystemStates.wait_name_ar)
async def process_name_ar(message: types.Message, state: FSMContext):
    await state.update_data(name_ar=message.text)
    await message.answer("🇺🇸 أرسل الاسم بـ **اللغة الإنجليزية** (سيظهر للأجانب):", parse_mode="Markdown")
    await state.set_state(SystemStates.wait_name_en)

@dp.message(SystemStates.wait_name_en)
async def process_name_en(message: types.Message, state: FSMContext):
    await state.update_data(name_en=message.text)
    await message.answer("🇷🇺 أرسل الاسم بـ **اللغة الروسية** (سيظهر للروس):", parse_mode="Markdown")
    await state.set_state(SystemStates.wait_name_ru)

@dp.message(SystemStates.wait_name_ru)
async def process_name_ru(message: types.Message, state: FSMContext):
    await state.update_data(name_ru=message.text)
    data = await state.get_data()
    
    if data['type'] in ['folder', 'link']:  
        await state.update_data(price=0.0)
        if data['type'] == 'folder':
            db_write('INSERT INTO elements (parent_id, type, name_ar, name_en, name_ru, content, price) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                     (data['parent_id'], 'folder', data['name_ar'], data['name_en'], data['name_ru'], 'none', 0.0))  
            await message.answer("✅ **تم إنشاء المجلد والمزامنة بجميع اللغات!**", parse_mode="Markdown")  
            await state.clear()  
        else:
            await message.answer("🔗 **أرسل رابط القناة أو الموقع الموجه له الآن:**\n(يبدأ بـ http:// أو https://)", parse_mode="Markdown")
            await state.set_state(SystemStates.wait_content)
    else:  
        await message.answer("💰 **أرسل سعر هذه السلعة بالدولار ($) [أرقام فقط]:**\n(مثال: 5 أو 12.50)", parse_mode="Markdown")  
        await state.set_state(SystemStates.wait_price)

@dp.message(SystemStates.wait_price)
async def process_price(message: types.Message, state: FSMContext):
    try:
        price_val = float(message.text)
        await state.update_data(price=price_val)
        await message.answer("📥 **أرسل الآن محتوى السلعة للتسليم التلقائي:**\n(إذا نصية: أرسل الحساب/الكود. إذا صورية: ارفع الصورة مباشرة)", parse_mode="Markdown")  
        await state.set_state(SystemStates.wait_content)
    except ValueError:
        await message.answer("❌ السعر غير صحيح! أرسل أرقام فقط (مثل: 10 أو 4.5):")

@dp.message(SystemStates.wait_content)
async def process_content(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data['type'] == 'media':
        if not message.photo: return await message.answer("❌ يرجى إرسال ملف صورة حصراً!")
        content = message.photo[-1].file_id
    else:
        if not message.text: return await message.answer("❌ يرجى إرسال نص أو رابط!")
        content = message.text

    db_write('INSERT INTO elements (parent_id, type, name_ar, name_en, name_ru, content, price) VALUES (?, ?, ?, ?, ?, ?, ?)', 
             (data['parent_id'], data['type'], data['name_ar'], data['name_en'], data['name_ru'], content, data.get('price', 0.0)))  
    await message.answer(f"🎯 **تم تثبيت السلعة والأسعار بدقة فائقة بجميع اللغات!**", parse_mode="Markdown")  
    await state.clear()

@dp.callback_query(F.data == "adm_delete_element")
async def adm_delete_element(call: types.CallbackQuery, state: FSMContext):
    items = db_read("SELECT id, name_ar, type FROM elements")
    if not items: return await call.answer("المتجر فارغ تماماً!", show_alert=True)
    text = "🗑 **قائمة عناصر المتجر المتوفرة للحذف:**\nأرسل رقم الـ ID للزر المراد مسحه نهائياً:\n\n"
    for i in items:
        icon = "📁" if i[2] == 'folder' else "🔗" if i[2] == 'link' else ("🔒" if i[2] == 'soon' else "💎")
        text += f"ID: `{i[0]}` | {icon} {i[1]}\n"
    await call.message.answer(text, parse_mode="Markdown")
    await state.set_state(SystemStates.wait_delete_id)

@dp.message(SystemStates.wait_delete_id)
async def execute_delete(message: types.Message, state: FSMContext):
    try:
        elem_id = int(message.text)
        db_write("DELETE FROM elements WHERE id=?", (elem_id,))
        await message.answer("✅ **تم مسح العنصر وتطهير شجرة المتجر بنجاح!**", parse_mode="Markdown")
    except:
        await message.answer("❌ الرقم المرسل غير صحيح!")
    await state.clear()

@dp.callback_query(F.data == "adm_add_balance")
async def adm_add_balance(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("👤 أرسل **معرف الايدي (ID)** للعميل المراد تزويده بالدولارات:", parse_mode="Markdown")
    await state.set_state(SystemStates.wait_add_balance_id)

@dp.message(SystemStates.wait_add_balance_id)
async def process_add_bal_id(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("❌ أرسل ارقام فقط!")
    await state.update_data(target_user=int(message.text))
    await message.answer("💵 كم **دولار** تريد إضافته لحسابه Privat؟", parse_mode="Markdown")
    await state.set_state(SystemStates.wait_add_balance_amount)

@dp.message(SystemStates.wait_add_balance_amount)
async def process_add_bal_amt(message: types.Message, state: FSMContext):
    try:
        amt = float(message.text)
        data = await state.get_data()
        db_write("UPDATE users SET balance = balance + ? WHERE user_id=?", (amt, data['target_user']))
        await message.answer(f"✅ **تم شحن حساب العميل بـ {amt}$ دولار بنجاح تامة!**", parse_mode="Markdown")
        try: 
            ul_data = db_read('SELECT lang FROM users WHERE user_id=?', (data['target_user'],))
            ul = ul_data[0][0] if ul_data and ul_data[0][0] != 'none' else 'ar'
            msg_notification = "🎁 تم شحن حسابك من قبل الإدارة بـ **{amt}$** دولار!" if ul == 'ar' else ("🎁 Your account has been charged with **${amt}** USD by admin!" if ul == 'en' else "🎁 Ваш баланс пополнен администрацией на **${amt}** USD!")
            await bot.send_message(chat_id=data['target_user'], text=msg_notification.format(amt=amt), parse_mode="Markdown")
        except: pass
    except:
        await message.answer("❌ القيمة المدخلة غير صحيحة.")
    await state.clear()

@dp.callback_query(F.data == "adm_stats")
async def adm_stats(call: types.CallbackQuery):
    u = db_read('SELECT COUNT(*) FROM users')[0][0]
    e = db_read('SELECT COUNT(*) FROM elements')[0][0]
    p = db_read('SELECT COUNT(*) FROM purchases')[0][0]
    
    stat_text = f"📊 **إحصائيات متجر Drov TG الشاملة:**\n\n👥 إجمالي العملاء المسجلين: `{u}`\n📦 إجمالي الأزرار والأقسام: `{e}`\n🛍 إجمالي السلع المباعة: `{p}`"
    
    await call.message.edit_text(text=stat_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 عودة", callback_data="super_admin_panel")]]), parse_mode="Markdown")

@dp.callback_query(F.data == "adm_broadcast")
async def adm_broadcast(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📢 أرسل نص الرسالة الإعلانية للبث والنشر الفوري للجميع:")
    await state.set_state(SystemStates.wait_broadcast)

@dp.message(SystemStates.wait_broadcast)
async def execute_broadcast(message: types.Message, state: FSMContext):
    await message.answer("🔄 جاري البث الفوري للمشتركين...")
    users = db_read('SELECT user_id FROM users')
    success = 0  
    for u in users:  
        try:  
            await bot.send_message(chat_id=u[0], text=message.text)  
            success += 1  
            await asyncio.sleep(0.05)
        except TelegramAPIError:
            continue
        except Exception:
            continue
    await message.answer(f"✅ تمت الإذاعة المطلقة بنجاح ووصلت إلى {success} مستخدم.")  
    await state.clear()

# --- دالة الاستجابة للمنفذ الوهمي لخدعة السيرفر لمنع حالة Completed ---
async def handle_ping(request):
    return web.Response(text="Drov Bot is Online and Running!")

# --- محرك التشغيل المزدوج (البوت + سيرفر الويب) ---
async def main():
    print("🚀 تشغيل السيرفر المزدوج لضمان بقاء البوت Online على Railway...")
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    asyncio.create_task(site.start())
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
