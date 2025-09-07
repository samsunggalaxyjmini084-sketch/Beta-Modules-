# checkers_module.py
# Шашки для Telethon Userbot
# Автор: @YourName | Версия: 2.3

import copy
from telethon import events, Button

# Импортируем client из твоего юзербота
# ⚠️ проверь точное имя — чаще всего "userbot" или "heroku"
from userbot import client  

active_games = {}
saved_games = {}

MODULE_NAME = "CheckersGame"
MODULE_VERSION = "2.3"
MODULE_AUTHOR = "@YourName"


# ================= ОБРАБОТЧИКИ =================
async def start_game(event):
    chat_id = event.chat_id
    user_id = event.sender_id
    active_games[chat_id] = {
        "board": init_board(),
        "turn": "w",
        "host": user_id,
        "multi_jump": None,
        "selected": None,
        "settings": {"force_take": True, "host_color": "w"}
    }
    await event.respond("♟️ Игра началась! Ходят белые",
                        buttons=render_inline_board(active_games[chat_id]["board"]))


async def resume_game(event):
    chat_id = event.chat_id
    if chat_id in saved_games:
        active_games[chat_id] = copy.deepcopy(saved_games[chat_id])
        await event.respond("♟️ Игра восстановлена!",
                            buttons=render_inline_board(active_games[chat_id]["board"]))
    else:
        await event.respond("❌ Нет сохранённой игры")


async def checkers_info(event):
    await event.respond(f"📦 Модуль: {MODULE_NAME}\n"
                        f"🔖 Версия: {MODULE_VERSION}\n"
                        f"👨‍💻 Разработчик: {MODULE_AUTHOR}")


async def handle_callback(event):
    data = event.data.decode("utf-8") if event.data else ""
    await event.answer(f"Нажата кнопка: {data}")


# ================= ДОСКА =================
def render_inline_board(board, highlight=None):
    symbols = {".": "⬜", "w": "⚪", "b": "⚫", "W": "🔵", "B": "🔴"}
    rows = []
    for i in range(8):
        row = []
        for j in range(8):
            row.append(Button.inline(symbols[board[i][j]], f"cell:{i}:{j}"))
        rows.append(row)
    rows.append([Button.inline("💾 Сохранить", "save_game")])
    return rows


def init_board():
    board = [["." for _ in range(8)] for _ in range(8)]
    for i in range(3):
        for j in range(8):
            if (i + j) % 2 == 1:
                board[i][j] = "b"
    for i in range(5, 8):
        for j in range(8):
            if (i + j) % 2 == 1:
                board[i][j] = "w"
    return board


# ================= РЕГИСТРАЦИЯ =================
def register():
    """Регистрируем обработчики прямо в глобальном client"""
    client.add_event_handler(start_game, events.NewMessage(pattern=r"\.checkers"))
    client.add_event_handler(resume_game, events.NewMessage(pattern=r"\.checkers_resume"))
    client.add_event_handler(checkers_info, events.NewMessage(pattern=r"\.checkers_info"))
    client.add_event_handler(handle_callback, events.CallbackQuery)
