import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import insert, MetaData, Table, Column, Integer, String, BigInteger, Float
from dotenv import load_dotenv

load_dotenv()

# Настройка базы
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
    # Ссылка на твой обновленный GitHub Pages
    web_app_url = "https://ueeeq11.github.io/my-way-app/"
    
    markup = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📝 Заполнить новую анкету", web_app=WebAppInfo(url=web_app_url))]
    ], resize_keyboard=True)
    
    await message.answer("Привет! Твоя база готова. Давай заполним анкету!", reply_markup=markup)

@dp.message(F.web_app_data)
async def handle_data(message: types.Message):
    data = json.loads(message.web_app_data.data)
    
    # Собираем данные из новой анкеты
    user_id = message.from_user.id
    name = data.get('name')
    gender = data.get('gender')
    age = int(data.get('age', 0))
    height = int(data.get('height', 0))
    weight = float(data.get('weight', 0))
    goal = data.get('goal')

    async with engine.begin() as conn:
        # Пытаемся сохранить
        stmt = insert(users_table).values(
            user_id=user_id, name=name, gender=gender,
            age=age, height=height, weight=weight, goal=goal
        )
        try:
            await conn.execute(stmt)
            await message.answer(f"✅ Готово, {name}! Данные в базе.\nВозраст: {age}, Вес: {weight} кг, Цель: {goal}.\n\nСкоро я подготовлю план!")
        except Exception as e:
            await message.answer("Данные обновлены! (или ты уже есть в базе)")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
