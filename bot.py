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
from sqlalchemy import MetaData, Table, Column, Integer, String, BigInteger, Float, text
from dotenv import load_dotenv

load_dotenv()

# --- 1. НАСТРОЙКА БАЗЫ ДАННЫХ (PostgreSQL) ---
DB_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DB_URL)

# --- 2. НАСТРОЙКА БОТА ---
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
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
            # Используем чистый SQL для Upsert в PostgreSQL
            query = text("""
                INSERT INTO users (
                    user_id, name, gender, age, weight, height, 
                    religion, addictions, kitchen_tools, sport_tools, health_status
                ) VALUES (
                    :uid, :n, :g, :a, :w, :h, :rel, :add, :k_t, :s_t, :h_s
                )
                ON CONFLICT (user_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    gender = EXCLUDED.gender,
                    age = EXCLUDED.age,
                    weight = EXCLUDED.weight,
                    height = EXCLUDED.height,
                    religion = EXCLUDED.religion,
                    addictions = EXCLUDED.addictions,
                    kitchen_tools = EXCLUDED.kitchen_tools,
                    sport_tools = EXCLUDED.sport_tools,
                    health_status = EXCLUDED.health_status;
            """)
            
            await conn.execute(query, {
                "uid": u_id,
                "n": data.get('name', 'Атлет'),
                "g": data.get('gender'),
                "a": int(data.get('age', 0)),
                "w": float(data.get('weight', 0)),
                "h": float(data.get('height', 0)),
                "rel": data.get('religion'),
                "add": data.get('addictions'),
                "k_t": data.get('kitchen_tools'),
                "s_t": data.get('sport_tools'),
                "h_s": data.get('health_status')
            })
        
        print(f"✅ Данные юзера {u_id} (включая религию и инвентарь) сохранены.")
        return {"status": "success"}
    except Exception as e:
        print(f"❌ Ошибка SQL: {e}")
        return {"status": "error", "message": str(e)}

# --- 4. ЗАПУСК БОТА И API ---
async def main():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, loop="asyncio")
    server = uvicorn.Server(config)
    
    await asyncio.gather(
        server.serve(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")
