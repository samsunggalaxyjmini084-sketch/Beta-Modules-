# meta developer: @yourhandle
# meta name: AutoPolesList
# meta version: 2.5.0
# 010000010101010001001111010100000100111101001100010001010101001101001100010010010101001101010100
import logging
import asyncio
import random
import urllib.parse
from datetime import datetime
from telethon.tl.types import Message, User
from telethon.errors import RPCError
from telethon import functions
import re
from collections import defaultdict
from typing import Optional, List, Tuple
from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class AutoPolesListMod(loader.Module):
    """Модуль для автоматизации мафии и скоростного сбора списка ролей (Poles List)."""

    strings = {
        "name": "AutoPolesList",
        "enabled": "✅ Модуль AutoPolesList включен.",
        "disabled": "❌ Модуль AutoPolesList выключен.",
        "status": "<emoji document_id=5875291072225087249>📊</emoji> Статус AutoPolesList:\n"
                  "Общий статус: {}\n"
                  "Разрешенные чаты: {}\n"
                  "Конфиг кнопок: {}\n"
                  "\n<emoji document_id=5771887475421090729>👤</emoji> Отслеживание ролей:\n"
                  "Активно: {}\n"
                  "Чат мониторинга: {}\n"
                  "Найдено ролей: {}\n"
                  "Осталось времени: {}\n"
                  "Чат вывода списка: {}",
        "role_tracked_success": "✅ Роль добавлена: <code>{nickname}</code> -> {role} ({status})",
        "tracked_roles_list": "<emoji document_id=5771887475421090729>👤</emoji> Список ролей ({total_count}):\n\n{active_roles_section}\n\n{inactive_roles_section}",
        "active_roles_header": "🟢 Активные:",
        "inactive_roles_header": "🔴 Неактивные:",
        "role_tracking_monitor_all": "Все разрешенные",
    }

    def __init__(self):
        super().__init__()
        self.config = loader.ModuleConfig(
            loader.ConfigValue("enabled", False, "Включен ли модуль", validator=loader.validators.Boolean()),
            loader.ConfigValue("delays", [0.5], "Задержки входа", validator=loader.validators.Series(loader.validators.Float())),
            loader.ConfigValue("lynch_delay", [0.5], "Задержки линча", validator=loader.validators.Series(loader.validators.Float())),
            loader.ConfigValue("bot_ids", [], "ID ботов мафии", validator=loader.validators.Series(loader.validators.Integer())),
            loader.ConfigValue("allowed_chats", [], "Разрешенные чаты", validator=loader.validators.Series(loader.validators.Integer())),
            loader.ConfigValue("button_keyword_configs_string", "присоединиться (default), играть (default)", "Конфиг кнопок"),
            loader.ConfigValue("active_button_config_id", "default", "ID активного конфига"),
            loader.ConfigValue("game_join_trigger_phrases", ["Ведётся набор в игру"], "Фразы набора"),
            loader.ConfigValue("lynch_trigger_phrases", ["Вы точно хотите линчевать"], "Фразы линча"),
            loader.ConfigValue("role_tracking_enabled", False, "Включено ли отслеживание ролей"),
            loader.ConfigValue("role_tracking_duration", 300, "Длительность отслеживания (сек)"),
            loader.ConfigValue("tracked_roles_to_monitor", ["мирный житель", "мафия (н)"], "Роли для поиска"),
            loader.ConfigValue("role_announcement_phrases", ["Моя роль:", "Я - "], "Триггеры объявления роли"),
            loader.ConfigValue("role_tracking_monitor_chat_id", 0, "ID чата для мониторинга ролей (0 - все)"),
            loader.ConfigValue("send_tracked_roles_chat_id", 0, "Куда слать список по итогу"),
            loader.ConfigValue("send_tracked_roles_delay", 30, "Задержка авто-отправки"),
            loader.ConfigValue("tracked_roles_display_chat_id", 0, "Чат для команды .aplshow"),
            loader.ConfigValue("player_to_lynch_user_id", 0, "ID игрока для выбора цели"),
            loader.ConfigValue("lynch_player_voting_trigger_phrases", ["Кого ты хочешь повесить?"], "Триггеры выбора цели"),
            loader.ConfigValue("role_forward_chat_id", 0, "Куда пересылать свою роль"),
            loader.ConfigValue("role_trigger_phrases", ["Ваша роль:"], "Триггеры своей роли"),
            loader.ConfigValue("auto_track_roles_trigger_phrases", [], "Авто-включение отслеживания"),
            loader.ConfigValue("auto_track_roles_bot_ids", [], "Боты для авто-включения"),
            loader.ConfigValue("auto_disable_track_roles_trigger_phrases", [], "Авто-выключение"),
            loader.ConfigValue("auto_disable_track_roles_bot_ids", [], "Боты для авто-выключения"),
            loader.ConfigValue("command_delay", 0.0, "Задержка команд"),
            loader.ConfigValue("lynch_target_marker", "", "Маркер для '👎'"),
        )
        self._player_nickname_to_lynch = None
        self._role_tracking_active = False
        self._role_tracking_start_time = None
        self._tracked_roles_list = []
        self._tracked_roles_lookup_set = set()
        self._compiled_tracked_role_patterns = []
        self._send_tracked_roles_task = None
        self._current_button_keywords_to_use = []

    async def client_ready(self, client, _):
        self._client = client
        self._update_button_keywords_from_config()
        self._update_tracked_roles_patterns()

    def _update_tracked_roles_patterns(self):
        self._compiled_tracked_role_patterns = []
        for raw in self.config["tracked_roles_to_monitor"]:
            phrase = raw.lower()
            is_active = not phrase.endswith("(н)")
            clean = phrase[:-3].strip() if not is_active else phrase
            pattern = re.compile(r"\b" + re.escape(clean) + r"\b", re.IGNORECASE)
            self._compiled_tracked_role_patterns.append((pattern, clean, is_active))

    def _update_button_keywords_from_config(self):
        raw = self.config["button_keyword_configs_string"]
        active_id = self.config["active_button_config_id"]
        parsed = defaultdict(list)
        for entry in [e.strip() for e in raw.split(',')]:
            match = re.match(r"(.+?)\s*\(([\w\d]+)\)", entry)
            if match: parsed[match.group(2)].append(match.group(1).lower())
        self._current_button_keywords_to_use = parsed.get(active_id, [])

    @loader.watcher(incoming=True)
    async def watcher(self, message: Message):
        if not self.config["enabled"] or not message.text: return

        text_low = message.text.lower()
        chat_id = message.chat_id
        sender_id = message.sender_id

        # 1. Быстрое включение отслеживания
        if any(p.lower() in text_low for p in self.config["auto_track_roles_trigger_phrases"]):
            if not self.config["auto_track_roles_bot_ids"] or sender_id in self.config["auto_track_roles_bot_ids"]:
                self._activate_tracking()

        # 2. Мгновенный сбор ролей
        if self._role_tracking_active:
            if (datetime.now() - self._role_tracking_start_time).total_seconds() > self.config["role_tracking_duration"]:
                self._role_tracking_active = False
            else:
                mon_id = self.config["role_tracking_monitor_chat_id"]
                if mon_id == 0 or chat_id == mon_id:
                    if any(p.lower() in text_low for p in self.config["role_announcement_phrases"]):
                        for pattern, clean, active in self._compiled_tracked_role_patterns:
                            if pattern.search(text_low):
                                if (sender_id, clean) not in self._tracked_roles_lookup_set:
                                    sender = await message.get_sender()
                                    nick = f"{sender.first_name} {sender.last_name or ''}".strip() or sender.username or "Unknown"
                                    self._tracked_roles_list.append((sender_id, nick, clean, active))
                                    self._tracked_roles_lookup_set.add((sender_id, clean))
                                break

        # 3. Игровые действия (проверка чата)
        allowed = self.config["allowed_chats"]
        if allowed and chat_id not in allowed: return

        if not self.config["bot_ids"] or sender_id in self.config["bot_ids"]:
            # Вход в игру
            if any(p.lower() in text_low for p in self.config["game_join_trigger_phrases"]):
                if message.buttons:
                    await asyncio.sleep(random.choice(self.config["delays"]))
                    for row in message.buttons:
                        for btn in row:
                            if any(k in btn.text.lower() for k in self._current_button_keywords_to_use):
                                await btn.click(); return

            # Линч
            elif any(p.lower() in text_low for p in self.config["lynch_trigger_phrases"]):
                if message.buttons:
                    await asyncio.sleep(random.choice(self.config["lynch_delay"]))
                    target = "👎" if self.config["lynch_target_marker"] in message.text else "👍"
                    for row in message.buttons:
                        for btn in row:
                            if target in btn.text: await btn.click(); return

    def _activate_tracking(self):
        self._role_tracking_active = True
        self._role_tracking_start_time = datetime.now()
        self._tracked_roles_list = []
        self._tracked_roles_lookup_set.clear()
        
        delay = self.config["send_tracked_roles_delay"]
        chat = self.config["send_tracked_roles_chat_id"]
        if chat and delay > 0:
            if self._send_tracked_roles_task: self._send_tracked_roles_task.cancel()
            self._send_tracked_roles_task = asyncio.create_task(self._scheduled_send(delay, chat))

    async def _scheduled_send(self, delay, chat_id):
        await asyncio.sleep(delay)
        if self._role_tracking_active: await self._client.send_message(chat_id, self._build_roles_msg())

    def _build_roles_msg(self):
        act = [f"• <code>{n}</code> ({r})" for _, n, r, a in self._tracked_roles_list if a]
        inact = [f"• <code>{n}</code> ({r})" for _, n, r, a in self._tracked_roles_list if not a]
        return self.strings("tracked_roles_list").format(
            total_count=len(self._tracked_roles_list),
            active_roles_section=self.strings("active_roles_header") + "\n" + ("\n".join(act) if act else "Пусто"),
            inactive_roles_section=self.strings("inactive_roles_header") + "\n" + ("\n".join(inact) if inact else "Пусто")
        )

    @loader.command()
    async def aplon(self, message):
        """Включить модуль"""
        self.set("enabled", True)
        await utils.answer(message, self.strings("enabled"))

    @loader.command()
    async def aploff(self, message):
        """Выключить модуль"""
        self.set("enabled", False)
        self._role_tracking_active = False
        await utils.answer(message, self.strings("disabled"))

    @loader.command()
    async def aplstatus(self, message):
        """Статус модуля"""
        conf = self.config
        await utils.answer(message, self.strings("status").format(
            "🟢 ON" if conf["enabled"] else "🔴 OFF",
            len(conf["allowed_chats"]) or "Все",
            conf["active_button_config_id"],
            "🟢" if self._role_tracking_active else "🔴",
            conf["role_tracking_monitor_chat_id"] or "Все разрешенные",
            len(self._tracked_roles_list),
            "Активно" if self._role_tracking_active else "-",
            conf["tracked_roles_display_chat_id"] or "Тут"
        ))

    @loader.command()
    async def aplshow(self, message):
        """Показать список ролей"""
        res = self._build_roles_msg()
        target = self.config["tracked_roles_display_chat_id"]
        if target:
            await self._client.send_message(target, res)
            await utils.answer(message, f"✅ Отправлено в {target}")
        else:
            await utils.answer(message, res)
