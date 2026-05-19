# meta developer: @yourhandle
# meta name: AutoJoinChat
# meta version: 1.0.1 # Обновлена версия, так как сделаны уточнения и поправки

import logging
import asyncio
import random
import re
from telethon.tl.types import Message, MessageEntityUrl, MessageEntityTextUrl, Channel, Chat, User
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class AutoJoinChatMod(loader.Module):
    """Модуль для автоматического присоединения к чатам/каналам Telegram по ссылкам, включая формат t.me/+, найденным в сообщениях.""" # Updated docstring

    strings = {
        "name": "AutoJoinChat",
        "_cls_doc": "Модуль для автоматического присоединения к чатам/каналам Telegram по ссылкам, включая формат t.me/+, найденным в сообщениях. Поддерживает отслеживание ссылок в определенном чате или во всех чатах.", # Updated
        "enabled": "✅ Автовход по ссылкам включен.",
        "disabled": "❌ Автовход по ссылкам выключен.",
        "status": "<emoji document_id=5875291072225087249>📊</emoji> Статус автовхода по ссылкам:\n"
                  "Статус: {}\n"
                  "Чат для отслеживания ссылок: {}\n"
                  "Задержка перед входом (секунды): {}",
        "help_text": """<emoji document_id=5931415565955503486>🤖</emoji> AutoJoinChat - Помощь

<emoji document_id=5935847413859225147>🏀</emoji> Команды:
<code>.ajcon</code> - Включить автовход по ссылкам
<code>.ajcoff</code> - Выключить автовход по ссылкам
<code>.ajcsetchat &lt;ID чата&gt;</code> - Установить ID чата, в котором модуль будет отслеживать ссылки. Если <code>0</code>, отслеживаются все чаты.
<code>.ajcstatus</code> - Показать статус
<code>.ajchelp</code> - Эта справка

<emoji document_id=5877260593903177342>⚙</emoji> Как работает:
Модуль отслеживает входящие сообщения. Если в сообщении найдена ссылка на Telegram чат/канал (например, <code>t.me/joinchat/...</code>, <code>t.me/+...</code>, <code>t.me/channel_username</code>), модуль автоматически пытается присоединиться к этому чату/каналу.
<b>Важное уточнение:</b> Модуль корректно обрабатывает ссылки вида <code>https://t.me/+ИдентификаторПриглашения</code>.

Можно настроить конкретный чат, в котором будут отслеживаться ссылки. Если чат для отслеживания не указан (или установлен в <code>0</code>), модуль будет реагировать на ссылки во всех чатах, где он активен.

<emoji document_id=5843843420468024653>⭐️</emoji> Настройки:
В конфиге модуля можно изменить:
<code>enabled</code>: Включено ли автоматическое присоединение. По умолчанию: <code>False</code>.
<code>listening_chat_id</code>: ID чата, в котором модуль будет отслеживать ссылки. Установите <code>0</code>, чтобы отслеживать ссылки во всех чатах. По умолчанию: <code>0</code>.
<code>join_delay</code>: Список задержек в секундах перед попыткой присоединения. Используется случайное значение из списка, чтобы имитировать действие человека. Если указано несколько, будет выбрано случайное. По умолчанию: <code>[1.0, 3.0]</code>.
""",
        "listening_chat_display_all": "Все чаты",
        "listening_chat_display_specific": "<code>{}</code>",
        "set_chat_usage": "⚠️ Использование: <code>.ajcsetchat &lt;ID чата&gt;</code> (например, <code>.ajcsetchat -1001234567890</code> или <code>.ajcsetchat 0</code> для всех чатов).",
        "chat_set_success": "✅ Чат для отслеживания ссылок установлен: {}.",
        "no_links_found": "ℹ️ В сообщении не найдено ссылок на Telegram чаты/каналы.",
        "delay_before_join": "⏳ AutoJoinChat: Обнаружена ссылка '{link}'. Ожидание {delay} секунд перед присоединением...",
        "joined_chat": "🎉 AutoJoinChat: Успешно присоединен к чату/каналу по ссылке '{link}'.",
        "join_error": "❌ AutoJoinChat: Ошибка при присоединении к чату/каналу по ссылке '{link}': {error}",
        "processing_link": "🔍 AutoJoinChat: Обработка ссылки: {link}",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "enabled",
                False,
                lambda: "Включено ли автоматическое присоединение к чатам/каналам по ссылкам",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "listening_chat_id",
                0, # 0 means all chats
                lambda: "ID чата, в котором модуль будет отслеживать ссылки. Установите 0, чтобы отслеживать ссылки во всех чатах.",
                validator=loader.validators.Integer(minimum=0)
            ),
            loader.ConfigValue(
                "join_delay",
                [1.0, 3.0], # Random delay between 1 and 3 seconds
                lambda: "Список задержек в секундах перед попыткой присоединения. Используется случайное значение из списка, чтобы имитировать действие человека.", # Clarified description
                validator=loader.validators.Series(loader.validators.Float(minimum=0.1, maximum=30.0))
            ),
        )
        self._client = None
        self._self_id = None
        self._processed_messages = set() # Для отслеживания уже обработанных сообщений
        self._processed_messages_cleanup_task = None

    async def client_ready(self, client, _):
        self._client = client
        self._self_id = (await self._client.get_me()).id
        if self._processed_messages_cleanup_task is None:
            self._processed_messages_cleanup_task = asyncio.create_task(self._cleanup_processed_messages_loop())

    async def _cleanup_processed_messages_loop(self):
        """Периодически очищает набор обработанных ID сообщений."""
        while True:
            await asyncio.sleep(300) # Очищать каждые 5 минут
            if self._processed_messages:
                logger.debug(f"AutoJoinChat: Очистка {len(self._processed_messages)} обработанных ID сообщений.")
                self._processed_messages.clear()
            
    async def _on_unload(self):
        """Останавливает задачи при выгрузке модуля."""
        if self._processed_messages_cleanup_task:
            self._processed_messages_cleanup_task.cancel()
            try:
                await self._processed_messages_cleanup_task
            except asyncio.CancelledError:
                logger.debug("AutoJoinChat: Задача очистки обработанных сообщений отменена.")

    @loader.command(ru_doc="Включить автовход по ссылкам")
    async def ajcon(self, message: Message):
        """Включить автовход по ссылкам."""
        self.config["enabled"] = True
        await utils.answer(message, self.strings("enabled"))

    @loader.command(ru_doc="Выключить автовход по ссылкам")
    async def ajcoff(self, message: Message):
        """Выключить автовход по ссылкам."""
        self.config["enabled"] = False
        await utils.answer(message, self.strings("disabled"))

    @loader.command(ru_doc="Установить ID чата для отслеживания ссылок")
    async def ajcsetchat(self, message: Message):
        """Установить ID чата, в котором модуль будет отслеживать ссылки. Установите 0, чтобы отслеживать ссылки во всех чатах."""
        args = utils.get_args_raw(message)
        try:
            chat_id = int(args)
            self.config["listening_chat_id"] = chat_id
            
            chat_display_name = ""
            if chat_id == 0:
                chat_display_name = self.strings("listening_chat_display_all")
            else:
                chat_display_name = self.strings("listening_chat_display_specific").format(chat_id)

            await utils.answer(message, self.strings("chat_set_success").format(chat_display_name))
        except ValueError:
            await utils.answer(message, self.strings("set_chat_usage"))

    @loader.command(ru_doc="Показать статус автовхода по ссылкам")
    async def ajcstatus(self, message: Message):
        """Показать текущий статус автовхода по ссылкам."""
        status = "🟢 Включен" if self.config["enabled"] else "🔴 Выключен"
        
        listening_chat_id = self.config["listening_chat_id"]
        chat_display_name = ""
        if listening_chat_id == 0:
            chat_display_name = self.strings("listening_chat_display_all")
        else:
            chat_display_name = self.strings("listening_chat_display_specific").format(listening_chat_id)

        join_delays = self.config["join_delay"]
        delay_display = f"[{', '.join(map(str, join_delays))}]" if len(join_delays) > 1 else str(join_delays[0])

        await utils.answer(message, self.strings("status").format(
            status,
            chat_display_name,
            delay_display
        ))

    @loader.command(ru_doc="Показать справку по модулю автовхода по ссылкам")
    async def ajchelp(self, message: Message):
        """Показать справку по модулю AutoJoinChat."""
        await utils.answer(message, self.strings("help_text"))

    @loader.watcher(incoming=True, outgoing=False)
    async def watcher(self, message: Message):
        """Отслеживает входящие сообщения для обнаружения ссылок и автоматического присоединения."""
        if not self.config["enabled"]:
            return

        if not getattr(message, 'text', None):
            return

        message_identifier = (message.chat_id, message.id)
        if message_identifier in self._processed_messages:
            logger.debug(f"AutoJoinChat: Сообщение {message.id} в чате {message.chat_id} уже было обработано. Пропускаю.")
            return
        
        self._processed_messages.add(message_identifier)

        listening_chat_id = self.config["listening_chat_id"]
        if listening_chat_id != 0 and message.chat_id != listening_chat_id:
            logger.debug(f"AutoJoinChat: Сообщение в чате {message.chat_id} не соответствует настроенному чату для отслеживания ({listening_chat_id}). Пропускаю.")
            return

        found_links = set() # Используем set для хранения уникальных ссылок

        # 1. Поиск ссылок через message.entities
        if message.entities:
            for entity in message.entities:
                url_text = None
                if isinstance(entity, MessageEntityUrl):
                    url_text = message.text[entity.offset:entity.offset + entity.length]
                elif isinstance(entity, MessageEntityTextUrl):
                    url_text = entity.url # Прямой URL из TextUrl
                
                # Check for t.me links, including t.me/+
                if url_text and ("t.me/joinchat/" in url_text or "t.me/+" in url_text or re.search(r"t\.me/[a-zA-Z0-9_]{5,}", url_text)):
                    if not url_text.startswith(("http://", "https://")):
                        url_text = "https://" + url_text # Добавляем схему, если отсутствует
                    found_links.add(url_text)

        # 2. Дополнительный поиск ссылок с помощью регулярного выражения в тексте сообщения
        # Этот regex более общий и явно учитывает t.me/+
        # Измененный паттерн для более надежного захвата t.me/+
        # Группы: 1 - hash для joinchat/, 2 - идентификатор для t.me/+, 3 - username для t.me/username
        telegram_link_pattern = r"(?:https?://)?t\.me/(?:joinchat/([a-zA-Z0-9_-]+)|(?:\+([a-zA-Z0-9_-]+))(?:\?.*)?|([a-zA-Z0-9_]{5,}))"
        matches = re.findall(telegram_link_pattern, message.text)
        for match in matches:
            # match will be a tuple like (joinchat_hash, plus_invite, channel_username)
            # Only one element in the tuple will be non-empty for a given match
            if match[0]: # joinchat invite hash
                found_links.add(f"https://t.me/joinchat/{match[0]}")
            elif match[1]: # +invite (captured as 'invite_hash' in group 1, so reconstruct)
                found_links.add(f"https://t.me/+{match[1]}") # Explicitly add '+'
            elif match[2]: # channel username (at least 5 chars)
                found_links.add(f"https://t.me/{match[2]}")


        if not found_links:
            logger.debug(f"AutoJoinChat: В сообщении {message.id} не найдено подходящих ссылок. Пропускаю.")
            return

        for link in found_links:
            logger.info(self.strings("processing_link").format(link=link))
            try:
                join_delay = random.choice(self.config["join_delay"])
                logger.info(self.strings("delay_before_join").format(link=link, delay=join_delay))
                await asyncio.sleep(join_delay)

                # Используем высокоуровневый метод join_chat, который сам разбирается с типом ссылки
                await self._client.join_chat(link)
                logger.info(self.strings("joined_chat").format(link=link))
            except Exception as e:
                # Если уже состоим в чате, это не ошибка, просто информационное сообщение
                if "USER_ALREADY_PARTICIPANT" in str(e).upper():
                    logger.info(f"AutoJoinChat: Уже состою в чате по ссылке '{link}'.")
                else:
                    logger.error(self.strings("join_error").format(link=link, error=e))
