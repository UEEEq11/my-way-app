import asyncio
import os
import json
import time
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import MetaData, Table, Column, Integer, String, BigInteger, Float, insert
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert
from dotenv import load_dotenv

load_dotenv()

# --- 1. НАСТРОЙКА БАЗЫ ДАННЫХ ---
# Используем SQLite (файл users_data.db), если в .env не указано иное
DB_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./users_data.db")
engine = create_async_engine(DB_URL)
metadata = MetaData()

users_table = Table('users', metadata,
    Column('user_id', BigInteger, primary_key=True),
    Column('name', String),
    Column('age', Integer),
    Column('height', Integer),
    Column('weight', Float),
    Column('data_json', String) # Сюда сохраним всё остальное (цели, веру и т.д.)
)

# --- 2. НАСТРОЙКА БОТА ---
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    # Анти-кэш ссылка
    web_app_url = f"https://ueeeq11.github.io/my-way-app/?v={int(time.time())}"
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡️ ЗАПУСТИТЬ MY WAY", web_app=WebAppInfo(url=web_app_url))]
    ])

    caption_text = (
        "🏆 **MY WAY — ТВОЙ ПУТЬ К ТРАНСФОРМАЦИИ**\n\n"
        "Заполни анкету, и мы сформируем твою личную карту прогресса."
    )

    if os.path.exists("banner.jpg"):
        await message.answer_photo(photo=FSInputFile("banner.jpg"), caption=caption_text, reply_markup=markup, parse_mode="Markdown")
    else:
        await message.answer(text=caption_text, reply_markup=markup, parse_mode="Markdown")

# --- 3. НАСТРОЙКА API (FastAPI) ---
app = FastAPI()

# Это важно, чтобы браузер (Mini App) мог слать запросы на твой сервер
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/save")
async def save_survey_data(request: Request):
    try:
        data = await request.json()
        u_id = int(data.get("user_id", 0))
        
        if u_id == 0:
            return {"status": "error", "message": "no user_id"}

        async with engine.begin() as conn:
            # Создаем таблицы, если их нет
            await conn.run_sync(metadata.create_all)
            
            # Логика "Добавь или Обнови" (Upsert)
            stmt = sqlite_upsert(users_table).values(
                user_id=u_id,
                name=data.get('name', 'Атлет'),
                age=int(data.get('age', 0)),
                height=int(data.get('height', 0)),
                weight=float(data.get('weight', 0)),
                data_json=json.dumps(data)
            )
            # Если такой user_id уже есть — обновляем поля
            stmt = stmt.on_conflict_do_update(
                index_elements=['user_id'],
                set_={
                    "name": stmt.excluded.name,
                    "age": stmt.excluded.age,
                    "height": stmt.excluded.height,
                    "weight": stmt.excluded.weight,
                    "data_json": stmt.excluded.data_json
                }
            )
            await conn.execute(stmt)
        
        print(f"✅ Данные юзера {u_id} сохранены в SQL")
        return {"status": "success"}
    except Exception as e:
        print(f"❌ Ошибка SQL: {e}")
        return {"status": "error", "message": str(e)}

# --- 4. ЗАПУСК БОТА И API ---
async def main():
    # Запускаем FastAPI на порту 8000 в фоновом режиме
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, loop="asyncio")
    server = uvicorn.Server(config)
    
    # Используем gather, чтобы бот и сервер работали одновременно
    await asyncio.gather(
        server.serve(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")
