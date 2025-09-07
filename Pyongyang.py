# checkers_game.py
# Модуль шашек для юзербота (Telethon)
# Автор: @YourName | Версия: 2.0

import copy
from telethon import events, Button

active_games = {}
saved_games = {}

MODULE_NAME = "CheckersGame"
MODULE_VERSION = "2.0"
MODULE_AUTHOR = "@YourName"


# ====== Команда: старт новой игры ======
@events.register(events.NewMessage(pattern=r"\.checkers"))
async def start_game(event):
    chat_id = event.chat_id
    user_id = event.sender_id

    active_games[chat_id] = {
        "board": init_board(),
        "turn": "w",
        "host": user_id,
        "multi_jump": None,
        "selected": None,  # выбранная шашка
        "settings": {
            "force_take": True,
            "host_color": "w"
        }
    }

    game = active_games[chat_id]
    await event.respond(
        f"♟️ Игра началась!\nХодят: белые",
        buttons=render_inline_board(game["board"])
    )


# ====== Инлайн-обработка ======
@events.register(events.CallbackQuery)
async def handle_callback(event):
    data = event.data.decode("utf-8")
    chat_id = event.chat_id

    if chat_id not in active_games:
        await event.answer("Нет активной игры")
        return

    game = active_games[chat_id]

    # ====== Настройки ======
    if data == "toggle_force":
        game["settings"]["force_take"] = not game["settings"]["force_take"]
        await event.edit(
            f"♟️ Обязательные взятия: {'✅' if game['settings']['force_take'] else '❌'}",
            buttons=render_inline_board(game["board"])
        )
        return
    elif data == "switch_color":
        game["settings"]["host_color"] = "b" if game["settings"]["host_color"] == "w" else "w"
        await event.edit(
            f"♟️ Хост теперь за {'белых' if game['settings']['host_color']=='w' else 'чёрных'}",
            buttons=render_inline_board(game["board"])
        )
        return
    elif data == "save_game":
        saved_games[chat_id] = copy.deepcopy(game)
        await event.answer("💾 Игра сохранена!", alert=True)
        return

    # ====== Игровая логика ======
    parts = data.split(":")
    if parts[0] == "cell":
        x, y = int(parts[1]), int(parts[2])

        # если шашка выбрана — пытаемся походить
        if game["selected"]:
            sx, sy = game["selected"]
            ok, new_board, msg, extra_jump = try_move(
                game["board"], sx, sy, x, y,
                game["turn"],
                game["settings"]["force_take"],
                game["multi_jump"]
            )
            if ok:
                game["board"] = new_board
                game["multi_jump"] = extra_jump
                game["selected"] = None

                # победа?
                winner = check_winner(new_board)
                if winner:
                    await event.edit(
                        f"🏆 Победили {'белые' if winner=='w' else 'чёрные'}!",
                        buttons=render_inline_board(new_board)
                    )
                    del active_games[chat_id]
                    return

                if extra_jump:
                    game["selected"] = (x, y)
                    await event.edit(
                        f"⚔️ Продолжи бой той же шашкой!",
                        buttons=render_inline_board(new_board, highlight=(x, y))
                    )
                    return

                game["turn"] = "b" if game["turn"] == "w" else "w"
                await event.edit(
                    f"✅ Ход выполнен: {msg}\nТеперь ходят: {'белые' if game['turn']=='w' else 'чёрные'}",
                    buttons=render_inline_board(new_board)
                )
            else:
                game["selected"] = None
                await event.answer(msg, alert=True)

        else:
            # выбираем шашку
            piece = game["board"][x][y]
            if piece != "." and piece.lower() == game["turn"]:
                game["selected"] = (x, y)
                await event.edit(
                    f"♟️ Выбрана шашка ({x},{y})",
                    buttons=render_inline_board(game["board"], highlight=(x, y))
                )
            else:
                await event.answer("❌ Это не твоя шашка", alert=True)


# ====== Доска кнопками ======
def render_inline_board(board, highlight=None):
    symbols = {
        ".": "⬜",
        "w": "⚪",
        "b": "⚫",
        "W": "🔵",
        "B": "🔴"
    }
    rows = []
    for i in range(8):
        row = []
        for j in range(8):
            label = symbols[board[i][j]]
            if highlight and (i, j) == highlight:
                label = "⭐"
            row.append(Button.inline(label, f"cell:{i}:{j}"))
        rows.append(row)
    # кнопки настроек
    rows.append([
        Button.inline("⚖️ Обяз. взятие", "toggle_force"),
        Button.inline("🔄 Цвет хоста", "switch_color"),
        Button.inline("💾 Сохранить", "save_game"),
    ])
    return rows


