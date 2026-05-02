meta developer: @TecnoPova7Neo
# meta name: AutoMafiaTournamentsGame
# meta version: 2.1.4 # Увеличена версия модуля
# 01000001010101000100111101001010010011100010000001000111010000010100110101000101
# 010000010101010001001111010010100100100101001110001000000100011101000001
# 010011010100010100100000010011010100111101000100010101010100110001000101
import logging
import asyncio
import random
import urllib.parse
import datetime # Import for timestamping
from collections import defaultdict # Import for role tracking storage
from telethon.tl.types import Message, MessageEntityMention, MessageEntityTextUrl, MessageEntityMentionName # Imports for mention parsing
from telethon import events
from telethon.utils import get_display_name # Import for getting user display name
from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class AutoMafiaTournamentsGame(loader.Module):
    """Модуль для автоматического нажатия кнопки при наборе в игру в ботах мафии, а также подтверждения линчевания и повешения, и голосования за конкретного игрока. Дополнительно: пересылка роли в мафии в указанный чат, и отслеживание ролей в чатах."""

    strings = {
        "name": "AutoMafiaTournamentsGame",
        "_cls_doc": "Модуль для автоматического нажатия кнопки при наборе в игру в ботах мафии, а также подтверждения линчевания и повешения, и голосования за конкретного игрока. Дополнительно: пересылка роли в мафии в указанный чат, и отслеживание ролей в чатах.",
        "enabled": "✅ Автовход в игру и автолинчевание включены.",
        "disabled": "❌ Автовход в игру и автолинчевание выключены.",
        "status": "<emoji document_id=5875291072225087249>📊</emoji> Статус автовхода и автолинчевания:\n"
                  "Статус: {}\n"
                  "Задержка входа (секунды): {}\n"
                  "Задержка линчевания (секунды): {}\n"
                  "Боты для отслеживания: {}\n"
                  "Разрешенные чаты: {}\n"
                  "Ключевые слова кнопок: {}\n"
                  "Режим Deep-Link: {}\n"
                  "Маркер линчевания для '👎': {}\n"
                  "Фразы-триггеры входа в игру: {}\n"
                  "Фразы-триггеры линчевания: {}\n"
                  "Фразы-триггеры повешения: {}\n"
                  "ID пользователя для линчевания игрока: {}\n"
                  "ID бота для голосования за игрока: {}\n"
                  "Фразы-триггеры голосования за игрока: {}\n"
                  "Последний ник игрока для линчевания: {}\n"
                  "\n<emoji document_id=5877485980901971030>📊</emoji> Статус пересылки роли:\n"
                  "Чат для пересылки роли: {}\n"
                  "Фразы-триггеры роли: {}\n"
                  "\n<emoji document_id=5862215160000851457>🎭</emoji> Статус отслеживания ролей:\n" # New section for role tracking
                  "Отслеживание ролей в чатах: {}\n"
                  "Ключевые слова ролей для отслеживания: {}\n"
                  "Чаты для отслеживания ролей: {}", # New string for role_tracking_allowed_chats
        "error": "❌ Ошибка при нажатии кнопки: {}",
        "no_button": "⚠️ Кнопка не найдена под сообщением",
        "help_text": """<emoji document_id=5931415565955503486>🤖</emoji> AutoMafiaTournamentsGame - Помощь

<emoji document_id=5935847413859225147>🏀</emoji> Команды:
<code>.ajgon</code> - Включить автовход в игру и автолинчевание
<code>.ajgoff</code> - Выключить автовход в игру и автолинчевание
<code>.ajgstatus</code> - Показать статус
<code>.ajghelp</code> - Эта справка
<code>.ajgtest</code> - Проверить последнее сообщение с набором в текущем чате
<code>.ajgid</code> - Показать список ID ботов для мафии
<code>.ajgtournaments</code> - Показать информацию о регистрации на турниры
<code>.ajglistroles</code> - Показать список обнаруженных ролей [НОВОЕ]

<emoji document_id=5877260593903177342>⚙</emoji> Как работает:
Ждет сообщение о наборе в игру или о голосовании (линчевание/повешение) от указанных ботов (или от любого бота, если список пуст).
Автоматически переходит по URL кнопки и отправляет /start для входа в игру.
Если бот спрашивает "Вы точно хотите линчевать..." или "Вы точно хотите повесить...", модуль автоматически нажмет кнопку.
Если в сообщении присутствует настроенный <code>lynch_target_marker</code> (по умолчанию 𝓝𝓚), модуль автоматически нажмет кнопку с эмодзи '👎'. В противном случае, если маркера нет, нажмет '👍'.
Работает только когда включен.
Дополнительно, если настроен <code>player_to_lynch_user_id</code>, модуль будет ожидать сообщение с ником игрока от этого пользователя. Как только ник получен, модуль будет искать сообщение о голосовании от <code>lynch_voting_bot_id</code>, содержащее <code>lynch_player_voting_trigger_phrases</code>, и затем автоматически нажмет кнопку с соответствующим ником игрока.
<b>Важное обновление:</b> Если сообщение от <code>player_to_lynch_user_id</code> начинается с символа <code>!</code>, этот символ будет автоматически удален из ника игрока перед использованием.
<b>Новая функция:</b> Модуль может автоматически пересылать сообщения с вашей ролью в мафии в указанный чат. Это работает, когда бот отправляет вам роль в приватном чате, и сообщение содержит одну из настроенных фраз-триггеров.
<b>Новая функция:</b> Модуль может отслеживать ключевые слова ролей в сообщениях от ботов во всех чатах и сохранять информацию о том, где и когда была упомянута роль, а также о любых упомянутых пользователях.

<emoji document_id=5843843420468024653>⭐️</emoji> Настройки:
В конфиге модуля можно изменить задержку(и) перед нажатием. Если указано несколько значений, будет выбрано случайное.
Можно указать список ID ботов, от которых ожидать сообщения о наборе.
Можно указать список ID чатов, в которых модуль будет активен. Если список пуст, модуль будет работать во всех чатах.
<b>Настройка:</b> <code>button_keywords</code> - список ключевых слов, которые должны содержаться в тексте кнопки для ее активации. Регистр не учитывается. <b>Если среди ключевых слов есть "🌚" или "🌝", активируется специальный режим обработки Deep-Link URL, при котором боту будет отправляться команда <code>/start &lt;параметр_start&gt;</code>, извлеченный из URL кнопки.</b>
<b>Настройка:</b> <code>lynch_target_marker</code> - строка-маркер, которая, если присутствует в сообщении-триггере для голосования, заставит модуль нажать кнопку '👎'. Если отсутствует или маркер не указан (пустая строка), нажимается '👍'. По умолчанию: "" (пусто).
<b>Настройка:</b> <code>game_join_trigger_phrases</code> - список фраз, которые модуль будет искать в сообщениях для активации автовхода в игру. По умолчанию: <code>[\"Ведётся набор в игру\", \"Регистрация началась!\"]</code>.
<b>Настройка:</b> <code>lynch_trigger_phrases</code> - список фраз, которые модуль будет искать в сообщениях для активации автолинчевания. По умолчанию: <code>[\"Вы точно хотите линчевать\"]</code>.
<b>Настройка:</b> <code>lynch_hang_trigger_phrases</code> - список фраз, которые модуль будет искать в сообщениях для активации автоповешения. По умолчанию: <code>[\"Вы точно хотите повесить\"]</code>.
<b>Настройка:</b> <code>player_to_lynch_user_id</code> - ID пользователя, чье сообщение будет использоваться как ник игрока для линчевания. Если <code>0</code>, то функция отключена.
<b>Настройка:</b> <code>lynch_voting_bot_id</code> - ID бота, который отправляет сообщение с кнопками для голосования за конкретного игрока. Если <code>0</code>, то функция отключена.
<b>Настройка:</b> <code>lynch_player_voting_trigger_phrases</code> - список фраз, которые модуль будет искать в сообщениях от <code>lynch_voting_bot_id</code> для активации голосования за конкретного игрока. По умолчанию: <code>[\"Пришло время искать виноватых!\", \"Кого ты хочешь повесить?\", \"Пришло время определить и наказать виновных\", \"Пришло время искать виноватых! Кого ты хочешь линчевать?\"]</code>.
<b>Новая настройка:</b> <code>role_forward_chat_id</code> - ID чата, куда будет пересылаться полученная роль в мафии. Если <code>0</code>, функция отключена.
<b>Новая настройка:</b> <code>role_trigger_phrases</code> - список фраз, которые модуль будет искать в сообщениях от бота в ЛС для определения роли. По умолчанию: <code>[\"Ваша роль:\", \"Ты - \", \"Твоя роль:\", \"Ты стал(а) \"]</code>.
<b>Новая настройка:</b> <code>track_roles_in_all_chats</code> - если <code>True</code>, модуль будет отслеживать ключевые слова ролей в сообщениях от ботов во всех активных чатах и сохранять информацию. По умолчанию: <code>False</code>.
<b>Новая настройка:</b> <code>roles_to_track_keywords</code> - список ключевых слов (названий ролей), которые модуль будет искать в сообщениях при активном <code>track_roles_in_all_chats</code>. Например: <code>[\"Мирный житель\", \"Мафия\"]</code>. Регистр не учитывается.
<b>Новая настройка:</b> <code>role_tracking_allowed_chats</code> - список ID чатов, в которых будет активно отслеживание ролей. Если список пуст, отслеживание ролей будет работать во всех чатах (где активен сам модуль).""",
        "ajgid_bots_list": """<emoji document_id=5771887475421090729>👤</emoji> Список ID ботов для мафии:

🤵🏻 True Mafia <code>468253535</code>
True Mafia Black <code>761250017</code>
True Tales (Былины) <code>606933972</code>
Mafia Baku <code>1050428643</code>
Mafia Baku Black <code>1044037207</code>
Mafia Baku Black 2 <code>724330306</code>
Mafioso <code>5424831786</code>
Mafioso Platinum <code>7199004377</code>
Mafia Combat Premium <code>1634167847</code>""",
        "ajgtournaments_text": """Регистрация для турнирных команд

🔴 или 🔵
Для Баку

🔵 или 🟠
Для Мафиосо

🌚 или 🌝

Для Комбата
Примечание, в Мафиосо платиум можно менять эмодзи которые стоят на регистрации, поэтому смотрите на регистрации какие там эмодзи и потом нужные ставите в .cfg 

Настроить можно в

.cfg AutoMafiaTournamentsGame button_keywords""",
        "lynch_triggered_positive": "<emoji document_id=5935968647901089910>🔫</emoji> Обнаружен запрос на линчевание/повешение. Нажимаю '👍'.",
        "lynch_button_not_found_positive": "⚠️ Запрос на линчевание/повешение обнаружен, но кнопка '👍' не найдена.",
        "lynch_triggered_negative": "<emoji document_id=5935968647901089910>🔫</emoji> Обнаружен запрос на линчевание/повешение с маркером '{marker}'. Нажимаю '👎'.",
        "lynch_button_not_found_negative": "⚠️ Запрос на линчевание/повешение с маркером '{marker}' обнаружен, но кнопка '👎' не найдена.",
        "player_nickname_set": "<emoji document_id=5839380580080293813>🖋</emoji> Установлен ник игрока для линчевания: <code>{nickname}</code>. Ожидаю голосования.",
        "player_lynch_triggered": "<emoji document_id=5935968647901089910>🔫</emoji> Обнаружен запрос на голосование за игрока. Ищу кнопку с ником <code>{nickname}</code>.",
        "player_lynch_button_found": "✅ AutoMafiaTournamentsGame: Найдена кнопка с ником <code>{nickname}</code>. Нажимаю.",
        "player_lynch_button_not_found": "⚠️ AutoMafiaTournamentsGame: Запрос на голосование за игрока найден, но кнопка с ником <code>{nickname}</code> не найдена.",
        "player_lynch_success": "🎉 AutoMafiaTournamentsGame: Успешно нажата кнопка с ником <code>{nickname}</code>. Ник сброшен.",
        "player_lynch_error": "❌ AutoMafiaTournamentsGame: Ошибка при нажатии кнопки с ником <code>{nickname}</code>: {error}",
        "ajgtest_player_nickname_would_be_set": "🔔 Сообщение ID <code>{msg_id}</code> от <code>{sender_id}</code> *установило бы* ник: <code>{nickname}</code>.",
        "ajgtest_player_nickname_not_set_yet": "ℹ️ Ник игрока для голосования не установлен в конфиге или не найден в последних 500 сообщениях.",
        "ajgtest_player_nickname_used": "ℹ️ Для последующих тестов используется ник: <code>{nickname}</code>.",
        "ajgtest_player_lynch_disabled": "ℹ️ ID пользователя для линчевания игрока не установлен в конфиге. Эта часть теста неактивна.",
        "ajgtest_no_matches": "❌ Сообщения с набором, запросом на линчевание или голосование за игрока от настроенных ботов/пользователя не найдено в текущем чате ID <code>{chat_id}</code>\n📊 Проверено сообщений: {count}",
        "ajgtest_error": "❌ Ошибка: <code>{error}</code>",
        "role_forward_chat_id_display": "Отключено (0)",
        "role_forward_trigger_phrases_display": "(пусто)",
        "role_forward_success": "🎉 AutoMafiaTournamentsGame: Роль успешно переслана в чат <code>{chat_id}</code>.",
        "role_forward_error": "❌ AutoMafiaTournamentsGame: Ошибка при пересылке роли в чат <code>{chat_id}</code>: {error}",
        
        # New strings for role tracking
        "ajglistroles_title": "<emoji document_id=5862215160000851457>🎭</emoji> Обнаруженные роли:",
        "ajglistroles_empty": "ℹ️ Пока не обнаружено ни одной роли, соответствующей настроенным ключевым словам.",
        "ajglistroles_role_entry": "<b>{}</b>:\n",
        "ajglistroles_info_entry": "  • <code>{}</code> (Чат: <code>{}</code>, Сообщение: <a href='https://t.me/c/{}/{}'>{}</a>, Упоминания: {})\n",
        "ajglistroles_mentions_none": "Нет",
        "ajglistroles_status_enabled": "🟢 Включено",
        "ajglistroles_status_disabled": "🔴 Выключено",
        "ajgtest_roles_tracking_enabled": "<emoji document_id=5843843420468024653>⭐️</emoji> Отслеживание ролей включено. Ищу ключевые слова: {}. Чаты для отслеживания: {}.\n", # Updated string
        "ajgtest_roles_tracking_match": "✅ Сообщение ID <code>{msg_id}</code> от <code>{sender_id}</code> *содержало бы* отслеживаемые роли: {}.\n"
                                        "  💬 Текст: <code>{}</code>\n"
                                        "  👤 Упоминания: {}\n",
        "ajgtest_roles_no_matches": "ℹ️ Сообщений с отслеживаемыми ключевыми словами ролей от ботов не найдено.",
        "ajgtest_roles_disabled_or_not_configured": "ℹ️ Отслеживание ролей, ключевые слова ролей или чаты для отслеживания не настроены.", # Updated string
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "enabled",
                False,
                lambda: "Включен ли автовход в игру и автолинчевание",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "delays",
                [0.5],
                lambda: "Список задержек перед нажатием кнопки входа в игру (секунды). Если указано несколько, будет выбрано случайное.",
                validator=loader.validators.Series(loader.validators.Float(minimum=0.1, maximum=10.0))
            ),
            loader.ConfigValue(
                "lynch_delay",
                [0.5],
                lambda: "Список задержек перед нажатием кнопки '👍' или '👎' при линчевании (секунды). Если указано несколько, будет выбрано случайное.",
                validator=loader.validators.Series(loader.validators.Float(minimum=0.1, maximum=10.0))
            ),
            loader.ConfigValue(
                "bot_ids",
                [],
                lambda: "Список ID ботов, от которых ожидается сообщение о наборе в игру или линчевании. Если список пуст, сообщения будут отслеживаться от любого бота.",
                validator=loader.validators.Series(loader.validators.Integer())
            ),
            loader.ConfigValue(
                "allowed_chats",
                [],
                lambda: "Список ID чатов, в которых модуль будет активен. Если список пуст, модуль будет работать во всех чатах.",
                validator=loader.validators.Series(loader.validators.Integer())
            ),
            loader.ConfigValue(
                "button_keywords",
                ["присоединиться", "играть", "🙋", "🎮", "✅", "🌚"],
                lambda: "Список ключевых слов в тексте кнопки для активации автовхода (регистронезависимо). Если среди ключевых слов есть '🌚' или '🌝', активируется специальный режим обработки Deep-Link URL.",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                "lynch_target_marker",
                "", 
                lambda: "Маркер (строка), который, если присутствует в сообщении-триггере для голосования, заставит модуль нажать кнопку '👎'. Если отсутствует или маркер не указан (пустая строка), нажимается '👍'.",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "game_join_trigger_phrases",
                ["Ведётся набор в игру", "Регистрация началась!"],
                lambda: "Список фраз, которые указывают на сообщение о наборе в игру.",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                "lynch_trigger_phrases",
                ["Вы точно хотите линчевать"],
                lambda: "Список фраз, которые указывают на сообщение для голосования за линчевание (без маркера).",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                "lynch_hang_trigger_phrases",
                ["Вы точно хотите повесить"],
                lambda: "Список фраз, которые указывают на сообщение для голосования за повешение игрока (без маркера).",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                "player_to_lynch_user_id",
                0,
                lambda: "ID пользователя, чье сообщение будет использоваться как ник игрока для линчевания. Если 0, то функция отключена.",
                validator=loader.validators.Integer(minimum=0)
            ),
            loader.ConfigValue(
                "lynch_voting_bot_id",
                0,
                lambda: "ID бота, который отправляет сообщение с кнопками для голосования за конкретного игрока. Если 0, то функция отключена.",
                validator=loader.validators.Integer(minimum=0)
            ),
            loader.ConfigValue(
                "lynch_player_voting_trigger_phrases",
                ["Пришло время искать виноватых!", "Кого ты хочешь повесить?", "Пришло время определить и наказать виновных", "Пришло время искать виноватых! Кого ты хочешь линчевать?"],
                lambda: "Список фраз, которые модуль будет искать в сообщениях от lynch_voting_bot_id для активации голосования за конкретного игрока.",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                "role_forward_chat_id",
                0,
                lambda: "ID чата, куда будет пересылаться полученная роль в мафии. Если 0, функция отключена.",
                validator=loader.validators.Integer(minimum=0)
            ),
            loader.ConfigValue(
                "role_trigger_phrases",
                ["Ваша роль:", "Ты - ", "Твоя роль:", "Ты стал(а) "],
                lambda: "Список фраз, которые модуль будет искать в сообщениях от бота в ЛС для определения роли.",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue( # New config
                "track_roles_in_all_chats",
                False,
                lambda: "Если True, модуль будет отслеживать ключевые слова ролей в сообщениях от ботов во всех активных чатах и сохранять информацию.",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue( # New config
                "roles_to_track_keywords",
                [],
                lambda: "Список ключевых слов (названий ролей), которые модуль будет искать в сообщениях при активном track_roles_in_all_chats. Например: [\"Мирный житель\", \"Мафия\"]. Регистр не учитывается.",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue( # NEW config for specific role tracking chats
                "role_tracking_allowed_chats",
                [],
                lambda: "Список ID чатов, в которых будет активно отслеживание ролей. Если список пуст, отслеживание ролей будет работать во всех чатах (где активен сам модуль).",
                validator=loader.validators.Series(loader.validators.Integer())
            ),
        )

        self.last_processed_msg = None
        self._player_nickname_to_lynch = None # Temporary storage for player nickname
        self._detected_roles_info = defaultdict(list) # Stores detected roles: role_keyword (str) -> list of dicts {timestamp, chat_id, message_id, mentions, text_preview}

    async def client_ready(self, client, _):
        self._client = client

    @loader.command(ru_doc="Включить автовход в игру и автолинчевание")
    async def ajgon(self, message: Message):
        """Включить автовход в игру и автолинчевание"""
        self.config["enabled"] = True
        await utils.answer(message, self.strings("enabled"))

    @loader.command(ru_doc="Выключить автовход в игру и автолинчевание")
    async def ajgoff(self, message: Message):
        """Выключить автовход в игру и автолинчевание"""
        self.config["enabled"] = False
        self.last_processed_msg = None 
        self._player_nickname_to_lynch = None # Clear nickname on disable
        await utils.answer(message, self.strings("disabled"))

    @loader.command(ru_doc="Показать статус автовхода и автолинчевания")
    async def ajgstatus(self, message: Message):
        """Показать статус автовхода и автолинчевания"""
        status = "🟢 Включен" if self.config["enabled"] else "🔴 Выключен"
        
        delays = self.config["delays"]
        delay_display = f"[{', '.join(map(str, delays))}]" if len(delays) > 1 else str(delays[0])

        lynch_delays = self.config["lynch_delay"]
        lynch_delay_display = f"[{', '.join(map(str, lynch_delays))}]" if len(lynch_delays) > 1 else str(lynch_delays[0])

        bot_ids_display = ", ".join(map(str, self.config["bot_ids"])) if self.config["bot_ids"] else "Не указаны (любой бот)"

        allowed_chats_display = ", ".join(map(str, self.config["allowed_chats"])) if self.config["allowed_chats"] else "Все чаты"

        configured_button_keywords_lower = [kw.lower() for kw in self.config["button_keywords"]]
        deep_link_mode_active = '🌚' in configured_button_keywords_lower or '🌝' in configured_button_keywords_lower

        button_keywords_display = ", ".join(self.config["button_keywords"])
        if not button_keywords_display:
            button_keywords_display = "(пусто)"

        deep_link_status_display = "🟢 Активен (включен '🌚' или '🌝' в ключевых словах)" if deep_link_mode_active else "🔴 Неактивен (нет '🌚' или '🌝' в ключевых словах)"

        lynch_target_marker_display = self.config["lynch_target_marker"] if self.config["lynch_target_marker"] else "(пусто)"

        game_join_trigger_phrases_display = ", ".join(self.config["game_join_trigger_phrases"]) if self.config["game_join_trigger_phrases"] else "(пусто)"
        lynch_trigger_phrases_display = ", ".join(self.config["lynch_trigger_phrases"]) if self.config["lynch_trigger_phrases"] else "(пусто)"
        lynch_hang_trigger_phrases_display = ", ".join(self.config["lynch_hang_trigger_phrases"]) if self.config["lynch_hang_trigger_phrases"] else "(пусто)"
        
        # New configs for player-specific lynching
        player_to_lynch_user_id_display = str(self.config["player_to_lynch_user_id"]) if self.config["player_to_lynch_user_id"] else "Отключено (0)"
        lynch_voting_bot_id_display = str(self.config["lynch_voting_bot_id"]) if self.config["lynch_voting_bot_id"] else "Отключено (0)"
        lynch_player_voting_trigger_phrases_display = ", ".join(self.config["lynch_player_voting_trigger_phrases"]) if self.config["lynch_player_voting_trigger_phrases"] else "(пусто)"
        current_player_nickname_display = self._player_nickname_to_lynch if self._player_nickname_to_lynch else "(нет)"

        # New configs for role forwarding
        role_forward_chat_id_display = str(self.config["role_forward_chat_id"]) if self.config["role_forward_chat_id"] else self.strings("role_forward_chat_id_display")
        role_trigger_phrases_display = ", ".join(self.config["role_trigger_phrases"]) if self.config["role_trigger_phrases"] else self.strings("role_forward_trigger_phrases_display")

        # New configs for role tracking
        track_roles_in_all_chats_status_display = self.strings("ajglistroles_status_enabled") if self.config["track_roles_in_all_chats"] else self.strings("ajglistroles_status_disabled")
        roles_to_track_keywords_display_value = ", ".join(self.config["roles_to_track_keywords"]) if self.config["roles_to_track_keywords"] else self.strings("role_forward_trigger_phrases_display")
        role_tracking_allowed_chats_display_value = ", ".join(map(str, self.config["role_tracking_allowed_chats"])) if self.config["role_tracking_allowed_chats"] else "Все чаты (где активен модуль)" # NEW

        await utils.answer(message, self.strings("status").format(
            status, 
            delay_display, 
            lynch_delay_display,
            bot_ids_display, 
            allowed_chats_display, 
            button_keywords_display, 
            deep_link_status_display,
            lynch_target_marker_display,
            game_join_trigger_phrases_display,
            lynch_trigger_phrases_display,
            lynch_hang_trigger_phrases_display,
            player_to_lynch_user_id_display,
            lynch_voting_bot_id_display,
            lynch_player_voting_trigger_phrases_display,
            current_player_nickname_display,
            role_forward_chat_id_display,
            role_trigger_phrases_display,
            track_roles_in_all_chats_status_display, 
            roles_to_track_keywords_display_value,
            role_tracking_allowed_chats_display_value # NEW param
        ))

    @loader.command(ru_doc="Показать справку")
    async def ajghelp(self, message: Message):
        """Показать справку"""
        await utils.answer(message, self.strings("help_text"))

    @loader.command(ru_doc="Проверить последнее сообщение с набором")
    async def ajgtest(self, message: Message):
        """Проверить последнее сообщение с набором в текущем чате"""
        current_chat_id = message.chat_id
        configured_bot_ids = self.config["bot_ids"]
        configured_button_keywords_lower = [kw.lower() for kw in self.config["button_keywords"]]
        keywords_to_check_for_test = configured_button_keywords_lower 
        deep_link_mode_active = '🌚' in configured_button_keywords_lower or '🌝' in configured_button_keywords_lower
        deep_link_status_test_display = "🟢 Активен" if deep_link_mode_active else "🔴 Неактивен"

        game_join_phrases_for_test = self.config["game_join_trigger_phrases"]
        lynch_phrases_for_test = self.config["lynch_trigger_phrases"] + self.config["lynch_hang_trigger_phrases"]
        player_lynch_phrases_for_test = self.config["lynch_player_voting_trigger_phrases"]
        
        all_trigger_phrases_for_test = game_join_phrases_for_test + lynch_phrases_for_test + player_lynch_phrases_for_test

        trigger_phrases_str = ", ".join(all_trigger_phrases_for_test) if all_trigger_phrases_for_test else "Не указаны"

        await utils.answer(message, f"<emoji document_id=5874960879434338403>🔎</emoji> Ищу сообщения, содержащие одну из фраз: \"{trigger_phrases_str}\" (регистронезависимо) в последних 500 сообщениях в текущем чате (ID: <code>{current_chat_id}</code>) от ботов/пользователя.\nРежим Deep-Link: {deep_link_status_test_display}...")

        try:
            results = []
            count = 0
            
            temp_player_nickname_for_test = None 
            
            # --- First pass: find the most recent nickname setter message ---
            if self.config["player_to_lynch_user_id"] != 0:
                async for msg_check_nickname in self._client.iter_messages(current_chat_id, limit=500):
                    sender_check_nickname = await msg_check_nickname.get_sender()
                    sender_id_check_nickname = getattr(sender_check_nickname, 'id', None)
                    if sender_id_check_nickname == self.config["player_to_lynch_user_id"] and getattr(msg_check_nickname, 'text', None):
                        nickname_raw = msg_check_nickname.text.strip()
                        if nickname_raw.startswith('!'):
                            temp_player_nickname_for_test = nickname_raw[1:].strip()
                        else:
                            temp_player_nickname_for_test = nickname_raw
                        results.append(self.strings("ajgtest_player_nickname_would_be_set").format(
                            msg_id=msg_check_nickname.id, 
                            sender_id=sender_id_check_nickname, 
                            nickname=temp_player_nickname_for_test
                        ))
                        break # Found the most recent one, stop looking
                if temp_player_nickname_for_test:
                    results.append(self.strings("ajgtest_player_nickname_used").format(nickname=temp_player_nickname_for_test))
                else:
                    results.append(self.strings("ajgtest_player_nickname_not_set_yet"))
            else:
                results.append(self.strings("ajgtest_player_lynch_disabled"))


            # --- Second pass: process actual bot messages and apply logic ---
            async for msg in self._client.iter_messages(current_chat_id, limit=500):
                count += 1

                if not getattr(msg, 'text', None):
                    continue

                sender = await msg.get_sender()
                sender_id = getattr(sender, 'id', None)

                # This filter should only apply if the sender is a bot
                if not getattr(sender, 'bot', False):
                    continue

                # Filter messages not from allowed bots for general triggers
                # Allow messages from `lynch_voting_bot_id` even if it's not in `bot_ids` for specific player voting
                if configured_bot_ids and sender_id not in configured_bot_ids and sender_id != self.config["lynch_voting_bot_id"]:
                    continue
                
                msg_text_lower = msg.text.lower() 
                
                # Check for trigger phrases from bots
                is_game_join_test_message = any(phrase.lower() in msg_text_lower for phrase in game_join_phrases_for_test)
                is_general_lynch_test_message = any(phrase.lower() in msg_text_lower for phrase in lynch_phrases_for_test)
                is_player_voting_test_message = any(phrase.lower() in msg_text_lower for phrase in player_lynch_phrases_for_test)

                if is_game_join_test_message or is_general_lynch_test_message or is_player_voting_test_message:
                    info_msg = f"✅ Найдено сообщение ID <code>{msg.id}</code> от <code>{sender_id if sender_id is not None else 'Неизвестно'}</code>:\n"
                    text_preview = msg.text[:100] + "..." if len(msg.text) > 100 else msg.text
                    info_msg += f"💬 Текст: <code>{text_preview}</code>\n"

                    if getattr(msg, 'buttons', None):
                        info_msg += "🔘 Есть кнопки: Да\n"
                        info_msg += "Список кнопок:\n"
                        button_matched_in_test = False
                        
                        # Player-specific lynching check (highest priority in test)
                        if (is_player_voting_test_message and 
                            sender_id == self.config["lynch_voting_bot_id"] and 
                            self.config["lynch_voting_bot_id"] != 0):
                            
                            if temp_player_nickname_for_test:
                                info_msg += f"  <emoji document_id=5935968647901089910>🔫</emoji> (Режим голосования за игрока: ищу ник <code>{temp_player_nickname_for_test}</code>)\n"
                                for row_idx, row in enumerate(msg.buttons):
                                    for btn_idx, btn in enumerate(row):
                                        btn_text = str(getattr(btn, 'text', f'Кнопка {btn_idx}'))
                                        if btn_text.lower() == temp_player_nickname_for_test.lower():
                                            info_msg += f"  • <code>{btn_text}</code> (✅ ПОДХОДИТ! Действие: *была бы* нажата кнопка с ником <code>{temp_player_nickname_for_test}</code>)\n"
                                            button_matched_in_test = True
                                        else:
                                            info_msg += f"  • <code>{btn_text}</code>\n"
                                if not button_matched_in_test:
                                    info_msg += f"\n⚠️ Кнопка с ником <code>{temp_player_nickname_for_test}</code> не найдена.\n"
                            else:
                                info_msg += self.strings("ajgtest_player_nickname_not_set_yet") + "\n"

                        # General lynch/hang messages
                        elif is_general_lynch_test_message:
                            lynch_marker = self.config["lynch_target_marker"]
                            target_emoji = "👎" if lynch_marker and lynch_marker in msg.text else "👍"
                            info_msg += f"  <emoji document_id=5935968647901089910>🔫</emoji> (Режим линчевания/повешения: ищу '{target_emoji}')\n"
                            for row_idx, row in enumerate(msg.buttons):
                                for btn_idx, btn in enumerate(row):
                                    btn_text = str(getattr(btn, 'text', f'Кнопка {btn_idx}'))
                                    if target_emoji in btn_text:
                                        info_msg += f"  • <code>{btn_text}</code> (✅ ПОДХОДИТ! Действие: *была бы* нажата '{target_emoji}')\n"
                                        button_matched_in_test = True
                                    else:
                                        info_msg += f"  • <code>{btn_text}</code>\n"
                            if not button_matched_in_test:
                                info_msg += f"\n⚠️ Кнопка '{target_emoji}' не найдена.\n"
                        # Game join messages
                        elif is_game_join_test_message:
                            info_msg += "  <emoji document_id=5935847413859225147>🏀</emoji> (Режим входа в игру: ищу ключевые слова)\n"
                            for row_idx, row in enumerate(msg.buttons):
                                for btn_idx, btn in enumerate(row):
                                    try:
                                        btn_text = str(getattr(btn, 'text', f'Кнопка {btn_idx}'))
                                        btn_url = getattr(btn, 'url', None)

                                        match_indicator = ""
                                        if any(keyword in btn_text.lower() for keyword in keywords_to_check_for_test):
                                            match_indicator = " (✅ ПОДХОДИТ!)"
                                            button_matched_in_test = True

                                        info_msg += f"  • <code>{btn_text}</code>{match_indicator}"
                                        if btn_url:
                                            parsed_url = urllib.parse.urlparse(btn_url)
                                            query_params = urllib.parse.parse_qs(parsed_url.query)
                                            start_param = query_params.get('start', [None])[0]

                                            bot_username = None
                                            if parsed_url.hostname in ['t.me', 'telegram.me'] and parsed_url.path:
                                                path_parts = parsed_url.path.lstrip('/').split('/')
                                                if path_parts and path_parts[0]:
                                                    bot_username = path_parts[0]
                                            elif parsed_url.scheme == 'tg' and parsed_url.netloc == 'resolve':
                                                query_params_tg = urllib.parse.parse_qs(parsed_url.query)
                                                bot_username = query_params_tg.get('domain', [None])[0]

                                            url_display = f" (URL: <code>{btn_url[:50]}...</code>)" if len(btn_url) > 50 else f" (URL: <code>{btn_url}</code>)"

                                            if start_param and deep_link_mode_active and bot_username:
                                                info_msg += f"{url_display} (Действие Deep-Link: *была бы* отправлена <code>/start {start_param}</code> боту @{bot_username})"
                                            elif start_param and not deep_link_mode_active and bot_username:
                                                info_msg += f"{url_display} (Действие Deep-Link: <b>не</b> была бы отправлена, режим Deep-Link неактивен)"
                                            else:
                                                info_msg += url_display
                                        else:
                                            info_msg += " (URL: Нет, это Callback кнопка. *Была бы* нажата.)"
                                        info_msg += "\n"
                                    except Exception as btn_ex:
                                        logger.warning(f"Error processing button in ajgtest: {btn_ex}")
                                        info_msg += f"  • Кнопка {btn_idx} (не удалось получить текст/URL: {btn_ex})\n"
                            if not button_matched_in_test and keywords_to_check_for_test:
                                info_msg += "\n⚠️ Ни одна кнопка не соответствует настроенным ключевым словам.\n"
                            elif not keywords_to_check_for_test:
                                info_msg += "\n⚠️ Список ключевых слов для кнопок пуст. Ни одна кнопка не будет активирована.\n"
                    else:
                        info_msg += "🔘 Есть кнопки: Нет\n"
                    
                    results.append(info_msg) # Add this message's info to results

            # --- Test role tracking ---
            if self.config["track_roles_in_all_chats"] and self.config["roles_to_track_keywords"]:
                role_keywords_for_test = self.config["roles_to_track_keywords"]
                role_keywords_str = ", ".join(role_keywords_for_test) if role_keywords_for_test else "Не указаны"
                
                role_tracking_allowed_chats_for_test = self.config["role_tracking_allowed_chats"]
                role_tracking_chats_str = ", ".join(map(str, role_tracking_allowed_chats_for_test)) if role_tracking_allowed_chats_for_test else "Все чаты"

                results.append(f"\n--- Тест отслеживания ролей ---\n" + self.strings("ajgtest_roles_tracking_enabled").format(role_keywords_str, role_tracking_chats_str))

                found_role_test_matches = False
                
                # Check if current chat is allowed for role tracking
                is_current_chat_allowed_for_role_tracking = not role_tracking_allowed_chats_for_test or current_chat_id in role_tracking_allowed_chats_for_test

                # This block is inside the main 'async for msg' loop, so 'msg' is the current message.
                msg_text_test_lower = msg.text.lower()
                matched_roles_in_test_msg = []
                for role_kw_test in role_keywords_for_test:
                    if role_kw_test.lower() in msg_text_test_lower:
                        matched_roles_in_test_msg.append(role_kw_test)

                if matched_roles_in_test_msg and getattr(sender, 'bot', False) and is_current_chat_allowed_for_role_tracking: # Only consider bot messages for roles AND if chat is allowed
                    found_role_test_matches = True
                    test_mentions = []
                    for entity, entity_text in msg.iter_entities():
                        if isinstance(entity, (MessageEntityMention, MessageEntityMentionName)):
                            try:
                                user_test = await self._client.get_entity(entity.user_id)
                                if user_test:
                                    test_mentions.append(get_display_name(user_test))
                            except Exception as e:
                                logger.debug(f"Error resolving mentioned user in ajgtest (roles): {e}")
                    
                    # If it's a private message and a role trigger, and no other mentions, assume it's for the current user.
                    if msg.is_private and not test_mentions and any(p.lower() in msg_text_test_lower for p in self.config["role_trigger_phrases"]):
                        self_user_test = await self._client.get_me()
                        if self_user_test:
                            test_mentions.append(get_display_name(self_user_test) + " (self)")

                    text_preview_for_test = msg.text[:100] + ("..." if len(msg.text) > 100 else "")
                    results.append(self.strings("ajgtest_roles_tracking_match").format(
                        msg_id=msg.id, 
                        sender_id=getattr(sender, 'id', 'N/A'), 
                        matched_roles=", ".join(matched_roles_in_test_msg),
                        text_preview=text_preview_for_test,
                        mentions=", ".join(test_mentions) if test_mentions else self.strings("ajglistroles_mentions_none")
                    ))
                elif self.config["track_roles_in_all_chats"] and self.config["roles_to_track_keywords"] and not found_role_test_matches and count == 500: # Only if at the end of loop and no matches
                    # Only append 'no matches' if it actually *should* have been looking in this chat
                    if is_current_chat_allowed_for_role_tracking:
                        results.append(self.strings("ajgtest_roles_no_matches"))
                    else:
                        results.append(f"ℹ️ Отслеживание ролей активно, но текущий чат (ID: <code>{current_chat_id}</code>) не находится в списке разрешенных чатов для отслеживания ролей: {role_tracking_chats_str}.")
            elif not self.config["track_roles_in_all_chats"] or not self.config["roles_to_track_keywords"] or not self.config["role_tracking_allowed_chats"]: # Combined condition
                if count == 500: # Only display if the loop has finished and it's still not enabled/configured
                     results.append(self.strings("ajgtest_roles_disabled_or_not_configured"))


            # End of main 'async for msg' loop
            if not results: # If no matches for any triggers
                await utils.answer(message, self.strings("ajgtest_no_matches").format(chat_id=current_chat_id, count=count))
            else:
                final_output = "\n---\n".join(results)
                final_output += f"\n\n📊 Проверено сообщений: {count}"
                await utils.answer(message, final_output)


        except Exception as e:
            logger.exception(f"Error in ajgtest: {e}")
            error_text = str(e) if str(e) else "Неизвестная ошибка"
            await utils.answer(message, self.strings("ajgtest_error").format(error=error_text))


    @loader.command(ru_doc="Показать список ID ботов для мафии")
    async def ajgid(self, message: Message):
        """Показать список ID ботов для мафии"""
        await utils.answer(message, self.strings("ajgid_bots_list"))

    @loader.command(ru_doc="Показать информацию о регистрации на турниры")
    async def ajgtournaments(self, message: Message):
        """Показать информацию о регистрации на турниры"""
        await utils.answer(message, self.strings("ajgtournaments_text"))
    
    @loader.command(ru_doc="Показать список обнаруженных ролей")
    async def ajglistroles(self, message: Message):
        """Показать список обнаруженных ролей"""
        if not self._detected_roles_info:
            await utils.answer(message, self.strings("ajglistroles_empty"))
            return

        output_parts = [self.strings("ajglistroles_title")]
        for role_kw, detections in self._detected_roles_info.items():
            output_parts.append(self.strings("ajglistroles_role_entry").format(role_kw))
            for entry in detections:
                chat_id_for_link = str(entry['chat_id']).replace('-100', '') # For public channels/groups, remove -100 prefix for t.me/c/ link
                mentions_str = ", ".join(entry['mentions']) if entry['mentions'] else self.strings("ajglistroles_mentions_none")
                output_parts.append(self.strings("ajglistroles_info_entry").format(
                    entry['text_preview'],
                    entry['chat_id'],
                    chat_id_for_link,
                    entry['message_id'],
                    entry['timestamp'],
                    mentions_str
                ))
        await utils.answer(message, "\n".join(output_parts))


    @loader.watcher(incoming=True, outgoing=False)
    async def watcher(self, message: Message):
        """Обработчик всех входящих сообщений для автовхода в игру, автолинчевания, пересылки роли и отслеживания ролей."""
        try:
            if not self.config["enabled"]:
                logger.debug("AutoMafiaTournamentsGame: Модуль выключен. Пропускаю сообщение.")
                return

            if not getattr(message, 'text', None):
                logger.debug(f"AutoMafiaTournamentsGame: Сообщение {message.id} не содержит текста. Пропускаю.")
                return
            
            sender = await message.get_sender()
            sender_id = getattr(sender, 'id', None)
            if sender_id is None:
                logger.warning(f"AutoMafiaTournamentsGame: Не удалось получить ID отправителя для сообщения {message.id}. Пропускаю.")
                return

            # Проверяем, было ли это сообщение уже обработано.
            # Это помогает избежать повторной обработки одного и того же события.
            if self.last_processed_msg == message.id:
                logger.debug(f"AutoMafiaTournamentsGame: Сообщение {message.id} уже было обработано. Пропускаю.")
                return
            
            # Устанавливаем ID текущего сообщения как последнее обработанное
            self.last_processed_msg = message.id 

            allowed_chats = self.config["allowed_chats"]
            if allowed_chats and message.chat_id not in allowed_chats:
                logger.debug(f"AutoMafiaTournamentsGame: Чат {message.chat_id} не в списке разрешенных чатов ({allowed_chats}). Пропускаю сообщение {message.id}.")
                return

            msg_text = message.text
            msg_text_lower = msg_text.lower() 

            # --- Обработка сообщения, устанавливающего ник игрока ---
            player_to_lynch_user_id = self.config["player_to_lynch_user_id"]
            if player_to_lynch_user_id != 0 and sender_id == player_to_lynch_user_id:
                nickname = message.text.strip()
                if nickname.startswith('!'):
                    nickname = nickname[1:].strip() # Удаляем '!' если присутствует
                
                self._player_nickname_to_lynch = nickname
                logger.info(self.strings("player_nickname_set").format(nickname=self._player_nickname_to_lynch))
                # Если сообщение от пользователя, устанавливающего ник, оно не должно быть от бота.
                # Поэтому дальнейшая обработка как сообщения от бота не требуется.
                return 
            
            # --- Обработка отслеживания ролей (НОВОЕ) ---
            if (self.config["track_roles_in_all_chats"] and 
                self.config["roles_to_track_keywords"] and 
                getattr(sender, 'bot', False)):
                
                # Check if current chat is allowed for role tracking
                role_tracking_allowed_chats = self.config["role_tracking_allowed_chats"]
                if role_tracking_allowed_chats and message.chat_id not in role_tracking_allowed_chats:
                    logger.debug(f"AutoMafiaTournamentsGame: Чат {message.chat_id} не в списке разрешенных чатов для отслеживания ролей. Пропускаю отслеживание ролей для сообщения {message.id}.")
                else:
                    matched_roles = []
                    for role_kw in self.config["roles_to_track_keywords"]:
                        if role_kw.lower() in msg_text_lower:
                            matched_roles.append(role_kw)

                    if matched_roles:
                        mentions = []
                        for entity, entity_text in message.iter_entities():
                            if isinstance(entity, (MessageEntityMention, MessageEntityMentionName)):
                                try:
                                    user = await self._client.get_entity(entity.user_id)
                                    if user:
                                        mentions.append(get_display_name(user))
                                except Exception as e:
                                    logger.debug(f"Error resolving mentioned user from entity in watcher (role tracking): {e}")
                        
                        # If it's a private message and a role trigger, and no other mentions, assume it's for the current user.
                        if message.is_private and not mentions and any(p.lower() in msg_text_lower for p in self.config["role_trigger_phrases"]):
                            self_user = await self._client.get_me()
                            if self_user:
                                mentions.append(get_display_name(self_user) + " (self)")

                        for role_kw_matched in matched_roles:
                            self._detected_roles_info[role_kw_matched].append({
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "chat_id": message.chat_id,
                                "message_id": message.id,
                                "mentions": mentions, # List of names/display names
                                "text_preview": msg_text[:100] + ("..." if len(msg_text) > 100 else "")
                            })
                            logger.info(f"Detected role keyword '{role_kw_matched}' in message {message.id} (chat {message.chat_id}). Mentions: {mentions}")
                    
                # Role tracking is passive and doesn't stop further processing for game actions.

            # --- Обработка пересылки роли ---
            role_forward_chat_id = self.config["role_forward_chat_id"]
            role_trigger_phrases = self.config["role_trigger_phrases"]

            if (role_forward_chat_id != 0 and
                    message.is_private and
                    getattr(sender, 'bot', False) and # Сообщения о роли приходят от ботов в приватных чатах
                    any(phrase.lower() in msg_text_lower for phrase in role_trigger_phrases)):
                try:
                    await self._client.forward_messages(
                        entity=role_forward_chat_id,
                        messages=message,
                        from_peer=message.chat_id
                    )
                    logger.info(self.strings("role_forward_success").format(chat_id=role_forward_chat_id))
                except Exception as e:
                    logger.error(self.strings("role_forward_error").format(chat_id=role_forward_chat_id, error=e))
                # This message is a private role, it might also contain game-join buttons for other games.
                # So we continue processing, do not 'return'.

            # Убедимся, что сообщение от бота для последующей обработки триггеров игры/линчевания
            if not getattr(sender, 'bot', False):
                logger.debug(f"AutoMafiaTournamentsGame: Сообщение {message.id} не от бота. Пропускаю дальнейшую обработку игровых триггеров.")
                return

            configured_bot_ids = self.config["bot_ids"] 
            lynch_voting_bot_id = self.config["lynch_voting_bot_id"]

            # Фильтруем сообщения не от разрешенных ботов для общих триггеров
            # Разрешаем сообщения от `lynch_voting_bot_id`, даже если его нет в `bot_ids`, для специфического голосования за игрока
            if configured_bot_ids and sender_id not in configured_bot_ids and sender_id != lynch_voting_bot_id:
                logger.debug(f"AutoMafiaTournamentsGame: Сообщение {message.id} от бота {sender_id}, но его ID не в списке разрешенных ботов для общих триггеров. Пропускаю.")
                return
            
            # --- Логика линчевания конкретного игрока (наивысший приоритет для голосования) ---
            if (lynch_voting_bot_id != 0 and sender_id == lynch_voting_bot_id and 
                self._player_nickname_to_lynch and 
                any(phrase.lower() in msg_text_lower for phrase in self.config["lynch_player_voting_trigger_phrases"])):
                
                if not getattr(message, 'buttons', None):
                    logger.warning(f"⚠️ AutoMafiaTournamentsGame: Запрос на голосование за игрока найден (msg_id: {message.id}), но кнопок нет. Пропускаю.")
                    self._player_nickname_to_lynch = None # Очищаем ник, так как голосование не может быть выполнено
                    return

                lynch_delays = self.config["lynch_delay"]
                chosen_lynch_delay = random.choice(lynch_delays)

                logger.info(self.strings("player_lynch_triggered").format(nickname=self._player_nickname_to_lynch))
                logger.info(f"⏳ AutoMafiaTournamentsGame: Ожидание {chosen_lynch_delay} секунд перед нажатием кнопки для голосования за игрока сообщения {message.id}...")
                await asyncio.sleep(chosen_lynch_delay)

                player_lynch_button_found = False
                for row in message.buttons:
                    for button in row:
                        try:
                            button_text = str(getattr(button, 'text', ''))
                        except Exception as e:
                            logger.warning(f"Error getting button text for player lynch message {message.id}: {e}")
                            button_text = ''

                        if button_text.lower() == self._player_nickname_to_lynch.lower():
                            logger.info(self.strings("player_lynch_button_found").format(nickname=self._player_nickname_to_lynch))
                            try:
                                await button.click()
                                logger.info(self.strings("player_lynch_success").format(nickname=self._player_nickname_to_lynch))
                                player_lynch_button_found = True
                                self._player_nickname_to_lynch = None # Очищаем ник после успешного нажатия
                                break 
                            except Exception as e:
                                logger.error(self.strings("player_lynch_error").format(nickname=self._player_nickname_to_lynch, error=e))
                                self._player_nickname_to_lynch = None # Очищаем ник при ошибке
                    if player_lynch_button_found:
                        break 
                
                if not player_lynch_button_found:
                    logger.warning(self.strings("player_lynch_button_not_found").format(nickname=self._player_nickname_to_lynch))
                    self._player_nickname_to_lynch = None # Очищаем ник, если кнопка не найдена

                return # Обработано линчевание конкретного игрока, дальнейшая обработка для этого сообщения не требуется

            # --- Существующая общая логика линчевания/повешения ---
            is_game_join = any(phrase.lower() in msg_text_lower for phrase in self.config["game_join_trigger_phrases"])
            all_lynch_trigger_phrases = self.config["lynch_trigger_phrases"] + self.config["lynch_hang_trigger_phrases"]
            is_general_lynch_message = any(phrase.lower() in msg_text_lower for phrase in all_lynch_trigger_phrases)

            if not (is_game_join or is_general_lynch_message):
                logger.debug(f"AutoMafiaTournamentsGame: Сообщение {message.id} не содержит ни одну из фраз для активации (вход в игру, общее линчевание/повешение). Пропускаю.")
                return
            
            if is_general_lynch_message:
                if not getattr(message, 'buttons', None):
                    logger.warning(f"⚠️ AutoMafiaTournamentsGame: Запрос на линчевание/повешение найден (msg_id: {message.id}), но кнопок нет. Пропускаю.")
                    return

                lynch_delays = self.config["lynch_delay"]
                chosen_lynch_delay = random.choice(lynch_delays)

                logger.info(f"⏳ AutoMafiaTournamentsGame: Ожидание {chosen_lynch_delay} секунд перед нажатием кнопки для линчевания/повешения сообщения {message.id}...")
                await asyncio.sleep(chosen_lynch_delay)

                lynch_marker = self.config["lynch_target_marker"]
                target_emoji = "👍" 
                success_log_message = f"🎉 AutoMafiaTournamentsGame: Успешно нажата кноп '{target_emoji}' для линчевания/повешения сообщения {message.id}."
                not_found_log_message = self.strings("lynch_button_not_found_positive")
                
                # Проверяем lynch_marker с учетом регистра в исходном msg_text, так как он может быть специфическим
                if lynch_marker and lynch_marker in msg_text:
                    target_emoji = "👎"
                    success_log_message = f"🎉 AutoMafiaTournamentsGame: Успешно нажата кноп '{target_emoji}' для линчевания/повешения с маркером '{lynch_marker}' сообщения {message.id}."
                    not_found_log_message = self.strings("lynch_button_not_found_negative").format(marker=lynch_marker)
                    logger.info(self.strings("lynch_triggered_negative").format(marker=lynch_marker))
                else:
                    logger.info(self.strings("lynch_triggered_positive"))

                lynch_button_found = False
                for row in message.buttons:
                    for button in row:
                        try:
                            button_text = str(getattr(button, 'text', ''))
                        except Exception as e:
                            logger.warning(f"Error getting button text for lynch message {message.id}: {e}")
                            button_text = ''

                        if target_emoji in button_text: # Сравнение текста кнопки для эмодзи чувствительно к регистру
                            logger.info(f"✅ AutoMafiaTournamentsGame: Найдена кноп '{target_emoji}' для линчевания/повешения: '{button_text}'")
                            try:
                                await button.click()
                                logger.info(success_log_message)
                                lynch_button_found = True
                                break 
                            except Exception as e:
                                logger.error(f"❌ AutoMafiaTournamentsGame: Ошибка при нажатии кнопки '{target_emoji}' для линчевания/повешения сообщения {message.id}: {e}")
                    if lynch_button_found:
                        break 
                
                if not lynch_button_found:
                    logger.warning(not_found_log_message)
                
                return 

            elif is_game_join: 
                logger.info(f"🎮 AutoMafiaTournamentsGame: Найдено сообщение с набором/регистрацией! (msg_id: {message.id}, chat_id: {message.chat_id})")

                if not getattr(message, 'buttons', None):
                    logger.warning(f"⚠️ AutoMafiaTournamentsGame: Сообщение с набором/регистрацией найдено (msg_id: {message.id}), но кнопок нет. Пропускаю.")
                    return

                delays = self.config["delays"]
                chosen_delay = random.choice(delays)

                logger.info(f"⏳ AutoMafiaTournamentsGame: Ожидание {chosen_delay} секунд перед обработкой сообщения {message.id} (выбрано из {delays})...")
                await asyncio.sleep(chosen_delay)

                configured_button_keywords_lower = [kw.lower() for kw in self.config["button_keywords"]]
                keywords_to_check = configured_button_keywords_lower

                deep_link_mode_active = '🌚' in configured_button_keywords_lower or '🌝' in configured_button_keywords_lower

                button_found = False
                for row in message.buttons:
                    for button in row:
                        try:
                            button_text = str(getattr(button, 'text', ''))
                        except Exception as e:
                            logger.warning(f"Error getting button text for message {message.id}: {e}")
                            button_text = ''

                        logger.debug(f"🔍 AutoMafiaTournamentsGame: Проверка кнопки: '{button_text}'")

                        if any(keyword in button_text.lower() for keyword in keywords_to_check):
                            logger.info(f"✅ AutoMafiaTournamentsGame: Найдена кнопка присоединения: '{button_text}'")

                            if getattr(button, 'url', None):
                                button_url = button.url
                                logger.info(f"🔗 AutoMafiaTournamentsGame: URL кнопки: {button_url}")

                                parsed_url = urllib.parse.urlparse(button_url)
                                
                                bot_username = None
                                if parsed_url.hostname in ['t.me', 'telegram.me'] and parsed_url.path:
                                    path_parts = parsed_url.path.lstrip('/').split('/')
                                    if path_parts and path_parts[0]:
                                        bot_username = path_parts[0]
                                elif parsed_url.scheme == 'tg' and parsed_url.netloc == 'resolve':
                                    query_params_tg = urllib.parse.parse_qs(parsed_url.query)
                                    bot_username = query_params_tg.get('domain', [None])[0]

                                query_params = urllib.parse.parse_qs(parsed_url.query)
                                start_param = query_params.get('start', [None])[0]

                                if deep_link_mode_active and bot_username and start_param:
                                    logger.info(f"📤 AutoMafiaTournamentsGame: Режим Deep-Link активен. Отправка /start {start_param} боту @{bot_username}")

                                    try:
                                        await self._client.send_message(
                                            bot_username,
                                            f'/start {start_param}'
                                        )
                                        logger.info("🎉 AutoMafiaTournamentsGame: Успешно отправлена команда /start (уведомление в чат не отправлено).")
                                        button_found = True
                                        break 
                                    except Exception as e:
                                        logger.error(f"❌ AutoMafiaTournamentsGame: Ошибка при отправке Deep-Link команды /start для сообщения {message.id}: {e}")
                                else:
                                    logger.warning(f"⚠️ AutoMafiaTournamentsGame: Найдена кнопка '{button_text}' с URL '{button_url}', но она не является Deep-Link или режим Deep-Link неактивен. Пропускаю.")
                            else: 
                                logger.info(f"📤 AutoMafiaTournamentsGame: Найдена кнопка '{button_text}' (CallbackQuery). Нажимаю.")
                                try:
                                    await button.click()
                                    logger.info(f"🎉 AutoMafiaTournamentsGame: Успешно нажата кноп '{button_text}' для присоединения к игре.")
                                    button_found = True
                                    break 
                                except Exception as e:
                                    logger.error(f"❌ AutoMafiaTournamentsGame: Ошибка при нажатии кнопки '{button_text}' для присоединения к игре: {e}")
                    if button_found:
                        break 

                if not button_found:
                    logger.warning(f"⚠️ AutoMafiaTournamentsGame: Кнопка присоединения не найдена под сообщением {message.id} после задержки.")

        except Exception as e:
            logger.exception(f"❌ AutoMafiaTournamentsGame: Критическая ошибка в watcher для сообщения {getattr(message, 'id', 'N/A')}: {e}")
