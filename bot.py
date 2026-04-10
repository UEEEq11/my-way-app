import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    exit("Ошибка: BOT_TOKEN не найден в файле .env")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Привет! Твой бот запущен и работает из облака. Нажми на кнопку меню!")

@dp.message(F.web_app_data)
async def handle_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        name = data.get('name') or "Друг"
        await message.answer(f"✅ Данные получены, {name}!")
    except Exception as e:
        await message.answer("Ошибка при чтении данных.")

async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
