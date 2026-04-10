import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart

# Твой токен уже здесь
TOKEN = "8687055249:AAHJVSsNyBAu4COckMIYf_9UGL9PFe0CGTI"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Приветствие
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Привет! Нажми на кнопку меню, чтобы заполнить анкету.")

# Тот самый «приемник» данных из Web App
@dp.message(F.web_app_data)
async def handle_data(message: types.Message):
    try:
        # Превращаем данные из анкеты в понятный для Python словарь
        data = json.loads(message.web_app_data.data)
        
        # Берем имя из данных анкеты или пишем "Друг", если имени нет
        name = data.get('name') or "Друг"
        
        await message.answer(f"✅ Данные получены, {name}!\nЯ всё запомнил. Скоро начнем.")
    except Exception as e:
        await message.answer("Произошла ошибка при обработке данных.")

async def main():
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())