# meta developer: @yourhandle
# meta name: AutoConfirmAdd
# meta version: 1.0.1 # Обновлена версия

import logging
import asyncio
import random
from telethon.tl.types import Message, User
from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class AutoConfirmAddMod(loader.Module):
    """Модуль для автоматического нажатия кнопки 'Подтвердить' в сообщениях-запросах на добавление, отправленных ботами или пользователями.""" # Updated docstring

    strings = {
        "name": "AutoConfirmAdd",
        "_cls_doc": "Модуль для автоматического нажатия кнопки 'Подтвердить' в сообщениях-запросах на добавление, отправленных ботами или пользователями.", # Updated
        "enabled": "✅ Автоподтверждение включено.",
        "disabled": "❌ Автоподтверждение выключено.",
        "status": "<emoji document_id=5776375003280838798>📊</emoji> Статус автоподтверждения:\n"
                  "Статус: {}\n"
                  "Фраза-триггер: '{}'\n"
                  "Текст кнопки: '{}'\n"
                  "Задержка (секунды): {}\n"
                  "Целевые отправители: {}", # Updated string
        "help_text": """<emoji document_id=5931415565955503486>🤖</emoji> AutoConfirmAdd - Помощь

<emoji document_id=5935847413859225147>🏀</emoji> Команды:
<code>.acacon</code> - Включить автоподтверждение
<code>.acacoff</code> - Выключить автоподтверждение
<code>.acastatus</code> - Показать статус
<code>.acahelp</code> - Эта справка

<emoji document_id=5877260593903177342>⚙</emoji> Как работает:
Модуль отслеживает входящие сообщения от ботов или конкретных пользователей (или от вашего юзербота) в любом чате.
Если сообщение содержит настроенную <code>trigger_phrase</code> (по умолчанию: "Ты действительно хочешь добавить") и имеет кнопку с настроенным <code>button_text</code> (по умолчанию: "Подтвердить"), модуль автоматически нажмет эту кнопку.

Это полезно для автоматического подтверждения добавления других модулей/плагинов, активации ботов и т.д., где требуется подтверждение.
Задержка перед нажатием кнопки настраивается, чтобы имитировать человеческое действие.

<emoji document_id=5843843420468024653>⭐️</emoji> Настройки:
В конфиге модуля можно изменить:
<code>trigger_phrase</code>: Строка, которую модуль будет искать в тексте сообщения для активации. Регистр не учитывается.
    По умолчанию: <code>"Ты действительно хочешь добавить"</code>
<code>button_text</code>: Точный текст кнопки, которую модуль должен нажать. Регистр учитывается.
    По умолчанию: <code>"Подтвердить"</code> (соответствует скриншоту)
<code>delay</code>: Список задержек в секундах перед нажатием кнопки. Если указано несколько значений, будет выбрано случайное.
    По умолчанию: <code>[0.5, 1.5]</code>
<code>target_bot_ids</code>: Список ID ботов <b>или пользователей</b>, от которых ожидаются сообщения-запросы. Если список пуст, сообщения будут отслеживаться от <i>любого бота</i> или <i>вашего юзербота</i>.
    По умолчанию: <code>[]</code> (пусто)
""",
        "trigger_detected": "<emoji document_id=5776375003280838798>✅</emoji> Обнаружен запрос на подтверждение: '{phrase}'. Ищу кнопку '{button_text}'.",
        "button_clicked": "🎉 AutoConfirmAdd: Успешно нажата кнопка '{button_text}'.",
        "button_not_found": "⚠️ AutoConfirmAdd: Запрос на подтверждение '{phrase}' найден, но кнопка '{button_text}' не найдена.",
        "click_error": "❌ AutoConfirmAdd: Ошибка при нажатии кнопки '{button_text}': {error}",
        "delay_message": "⏳ AutoConfirmAdd: Ожидание {delay} секунд перед нажатием кнопки...",
        "target_bot_ids_display": "Не указаны (любой бот или юзербот)", # Updated string to reflect "any bot or userbot" fallback
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "enabled",
                False,
                lambda: "Включено ли автоматическое подтверждение",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "trigger_phrase",
                "Ты действительно хочешь добавить",
                lambda: "Фраза-триггер в сообщении для активации автоподтверждения (регистронезависимо).",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "button_text",
                "Подтвердить", 
                lambda: "Точный текст кнопки, которую нужно нажать (регистр учитывается).",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "delay",
                [0.5, 1.5],
                lambda: "Список задержек перед нажатием кнопки (секунды). Если указано несколько, будет выбрано случайное.",
                validator=loader.validators.Series(loader.validators.Float(minimum=0.1, maximum=10.0))
            ),
            loader.ConfigValue(
                "target_bot_ids", # Renamed to target_sender_ids for internal clarity, but kept config key for compatibility
                [],
                lambda: "Список ID ботов или пользователей, от которых ожидаются сообщения-запросы. Если список пуст, сообщения будут отслеживаться от любого бота или вашего юзербота.", # Updated description
                validator=loader.validators.Series(loader.validators.Integer())
            ),
        )
        self._client = None
        self._self_id = None

    async def client_ready(self, client, _):
        self._client = client
        self._self_id = (await self._client.get_me()).id

    @loader.command(ru_doc="Включить автоподтверждение")
    async def acacon(self, message: Message):
        """Включить автоматическое подтверждение."""
        self.config["enabled"] = True
        await utils.answer(message, self.strings("enabled"))

    @loader.command(ru_doc="Выключить автоподтверждение")
    async def acacoff(self, message: Message):
        """Выключить автоматическое подтверждение."""
        self.config["enabled"] = False
        await utils.answer(message, self.strings("disabled"))

    @loader.command(ru_doc="Показать статус автоподтверждения")
    async def acastatus(self, message: Message):
        """Показать текущий статус автоматического подтверждения."""
        status = "🟢 Включен" if self.config["enabled"] else "🔴 Выключен"
        delay_display = f"[{', '.join(map(str, self.config['delay']))}]" if len(self.config['delay']) > 1 else str(self.config['delay'][0])
        
        # Displaying target_bot_ids (now functions as target_sender_ids)
        target_senders_display = ", ".join(map(str, self.config["target_bot_ids"])) if self.config["target_bot_ids"] else self.strings("target_bot_ids_display")

        await utils.answer(message, self.strings("status").format(
            status,
            self.config["trigger_phrase"],
            self.config["button_text"],
            delay_display,
            target_senders_display # Updated variable name
        ))

    @loader.command(ru_doc="Показать справку по модулю автоподтверждения")
    async def acahelp(self, message: Message):
        """Показать справку по модулю AutoConfirmAdd."""
        await utils.answer(message, self.strings("help_text"))

    @loader.watcher(incoming=True, outgoing=False)
    async def watcher(self, message: Message):
        """Отслеживает входящие сообщения для автоматического подтверждения."""
        if not self.config["enabled"]:
            return

        # Пропускаем сообщения без текста или кнопок
        if not getattr(message, 'text', None) or not getattr(message, 'buttons', None):
            return

        sender = await message.get_sender()
        sender_id = getattr(sender, 'id', None)
        
        if sender_id is None:
            return # Не удалось определить отправителя

        # --- Логика фильтрации отправителей (обновлено) ---
        if self.config["target_bot_ids"]: # Если список целевых отправителей (ботов/пользователей) НЕ пуст
            if sender_id not in self.config["target_bot_ids"]:
                logger.debug(f"AutoConfirmAdd: Сообщение {message.id} от отправителя {sender_id} не в списке разрешенных ID ({self.config['target_bot_ids']}). Пропускаю.")
                return
        else: # Если список целевых отправителей пуст, реагируем только на ботов или на самого юзербота
            is_from_bot_or_self = getattr(sender, 'bot', False) or (sender_id == self._self_id)
            if not is_from_bot_or_self:
                 logger.debug(f"AutoConfirmAdd: Сообщение {message.id} не от бота и не от юзербота, и не указаны целевые отправители. Пропускаю.")
                 return
        # --- Конец логики фильтрации отправителей ---


        # Проверяем наличие фразы-триггера в тексте сообщения (регистронезависимо)
        if self.config["trigger_phrase"].lower() in message.text.lower():
            trigger_phrase = self.config["trigger_phrase"]
            button_text_to_click = self.config["button_text"]

            logger.info(self.strings("trigger_detected").format(
                phrase=trigger_phrase,
                button_text=button_text_to_click
            ))

            # Применяем случайную задержку
            delays = self.config["delay"]
            chosen_delay = random.choice(delays)
            logger.info(self.strings("delay_message").format(delay=chosen_delay))
            await asyncio.sleep(chosen_delay)

            button_found = False
            for row in message.buttons:
                for button in row:
                    try:
                        button_text = str(getattr(button, 'text', ''))
                    except Exception as e:
                        logger.warning(f"Error getting button text for message {message.id}: {e}")
                        continue
                    
                    # Проверяем точное совпадение текста кнопки
                    if button_text == button_text_to_click:
                        logger.info(f"✅ AutoConfirmAdd: Найдена кнопка '{button_text_to_click}'. Нажимаю.")
                        try:
                            await button.click()
                            logger.info(self.strings("button_clicked").format(button_text=button_text_to_click))
                            button_found = True
                            return # Выходим после успешного нажатия кнопки
                        except Exception as e:
                            logger.error(self.strings("click_error").format(button_text=button_text_to_click, error=e))
                        break # Выходим из внутреннего цикла, если кнопка найдена (даже если ошибка)
                if button_found:
                    break # Выходим из внешнего цикла, если кнопка найдена

            if not button_found:
                logger.warning(self.strings("button_not_found").format(phrase=trigger_phrase, button_text=button_text_to_click))
