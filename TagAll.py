# meta developer: @your_username
# requires: telethon

import asyncio
import html
from telethon.tl.types import ChannelParticipantsAdmins
from .. import loader, utils


@loader.tds
class TagAllMod(loader.Module):
    """Модуль для тега (упоминания) всех участников чата с гибкой настройкой"""

    strings = {
        "name": "TagAll",
        "gathering": "<b>[TagAll]</b> Сбор участников чата...",
        "started": "<b>[TagAll]</b> Начинаю тегать участников...",
        "stopped": "<b>[TagAll]</b> Тег остановлен.",
        "no_group": "<b>[TagAll]</b> Эту команду можно использовать только в группах.",
        "done": "<b>[TagAll]</b> Все участники успешно отмечены!",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "USERS_PER_MESSAGE",
                5,
                "Количество пользователей, которых нужно тегать в одном сообщении",
                validator=loader.validators.Integer(),
            ),
            loader.ConfigValue(
                "DELAY",
                3.0,
                "Задержка между сообщениями в секундах (не рекомендуется ставить меньше 2.0-3.0 во избежание лимитов Telegram)",
                validator=loader.validators.Float(),
            ),
        )
        self.active_tasks = {}

    async def tagallcmd(self, message):
        """<текст> - Тегнуть всех участников группы. Чтобы остановить, напишите .tagstop"""
        if not message.is_group:
            await utils.answer(message, self.strings["no_group"])
            return

        chat_id = message.chat_id
        if chat_id in self.active_tasks:
            await utils.answer(message, "В этом чате уже запущен тег!")
            return

        # Текст, который будет идти перед тегами
        args = utils.get_args_raw(message)
        text_prefix = f"<b>{args}</b>\n\n" if args else ""

        await utils.answer(message, self.strings["gathering"])

        # Собираем пользователей
        all_users = []
        async for user in message.client.iter_participants(chat_id):
            if user.bot:
                continue  # Пропускаем ботов
            all_users.append(user)

        if not all_users:
            await utils.answer(message, "Не удалось найти участников.")
            return

        self.active_tasks[chat_id] = True
        await message.delete()

        chunk_size = self.config["USERS_PER_MESSAGE"]
        delay = self.config["DELAY"]

        # Форматируем теги
        tags = []
        for u in all_users:
            if u.username:
                tags.append(f"@{u.username}")
            else:
                # Если нет юзернейма, делаем кликабельное имя через HTML
                name = html.escape(u.first_name or "Пользователь")
                tags.append(f'<a href="tg://user?id={u.id}">{name}</a>')

        # Разбиваем список на порции и отправляем
        try:
            for i in range(0, len(tags), chunk_size):
                if chat_id not in self.active_tasks:
                    break

                chunk = tags[i : i + chunk_size]
                msg_text = text_prefix + " ".join(chunk)

                await message.client.send_message(
                    chat_id, msg_text, parse_mode="html"
                )
                await asyncio.sleep(delay)

            if chat_id in self.active_tasks:
                await message.client.send_message(
                    chat_id, self.strings["done"]
                )

        except Exception as e:
            await message.client.send_message(
                chat_id, f"<b>[TagAll] Произошла ошибка:</b> {e}"
            )
        finally:
            self.active_tasks.pop(chat_id, None)

    async def tagstopcmd(self, message):
        """Остановить процесс упоминания пользователей в этом чате"""
        chat_id = message.chat_id
        if chat_id in self.active_tasks:
            self.active_tasks.pop(chat_id, None)
            await utils.answer(message, self.strings["stopped"])
        else:
            await utils.answer(message, "В этом чате сейчас нет активного тега.")
