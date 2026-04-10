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

# Загружаем переменные окружения
load_dotenv()

# Настройка базы данных (используем SQLite для начала или твой URL из .env)
DB_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DB_URL)
metadata = MetaData()

# Описываем таблицу под твою новую анкету
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

# Главное меню, которое появится ПОСЛЕ заполнения анкеты
main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="💪 Моя тренировка"), KeyboardButton(text="📊 Профиль")],
    [KeyboardButton(text="⚙️ Настройки ИИ")]
], resize_keyboard=True)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    # Анти-кэш: добавляем текущую секунду в ссылку
    timestamp = int(time.time())
    web_app_url = f"https://ueeeq11.github.io/my-way-app/?v={timestamp}"
    
    markup = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📝 Заполнить анкету", web_app=WebAppInfo(url=web_app_url))]
    ], resize_keyboard=True)
    
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Чтобы я мог составить для тебя план тренировок, мне нужно знать твою базу.\n"
        "Жми на кнопку ниже и заполни анкету:",
        reply_markup=markup
    )

@dp.message(F.web_app_data)
async def handle_data(message: types.Message):
    try:
        # Распаковываем JSON из анкеты
        data = json.loads(message.web_app_data.data)
        
        user_id = message.from_user.id
        name = data.get('name', 'Аноним')
        gender = data.get('gender')
        age = int(data.get('age', 0))
        height = int(data.get('height', 0))
        weight = float(data.get('weight', 0))
        goal = data.get('goal')

        # Сохраняем в базу данных
        async with engine.begin() as conn:
            # Сначала пробуем создать таблицу, если её нет
            await conn.run_sync(metadata.create_all)
            
            # Записываем данные (если юзер уже есть, вылетит ошибка - обработаем её ниже)
            stmt = insert(users_table).values(
                user_id=user_id, 
                name=name, 
                gender=gender,
                age=age, 
                height=height, 
                weight=weight, 
                goal=goal
            )
            await conn.execute(stmt)

        # Текст ответа в зависимости от цели
        goals_map = {
            'weight_loss': 'Похудение 📉',
            'muscle_gain': 'Набор массы 📈',
            'keep_fit': 'Поддержание формы ✨'
        }
        
        res_goal = goals_map.get(goal, goal)

        await message.answer(
            f"✅ **Данные приняты, {name}!**\n\n"
            f"Твои параметры:\n"
            f"— Пол: {'Мужской' if gender == 'male' else 'Женский'}\n"
            f"— Возраст: {age} лет\n"
            f"— Рост/Вес: {height}см / {weight}кг\n"
            f"— Цель: {res_goal}\n\n"
            "Теперь ты можешь пользоваться главным меню:",
            reply_markup=main_menu,
            parse_mode="Markdown"
        )

    except Exception as e:
        # Если юзер уже есть в базе, SQLAlchemy выдаст ошибку IntegrityError
        # Для начала просто напишем, что данные обновлены
        await message.answer(
            "Твой профиль уже существует! Если хочешь изменить данные, "
            "просто заполни анкету еще раз (функция обновления будет скоро).",
            reply_markup=main_menu
        )
        print(f"Ошибка БД: {e}")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
