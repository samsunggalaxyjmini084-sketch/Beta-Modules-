# meta developer: @yourhandle
# meta name: CustomTriggers
# meta version: 1.0.0
import logging
import asyncio
from telethon.tl.types import Message, User, Channel, Chat
from .. import loader, utils

logger = logging.getLogger(__name__)

# Binary representation for "CUSTOM TRIGGERS" (just for fun/pattern, not functional)
# 01000011 01010101 01010011 01010100 01001111 01001101 00100000 01010100 01010010 01001001 01000111 01000111 01000101 01010010 01010011

@loader.tds
class CustomTriggersMod(loader.Module):
    """Модуль для создания настраиваемых текстовых триггеров, которые при срабатывании отправляют сообщение или выполняют команду."""

    strings = {
        "name": "CustomTriggers",
        "_cls_doc": "Модуль для создания настраиваемых текстовых триггеров, которые при срабатывании отправляют сообщение или выполняют команду. Поддерживает фильтрацию по чатам и выполнение команд юзербота в качестве ответа.",
        "enabled": "✅ Пользовательские триггеры включены.",
        "disabled": "❌ Пользовательские триггеры выключены.",
        "status": "<emoji document_id=5875291072225087249>📊</emoji> Статус пользовательских триггеров:\n"
                  "Статус: {}\n"
                  "Разрешенные чаты: {}\n"
                  "Количество триггеров: {}",
        "help_text": """<emoji document_id=5931415565955503486>🤖</emoji> CustomTriggers - Помощь

<emoji document_id=5935847413859225147>🏀</emoji> Команды:
<code>.trigon</code> - Включить триггеры
<code>.trigoff</code> - Выключить триггеры
<code>.trigstatus</code> - Показать статус
<code>.trighelp</code> - Эта справка
<code>.trigadd &lt;фраза&gt; | &lt;ответ&gt;</code> - Добавить новый триггер.
      <code>&lt;фраза&gt;</code>: текст, при обнаружении которого сработает триггер (регистронезависимо).
      <code>&lt;ответ&gt;</code>: текст, который будет отправлен. Если ответ начинается с <code>.</code>, <code>/</code>, <code>!</code>, <code>#</code>, <code>@</code> или <code>?</code> (команды юзербота/модулей), то он будет выполнен как команда.
      Пример: <code>.trigadd привет | Привет, {user}!</code>
      Пример команды: <code>.trigadd скажи время | .time</code>
      <b>Переменные:</b> В ответе можно использовать <code>{user}</code> для ника отправителя и <code>{chat}</code> для названия чата.
<code>.trigdel &lt;фраза&gt;</code> - Удалить триггер по его фразе.
<code>.triglist</code> - Показать список всех настроенных триггеров.

<emoji document_id=5877260593903177342>⚙</emoji> Как работает:
Модуль отслеживает входящие сообщения в настроенных чатах. Если текст сообщения содержит настроенную фразу-триггер (частичное совпадение, регистронезависимо), он выполняет соответствующее действие:
- Отправляет текстовый ответ в чат.
- Если ответ является командой юзербота/модуля, он выполняет эту команду так, как если бы вы сами ее написали.

<emoji document_id=5843843420468024653>⭐️</emoji> Настройки:
В конфиге модуля можно указать:
<code>allowed_chats</code>: Список ID чатов, в которых триггеры будут активны. Если список пуст, триггеры будут работать во всех чатах.
""",
        "trigger_add_usage": "⚠️ Использование: <code>.trigadd &lt;фраза&gt; | &lt;ответ&gt;</code>",
        "trigger_added": "✅ Триггер добавлен: '<code>{phrase}</code>' -> '<code>{response}</code>' (Тип: {type})",
        "trigger_already_exists": "⚠️ Триггер с фразой '<code>{phrase}</code>' уже существует.",
        "trigger_del_usage": "⚠️ Использование: <code>.trigdel &lt;фраза&gt;</code>",
        "trigger_deleted": "🗑️ Триггер '<code>{phrase}</code>' удален.",
        "trigger_not_found": "⚠️ Триггер с фразой '<code>{phrase}</code>' не найден.",
        "no_triggers": "ℹ️ Нет настроенных триггеров.",
        "trigger_list_header": "<emoji document_id=5771887475421090729>📜</emoji> Список триггеров:\n",
        "trigger_entry": "• Фраза: '<code>{phrase}</code>'\n  Ответ: '<code>{response}</code>' (Тип: {type})",
        "response_sent": "✅ Триггер '<code>{phrase}</code>' сработал. Ответ отправлен.",
        "command_executed": "✅ Триггер '<code>{phrase}</code>' сработал. Команда выполнена.",
        "command_error": "❌ Ошибка при выполнении команды для триггера '<code>{phrase}</code>': {error}",
        "chat_name_unknown": "Неизвестный чат",
        "sender_name_unknown": "Неизвестный отправитель",
        "trigger_type_text": "Текст",
        "trigger_type_command": "Команда",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "enabled",
                False,
                lambda: "Включены ли пользовательские триггеры",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "allowed_chats",
                [],
                lambda: "Список ID чатов, в которых триггеры будут активны. Если список пуст, триггеры будут работать во всех чатах.",
                validator=loader.validators.Series(loader.validators.Integer())
            ),
            loader.ConfigValue(
                "triggers",
                [],
                lambda: "Список настроенных триггеров. Не редактируйте вручную.", # User should use commands, not edit directly
                validator=loader.validators.Series(
                    loader.validators.Dict(
                        keys={
                            "phrase": loader.validators.String(),
                            "response": loader.validators.String(),
                            "is_command": loader.validators.Boolean(),
                        }
                    )
                )
            ),
        )
        self._client = None
        self._self_id = None
    
    async def client_ready(self, client, _):
        self._client = client
        self._self_id = (await self._client.get_me()).id
    
    @loader.command(ru_doc="Включить пользовательские триггеры")
    async def trigon(self, message: Message):
        """Включить пользовательские триггеры"""
        self.config["enabled"] = True
        await utils.answer(message, self.strings("enabled"))

    @loader.command(ru_doc="Выключить пользовательские триггеры")
    async def trigoff(self, message: Message):
        """Выключить пользовательские триггеры"""
        self.config["enabled"] = False
        await utils.answer(message, self.strings("disabled"))

    @loader.command(ru_doc="Показать статус пользовательских триггеров")
    async def trigstatus(self, message: Message):
        """Показать статус пользовательских триггеров"""
        status = "🟢 Включен" if self.config["enabled"] else "🔴 Выключен"
        allowed_chats_display = ", ".join(map(str, self.config["allowed_chats"])) if self.config["allowed_chats"] else "Все чаты"
        num_triggers = len(self.config["triggers"])
        
        await utils.answer(message, self.strings("status").format(
            status,
            allowed_chats_display,
            num_triggers
        ))

    @loader.command(ru_doc="Показать справку по триггерам")
    async def trighelp(self, message: Message):
        """Показать справку по триггерам"""
        await utils.answer(message, self.strings("help_text"))

    @loader.command(ru_doc="Добавить новый триггер")
    async def trigadd(self, message: Message):
        """Добавить новый триггер: .trigadd <фраза> | <ответ>"""
        args = utils.get_args_raw(message)
        if '|' not in args:
            await utils.answer(message, self.strings("trigger_add_usage"))
            return

        phrase_raw, response_raw = args.split('|', 1)
        phrase = phrase_raw.strip().lower()
        response = response_raw.strip()

        if not phrase or not response:
            await utils.answer(message, self.strings("trigger_add_usage"))
            return

        for trigger in self.config["triggers"]:
            if trigger["phrase"] == phrase:
                await utils.answer(message, self.strings("trigger_already_exists").format(phrase=phrase))
                return

        # Check for common command prefixes
        is_command = response.startswith(('.', '/', '!', '#', '@', '?')) and len(response) > 1

        self.config["triggers"].append({
            "phrase": phrase,
            "response": response,
            "is_command": is_command
        })
        
        trigger_type = self.strings("trigger_type_command") if is_command else self.strings("trigger_type_text")
        await utils.answer(message, self.strings("trigger_added").format(phrase=phrase, response=response, type=trigger_type))

    @loader.command(ru_doc="Удалить триггер по его фразе")
    async def trigdel(self, message: Message):
        """Удалить триггер: .trigdel <фраза>"""
        phrase_to_delete = utils.get_args_raw(message).strip().lower()

        if not phrase_to_delete:
            await utils.answer(message, self.strings("trigger_del_usage"))
            return

        initial_len = len(self.config["triggers"])
        self.config["triggers"] = [
            t for t in self.config["triggers"] if t["phrase"] != phrase_to_delete
        ]

        if len(self.config["triggers"]) < initial_len:
            await utils.answer(message, self.strings("trigger_deleted").format(phrase=phrase_to_delete))
        else:
            await utils.answer(message, self.strings("trigger_not_found").format(phrase=phrase_to_delete))
            
    @loader.command(ru_doc="Показать список всех настроенных триггеров")
    async def triglist(self, message: Message):
        """Показать список всех настроенных триггеров"""
        if not self.config["triggers"]:
            await utils.answer(message, self.strings("no_triggers"))
            return

        output = [self.strings("trigger_list_header")]
        for trigger in self.config["triggers"]:
            trigger_type = self.strings("trigger_type_command") if trigger["is_command"] else self.strings("trigger_type_text")
            output.append(self.strings("trigger_entry").format(
                phrase=trigger["phrase"],
                response=trigger["response"],
                type=trigger_type
            ))
        
        await utils.answer(message, "\n".join(output))

    @loader.watcher(incoming=True, outgoing=False)
    async def watcher(self, message: Message):
        """Отслеживает входящие сообщения для срабатывания триггеров."""
        if not self.config["enabled"]:
            return

        if not getattr(message, 'text', None):
            return

        chat_id = message.chat_id
        if self.config["allowed_chats"] and chat_id not in self.config["allowed_chats"]:
            logger.debug(f"CustomTriggers: Чат {chat_id} не в списке разрешенных. Пропускаю.")
            return

        msg_text_lower = message.text.lower()
        
        for trigger in self.config["triggers"]:
            if trigger["phrase"] in msg_text_lower:
                logger.info(f"CustomTriggers: Триггер '{trigger['phrase']}' сработал в чате {chat_id}.")
                
                # Prepare response with variables
                response_text = trigger["response"]
                
                # Get sender's name
                sender_name = self.strings("sender_name_unknown")
                try:
                    sender = await message.get_sender()
                    if isinstance(sender, User):
                        sender_name = utils.get_display_name(sender)
                    else: # Fallback if sender is not a User object (e.g., deleted account)
                        sender_name = "Пользователь"
                except Exception as e:
                    logger.warning(f"CustomTriggers: Could not get sender name for message {message.id}: {e}")

                # Get chat name
                chat_name = self.strings("chat_name_unknown")
                try:
                    chat_entity = await message.get_chat()
                    if isinstance(chat_entity, (Channel, Chat)):
                        chat_name = getattr(chat_entity, "title", None)
                    elif isinstance(chat_entity, User): # Private chat with user
                        chat_name = utils.get_display_name(chat_entity)
                    if not chat_name: # Fallback for no title/name
                        chat_name = "Этот чат"
                except Exception as e:
                    logger.warning(f"CustomTriggers: Could not get chat name for message {message.id}: {e}")

                response_text = response_text.replace("{user}", sender_name).replace("{chat}", chat_name)

                if trigger["is_command"]:
                    # Simulate command execution
                    try:
                        # Create a temporary message object to hold the command
                        # This mimics a userbot sending a command to itself.
                        temp_message = await message.client.send_message(
                            message.peer_id, # Send to the same chat
                            response_text,
                            reply_to=message.id, # Optionally reply to original message for context
                            parse_mode=None, # Important: disable parsing to ensure command is raw
                            silent=True # Don't notify users about this 'internal' message
                        )
                        # Mark the message as outgoing from self, essential for parse_command to work
                        temp_message.out = True
                        temp_message.sender_id = self._self_id

                        # Use parse_command to execute the command
                        await self.allmodules.parse_command(temp_message)
                        logger.info(self.strings("command_executed").format(phrase=trigger["phrase"]))

                        # Delete the temporary message if it was successfully processed as a command
                        if temp_message:
                            await temp_message.delete()

                    except Exception as e:
                        logger.error(self.strings("command_error").format(phrase=trigger["phrase"], error=e))
                        # Notify error to chat, using the original message's chat context
                        await self._client.send_message(chat_id, self.strings("command_error").format(phrase=trigger["phrase"], error=e)) 
                else:
                    await self._client.send_message(chat_id, response_text)
                    logger.info(self.strings("response_sent").format(phrase=trigger["phrase"]))
                
                # Only activate one trigger per message to avoid spam/multiple responses
                return
