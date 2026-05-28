import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# جلب التوكن
API_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message()
async def send_welcome(message: types.Message):
    if message.text == '/start':
        # إنشاء الأزرار
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="زر 1", callback_data="btn1"),
             InlineKeyboardButton(text="زر 2", callback_data="btn2")]
        ])
        await message.answer("أهلاً بك! هذه هي الأزرار:", reply_markup=markup)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
