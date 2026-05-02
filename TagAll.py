# meta developer: @yourhandle
# meta name: TagAll
# meta version: 2.1.0

import asyncio
import contextlib
import logging
import random
import time
import re

from hikkatl.tl.functions.channels import InviteToChannelRequest
from hikkatl.tl.types import Message

from .. import loader, utils

logger = logging.getLogger(__name__)


class StopEvent:
    def __init__(self, chat_id: int):
        self.state = True
        self.chat_id = chat_id
        self.last_timeout: float | None = None

    def stop(self):
        self.state = False


@loader.tds
class TagAllMod(loader.Module):
    """Отмечает всех участников чата через команды или триггеры в тексте"""

    strings = {
        "name": "TagAll",
        "bot_error": "🚫 <b>Не получилось пригласить бота в чат.</b>",
        "_cfg_doc_delete": "Удалять сообщения после тега",
        "_cfg_doc_use_bot": "Использовать бота для тегов",
        "_cfg_doc_timeout": "Время между сообщениями (число, список или диапазон 0.1-1.0)",
        "_cfg_doc_silent": "Не отправлять сообщение с кнопкой отмены",
        "_cfg_doc_cycle_tagging": "Цикличный тег (пока не остановите)",
        "_cfg_doc_cycle_delay": "Задержка между циклами (сек)",
        "_cfg_doc_chunk_size": "Сколько пользователей в одном сообщении",
        "_cfg_doc_duration": "Длительность работы (0 = бесконечно)",
        "_cfg_doc_exclude_user_ids": "ID пользователей-исключений",
        "_cfg_doc_allowed_chat_ids": "ID разрешенных чатов",
        "_cfg_start_trigger": "Триггер для запуска (если есть в тексте сообщения)",
        "_cfg_stop_trigger": "Триггер для остановки (если есть в тексте сообщения)",
        "tagall_not_running": "🚫 <b>TagAll не запущен в чате {chat_id}.</b>",
        "tagall_already_running": "🚫 <b>TagAll уже запущен в чате {chat_id}.</b>",
        "no_eligible_participants": "🚫 <b>Нет подходящих участников.</b>",
        "cmd_redirected": "➡️ <b>Перенаправлено в чат</b> <code>{target_chat_id}</code>.",
        "cmd_not_allowed_multiple": "🚫 <b>Чат не в белом списке. Разрешенные:</b> {allowed_chats}.",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue("delete", False, lambda: self.strings("_cfg_doc_delete"), validator=loader.validators.Boolean()),
            loader.ConfigValue("use_bot", False, lambda: self.strings("_cfg_doc_use_bot"), validator=loader.validators.Boolean()),
            loader.ConfigValue("timeout", "0.1", lambda: self.strings("_cfg_doc_timeout"), validator=loader.validators.String()),
            loader.ConfigValue("silent", False, lambda: self.strings("_cfg_doc_silent"), validator=loader.validators.Boolean()),
            loader.ConfigValue("cycle_tagging", False, lambda: self.strings("_cfg_doc_cycle_tagging"), validator=loader.validators.Boolean()),
            loader.ConfigValue("cycle_delay", 0, lambda: self.strings("_cfg_doc_cycle_delay"), validator=loader.validators.Integer(minimum=0)),
            loader.ConfigValue("chunk_size", 3, lambda: self.strings("_cfg_doc_chunk_size"), validator=loader.validators.Integer(minimum=1)),
            loader.ConfigValue("duration", 0, lambda: self.strings("_cfg_doc_duration"), validator=loader.validators.Integer(minimum=0)),
            loader.ConfigValue("exclude_user_ids", "", lambda: self.strings("_cfg_doc_exclude_user_ids"), validator=loader.validators.String()),
            loader.ConfigValue("allowed_chat_ids", "", lambda: self.strings("_cfg_doc_allowed_chat_ids"), validator=loader.validators.String()),
            loader.ConfigValue("start_trigger", "тагалл", lambda: self.strings("_cfg_start_trigger"), validator=loader.validators.String()),
            loader.ConfigValue("stop_trigger", "стоп таг", lambda: self.strings("_cfg_stop_trigger"), validator=loader.validators.String()),
        )
        self._tagall_events: dict[int, StopEvent] = {}

    async def client_ready(self, client, db):
        self._client = client
        self._db = db

    async def on_unload(self):
        for event in list(self._tagall_events.values()):
            event.stop()
        self._tagall_events.clear()

    @loader.watcher()
    async def watcher(self, message: Message):
        if not isinstance(message, Message) or not message.text:
            return

        text = message.text.lower()
        start_trigger = self.config["start_trigger"].lower()
        stop_trigger = self.config["stop_trigger"].lower()

        # Сначала проверяем стоп-триггер
        if stop_trigger and stop_trigger in text:
            await self._stop_logic(message, "")
            return

        # Затем старт-триггер
        if start_trigger and start_trigger in text:
            # Убираем сам триггер из текста, чтобы использовать остаток как префикс
            prefix = message.text.replace(self.config["start_trigger"], "").strip()
            await self._start_logic(message, prefix)

    def _get_allowed_chat_ids_map(self) -> dict[int, int]:
        allowed_ids_raw = self.config["allowed_chat_ids"]
        allowed_chats_map = {}
        cleaned = re.sub(r"[^0-9,]", "", allowed_ids_raw)
        if not cleaned: return {}
        for i, chat_id_str in enumerate(cleaned.split(',')):
            if chat_id_str:
                with contextlib.suppress(ValueError):
                    allowed_chats_map[i + 1] = int(chat_id_str)
        return allowed_chats_map

    async def _resolve_target_chat(self, message: Message, raw_args: str) -> tuple[int | None, str | None]:
        original_chat_id = message.chat_id
        remaining_args = raw_args.strip()
        allowed_chats_map = self._get_allowed_chat_ids_map()
        allowed_chat_ids_set = set(allowed_chats_map.values())

        chat_index_match = re.match(r"^\s*(\d+)\s*(.*)$", remaining_args)
        if chat_index_match:
            index = int(chat_index_match.group(1))
            if index in allowed_chats_map:
                target_id = allowed_chats_map[index]
                if target_id != original_chat_id:
                    await utils.answer(message, f"➡️ Перенаправлено в {target_id}")
                return target_id, chat_index_match.group(2).strip()

        if not allowed_chat_ids_set or original_chat_id in allowed_chat_ids_set:
            return original_chat_id, remaining_args
        
        if len(allowed_chat_ids_set) == 1:
            target_id = next(iter(allowed_chat_ids_set))
            await utils.answer(message, self.strings("cmd_redirected").format(target_chat_id=target_id))
            return target_id, remaining_args

        await utils.answer(message, self.strings("cmd_not_allowed_multiple").format(
            allowed_chats=", ".join(map(str, allowed_chat_ids_set))
        ))
        return None, None

    async def _start_logic(self, message: Message, prefix: str):
        target_chat_id, message_prefix = await self._resolve_target_chat(message, prefix)
        if target_chat_id is None:
            return

        if target_chat_id in self._tagall_events and self._tagall_events[target_chat_id].state:
            return # Уже запущен

        if message.out:
            with contextlib.suppress(Exception): await message.delete()

        event = StopEvent(target_chat_id)
        self._tagall_events[target_chat_id] = event
        self._client.loop.create_task(self._run_tagall_process(target_chat_id, message_prefix, event))

    async def _stop_logic(self, message: Message, args: str):
        target_chat_id, _ = await self._resolve_target_chat(message, args)
        if target_chat_id is None: return
        
        event = self._tagall_events.get(target_chat_id)
        if event and event.state:
            event.stop()
            if message.out:
                with contextlib.suppress(Exception): await message.delete()
        else:
            await utils.answer(message, self.strings("tagall_not_running").format(chat_id=target_chat_id))

    @loader.command()
    async def tagall(self, message: Message):
        """[текст] - Запустить тег всех"""
        await self._start_logic(message, utils.get_args_raw(message))

    @loader.command()
    async def stoptagall(self, message: Message):
        """Остановить тег всех"""
        await self._stop_logic(message, utils.get_args_raw(message))

    def _get_random_timeout(self, event: StopEvent) -> float:
        timeout_str = str(self.config["timeout"])
        try:
            cleaned = re.sub(r"[^0-9.,-]", "", timeout_str)
            if "-" in cleaned:
                parts = cleaned.split("-")
                return random.uniform(float(parts[0]), float(parts[1]))
            if "," in cleaned:
                vals = [float(x) for x in cleaned.split(",") if x]
                return random.choice(vals)
            return float(cleaned)
        except:
            return 0.1

    async def _run_tagall_process(self, chat_id: int, message_prefix: str, event: StopEvent):
        del_ids_user = []
        del_ids_bot = []
        is_bot = self.config["use_bot"]

        try:
            chat_entity = await self._client.get_input_entity(chat_id)
            if is_bot:
                bot_username = self.inline.bot_username
                bot_entity = await self._client.get_input_entity(bot_username)
                with contextlib.suppress(Exception):
                    await self._client(InviteToChannelRequest(chat_entity, [bot_entity]))
        except Exception as e:
            logger.error(f"Error: {e}")
            event.stop()
            return

        excluded = {int(x.strip()) for x in self.config["exclude_user_ids"].split(",") if x.strip().isdigit()}
        owner_id = self._client.tg_id

        participants = []
        async for user in self._client.iter_participants(chat_id):
            if not user.bot and not user.deleted and user.id != owner_id and user.id not in excluded:
                participants.append(user)

        if not participants:
            await self._client.send_message(chat_id, self.strings("no_eligible_participants"))
            event.stop()
            return

        start_time = time.time()
        try:
            while event.state:
                random.shuffle(participants)
                for chunk in utils.chunks(participants, self.config["chunk_size"]):
                    if not event.state: break
                    if self.config["duration"] > 0 and (time.time() - start_time) > self.config["duration"]:
                        event.stop(); break

                    tags = []
                    for u in chunk:
                        name = utils.escape_html(u.first_name or "User")
                        tags.append(f'<a href="tg://user?id={u.id}">{name}</a>')

                    text = f"{message_prefix}\n{' '.join(tags)}" if message_prefix else " ".join(tags)

                    if is_bot and getattr(self.inline, "bot_client", None):
                        m = await self.inline.bot_client.send_message(chat_id, text, parse_mode="HTML")
                        if self.config["delete"]: del_ids_bot.append(m.id)
                    else:
                        m = await self._client.send_message(chat_entity, text, parse_mode="HTML")
                        if self.config["delete"]: del_ids_user.append(m.id)

                    await asyncio.sleep(self._get_random_timeout(event))

                if not self.config["cycle_tagging"] or not event.state: break
                await asyncio.sleep(self.config["cycle_delay"])
        finally:
            if self.config["delete"]:
                with contextlib.suppress(Exception):
                    for cid in utils.chunks(del_ids_user, 100): await self._client.delete_messages(chat_entity, cid)
                    if is_bot and getattr(self.inline, "bot_client", None):
                        for cid in utils.chunks(del_ids_bot, 100): await self.inline.bot_client.delete_messages(chat_entity, cid)
            if chat_id in self._tagall_events: del self._tagall_events[chat_id]
