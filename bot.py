print("БОТ СТАРТУЕТ")
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
import aiosqlite
from dotenv import load_dotenv

# --- LOAD ENV ---
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- DATABASE ---
async def init_db():
    async with aiosqlite.connect("fitness.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            user_id INTEGER,
            exercise TEXT,
            weight INTEGER,
            reps INTEGER
        )
        """)
        await db.commit()

# --- KEYBOARDS ---
level_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Легкий"), KeyboardButton(text="Продвинутый")]],
    resize_keyboard=True
)

menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Программа")],
        [KeyboardButton(text="Записать тренировку")],
        [KeyboardButton(text="Прогресс")]
    ],
    resize_keyboard=True
)

exercise_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Жим гантелей"), KeyboardButton(text="Разводка")],
        [KeyboardButton(text="Брусья"), KeyboardButton(text="Бицепс")],
        [KeyboardButton(text="Назад")]
    ],
    resize_keyboard=True
)

# --- USER DATA ---
user_level = {}
user_data = {}

# --- GIFS ---
GIFS = {
    "Жим гантелей": "https://media.giphy.com/media/3o7TKMt1VVNkHV2PaE/giphy.gif",
    "Разводка": "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
    "Брусья": "https://media.giphy.com/media/26gsspfbt1HfVQ9va/giphy.gif",
    "Бицепс": "https://media.giphy.com/media/xT0GqeSlGSRQut8KOk/giphy.gif"
}

# --- START ---
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("💪 Привет! Давай сделаем тебя сильнее!", reply_markup=level_kb)

# --- LEVEL ---
@dp.message(F.text.in_(["Легкий", "Продвинутый"]))
async def set_level(message: types.Message):
    user_level[message.from_user.id] = message.text
    await message.answer("Уровень выбран ✅", reply_markup=menu_kb)

# --- PROGRAM ---
@dp.message(F.text == "Программа")
async def program(message: types.Message):
    level = user_level.get(message.from_user.id)

    if level == "Легкий":
        text = (
            "📅 День 1:\nЖим гантелей\nРазводка\nБрусья\nБицепс\n\n"
            "📅 День 2:\nНоги\n\n📅 День 3:\nСпина и плечи"
        )
    else:
        text = (
            "🔥 Продвинутый уровень\n\n"
            "📅 День 1: Жим штанги\n"
            "📅 День 2: Становая\n"
            "📅 День 3: Спина"
        )

    await message.answer(text)

# --- START WORKOUT LOG ---
@dp.message(F.text == "Записать тренировку")
async def choose_exercise(message: types.Message):
    user_data[message.from_user.id] = {"state": "choose_ex"}
    await message.answer("Выбери упражнение:", reply_markup=exercise_kb)

# --- BACK BUTTON ---
@dp.message(F.text == "Назад")
async def go_back(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer("Главное меню", reply_markup=menu_kb)

# --- EXERCISE ---
@dp.message(F.text.in_(["Жим гантелей", "Разводка", "Брусья", "Бицепс"]))
async def exercise_selected(message: types.Message):
    user_data[message.from_user.id] = {
        "state": "enter_weight",
        "exercise": message.text
    }

    gif = GIFS.get(message.text)
    if gif:
        await message.answer_animation(gif)

    await message.answer("Введи вес (число):")

# --- WEIGHT ---
@dp.message(lambda msg: user_data.get(msg.from_user.id, {}).get("state") == "enter_weight")
async def enter_weight(message: types.Message):
    if not message.text.isdigit():
        await message.answer("❗ Введи число (например 10)")
        return

    user_data[message.from_user.id]["weight"] = int(message.text)
    user_data[message.from_user.id]["state"] = "enter_reps"

    await message.answer("Теперь введи повторения:")

# --- REPS ---
@dp.message(lambda msg: user_data.get(msg.from_user.id, {}).get("state") == "enter_reps")
async def enter_reps(message: types.Message):
    if not message.text.isdigit():
        await message.answer("❗ Введи число")
        return

    data = user_data.get(message.from_user.id)

    async with aiosqlite.connect("fitness.db") as db:
        await db.execute(
            "INSERT INTO progress VALUES (?, ?, ?, ?)",
            (
                message.from_user.id,
                data["exercise"],
                int(data["weight"]),
                int(message.text)
            )
        )
        await db.commit()

    user_data[message.from_user.id] = {}

    await message.answer("Сохранено 💪", reply_markup=menu_kb)

# --- PROGRESS ---
@dp.message(F.text == "Прогресс")
async def progress(message: types.Message):
    async with aiosqlite.connect("fitness.db") as db:
        cursor = await db.execute(
            "SELECT exercise, weight, reps FROM progress WHERE user_id = ?",
            (message.from_user.id,)
        )
        rows = await cursor.fetchall()

    if not rows:
        await message.answer("Пока нет записей")
        return

    text = "📊 Прогресс:\n\n"
    for r in rows:
        text += f"{r[0]} — {r[1]} кг — {r[2]} повторений\n"

    text += "\n🔥 Отличная работа! Продолжай!"

    await message.answer(text)

# --- RUN ---
async def main():
    print("MAIN ЗАПУЩЕН")
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

