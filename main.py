import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# جلب التوكن
API_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# دالة لإنشاء الأزرار (مرتبة كما في الصورة)
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 شراء حساب 📧", callback_data="buy_acc")],
        [InlineKeyboardButton(text="📂 شراء جلسات", callback_data="buy_ses"), InlineKeyboardButton(text="📞 SMS - NUMBER", callback_data="sms")],
        [InlineKeyboardButton(text="👤 الدعم الفني", url="https://t.me/xq_7d"), InlineKeyboardButton(text="🌐 الوكلاء", callback_data="agents")],
        [InlineKeyboardButton(text="💳 شحن رصيد", callback_data="charge")],
        [InlineKeyboardButton(text="✅ قناة التفعيلات", url="https://t.me/drov70"), InlineKeyboardButton(text="⚙️ مشترياتي", callback_data="my_orders")],
        [InlineKeyboardButton(text="🔗 الإحالة", callback_data="referral")]
    ])

# دالة معالجة الرسائل
@dp.message()
async def handle_messages(message: types.Message):
    # استخدام message.answer فقط عند استلام الأمر /start
    if message.text == '/start':
        user_id = message.from_user.id
        text = (
            f"أهلاً بك في - 𝗗𝗿𝗼𝘃 𝗧𝗚 👋\n\n"
            f"🚀 أقوى سوق لبيع وشراء حسابات تيليجرام الجاهزة والجديدة حول العالم 🌐.\n\n"
            f"- ايديك: {user_id} 🆔.\n"
            f"- 👍 رصيدك: 0.0$ 💵.\n\n"
            f"👍 ابدأ باستخدام البوت الآن بالضغط على الأزرار بالأسفل ⬇️."
        )
        # إرسال الرسالة مع الأزرار
        await message.answer(text, reply_markup=get_main_menu())

    # لكي لا تتكرر الرسالة إذا ضغط المستخدم على الأزرار، نستخدم callback_query_handler
    # (هذا الجزء يمنع تكرار الرسالة عند التفاعل)

@dp.callback_query()
async def callback_handler(call: types.CallbackQuery):
    # هنا تضع الردود على الأزرار (مثلاً عند الضغط على شحن رصيد)
    if call.data == "charge":
        await call.message.answer("لشحن الرصيد يرجى التواصل مع الإدارة.")
    await call.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
