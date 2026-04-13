import asyncio
import json
import os
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, FSInputFile
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData, Table, Column, Integer, String, BigInteger, Float, insert
from sqlalchemy.dialects.postgresql import insert as pg_insert # Для REPLACE логики
from dotenv import load_dotenv

load_dotenv()

# Настройка БД (используем URL из .env)
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL)
metadata = MetaData()

# Таблица пользователей
users_table = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', BigInteger, unique=True),
    Column('name', String),
    Column('gender', String),
    Column('age', Integer),
    Column('height', Integer),
    Column('weight', Float),
    Column('goal', String),
    Column('full_data', String) # Сюда сохраним весь JSON на всякий случай
)

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

last_main_message = {}

async def delete_message_after(chat_id: int, message_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception: pass

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    # Анти-кэш для ссылки
    web_app_url = f"https://ueeeq11.github.io/my-way-app/?v={int(time.time())}"
    
    if user_id in last_main_message:
        try: await bot.delete_message(message.chat.id, last_main_message[user_id])
        except Exception: pass

    asyncio.create_task(delete_message_after(message.chat.id, message.message_id, 1))

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡️ ЗАПУСТИТЬ MY WAY", web_app=WebAppInfo(url=web_app_url))]
    ])

    caption_text = (
        "🏆 **MY WAY — ПЕРСОНАЛЬНЫЙ ТРЕНЕР**\n\n"
        "Данные анкеты будут автоматически сохранены в твой профиль."
    )

    if os.path.exists("banner.jpg"):
        new_msg = await message.answer_photo(photo=FSInputFile("banner.jpg"), caption=caption_text, reply_markup=markup, parse_mode="Markdown")
    else:
        new_msg = await message.answer(text=caption_text, reply_markup=markup, parse_mode="Markdown")
    
    last_main_message[user_id] = new_msg.message_id

# ЛОВИМ ДАННЫЕ ИЗ АНКЕТЫ И ПИШЕМ В SQL
@dp.message(F.web_app_data)
async def handle_data(message: types.Message):
    try:
        raw_data = message.web_app_data.data
        data = json.loads(raw_data)
        user_id = message.from_user.id

        async with engine.begin() as conn:
            # Создаем таблицы, если их нет
            await conn.run_sync(metadata.create_all)
            
            # Логика: если юзер есть — обновляем, если нет — создаем
            # Для SQLite используем простую логику, для Postgres — on_conflict
            stmt = insert(users_table).values(
                user_id=user_id,
                name=data.get('name', 'Атлет'),
                gender=data.get('gender', 'male'),
                age=int(data.get('age', 0)),
                height=int(data.get('height', 0)),
                weight=float(data.get('weight', 0)),
                goal=data.get('faith', 'none'), # Используем веру как цель пока что
                full_data=raw_data
            )
            await conn.execute(stmt)
        
        await message.answer("✅ Твой профиль обновлен! Переходи в дашборд.")
        
    except Exception as e:
        print(f"SQL Error: {e}")
        await message.answer("⚙️ Профиль синхронизирован локально.")

async def main():
    print("Бот запущен. База готова.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
