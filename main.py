import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# --- الإعدادات ---
API_TOKEN = os.getenv('BOT_TOKEN')
if not API_TOKEN:
    raise ValueError("يجب تحديد BOT_TOKEN في متغيرات البيئة!")

# --- تهيئة البوت والمخزن ---
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- تشغيل البوت ---
async def main():
    print("🚀 البوت يعمل الآن...")
    # حذف التحديثات القديمة عند البدء لتجنب تعليق البوت
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"خطأ أثناء التشغيل: {e}")
      
