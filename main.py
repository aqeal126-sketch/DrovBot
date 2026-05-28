import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# جلب التوكن من Railway
API_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# دالة القائمة الرئيسية
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
    # أمر البدء
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

    # زر الإحالة
    elif message.text == "🔗 الإحالة":
        user_id = message.from_user.id
        link = f"https://t.me/dro7bot?start={user_id}"
        text = (
            f"🤑 ⌯ إربح دولارات الآن مجاناً عبر مشاركة رابط البوت إلى أصدقائك 👥 "
            f"واحصل على 0.01 دولار مقابل كل شخص يقوم بالدخول إلى البوت عبر الرابط الخاص بك ✅.\n\n"
            f"رابطك الخاص:\n{link}"
        )
        await message.answer(text)

    # زر الدعم الفني
    elif message.text == "💻 الدعم الفني":
        support_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 اضغط هنا للتحويل للخاص", url="https://t.me/xq_7d")]
        ])
        await message.answer("أهلاً بك! يمكنك التواصل مع الإدارة مباشرة عبر الرابط بالأسفل:", reply_markup=support_kb)

    # ردود افتراضية للأزرار الأخرى
    elif message.text in ["🛒 شراء حساب", "📞 SMS - NUMBER", "📂 شراء جلسات", "💳 شحن رصيد", "✅ قناة التفعيلات", "⚙️ مشترياتي"]:
        await message.answer(f"لقد اخترت: {message.text} - هذا القسم تحت التطوير حالياً، انتظر التحديثات!")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
