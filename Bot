import asyncio
import random
import sqlite3
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

conn = sqlite3.connect("discipline.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    task TEXT,
    done INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS punishments (
    user_id INTEGER,
    count INTEGER DEFAULT 0
)
""")
conn.commit()


def get_keyboard(task_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅", callback_data=f"done:{task_id}"),
            InlineKeyboardButton(text="❌", callback_data=f"fail:{task_id}")
        ]
    ])


def generate_punishment(count):
    base = 50 * (count + 1)
    options = [
        f"{base} отжиманий",
        f"{base//2} отжиманий + {base//2} приседаний",
        f"{base//2} секунд планки"
    ]
    return random.choice(options)


@dp.message(Command("start"))
async def start(message: types.Message):
    cur.execute("INSERT OR IGNORE INTO punishments (user_id, count) VALUES (?, 0)", (message.from_user.id,))
    conn.commit()
    await message.answer("Система дисциплины запущена.")


@dp.message(Command("add"))
async def add_task(message: types.Message):
    text = message.text.replace("/add ", "")
    cur.execute("INSERT INTO tasks (user_id, task) VALUES (?, ?)", (message.from_user.id, text))
    conn.commit()
    await message.answer(f"Добавлено: {text}")


@dp.message(Command("today"))
async def today(message: types.Message):
    cur.execute("SELECT id, task FROM tasks WHERE user_id=? AND done=0", (message.from_user.id,))
    rows = cur.fetchall()

    if not rows:
        await message.answer("Нет задач.")
        return

    for task_id, task in rows:
        await message.answer(task, reply_markup=get_keyboard(task_id))


@dp.callback_query()
async def callbacks(call: types.CallbackQuery):
    action, task_id = call.data.split(":")
    task_id = int(task_id)
    user_id = call.from_user.id

    if action == "done":
        cur.execute("UPDATE tasks SET done=1 WHERE id=?", (task_id,))
        conn.commit()
        await call.message.edit_text("✅ Выполнено")

    elif action == "fail":
        cur.execute("SELECT count FROM punishments WHERE user_id=?", (user_id,))
        count = cur.fetchone()[0]

        punishment = generate_punishment(count)

        cur.execute("UPDATE punishments SET count=count+1 WHERE user_id=?", (user_id,))
        conn.commit()

        await call.message.edit_text(f"❌ Провалено\nНаказание: {punishment}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
