import asyncio
import random
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import os
TOKEN = os.getenv("TOKEN")  # токен из переменных Railway

bot = Bot(token=TOKEN)
dp = Dispatcher()

# база
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

# состояние пользователя для добавления задач
user_states = {}  # user_id -> "adding_task"


# Главное меню
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить задачу", callback_data="menu_add")],
        [InlineKeyboardButton(text="📋 Посмотреть задачи", callback_data="menu_today")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="menu_stats")]
    ])


# Кнопки для каждой задачи
def get_task_buttons(task_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅", callback_data=f"done:{task_id}"),
            InlineKeyboardButton(text="❌", callback_data=f"fail:{task_id}")
        ]
    ])


# Генерация наказания
def generate_punishment(count):
    base = 50 * (count + 1)
    options = [
        f"{base} отжиманий",
        f"{base//2} отжиманий + {base//2} приседаний",
        f"{base//2} секунд планки"
    ]
    return random.choice(options)


# Старт
@dp.message(Command("start"))
async def start(message: types.Message):
    # создаём запись о штрафах, если нет
    cur.execute("INSERT OR IGNORE INTO punishments (user_id, count) VALUES (?, 0)", (message.from_user.id,))
    conn.commit()
    await message.answer("Главное меню:", reply_markup=main_menu())


# Обработка нажатий в меню и задачах
@dp.callback_query()
async def callbacks(call: types.CallbackQuery):
    user_id = call.from_user.id

    # Главное меню
    if call.data == "menu_add":
        await call.message.answer("Напиши текст задачи:")
        user_states[user_id] = "adding_task"

    elif call.data == "menu_today":
        cur.execute("SELECT id, task FROM tasks WHERE user_id=? AND done=0", (user_id,))
        rows = cur.fetchall()
        if not rows:
            await call.message.answer("Нет задач на сегодня.")
        else:
            for task_id, task in rows:
                await call.message.answer(task, reply_markup=get_task_buttons(task_id))

    elif call.data == "menu_stats":
        cur.execute("SELECT count FROM punishments WHERE user_id=?", (user_id,))
        count = cur.fetchone()[0]
        await call.message.answer(f"Количество провалов: {count}")

    # Кнопки задач
    elif call.data.startswith("done:"):
        task_id = int(call.data.split(":")[1])
        cur.execute("UPDATE tasks SET done=1 WHERE id=?", (task_id,))
        conn.commit()
        await call.message.edit_text("✅ Выполнено")

    elif call.data.startswith("fail:"):
        task_id = int(call.data.split(":")[1])
        # увеличиваем штраф
        cur.execute("SELECT count FROM punishments WHERE user_id=?", (user_id,))
        count = cur.fetchone()[0]
        punishment = generate_punishment(count)
        cur.execute("UPDATE punishments SET count=count+1 WHERE user_id=?", (user_id,))
        conn.commit()
        await call.message.edit_text(f"❌ Провалено\nНаказание: {punishment}")


# Обработка текстовых сообщений
@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    if user_states.get(user_id) == "adding_task":
        # добавляем задачу
        task_text = message.text
        cur.execute("INSERT INTO tasks (user_id, task) VALUES (?, ?)", (user_id, task_text))
        conn.commit()
        user_states[user_id] = None
        await message.answer(f"Задача добавлена: {task_text}", reply_markup=main_menu())
    else:
        await message.answer("Выбери действие:", reply_markup=main_menu())


# Запуск
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
