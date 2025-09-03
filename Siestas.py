# ╔════════════════════════════════════════════════╗
# ║               Chat Folder Manager              ║
# ║            Версия: 1.0 | Автор: @Androfon_AI ║
# ╚════════════════════════════════════════════════╝

__mod__ = "ChatFolderManager"
__version__ = "1.0"
__author__ = "@your_username"  # Замени на свой никнейм

import json
import os
from telethon import events, functions, types

FOLDER_FILE = "folders.json"

# Загрузка папок из файла
if os.path.exists(FOLDER_FILE):
    with open(FOLDER_FILE, "r", encoding="utf-8") as f:
        folders_db = json.load(f)
        folders_db = {k: list(map(int, v)) for k, v in folders_db.items()}
else:
    folders_db = {}

# Сохранение папок в файл
def save_folders():
    with open(FOLDER_FILE, "w", encoding="utf-8") as f:
        json.dump(folders_db, f, indent=2)

# Создание папки
@bot.on(events.NewMessage(pattern=r'\.createfolder (.+)'))
async def create_folder(event):
    name = event.pattern_match.group(1).strip()
    if name in folders_db:
        await event.reply(f"Папка **{name}** уже существует.")
        return
    folders_db[name] = []
    save_folders()
    await event.reply(f"✅ Папка **{name}** создана.")

# Удаление папки
@bot.on(events.NewMessage(pattern=r'\.deletefolder (.+)'))
async def delete_folder(event):
    name = event.pattern_match.group(1).strip()
    if name not in folders_db:
        await event.reply(f"❌ Папка **{name}** не найдена.")
        return
    del folders_db[name]
    save_folders()
    await event.reply(f"🗑️ Папка **{name}** удалена.")

# Добавление чата в папку
@bot.on(events.NewMessage(pattern=r'\.addtofolder (\S+) (\S+)'))
async def add_to_folder(event):
    name, chat = event.pattern_match.group(1), event.pattern_match.group(2)
    if name not in folders_db:
        await event.reply("Папка не найдена.")
        return
    try:
        entity = await bot.get_entity(chat)
        if entity.id not in folders_db[name]:
            folders_db[name].append(entity.id)
            save_folders()
            await event.reply(f"✅ Чат **{get_display_name(entity)}** добавлен в папку **{name}**.")
        else:
            await event.reply("Этот чат уже есть в папке.")
    except Exception as e:
        await event.reply(f"Ошибка: {e}")

# Удаление чата из папки
@bot.on(events.NewMessage(pattern=r'\.removefromfolder (\S+) (\S+)'))
async def remove_from_folder(event):
    name, chat = event.pattern_match.group(1), event.pattern_match.group(2)
    if name not in folders_db:
        await event.reply("Папка не найдена.")
        return
    try:
        entity = await bot.get_entity(chat)
        if entity.id in folders_db[name]:
            folders_db[name].remove(entity.id)
            save_folders()
            await event.reply(f"❎ Чат **{get_display_name(entity)}** удалён из папки **{name}**.")
        else:
            await event.reply("Этот чат не находится в указанной папке.")
    except Exception as e:
        await event.reply(f"Ошибка: {e}")

# Показать список всех папок
@bot.on(events.NewMessage(pattern=r'\.listfolders'))
async def list_folders(event):
    if not folders_db:
        await event.reply("Нет созданных папок.")
        return
    msg = "**📁 Список папок:**\n"
    for name, ids in folders_db.items():
        msg += f"\n🔹 **{name}** ({len(ids)} чатов):\n"
        for chat_id in ids:
            try:
                entity = await bot.get_entity(chat_id)
                msg += f"  └─ {get_display_name(entity)} (`{chat_id}`)\n"
            except:
                msg += f"  └─ [не найден] `{chat_id}`\n"
    await event.reply(msg)

# Вспомогательная функция
def get_display_name(entity):
    if isinstance(entity, types.User):
        return f"{entity.first_name or ''} {entity.last_name or ''}".strip()
    if isinstance(entity, types.Chat) or isinstance(entity, types.Channel):
        return entity.title
    return str(entity.id) 
