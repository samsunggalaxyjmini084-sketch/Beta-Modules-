# meta developer: @yourhandle
# meta name: AutoJoinChat
# meta version: 1.0.1 # Обновлена версия
import asyncio
import logging
import random
import re
import urllib.parse
from datetime import datetime, timedelta

from telethon import events
from telethon.tl.types import Message, User, Channel, Chat
from telethon.errors import (##
    ChannelPrivateError,
    InviteHashExpiredError,
    UserChannelsTooMuchError,
    UserAlreadyParticipantError,
    RPCError,
)

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class AutoJoinChatMod(loader.Module):
    """
    Модуль для автоматического вступления в чаты по ссылкам в сообщениях или по кнопкам.
    """

    strings = {
        "name": "AutoJoinChat",
        "_cls_doc": "Модуль для автоматического вступления в чаты по ссылкам в сообщениях или по кнопкам.",
        "enabled": "✅ Автовход в чаты включен.",
        "disabled": "❌ Автовход в чаты выключен.",
        "status": "<emoji document_id=5875291072225087249>📊</emoji> Статус автовхода в чаты:\n"
                  "Статус: {}\n"
                  "Вступление по ссылкам: {}\n"
                  "Вступление по кнопкам: {}\n"
                  "Разрешенные чаты для отслеживания: {}\n"
                  "Игнорируемые целевые чаты: {}\n"
                  "Задержка вступления (сек): {}\n"
                  "Ключевые слова кнопок: {}\n"
                  "Обрабатывать только новые сообщения: {}",
        "joined_chat_success": "🎉 AutoJoinChat: Успешно вступил в чат <b>{}</b> (ID: <code>{}</code>).",
        "already_in_chat": "ℹ️ AutoJoinChat: Уже являюсь участником чата <b>{}</b> (ID: <code>{}</code>). Пропускаю.",
        "ignored_target_chat": "🚫 AutoJoinChat: Чат <b>{}</b> (ID: <code>{}</code>) находится в списке игнорируемых. Покинул чат.",
        "private_channel_error": "❌ AutoJoinChat: Не удалось вступить в чат <code>{}</code>: это приватный канал/группа, для вступления нужен invite-hash, а предоставленная ссылка не является полноценным invite, или она недействительна.",
        "invite_expired_error": "❌ AutoJoinChat: Не удалось вступить в чат <code>{}</code>: ссылка-приглашение истекла или недействительна.",
        "too_many_channels": "❌ AutoJoinChat: Слишком много каналов. Невозможно вступить в <b>{}</b>.",
        "join_error": "❌ AutoJoinChat: Ошибка при вступлении в чат <b>{}</b>: <code>{}</code>",
        "help_text": """<emoji document_id=5931415565955503486>🤖</emoji> <b>AutoJoinChat</b> - Помощь
        
        <emoji document_id=5935847413859225147>🚀</emoji> <b>Команды:</b>
        <code>.ajcon</code> - Включить автовход в чаты
        <code>.ajcoff</code> - Выключить автовход в чаты
        <code>.ajcstatus</code> - Показать статус
        <code>.ajchelp</code> - Эта справка
        
        <emoji document_id=5877260593901971030>⚙</emoji> <b>Как работает:</b>
        Модуль автоматически вступает в чаты по ссылкам, найденным в сообщениях, или по кнопкам.
        
        <b>Сценарий 1: Ссылки в сообщениях</b>
        Если в разрешенном чате (<code>allowed_source_chats</code>) появляется сообщение, содержащее Telegram-ссылку (<code>t.me/...</code>, <code>tg://...</code>), модуль попытается вступить в этот чат после небольшой задержки.
        
        <b>Сценарий 2: Кнопки 'Вступить'</b>
        Если в разрешенном чате появляется сообщение с инлайн-кнопкой, текст которой содержит одно из настроенных ключевых слов (<code>button_join_keywords</code>, например "вступить", "join"), и эта кнопка является URL-кнопкой, модуль попытается вступить в чат по этому URL.
        
        <b>Важное примечание о кнопке "Вступить в группу" (голубая кнопка в UI)</b>:
        Когда вы переходите по invite-ссылке в официальном Telegram-клиенте, часто появляется экран предпросмотра с большой голубой кнопкой "Вступить в группу". Ваш юзербот, работая через API Telegram (Telethon), **не может напрямую взаимодействовать с этим элементом интерфейса**. Вместо этого, метод <code>client.join_chat(ссылка)</code> отправляет программный запрос на серверы Telegram, который **эквивалентен нажатию этой кнопки**. То есть, модуль уже выполняет это действие программно.

        <emoji document_id=5843843420468024653>⭐️</emoji> <b>Настройки (.cfg):</b>
        <code>enabled</code> (<code>bool</code>, по умолчанию <code>False</code>): Включить/выключить модуль.
        <code>auto_join_from_links</code> (<code>bool</code>, по умолчанию <code>True</code>): Включает/выключает вступление по ссылкам.
        <code>auto_join_from_buttons</code> (<code>bool</code>, по умолчанию <code>True</code>): Включает/выключает вступление по кнопкам.
        <code>allowed_source_chats</code> (<code>list</code>, по умолчанию <code>[]</code>): Список ID чатов, где модуль будет искать ссылки/кнопки. Если список пуст, отслеживаются все чаты.
        <code>ignored_target_chats</code> (<code>list</code>, по умолчанию <code>[]</code>): Список ID чатов, в которые модуль НИКОГДА не будет вступать автоматически, даже если найдет ссылку/кнопку. Если модуль вступит в такой чат, он попытается сразу же его покинуть.
        <code>join_delay</code> (<code>list</code>, по умолчанию <code>[2, 5]</code>): Диапазон случайной задержки (в секундах) перед попыткой вступления. Помогает избежать флуд-контроля. Если указано одно число, задержка фиксированная.
        <code>button_join_keywords</code> (<code>list</code>, по умолчанию <code>[\"вступить\", \"join\", \"присоединиться\", \"в канал\", \"в группу\"]</code>): Список ключевых слов (регистронезависимых), которые должны содержаться в тексте URL-кнопки для ее активации.
        <code>process_only_new_messages</code> (<code>bool</code>, по умолчанию <code>True</code>): Если <code>True</code>, модуль будет обрабатывать только сообщения, пришедшие после его загрузки/включения. Если <code>False</code>, он может попытаться обработать последние сообщения в чате при старте (не рекомендуется).
        """
    }

    # Регулярное выражение для поиска различных форматов Telegram-ссылок, включая t.me/+HASH
    TELEGRAM_LINK_PATTERN = re.compile(
        r'(?:https?://)?(?:t\.me|telegram\.me)/'
        r'(?:'
            r'(joinchat/[a-zA-Z0-9_\-]+)' # Group 1: joinchat/HASH
            r'|'
            r'(\+[a-zA-Z0-9_\-]+)'       # Group 2: +HASH (e.g., t.me/+HASH, как на скриншоте)
            r'|'
            r'([a-zA-Z0-9_]{5,})'        # Group 3: username (минимум 5 символов для публичных хэндлов)
        r')\b'
        r'|'
        r'tg://(?:resolve\?domain=|join\?invite=)([a-zA-Z0-9_\-]+)\b' # Group 4: domain или hash из tg://
    )

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "enabled",
                False,
                lambda: "Включен ли автовход в чаты.",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "auto_join_from_links",
                True,
                lambda: "Автоматически вступать в чаты по ссылкам в сообщениях.",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "auto_join_from_buttons",
                True,
                lambda: "Автоматически вступать в чаты по кнопкам 'Вступить' в сообщениях.",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "allowed_source_chats",
                [],
                lambda: "Список ID чатов, где будут отслеживаться ссылки/кнопки для входа. Если пуст, отслеживаются все чаты.",
                validator=loader.validators.Series(loader.validators.Integer())
            ),
            loader.ConfigValue(
                "ignored_target_chats",
                [],
                lambda: "Список ID чатов, в которые НЕ нужно автоматически вступать. Если модуль вступит в такой чат, он попытается сразу же его покинуть.",
                validator=loader.validators.Series(loader.validators.Integer())
            ),
            loader.ConfigValue(
                "join_delay",
                [2, 5],
                lambda: "Диапазон задержки (в секундах) перед вступлением в чат/нажатием кнопки. Если несколько значений, будет выбрано случайное.",
                validator=loader.validators.Series(loader.validators.Float(minimum=0.5))
            ),
            loader.ConfigValue(
                "button_join_keywords",
                ["вступить", "join", "присоединиться", "в канал", "в группу"],
                lambda: "Ключевые слова в тексте кнопки для автоматического вступления в чат (регистронезависимо).",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                "process_only_new_messages",
                True,
                lambda: "Обрабатывать только новые входящие сообщения (True) или также сообщения после перезагрузки/старта (False).",
                validator=loader.validators.Boolean()
            ),
        )
        self._processed_messages_ids = set() 
        self._cleanup_task = None
    
    async def client_ready(self, client, _):
        self._client = client
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_processed_messages_loop())

    async def _cleanup_processed_messages_loop(self):
        """Периодически очищает набор обработанных ID сообщений."""
        while True:
            await asyncio.sleep(3600)  # Чистим каждый час
            if self._processed_messages_ids:
                logger.debug(f"AutoJoinChat: Очистка {len(self._processed_messages_ids)} обработанных ID сообщений.")
                self._processed_messages_ids.clear()

    async def _on_unload(self):
        """Останавливает задачи при выгрузке модуля."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                logger.debug("AutoJoinChat: Задача очистки обработанных сообщений отменена.")

    def _get_entity_name(self, entity):
        """Вспомогательная функция для получения читаемого имени сущности Telethon."""
        if isinstance(entity, User):
            if entity.first_name and entity.last_name:
                return f"{entity.first_name} {entity.last_name}"
            if entity.first_name:
                return entity.first_name
            if entity.username:
                return f"@{entity.username}"
            return f"User {entity.id}"
        elif isinstance(entity, (Channel, Chat)):
            return entity.title
        return f"Entity {entity.id}"

    async def _join_chat_action(self, target_identifier: str, message: Message):
        """
        Внутренняя функция для выполнения действия вступления в чат.
        `target_identifier` может быть invite-hash, username или полной ссылкой.
        """
        if not self.config["enabled"]:
            logger.debug("AutoJoinChat: Модуль выключен, пропуск действия вступления.")
            return

        delay_range = self.config["join_delay"]
        chosen_delay = random.uniform(delay_range[0], delay_range[1]) if len(delay_range) > 1 else delay_range[0]

        logger.debug(f"AutoJoinChat: Ожидание {chosen_delay:.2f} секунд перед попыткой вступления в чат '{target_identifier}'...")
        await asyncio.sleep(chosen_delay)

        try:
            # Пытаемся вступить в чат
            await self._client.join_chat(target_identifier)

            # После успешного вступления получаем фактическую сущность и ее имя/ID
            joined_entity = await self._client.get_entity(target_identifier)
            joined_entity_name = self._get_entity_name(joined_entity)
            joined_entity_id = getattr(joined_entity, 'id', 'N/A')

            # Проверяем, находится ли чат в списке игнорируемых
            if joined_entity_id in self.config["ignored_target_chats"]:
                logger.info(self.strings("ignored_target_chat").format(joined_entity_name, joined_entity_id))
                await utils.answer(message, self.strings("ignored_target_chat").format(joined_entity_name, joined_entity_id))
                # Покидаем чат, так как он игнорируется
                try:
                    await self._client.delete_dialog(joined_entity)
                    logger.info(f"AutoJoinChat: Успешно покинул игнорируемый чат {joined_entity_name} ({joined_entity_id}).")
                except Exception as e:
                    logger.warning(f"AutoJoinChat: Не удалось покинуть игнорируемый чат {joined_entity_name} ({joined_entity_id}): {e}")
                return

            logger.info(self.strings("joined_chat_success").format(joined_entity_name, joined_entity_id))
            await utils.answer(message, self.strings("joined_chat_success").format(joined_entity_name, joined_entity_id))

        except UserAlreadyParticipantError:
            # Если уже состоим в чате, пытаемся получить его данные для логов и проверки на игнорирование
            existing_entity_name = target_identifier
            existing_entity_id = "N/A"
            try:
                existing_entity = await self._client.get_entity(target_identifier)
                existing_entity_name = self._get_entity_name(existing_entity)
                existing_entity_id = getattr(existing_entity, 'id', 'N/A')
            except Exception as e:
                logger.debug(f"AutoJoinChat: Не удалось разрешить сущность для '{target_identifier}' после UserAlreadyParticipantError: {e}")

            if existing_entity_id in self.config["ignored_target_chats"]:
                logger.info(self.strings("ignored_target_chat").format(existing_entity_name, existing_entity_id))
                await utils.answer(message, self.strings("ignored_target_chat").format(existing_entity_name, existing_entity_id))
                return # Не покидаем, т.к. уже были участником и это был только повторный join_chat
            
            logger.info(self.strings("already_in_chat").format(existing_entity_name, existing_entity_id))
            await utils.answer(message, self.strings("already_in_chat").format(existing_entity_name, existing_entity_id))

        except ChannelPrivateError:
            logger.warning(self.strings("private_channel_error").format(target_identifier))
            await utils.answer(message, self.strings("private_channel_error").format(target_identifier))
        except InviteHashExpiredError:
            logger.warning(self.strings("invite_expired_error").format(target_identifier))
            await utils.answer(message, self.strings("invite_expired_error").format(target_identifier))
        except UserChannelsTooMuchError:
            logger.warning(self.strings("too_many_channels").format(target_identifier))
            await utils.answer(message, self.strings("too_many_channels").format(target_identifier))
        except RPCError as e:
            logger.error(self.strings("join_error").format(target_identifier, e))
            await utils.answer(message, self.strings("join_error").format(target_identifier, e))
        except Exception as e:
            logger.exception(f"AutoJoinChat: Неожиданная ошибка при вступлении в чат '{target_identifier}': {e}")
            await utils.answer(message, self.strings("join_error").format(target_identifier, e))

    @loader.command(ru_doc="Включить автовход в чаты")
    async def ajcon(self, message: Message):
        """Включить автовход в чаты"""
        self.config["enabled"] = True
        await utils.answer(message, self.strings("enabled"))

    @loader.command(ru_doc="Выключить автовход в чаты")
    async def ajcoff(self, message: Message):
        """Выключить автовход в чаты"""
        self.config["enabled"] = False
        self._processed_messages_ids.clear()
        await utils.answer(message, self.strings("disabled"))

    @loader.command(ru_doc="Показать статус автовхода в чаты")
    async def ajcstatus(self, message: Message):
        """Показать статус автовхода в чаты"""
        status = "🟢 Включен" if self.config["enabled"] else "🔴 Выключен"
        
        join_links_status = "✅ Включено" if self.config["auto_join_from_links"] else "❌ Выключено"
        join_buttons_status = "✅ Включено" if self.config["auto_join_from_buttons"] else "❌ Выключено"

        allowed_chats_display = ", ".join(map(str, self.config["allowed_source_chats"])) if self.config["allowed_source_chats"] else "Все чаты"
        ignored_chats_display = ", ".join(map(str, self.config["ignored_target_chats"])) if self.config["ignored_target_chats"] else "(пусто)"

        join_delays = self.config["join_delay"]
        delay_display = f"[{', '.join(map(str, join_delays))}]" if len(join_delays) > 1 else str(join_delays[0])

        button_keywords_display = ", ".join(self.config["button_join_keywords"]) if self.config["button_join_keywords"] else "(пусто)"
        
        process_only_new_messages_display = "Да" if self.config["process_only_new_messages"] else "Нет"

        await utils.answer(message, self.strings("status").format(
            status,
            join_links_status,
            join_buttons_status,
            allowed_chats_display,
            ignored_chats_display,
            delay_display,
            button_keywords_display,
            process_only_new_messages_display
        ))

    @loader.command(ru_doc="Показать справку по модулю")
    async def ajchelp(self, message: Message):
        """Показать справку"""
        await utils.answer(message, self.strings("help_text"))

    @loader.watcher(incoming=True, outgoing=False) # Отслеживаем только входящие сообщения
    async def watcher(self, message: Message):
        """Обработчик всех входящих сообщений для автовхода."""
        try:
            if not self.config["enabled"]:
                return

            if not getattr(message, 'text', None) and not getattr(message, 'buttons', None):
                # Если нет ни текста, ни кнопок, нет смысла обрабатывать
                return
            
            # Идентификатор сообщения для отслеживания (chat_id, message_id)
            message_identifier = (message.chat_id, message.id) 
            if self.config["process_only_new_messages"] and message_identifier in self._processed_messages_ids:
                logger.debug(f"AutoJoinChat: Сообщение {message.id} в чате {message.chat_id} уже было обработано. Пропускаю.")
                return
            
            # Добавляем сообщение в набор обработанных ID
            self._processed_messages_ids.add(message_identifier)

            # Фильтруем по разрешенным чатам-источникам
            allowed_source_chats = self.config["allowed_source_chats"]
            if allowed_source_chats and message.chat_id not in allowed_source_chats:
                logger.debug(f"AutoJoinChat: Чат {message.chat_id} не в списке разрешенных источников. Пропускаю сообщение {message.id}.")
                return

            msg_text = message.text if message.text else "" # Убедимся, что text не None
            
            # --- Сценарий 1: Автовход по ссылкам в сообщениях ---
            if self.config["auto_join_from_links"] and msg_text:
                extracted_identifiers = set()

                for match in self.TELEGRAM_LINK_PATTERN.finditer(msg_text):
                    identifier = None
                    if match.group(1): # joinchat/HASH
                        identifier = match.group(1) 
                    elif match.group(2): # +HASH (e.g., t.me/+HASH)
                        identifier = match.group(2)
                    elif match.group(3): # username
                        identifier = match.group(3)
                    elif match.group(4): # tg:// domain or hash
                        identifier = match.group(4)
                    
                    if identifier:
                        extracted_identifiers.add(identifier)
                
                for identifier in extracted_identifiers:
                    logger.info(f"AutoJoinChat: Обнаружен идентификатор чата '{identifier}' в сообщении {message.id}. Попытка вступить.")
                    await self._join_chat_action(identifier, message)

            # --- Сценарий 2: Автовход по кнопкам "Вступить" ---
            if self.config["auto_join_from_buttons"] and getattr(message, 'buttons', None):
                button_keywords_lower = [kw.lower() for kw in self.config["button_join_keywords"]]
                
                for row in message.buttons:
                    for button in row:
                        button_text = getattr(button, 'text', '')
                        if any(keyword in button_text.lower() for keyword in button_keywords_lower):
                            if getattr(button, 'url', None):
                                button_url = button.url
                                logger.info(f"AutoJoinChat: Обнаружена кнопка присоединения '{button_text}' с URL '{button_url}' в сообщении {message.id}. Попытка вступить.")
                                await self._join_chat_action(button_url, message)
                            elif getattr(button, 'data', None):
                                logger.warning(
                                    f"AutoJoinChat: Обнаружена callback-кнопка '{button_text}' в сообщении {message.id}. "
                                    "Модуль не поддерживает автоматическое нажатие callback-кнопок для вступления (обычно требуют дополнительных действий)."
                                )
                            # Не используем break здесь, чтобы дать возможность обработать все кнопки в сообщении, если их несколько.
                            # Если нужно обрабатывать только одну кнопку, можно вернуть break.
            
        except Exception as e:
            logger.exception(f"❌ AutoJoinChat: Критическая ошибка в watcher для сообщения {getattr(message, 'id', 'N/A')} в чате {getattr(message, 'chat_id', 'N/A')}: {e}")
