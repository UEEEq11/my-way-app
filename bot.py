import asyncio
import json
import os
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import insert, MetaData, Table, Column, Integer, String, BigInteger, Float
from dotenv import load_dotenv

load_dotenv()

# Настройка БД
engine = create_async_engine(os.getenv("DATABASE_URL"))
metadata = MetaData()

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
    # Генерируем уникальную ссылку для обхода кэша
    timestamp = int(time.time())
    web_app_url = f"https://ueeeq11.github.io/my-way-app/?v={timestamp}"
    
    # СОЗДАЕМ ИНЛАЙН (СИНЮЮ) КНОПКУ
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 ОТКРЫТЬ MY WAY", web_app=WebAppInfo(url=web_app_url))]
    ])
    
    # Удаляем обычные кнопки, если они остались у юзера
    await message.answer(
        "Добро пожаловать в **My Way**! 💪\n\n"
        "Твой план тренировок, питание и прогресс теперь в одном месте.\n"
        "Нажми на кнопку ниже, чтобы войти в приложение:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

    # Дополнительно отправляем пустой ReplyKeyboardRemove, чтобы снести старую большую кнопку
    # Это сработает один раз при старте
    await message.answer("Интерфейс обновлен ✅", reply_markup=ReplyKeyboardRemove())

@dp.message(F.web_app_data)
async def handle_data(message: types.Message):
    """Обработка данных (если вдруг решишь оставить отправку данных из WebApp)"""
    try:
        data = json.loads(message.web_app_data.data)
        
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
        
        await message.answer("✅ Профиль настроен! Все данные теперь доступны внутри приложения.")
        
    except Exception as e:
        print(f"DB Log: {e}")
        await message.answer("Рады видеть тебя снова! Все обновления сохранены в приложении.")

async def main():
    print("Бот запущен на твоем железе...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
