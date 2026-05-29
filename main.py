import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- الإعدادات ---
API_TOKEN = os.getenv('BOT_TOKEN')
SUPER_ADMIN = 8333784255
REQ_CHANNEL = "@drov8" # القناة المطلوبة

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- دالة فحص الاشتراك ---
async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=REQ_CHANNEL, user_id=user_id)
        # إذا كان عضو أو مشرف أو مالك، يعني مشترك
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# --- الكيبورد ---
def get_start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 اشترك في القناة", url=f"https://t.me/{REQ_CHANNEL.replace('@', '')}")],
        [InlineKeyboardButton(text="✅ تأكيد الاشتراك", callback_data="check_sub")]
    ])

# --- أمر البداية ---
@dp.message(CommandStart())
async def start(message: types.Message):
    if await is_subscribed(message.from_user.id):
        await message.answer("أهلاً بك في المتجر الرئيسي! 🛒", reply_markup=get_main_kb())
    else:
        await message.answer("❌ عذراً، يجب عليك الاشتراك في القناة أولاً لفتح المتجر:", reply_markup=get_start_kb())

# --- معالج تأكيد الاشتراك ---
@dp.callback_query(F.data == "check_sub")
async def check_sub_handler(call: types.CallbackQuery):
    if await is_subscribed(call.from_user.id):
        await call.message.edit_text("✅ شكراً لاشتراكك! تم فتح المتجر.", reply_markup=get_main_kb())
    else:
        await call.answer("❌ لم تشترك بعد! يرجى الاشتراك ثم الضغط مجدداً.", show_alert=True)

def get_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 تصفح المنتجات", callback_data="products")]
    ])

# --- تشغيل ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
