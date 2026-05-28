import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

# إعدادات البوت
API_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = "-1003077671245" 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# دالة الأزرار الملاصقة (بدون قائمة سفلية)
def get_inline_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 شراء حساب", callback_data="buy_acc")],
        [InlineKeyboardButton(text="📂 شراء جلسات", callback_data="buy_ses"), InlineKeyboardButton(text="📞 SMS - NUMBER", callback_data="sms")],
        [InlineKeyboardButton(text="👤 الدعم الفني", url="https://t.me/xq_7d"), InlineKeyboardButton(text="🌐 الوكلاء", callback_data="agents")],
        [InlineKeyboardButton(text="💳 شحن رصيد", callback_data="charge")],
        [InlineKeyboardButton(text="✅ قناة التفعيلات", url="https://t.me/drov70"), InlineKeyboardButton(text="⚙️ مشترياتي", callback_data="my_orders")],
        [InlineKeyboardButton(text="🔗 الإحالة", callback_data="referral")]
    ])

@dp.message()
async def handle_messages(message: types.Message):
    # أمر البدء - يحذف القائمة القديمة ويرسل الجديد
    if message.text == '/start':
        await message.answer("مرحباً بك في Drov TG", reply_markup=ReplyKeyboardRemove())
        
        user_id = message.from_user.id
        text = (
            f"أهلاً بك في - 𝗗𝗿𝗼𝘃 𝗧𝗚 👋\n\n"
            f"🚀 أقوى سوق لبيع وشراء حسابات تيليجرام الجاهزة والجديدة 🌐.\n\n"
            f"- ايديك: {user_id} 🆔.\n"
            f"- 👍 رصيدك: 0.0$ 💵.\n\n"
            f"👍 ابدأ باستخدام البوت الآن بالضغط على الأزرار بالأسفل ⬇️."
        )
        await message.answer(text, reply_markup=get_inline_menu())

    # تجربة زر الإحالة
    if message.text == "🔗 الإحالة": # إذا حاول الضغط عليها من مكان آخر
        user_id = message.from_user.id
        await message.answer(f"رابطك الخاص:\nhttps://t.me/dro7bot?start={user_id}")

@dp.callback_query()
async def callback_handler(call: types.CallbackQuery):
    # نظام الإحالة عند الضغط على الزر
    if call.data == "referral":
        link = f"https://t.me/dro7bot?start={call.from_user.id}"
        await call.message.answer(f"🤑 ⌯ إربح دولارات الآن مجاناً عبر مشاركة رابط البوت:\n\n{link}")
    
    # مثال محاكاة الشراء (عند الضغط على شراء حساب)
    elif call.data == "buy_acc":
        await call.message.answer("تمت عملية الشراء! جاري إرسال التقرير لقناة التفعيلات...")
        report = (
            f"- تم شراء حساب جديد من البوت\n\n"
            f"- الدولة : العراق 🇮🇶\n"
            f"- المنصة : تليجرام\n"
            f"- الرقم : *****88\n"
            f"- السعر : 1.5$\n"
            f"- العميل : {call.from_user.id}\n"
            f"- الحالة : تم التفعيل ✅\n"
            f"- التاريخ : {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        try:
            await bot.send_message(CHANNEL_ID, report)
        except:
            await call.message.answer("خطأ: تأكد أن البوت مشرف في القناة!")
            
    await call.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