# ====== Инициализация доски ======
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


# ====== Логика ходов ======
def try_move(board, x1, y1, x2, y2, turn, force_take, multi_jump):
    if not (0 <= x1 < 8 and 0 <= y1 < 8 and 0 <= x2 < 8 and 0 <= y2 < 8):
        return False, board, "Координаты вне доски", None

    piece = board[x1][y1]
    if piece == ".":
        return False, board, "Там нет шашки", None
    if piece.lower() != turn:
        return False, board, "Ход не вашего цвета", None

    if multi_jump and (x1, y1) != multi_jump:
        return False, board, "Ты обязан продолжить той же шашкой", None

    if board[x2][y2] != ".":
        return False, board, "Клетка занята", None

    dx, dy = x2 - x1, y2 - y1
    step_x = 1 if dx > 0 else -1
    step_y = 1 if dy > 0 else -1

    new_board = copy.deepcopy(board)
    captured = False

    # дамки
    if piece in ("W", "B"):
        if abs(dx) != abs(dy):
            return False, board, "Дамка ходит по диагонали", None

        cx, cy = x1 + step_x, y1 + step_y
        beaten = []
        while cx != x2 and cy != y2:
            if new_board[cx][cy] != ".":
                if new_board[cx][cy].lower() == turn:
                    return False, board, "Нельзя перепрыгивать свои", None
                if beaten:
                    return False, board, "Можно бить только одну шашку за раз", None
                beaten.append((cx, cy))
            cx += step_x
            cy += step_y

        if beaten:
            bx, by = beaten[0]
            new_board[bx][by] = "."
            captured = True

        new_board[x1][y1] = "."
        new_board[x2][y2] = piece

    # обычные шашки
    else:
        if abs(dx) == 1 and abs(dy) == 1 and not force_take:
            if (turn == "w" and dx == -1) or (turn == "b" and dx == 1):
                new_board[x1][y1] = "."
                new_board[x2][y2] = piece
            else:
                return False, board, "Нельзя ходить назад", None
        elif abs(dx) == 2 and abs(dy) == 2:
            mx, my = (x1 + x2) // 2, (y1 + y2) // 2
            if new_board[mx][my] != "." and new_board[mx][my].lower() != turn:
                new_board[mx][my] = "."
                new_board[x1][y1] = "."
                new_board[x2][y2] = piece
                captured = True
            else:
                return False, board, "Неправильное взятие", None
        else:
            return False, board, "Неправильный ход", None

    # превращение в дамку
    if x2 == 0 and piece == "w":
        new_board[x2][y2] = "W"
    if x2 == 7 and piece == "b":
        new_board[x2][y2] = "B"

    # проверка на продолжение боя
    if captured and has_more_captures(new_board, x2, y2):
        return True, new_board, f"({x1},{y1}) → ({x2},{y2})", (x2, y2)

    return True, new_board, f"({x1},{y1}) → ({x2},{y2})", None


def has_more_captures(board, x, y):
    piece = board[x][y]
    dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    if piece in ("w", "b"):
        for dx, dy in dirs:
            nx, ny = x + 2*dx, y + 2*dy
            mx, my = x + dx, y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                if board[nx][ny] == "." and board[mx][my] != "." and board[mx][my].lower() != piece.lower():
                    return True
    else:  # дамки
        for dx, dy in dirs:
            cx, cy = x + dx, y + dy
            found_enemy = False
            while 0 <= cx+dx < 8 and 0 <= cy+dy < 8:
                if board[cx][cy] == ".":
                    if found_enemy:
                        return True
                elif board[cx][cy].lower() != piece.lower() and not found_enemy:
                    found_enemy = True
                else:
                    break
                cx += dx
                cy += dy
    return False


def check_winner(board):
    has_w = any(cell.lower() == "w" for row in board for cell in row)
    has_b = any(cell.lower() == "b" for row in board for cell in row)
    if not has_w:
        return "b"
    if not has_b:
        return "w"
    return None


# ====== Инфо о модуле ======
@events.register(events.NewMessage(pattern=r"\.checkers_info"))
async def checkers_info(event):
    await event.respond(
        f"📦 Модуль: {MODULE_NAME}\n"
        f"🔖 Версия: {MODULE_VERSION}\n"
        f"👨‍💻 Разработчик: {MODULE_AUTHOR}"
    )
