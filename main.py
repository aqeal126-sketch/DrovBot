import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# جلب التوكن
API_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    # إنشاء الأزرار (Inline)
    markup = InlineKeyboardMarkup()
    btn1 = InlineKeyboardButton("زر 1", callback_data="btn1")
    btn2 = InlineKeyboardButton("زر 2", callback_data="btn2")
    markup.add(btn1, btn2)

    # إرسال الرسالة مع الأزرار
    await message.answer("أهلاً بك! هذه هي الأزرار تحت الرسالة:", reply_markup=markup)

# معالجة الضغط على الزر
@dp.callback_query_handler(lambda c: c.data == 'btn1')
async def handle_btn1(callback_query: types.CallbackQuery):
    await callback_query.answer("تم الضغط!")
    await bot.send_message(callback_query.from_user.id, "أحسنت! هذا هو الزر الأول.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    
