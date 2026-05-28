import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# جلب التوكن
API_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message()
async def send_welcome(message: types.Message):
    # هنا نضع القائمة (الأزرار الثابتة أسفل الشاشة)
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
    
    # التحقق من أمر البدء
    if message.text == '/start':
        await message.answer("أهلاً بك في بوت الخدمات، اختر ما تحتاجه:", reply_markup=keyboard)
    
    # إضافة ردود فعل للأزرار (مثلاً عند الضغط على شحن رصيد)
    elif message.text == "💳 شحن رصيد":
        await message.answer("قم بتحويل الرصيد إلى المعرف التالي: ...")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
