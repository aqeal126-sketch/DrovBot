import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# جلب التوكن من إعدادات Railway
API_TOKEN = os.getenv('BOT_TOKEN')
# ضع رقم قناتك هنا الذي استخرجناه:
CHANNEL_ID = "-1003077671245" 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# القائمة الثابتة (التي تظهر أسفل الشاشة)
def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 شراء حساب"), KeyboardButton(text="📞 SMS - NUMBER")],
            [KeyboardButton(text="📂 شراء جلسات"), KeyboardButton(text="💻 الدعم الفني")],
            [KeyboardButton(text="💳 شحن رصيد")],
            [KeyboardButton(text="✅ قناة التفعيلات"), KeyboardButton(text="⚙️ مشترياتي")],
            [KeyboardButton(text="🔗 الإحالة")]
        ],
        resize_keyboard=True
    )

@dp.message()
async def handle_messages(message: types.Message):
    
    # 1. أمر البدء
    if message.text == '/start':
        user_id = message.from_user.id
        text = (
            f"أهلاً بك في - 𝗗𝗿𝗼𝘃 𝗧𝗚 👋\n\n"
            f"🚀 أقوى سوق لبيع وشراء حسابات تيليجرام الجاهزة والجديدة لجميع الدول حول العالم 🌐.\n\n"
            f"- ايديك: {user_id} 🆔.\n"
            f"- 👍 رصيدك: 0.0$ 💵.\n\n"
            f"👍 ابدأ باستخدام البوت الآن بالضغط على الأزرار بالأسفل ⬇️."
        )
        await message.answer(text, reply_markup=get_main_menu())

    # 2. زر قناة التفعيلات
    elif message.text == "✅ قناة التفعيلات":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 اضغط للذهاب للقناة", url="https://t.me/drov70")]
        ])
        await message.answer("تفضل، هذه هي قناة التفعيلات الخاصة بنا:", reply_markup=kb)

    # 3. زر الإحالة
    elif message.text == "🔗 الإحالة":
        user_id = message.from_user.id
        link = f"https://t.me/dro7bot?start={user_id}"
        await message.answer(f"🤑 ⌯ إربح دولارات الآن مجاناً عبر مشاركة رابط البوت:\n\n{link}")

    # 4. زر الدعم الفني
    elif message.text == "💻 الدعم الفني":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 اضغط هنا للتحويل للخاص", url="https://t.me/xq_7d")]
        ])
        await message.answer("للتواصل مع الإدارة مباشرة:", reply_markup=kb)

    # 5. محاكاة الشراء وإرسال تقرير للقناة (مثال)
    elif message.text == "🛒 شراء حساب":
        await message.answer("تمت عملية الشراء! جاري معالجة الطلب...")
        report = (
            f"- تم شراء حساب جديد من البوت\n\n"
            f"- الدولة : العراق 🇮🇶\n"
            f"- المنصة : تليجرام\n"
            f"- الرقم : *****88\n"
            f"- السعر : 1.5$\n"
            f"- العميل : {message.from_user.id}\n"
            f"- كود التفعيل : 12345\n"
            f"- الحالة : تم التفعيل ✅\n"
            f"- التاريخ : {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        try:
            await bot.send_message(CHANNEL_ID, report)
        except Exception as e:
            await message.answer("حدث خطأ أثناء إرسال التقرير للقناة، تأكد أن البوت مشرف فيها!")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
