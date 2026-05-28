import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# التوكن الخاص بمتجر Drov TG
import os
API_TOKEN = os.getenv('BOT_TOKEN')


bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# تصميم الأزرار
def main_menu():
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 شراء حساب"), KeyboardButton(text="💰 شحن الرصيد")],
            [KeyboardButton(text="👤 ملفي الشخصي"), KeyboardButton(text="📞 الدعم الفني")]
        ],
        resize_keyboard=True
    )
    return markup

# أمر البدء
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        f"أهلاً بك يا {message.from_user.first_name} في 𝗗𝗿𝗼𝘃 𝗧𝗚 💎\n\n"
        "أقوى سوق لبيع حسابات تليجرام جاهزة.",
        reply_markup=main_menu()
    )

# دالة التشغيل الحديثة
async def main():
    print("البوت يعمل الآن..")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
