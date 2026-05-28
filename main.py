import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# جلب التوكن من Railway
API_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# تعريف القائمة الثابتة (مثل ديفل)
def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 شراء حساب"), KeyboardButton(text="📞 SMS - NUMBER")],
            [KeyboardButton(text="📂 شراء جلسات"), KeyboardButton(text="🌐 الوكلاء")],
            [KeyboardButton(text="💳 شحن رصيد")],
            [KeyboardButton(text="✅ قناة التفعيلات"), KeyboardButton(text="⚙️ مشترياتي")],
            [KeyboardButton(text="🔗 الإحالة")]
        ],
        resize_keyboard=True
    )
    return keyboard

@dp.message()
async def handle_messages(message: types.Message):
    if message.text == '/start':
        user_id = message.from_user.id
        # رسالتك الترحيبية مع المتغيرات
        text = (
            f"أهلاً بك في - 𝗗𝗿𝗼𝘃 𝗧𝗚 👋\n\n"
            f"🚀 أقوى سوق لبيع وشراء حسابات تيليجرام الجاهزة والجديدة لجميع الدول حول العالم 🌐.\n\n"
            f"- ايديك: {user_id} 🆔.\n"
            f"- 👍 رصيدك: 0.0$ 💵.\n\n"
            f"👍 ابدأ باستخدام البوت الآن بالضغط على الأزرار بالأسفل ⬇️."
        )
        await message.answer(text, reply_markup=get_main_menu())
    
    # يمكنك إضافة ردود للأزرار هنا مستقبلاً
    elif message.text == "💳 شحن رصيد":
        await message.answer("يرجى إرسال وصل التحويل للإدارة.")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
