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

# --- MINI WEB (для Render) ---
import threading
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web).start()

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

day_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Грудь / Руки")],
        [KeyboardButton(text="Ноги")],
        [KeyboardButton(text="Спина / Плечи")],
        [KeyboardButton(text="Назад")]
    ],
    resize_keyboard=True
)

# --- USER DATA ---
user_level = {}
user_data = {}

EXERCISES_BY_DAY = {
    "Грудь / Руки": [
        "Жим гантелей на наклонной скамье",
        "Разводка гантелей на наклонной скамье",
        "Брусья в гравитроне",
        "Разгибания с прямой рукояткой в кроссовере",
        "Сгибания на бицепс с гантелями",
        "Жим штанги лежа",
        "Французский жим",
        "Бицепс со штангой"
    ],
    "Ноги": [
        "Разгибания ног сидя",
        "Сведения ног сидя",
        "Плие с гантелей",
        "Ягодичный мостик",
        "Сгибания ног сидя",
        "Разведения ног сидя",
        "Махи боковые лежа с резинкой",
        "Гиперэкстензия",
        "Становая тяга",
        "Румынская тяга"
    ],
    "Спина / Плечи": [
        "Подтягивания в гравитроне",
        "Вертикальная тяга широким хватом",
        "Вертикальная тяга узким хватом",
        "Тяга горизонтального блока узким хватом",
        "Тяга сидя в хамере",
        "Жим гантелей сидя",
        "Жим штанги стоя",
        "Махи гантелей в стороны",
        "Махи гантелей перед собой"
    ]
}

ALL_EXERCISES = sum(EXERCISES_BY_DAY.values(), [])

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
            "💪 ЛЕГКИЙ УРОВЕНЬ\n\n"
            "📅 Грудь, трицепс, бицепс:\n"
            "• Жим гантелей на наклонной скамье\n"
            "• Разводка гантелей на наклонной скамье\n"
            "• Брусья в гравитроне\n"
            "• Разгибания с прямой рукояткой в кроссовере\n"
            "• Сгибания на бицепс с гантелями\n\n"
            "🦵 Ноги:\n"
            "• Разгибания ног сидя + сведения ног сидя\n"
            "• Плие с гантелей\n"
            "• Ягодичный мостик\n"
            "• Сгибания ног сидя + разведения ног сидя\n"
            "• Махи боковые лежа с резинкой\n\n"
            "🏋️ Спина, плечи:\n"
            "• Подтягивания в гравитроне\n"
            "• Вертикальная тяга широким хватом\n"
            "• Тяга горизонтального блока узким хватом\n"
            "• Жим гантелей сидя\n"
            "• Махи гантелей в стороны + перед собой"
        )
    else:
        text = (
            "🔥 ПРОДВИНУТЫЙ УРОВЕНЬ\n\n"
            "📅 Грудь, трицепс, бицепс:\n"
            "• Жим штанги лежа\n"
            "• Жим гантелей на наклонной скамье\n"
            "• Разводка гантелей на наклонной скамье\n"
            "• Французский жим\n"
            "• Бицепс со штангой + разгибания в кроссовере\n\n"
            "🦵 Ноги:\n"
            "• Разгибания ног сидя + сведения ног сидя\n"
            "• Гиперэкстензия\n"
            "• Становая тяга\n"
            "• Румынская тяга\n"
            "• Сгибания ног сидя + разведение ног сидя\n\n"
            "🏋️ Спина, плечи:\n"
            "• Вертикальная тяга широким хватом\n"
            "• Вертикальная тяга узким хватом\n"
            "• Тяга сидя в хамере\n"
            "• Жим штанги стоя\n"
            "• Жим гантелей сидя"
        )

    await message.answer(text)

# --- ВЫБОР ДНЯ ---
@dp.message(F.text == "Записать тренировку")
async def choose_day(message: types.Message):
    user_data[message.from_user.id] = {"state": "choose_day"}
    await message.answer("Выбери день:", reply_markup=day_kb)

# --- НАЗАД ---
@dp.message(F.text == "Назад")
async def go_back(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer("Главное меню", reply_markup=menu_kb)

# --- ВЫБОР УПРАЖНЕНИЯ ---
@dp.message(F.text.in_(EXERCISES_BY_DAY.keys()))
async def choose_exercise(message: types.Message):
    exercises = EXERCISES_BY_DAY[message.text]

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=ex)] for ex in exercises] + [[KeyboardButton(text="Назад")]],
        resize_keyboard=True
    )

    user_data[message.from_user.id] = {"state": "choose_ex"}
    await message.answer("Выбери упражнение:", reply_markup=kb)

# --- УПРАЖНЕНИЕ ---
@dp.message(F.text.in_(ALL_EXERCISES))
async def exercise_selected(message: types.Message):
    user_data[message.from_user.id] = {
        "state": "enter_weight",
        "exercise": message.text
    }

    await message.answer("Введи вес (число):")

# --- WEIGHT ---
@dp.message(lambda msg: user_data.get(msg.from_user.id, {}).get("state") == "enter_weight")
async def enter_weight(message: types.Message):
    if not message.text.isdigit():
        await message.answer("❗ Введи число")
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

    text += "\n🔥 Ты молодец, прогресс растет и растет, все падают при виде такой машины 😎"

    await message.answer(text)

# --- RUN ---
async def main():
    print("MAIN ЗАПУЩЕН")
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
