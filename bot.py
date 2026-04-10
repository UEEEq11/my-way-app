import asyncio
import json
import os
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import insert, MetaData, Table, Column, Integer, String, BigInteger, Float
from dotenv import load_dotenv

# Загружаем ключи
load_dotenv()

# Настройка базы данных
engine = create_async_engine(os.getenv("DATABASE_URL"))
metadata = MetaData()

# Таблица пользователей (под актуальную анкету)
users_table = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', BigInteger, unique=True),
    Column('name', String),
    Column('gender', String),
    Column('age', Integer),
    Column('height', Integer),
    Column('weight', Float),
    Column('goal', String)
)

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    # Уникальный timestamp для обхода кэша Telegram
    timestamp = int(time.time())
    web_app_url = f"https://ueeeq11.github.io/my-way-app/?v={timestamp}"
    
    # Оставляем только ОДНУ главную кнопку входа в приложение
    markup = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Открыть My Way", web_app=WebAppInfo(url=web_app_url))]
    ], resize_keyboard=True)
    
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Это **My Way** — твой личный ИИ-тренер.\n"
        "Внутри тебя ждут тренировки, план питания и трекер прогресса.\n\n"
        "Нажми кнопку ниже, чтобы войти в приложение:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@dp.message(F.web_app_data)
async def handle_data(message: types.Message):
    """Этот обработчик сработает, когда анкета в Mini App нажмет 'Завершить'"""
    try:
        data = json.loads(message.web_app_data.data)
        
        # Если это данные анкеты
        if data.get('action') == 'survey_done' or 'name' in data:
            async with engine.begin() as conn:
                await conn.run_sync(metadata.create_all)
                
                stmt = insert(users_table).values(
                    user_id=message.from_user.id,
                    name=data.get('name'),
                    gender=data.get('gender'),
                    age=int(data.get('age', 0)),
                    height=int(data.get('height', 0)),
                    weight=float(data.get('weight', 0)),
                    goal=data.get('goal')
                )
                await conn.execute(stmt)
            
            # В чат пишем только подтверждение, всё остальное юзер видит в приложении
            await message.answer("✅ Профиль успешно создан! Теперь все функции доступны в приложении.")

    except Exception as e:
        # Если юзер уже есть в базе
        print(f"Log: {e}")
        await message.answer("С возвращением! Твои данные уже обновлены.")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
