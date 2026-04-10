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

async def delete_message_after(chat_id: int, message_id: int, delay: int):
    """Фоновая задача для удаления сообщения через заданное время"""
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass # Сообщение уже удалено

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    # Генерируем ссылку с таймстампом против кэша
    timestamp = int(time.time())
    web_app_url = f"https://ueeeq11.github.io/my-way-app/?v={timestamp}"
    
    # СИНЯЯ КНОПКА ПОД СООБЩЕНИЕМ
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 ВОЙТИ В MY WAY", web_app=WebAppInfo(url=web_app_url))]
    ])
    
    # 1. Удаляем старую большую кнопку снизу экрана (если она была)
    clean_kb = await message.answer("Обновление интерфейса...", reply_markup=ReplyKeyboardRemove())
    asyncio.create_task(delete_message_after(message.chat.id, clean_kb.message_id, 3)) # Удалим через 3 сек

    # 2. Удаляем команду /start от юзера, чтобы не мусорить в чате
    asyncio.create_task(delete_message_after(message.chat.id, message.message_id, 3))
    
    # 3. Отправляем ГЛАВНОЕ сообщение, которое останется в чате
    await message.answer(
        "👋 **Добро пожаловать в твой личный кабинет My Way.**\n\n"
        "Здесь нет лишнего шума — только твой прогресс.\n"
        "Используй кнопку ниже для доступа к приложению.",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@dp.message(F.web_app_data)
async def handle_data(message: types.Message):
    """Сохраняем данные анкеты в БД"""
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
        
        # Это сообщение само удалится через 5 минут
        success_msg = await message.answer("✅ Профиль настроен!")
        asyncio.create_task(delete_message_after(message.chat.id, success_msg.message_id, 300))
        
    except Exception as e:
        print(f"DB Log: {e}")
        # Если юзер просто перезашел
        welcome_back = await message.answer("С возвращением! Все данные сохранены.")
        asyncio.create_task(delete_message_after(message.chat.id, welcome_back.message_id, 300))

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
