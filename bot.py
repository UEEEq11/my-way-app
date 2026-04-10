import asyncio
import json
import os
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardRemove, FSInputFile
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

# Словарь для хранения ID последнего "вечного" сообщения для каждого юзера
last_main_message = {}

async def delete_message_after(chat_id: int, message_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    timestamp = int(time.time())
    web_app_url = f"https://ueeeq11.github.io/my-way-app/?v={timestamp}"
    
    # 1. Удаляем ПРЕДЫДУЩЕЕ главное сообщение, если оно было
    if user_id in last_main_message:
        try:
            await bot.delete_message(message.chat.id, last_main_message[user_id])
        except Exception:
            pass

    # 2. Убираем старую серую кнопку внизу (ReplyKeyboardRemove)
    temp_msg = await message.answer("Обновление интерфейса...", reply_markup=ReplyKeyboardRemove())
    asyncio.create_task(delete_message_after(message.chat.id, temp_msg.message_id, 3))
    
    # 3. Удаляем саму команду /start от юзера
    asyncio.create_task(delete_message_after(message.chat.id, message.message_id, 3))

    # Настройка кнопки
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 ОТКРЫТЬ MY WAY", web_app=WebAppInfo(url=web_app_url))]
    ])

    caption_text = (
        "✨ **MY WAY — ТВОЙ ЛИЧНЫЙ ПУТЬ**\n\n"
        "Твой прогресс не терпит суеты. Мы подготовили всё для твоей трансформации в одном приложении.\n\n"
        "📊 **Доступные модули:**\n"
        "├ Контроль КБЖУ и веса\n"
        "├ Тренировочные сплиты\n"
        "└ Аналитика активности\n\n"
        "🚀 *Нажми кнопку ниже, чтобы войти:*"
    )

    # 4. Отправляем новое "вечное" сообщение (с фото или без)
    new_msg = None
    if os.path.exists("banner.jpg"):
        photo = FSInputFile("banner.jpg")
        new_msg = await message.answer_photo(
            photo=photo,
            caption=caption_text,
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        new_msg = await message.answer(
            text=caption_text,
            reply_markup=markup,
            parse_mode="Markdown"
        )
    
    # Запоминаем ID, чтобы удалить его при следующем /start
    last_main_message[user_id] = new_msg.message_id

@dp.message(F.web_app_data)
async def handle_data(message: types.Message):
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
        
        res = await message.answer("✅ Данные синхронизированы!")
        asyncio.create_task(delete_message_after(message.chat.id, res.message_id, 30))
        
    except Exception:
        res = await message.answer("💪 Рады видеть тебя снова!")
        asyncio.create_task(delete_message_after(message.chat.id, res.message_id, 30))

async def main():
    print("Бот запущен. Режим 'Чистый чат' активен.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
