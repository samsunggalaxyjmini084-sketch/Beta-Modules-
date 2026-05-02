# meta developer: @yourhandle
# meta name: AutoJoinGame
# meta version: 2.3.9
# 01000001010101000100111101001010010011100010000001000111010000010100110101000101
# 010000010101010001001111010010100100100101001110001000000100011101000001
# 0100110101000101001000000100110101000100010101010100110001000101
import logging
import asyncio
import random
import urllib.parse
from datetime import datetime, timedelta
from telethon.tl.types import Message, User
from telethon import events
from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class AutoJoinGameMod(loader.Module):
    """Модуль для автоматического нажатия кнопки при наборе в игру в ботах мафии, а также подтверждения линчевания и повешения, и голосования за конкретного игрока. Дополнительно: пересылка роли в мафии в указанный чат, отслеживание определенных ролей и автоматическая отправка списка отслеживаемых ролей в чат после активации. Поддерживает автоматическую активацию отслеживания ролей по ключевым словам."""

    strings = {
        "name": "AutoJoinGame",
        "_cls_doc": "Модуль для автоматического нажатия кнопки при наборе в игру в ботах мафии, а также подтверждения линчевания и повешения, и голосования за конкретного игрока. Дополнительно: пересылка роли в мафии в указанный чат, отслеживание определенных ролей и автоматическая отправка списка отслеживаемых ролей в чат после активации. Поддерживает автоматическую активацию отслеживания ролей по ключевым словам.",
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
                  "\n<emoji document_id=5771887475421090729>👤</emoji> Статус отслеживания ролей:\n"
                  "Отслеживание ролей: {}\n"
                  "Длительность отслеживания (секунды): {}\n"
                  "Фразы для отслеживаемых ролей: {}\n"
                  "Фразы-триггеры объявления роли: {}\n"
                  "Отслеживаемых ролей найдено: {}\n"
                  "Время до окончания отслеживания: {}\n"
                  "Чат для отправки списка отслеживаемых ролей: {}\n"
                  "Задержка отправки списка отслеживаемых ролей (секунды): {}\n"
                  "Автоматическое включение отслеживания ролей (фразы): {}\n"
                  "Автоматическое включение отслеживания ролей (боты): {}",
        "error": "❌ Ошибка при нажатии кнопки: {}",
        "no_button": "⚠️ Кнопка не найдена под сообщением",
        "help_text": """<emoji document_id=5931415565955503486>🤖</emoji> AutoJoinGame - Помощь

<emoji document_id=5935847413859225147>🏀</emoji> Команды:
<code>.ajgon</code> - Включить автовход в игру и автолинчевание
<code>.ajgoff</code> - Выключить автовход в игру и автолинчевание
<code>.ajgstatus</code> - Показать статус
<code>.ajghelp</code> - Эта справка
<code>.ajgtest</code> - Проверить последнее сообщение с набором в текущем чате
<code>.ajgid</code> - Показать список ID ботов для мафии
<code>.ajgtournaments</code> - Показать информацию о регистрации на турниры
<code>.ajgtrackroles</code> - Включить/выключить отслеживание ролей
<code>.ajgshowtrackedroles</code> - Показать список найденных отслеживаемых ролей

<emoji document_id=5877260593903177342>⚙</emoji> Как работает:
Ждет сообщение о наборе в игру или о голосовании (линчевание/повешение) от указанных ботов (или от любого бота, если список пуст).
Автоматически переходит по URL кнопки и отправляет /start для входа в игру.
Если бот спрашивает "Вы точно хотите линчевать..." или "Вы точно хотите повесить...", модуль автоматически нажмет кнопку.
Если в сообщении присутствует настроенный <code>lynch_target_marker</code> (по умолчанию 𝓝𝓚), модуль автоматически нажмет кнопку с эмодзи '👎'. В противном случае, если маркера нет, нажмет '👍'.
Работает только когда включен.
Дополнительно, если настроен <code>player_to_lynch_user_id</code>, модуль будет ожидать сообщение с ником игрока от этого пользователя. Как только ник получен, модуль будет искать сообщение о голосовании от <code>lynch_voting_bot_id</code>, содержащее <code>lynch_player_voting_trigger_phrases</code>, и затем автоматически нажмет кнопку с соответствующим ником игрока.
<b>Важное обновление:</b> Если сообщение от <code>player_to_lynch_user_id</code> начинается с символа <code>!</code>, этот символ будет автоматически удален из ника игрока перед использованием.
<b>Новая функция:</b> Модуль может автоматически пересылать сообщения с вашей ролью в мафии в указанный чат. Это работает, когда бот отправляет вам роль в приватном чате, и сообщение содержит одну из настроенных фраз-триггеров.
<b>Улучшенная функция:</b> Модуль может отслеживать сообщения пользователей, объявляющих свою роль, и сохранять их ники и <b>конкретную объявленную роль</b> в список, если эта роль соответствует одной из настроенных фраз. Отслеживание можно включить/выключить и настроить его длительность.
<b>Новая функция:</b> Модуль может автоматически отправлять список отслеживаемых ролей в указанный чат через заданное время после активации отслеживания ролей.
<b>Новая функция:</b> Модуль может автоматически включать отслеживание ролей при получении сообщения, содержащего определенные фразы, от указанных ботов.

<emoji document_id=5843843420468024653>⭐️</emoji> Настройки:
В конфиге модуля можно изменить задержку(и) перед нажатием. Если указано несколько значений, будет выбрано случайное.
Можно указать список ID ботов, от которых ожидать сообщение о наборе.
Можно указать список ID чатов, в которых модуль будет активен. Если список пуст, модуль будет работать во всех чатах.
<b>Настройка:</b> <code>button_keywords</code> - список ключевых слов, которые должны содержаться в тексте кнопки для ее активации. Регистр не учитывается. <b>Если среди ключевых слов есть "🌚" или "🌝", активируется специальный режим обработки Deep-Link URL, при котором боту будет отправляться команда <code>/start &lt;параметр_start&gt;</code>, извлеченный из URL кнопки.</b>
<b>Настройка:</b> <code>lynch_target_marker</code> - строка-маркер, которая, если присутствует в сообщении-триггере для голосования, заставит модуль нажать кнопку '👎'. Если отсутствует или маркер не указан (пустая строка), нажимается '👍'. По умолчанию: "" (пусто).
<b>Настройка:</b> <code>game_join_trigger_phrases</code> - список фраз, которые модуль будет искать в сообщениях для активации автовхода в игру. По умолчанию: <code>[\"Ведётся набор в игру\", \"Регистрация началась!\"]</code>.
<b>Настройка:</b> <code>lynch_trigger_phrases</code> - список фраз, которые модуль будет искать в сообщениях для активации автолинчевания. По умолчанию: <code>[\"Вы точно хотите линчевать\"]</code>.
<b>Настройка:</b> <code>lynch_hang_trigger_phrases</code> - список фраз, которые модуль будет искать в сообщениях для активации автоповешения. По умолчанию: <code>[\"Вы точно хотите повесить\"]</code>.
<b>Настройка:</b> <code>player_to_lynch_user_id</code> - ID пользователя, чье сообщение будет использоваться как ник игрока для линчевания. Если <code>0</code>, то функция отключена.
<b>Настройка:</b> <code>lynch_voting_bot_id</code> - ID бота, который отправляет сообщение с кнопками для голосования за конкретного игрока. Если <code>0</code>, то функция отключена.
<b>Настройка:</b> <code>lynch_player_voting_trigger_phrases</code> - список фраз, которые модуль будет искать в сообщениях от <code>lynch_voting_bot_id</code> для активации голосования за конкретного игрока. По умолчанию: <code>[\"Пришло время искать виноватых!\", \"Кого ты хочешь повесить?\", \"Пришло время определить и наказать виновных\", \"Пришло время искать виноватых! Кого ты хочешь линчевать?\"]</code>.
<b>Настройка:</b> <code>role_forward_chat_id</code> - ID чата, куда будет пересылаться полученная роль в мафии. Если <code>0</code>, функция отключена.
<b>Настройка:</b> <code>role_trigger_phrases</code> - список фраз, которые модуль будет искать в сообщениях от бота в ЛС для определения роли. По умолчанию: <code>[\"Ваша роль:\", \"Ты - \", \"Твоя роль:\", \"Ты стал(а) \"]</code>.
<b>Настройка:</b> <code>role_tracking_enabled</code> - Включено ли отслеживание ролей. По умолчанию: <code>False</code>.
<b>Настройка:</b> <code>role_tracking_duration</code> - Длительность отслеживания ролей в секундах. По умолчанию: <code>300</code> (5 минут).
<b>Улучшенная настройка:</b> <code>tracked_roles_to_monitor</code> - Список фраз, указывающих на роли, которые нужно отслеживать. Модуль будет искать эти фразы в объявлениях ролей пользователей. Например: <code>[\"мирный житель\", \"мафия\", \"комиссар\"]</code>.
<b>Настройка:</b> <code>role_announcement_phrases</code> - Список фраз, которые пользователи могут использовать для объявления своей роли. По умолчанию: <code>[\"Моя роль:\", \"Я - \", \"Моя роль\", \"Я \", \"роль:\", \"моя роль\"]</code>.
<b>Новая настройка:</b> <code>send_tracked_roles_chat_id</code> - ID чата, куда будет отправлен список отслеживаемых ролей после активации. Если <code>0</code>, функция отключена.
<b>Новая настройка:</b> <code>send_tracked_roles_delay</code> - Задержка в секундах, через которую будет отправлен список отслеживаемых ролей после активации отслеживания.
<b>Новая настройка:</b> <code>auto_track_roles_trigger_phrases</code> - Список фраз, которые модуль будет искать в сообщениях для автоматического включения отслеживания ролей. По умолчанию: <code>[]</code>.
<b>Новая настройка:</b> <code>auto_track_roles_bot_ids</code> - Список ID ботов, от которых ожидается сообщение с фразами для автоматического включения отслеживания ролей. Если список пуст, сообщения будут отслеживаться от любого бота. По умолчанию: <code>[]</code>.
""",
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

.cfg AutoJoinGame button_keywords""",
        "lynch_triggered_positive": "<emoji document_id=5935968647901089910>🔫</emoji> Обнаружен запрос на линчевание/повешение. Нажимаю '👍'.",
        "lynch_button_not_found_positive": "⚠️ Запрос на линчевание/повешение обнаружен, но кнопка '👍' не найдена.",
        "lynch_triggered_negative": "<emoji document_id=5935968647901089910>🔫</emoji> Обнаружен запрос на линчевание/повешение с маркером '{marker}'. Нажимаю '👎'.",
        "lynch_button_not_found_negative": "⚠️ Запрос на линчевание/повешение с маркером '{marker}' обнаружен, но кнопка '👎' не найдена.",
        "player_nickname_set": "<emoji document_id=5839380580080293813>🖋</emoji> Установлен ник игрока для линчевания: <code>{nickname}</code>. Ожидаю голосования.",
        "player_lynch_triggered": "<emoji document_id=5935968647901089910>🔫</emoji> Обнаружен запрос на голосование за игрока. Ищу кнопку с ником <code>{nickname}</code>.",
        "player_lynch_button_found": "✅ AutoJoinGame: Найдена кнопка с ником <code>{nickname}</code>. Нажимаю.",
        "player_lynch_button_not_found": "⚠️ AutoJoinGame: Запрос на голосование за игрока найден, но кнопка с ником <code>{nickname}</code> не найдена.",
        "player_lynch_success": "🎉 AutoJoinGame: Успешно нажата кнопка с ником <code>{nickname}</code>. Ник сброшен.",
        "player_lynch_error": "❌ AutoJoinGame: Ошибка при нажатии кнопки с ником <code>{nickname}</code>: {error}",
        "ajgtest_player_nickname_would_be_set": "🔔 Сообщение ID <code>{msg_id}</code> от <code>{sender_id}</code> *установило бы* ник: <code>{nickname}</code>.",
        "ajgtest_player_nickname_not_set_yet": "ℹ️ Ник игрока для голосования не установлен в конфиге или не найден в последних 500 сообщениях.",
        "ajgtest_player_nickname_used": "ℹ️ Для последующих тестов используется ник: <code>{nickname}</code>.",
        "ajgtest_player_lynch_disabled": "ℹ️ ID пользователя для линчевания игрока не установлен в конфиге. Эта часть теста неактивна.",
        "ajgtest_no_matches": "❌ Сообщения с набором, запросом на линчевание или голосование за игрока от настроенных ботов/пользователя не найдено в текущем чате ID <code>{chat_id}</code>\n📊 Проверено сообщений: {count}",
        "ajgtest_error": "❌ Ошибка: <code>{error}</code>",
        "role_forward_chat_id_display": "Отключено (0)",
        "role_forward_trigger_phrases_display": "(пусто)",
        "role_forward_success": "🎉 AutoJoinGame: Роль успешно переслана в чат <code>{chat_id}</code>.",
        "role_forward_error": "❌ AutoJoinGame: Ошибка при пересылке роли в чат <code>{chat_id}</code>: {error}",
        "role_tracking_started": "✅ Отслеживание ролей включено на {duration} секунд.",
        "role_tracking_started_with_send": "✅ Отслеживание ролей включено на {duration} секунд. Список будет отправлен в чат <code>{chat_id}</code> через {delay} секунд.",
        "role_tracking_stopped": "❌ Отслеживание ролей выключено.",
        "role_tracking_already_active": "⚠️ Отслеживание ролей уже активно. Чтобы начать заново, сначала выключите его.",
        "role_tracking_inactive": "⚠️ Отслеживание ролей неактивно.",
        "tracked_roles_list": "<emoji document_id=5771887475421090729>👤</emoji> Список отслеживаемых ролей (найдено {count}):\n{list_items}",
        "no_tracked_roles": "<emoji document_id=5771887475421090729>👤</emoji> Пока не найдено ни одной отслеживаемой роли.",
        "role_tracked_success": "✅ Отслеживание ролей: Пользователь <code>{nickname}</code> (Роль: {role}) добавлен в список отслеживаемых ролей.",
        "role_tracking_expired": "⚠️ Время отслеживания ролей истекло. Отслеживание остановлено.",
        "role_tracking_status_active": "🟢 Активно",
        "role_tracking_status_inactive": "🔴 Неактивно",
        "time_remaining_format": "{minutes}м {seconds}с",
        "no_time_remaining": "N/A",
        "tracked_roles_send_success": "🎉 AutoJoinGame: Список отслеживаемых ролей успешно отправлен в чат <code>{chat_id}</code>.",
        "tracked_roles_send_error": "❌ AutoJoinGame: Ошибка при отправке списка отслеживаемых ролей в чат <code>{chat_id}</code>: {error}",
        "send_tracked_roles_chat_id_display": "Отключено (0)",
        "send_tracked_roles_delay_display": "Отключено (0)",
        "auto_track_roles_trigger_phrases_display": "(пусто)",
        "auto_track_roles_bot_ids_display": "Не указаны (любой бот)",
        "auto_role_tracking_activated": "<emoji document_id=5776375003280838798>✅</emoji> Автоматическое отслеживание ролей включено на {duration} секунд.",
        "auto_role_tracking_activated_with_send": "<emoji document_id=5776375003280838798>✅</emoji> Автоматическое отслеживание ролей включено на {duration} секунд. Список будет отправлен в чат <code>{chat_id}</code> через {delay} секунд.",
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
                validator=loader.validators.Series(loader.validators.String()) # Changed to Series to match config
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
            loader.ConfigValue(
                "role_tracking_enabled",
                False,
                lambda: "Включено ли отслеживание ролей.",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "role_tracking_duration",
                300, # 5 минут
                lambda: "Длительность отслеживания ролей в секундах.",
                validator=loader.validators.Integer(minimum=10)
            ),
            loader.ConfigValue(
                "tracked_roles_to_monitor",
                ["мирный житель", "мирный"],
                lambda: "Список фраз, указывающих на роли, которые нужно отслеживать. Модуль будет искать эти фразы в объявлениях ролей пользователей.",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                "role_announcement_phrases",
                ["Моя роль:", "Я - ", "Моя роль", "Я ", "роль:", "моя роль"],
                lambda: "Список фраз, которые пользователи могут использовать для объявления своей роли.",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                "send_tracked_roles_chat_id",
                0,
                lambda: "ID чата, куда будет отправлен список отслеживаемых ролей после активации. Если 0, функция отключена.",
                validator=loader.validators.Integer(minimum=0)
            ),
            loader.ConfigValue(
                "send_tracked_roles_delay",
                30, # 30 секунд
                lambda: "Задержка в секундах, через которую будет отправлен список отслеживаемых ролей после активации отслеживания.",
                validator=loader.validators.Integer(minimum=0)
            ),
            loader.ConfigValue(
                "auto_track_roles_trigger_phrases",
                [],
                lambda: "Список фраз, которые модуль будет искать в сообщениях для автоматического включения отслеживания ролей.",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                "auto_track_roles_bot_ids",
                [],
                lambda: "Список ID ботов, от которых ожидается сообщение с фразами для автоматического включения отслеживания ролей. Если список пуст, сообщения будут отслеживаться от любого бота.",
                validator=loader.validators.Series(loader.validators.Integer())
            ),
        )

        self._player_nickname_to_lynch = None 
        self._role_tracking_active = False
        self._role_tracking_start_time = None
        self._tracked_roles_list = [] # Stores (user_id, nickname, role_text)
        self._self_id = None 
        self._processed_messages = set() 
        self._processed_messages_cleanup_task = None 
        self._send_tracked_roles_task = None # Task for sending tracked roles list

    async def client_ready(self, client, _):
        self._client = client
        self._self_id = (await self._client.get_me()).id 
        if self._processed_messages_cleanup_task is None:
            self._processed_messages_cleanup_task = asyncio.create_task(self._cleanup_processed_messages_loop())

    async def _cleanup_processed_messages_loop(self):
        """Периодически очищает набор обработанных ID сообщений."""
        while True:
            await asyncio.sleep(300) 
            if self._processed_messages:
                logger.debug(f"AutoJoinGame: Очистка {len(self._processed_messages)} обработанных ID сообщений.")
                self._processed_messages.clear()
            
    async def _on_unload(self):
        """Останавливает задачи при выгрузке модуля."""
        if self._processed_messages_cleanup_task:
            self._processed_messages_cleanup_task.cancel()
            try:
                await self._processed_messages_cleanup_task
            except asyncio.CancelledError:
                logger.debug("AutoJoinGame: Задача очистки обработанных сообщений отменена.")
        
        if self._send_tracked_roles_task:
            self._send_tracked_roles_task.cancel()
            try:
                await self._send_tracked_roles_task
            except asyncio.CancelledError:
                logger.debug("AutoJoinGame: Задача отправки списка отслеживаемых ролей отменена при выгрузке.")


    def _get_user_nickname(self, user: User) -> str:
        """Получает никнейм пользователя, предпочитая имя и фамилию."""
        if user.first_name and user.last_name:
            return f"{user.first_name} {user.last_name}"
        if user.first_name:
            return user.first_name
        if user.username:
            return user.username 
        return f"Неизвестный пользователь" 
    
    async def _send_tracked_roles_list_scheduled(self, delay: int, chat_id: int):
        """Задача для отправки списка отслеживаемых ролей через заданное время."""
        try:
            await asyncio.sleep(delay)
            if not self._role_tracking_active: 
                logger.debug("AutoJoinGame: Отправка списка отслеживаемых ролей отменена, так как отслеживание неактивно.")
                return

            if not self._tracked_roles_list:
                message_text = self.strings("no_tracked_roles")
            else:
                list_items = "\n".join([f"• <code>{nickname}</code> (Роль: {role_text})" for _, nickname, role_text in self._tracked_roles_list])
                message_text = self.strings("tracked_roles_list").format(count=len(self._tracked_roles_list), list_items=list_items)
            
            await self._client.send_message(chat_id, message_text)
            logger.info(self.strings("tracked_roles_send_success").format(chat_id=chat_id))

        except asyncio.CancelledError:
            logger.debug("AutoJoinGame: Задача по отправке списка отслеживаемых ролей отменена.")
        except Exception as e:
            logger.error(self.strings("tracked_roles_send_error").format(chat_id=chat_id, error=e))

    @loader.command(ru_doc="Включить автовход в игру и автолинчевание")
    async def ajgon(self, message: Message):
        """Включить автовход в игру и автолинчевание"""
        self.config["enabled"] = True
        await utils.answer(message, self.strings("enabled"))

    @loader.command(ru_doc="Выключить автовход в игру и автолинчевание")
    async def ajgoff(self, message: Message):
        """Выключить автовход в игру и автолинчевание"""
        self.config["enabled"] = False
        self._player_nickname_to_lynch = None 
        self._role_tracking_active = False 
        self._role_tracking_start_time = None
        self._tracked_roles_list = [] # Clear tracked roles on disable
        self._processed_messages.clear() # Очищаем processed_messages при выключении модуля
        if self._send_tracked_roles_task:
            self._send_tracked_roles_task.cancel()
            self._send_tracked_roles_task = None
        await utils.answer(message, self.strings("disabled"))

    @loader.command(ru_doc="Включить/выключить отслеживание ролей")
    async def ajgtrackroles(self, message: Message):
        """Включить/выключить отслеживание ролей"""
        if self.config["role_tracking_enabled"]:
            self.config["role_tracking_enabled"] = False
            self._role_tracking_active = False
            self._role_tracking_start_time = None
            self._tracked_roles_list = []
            if self._send_tracked_roles_task:
                self._send_tracked_roles_task.cancel()
                self._send_tracked_roles_task = None
            self._processed_messages.clear() # Очищаем processed_messages при выключении отслеживания
            await utils.answer(message, self.strings("role_tracking_stopped"))
        else:
            self.config["role_tracking_enabled"] = True
            self._role_tracking_active = True
            self._role_tracking_start_time = datetime.now()
            self._tracked_roles_list = [] 
            self._processed_messages.clear() # Очищаем processed_messages при включении отслеживания
            
            send_chat_id = self.config["send_tracked_roles_chat_id"]
            send_delay = self.config["send_tracked_roles_delay"]

            if send_chat_id != 0 and send_delay > 0:
                if self._send_tracked_roles_task:
                    self._send_tracked_roles_task.cancel()
                    self._send_tracked_roles_task = None
                self._send_tracked_roles_task = asyncio.create_task(
                    self._send_tracked_roles_list_scheduled(send_delay, send_chat_id)
                )
                await utils.answer(message, self.strings("role_tracking_started_with_send").format(
                    duration=self.config["role_tracking_duration"],
                    delay=send_delay,
                    chat_id=send_chat_id
                ))
            else:
                await utils.answer(message, self.strings("role_tracking_started").format(duration=self.config["role_tracking_duration"]))

    @loader.command(ru_doc="Показать список найденных отслеживаемых ролей")
    async def ajgshowtrackedroles(self, message: Message):
        """Показать список найденных отслеживаемых ролей"""
        if not self._tracked_roles_list:
            await utils.answer(message, self.strings("no_tracked_roles"))
            return

        list_items = "\n".join([f"• <code>{nickname}</code> (Роль: {role_text})" for _, nickname, role_text in self._tracked_roles_list])
        await utils.answer(message, self.strings("tracked_roles_list").format(count=len(self._tracked_roles_list), list_items=list_items))

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
        
        player_to_lynch_user_id_display = str(self.config["player_to_lynch_user_id"]) if self.config["player_to_lynch_user_id"] else "Отключено (0)"
        lynch_voting_bot_id_display = str(self.config["lynch_voting_bot_id"]) if self.config["lynch_voting_bot_id"] else "Отключено (0)"
        lynch_player_voting_trigger_phrases_display = ", ".join(self.config["lynch_player_voting_trigger_phrases"]) if self.config["lynch_player_voting_trigger_phrases"] else "(пусто)"
        current_player_nickname_display = self._player_nickname_to_lynch if self._player_nickname_to_lynch else "(нет)"

        role_forward_chat_id_display = str(self.config["role_forward_chat_id"]) if self.config["role_forward_chat_id"] else self.strings("role_forward_chat_id_display")
        role_trigger_phrases_display = ", ".join(self.config["role_trigger_phrases"]) if self.config["role_trigger_phrases"] else self.strings("role_forward_trigger_phrases_display")

        role_tracking_status = self.strings("role_tracking_status_active") if self.config["role_tracking_enabled"] and self._role_tracking_active else self.strings("role_tracking_status_inactive")
        role_tracking_duration_display = str(self.config["role_tracking_duration"])
        tracked_roles_to_monitor_display = ", ".join(self.config["tracked_roles_to_monitor"]) if self.config["tracked_roles_to_monitor"] else "(пусто)"
        role_announcement_phrases_display = ", ".join(self.config["role_announcement_phrases"]) if self.config["role_announcement_phrases"] else "(пусто)"
        tracked_roles_count = len(self._tracked_roles_list)

        time_remaining_display = self.strings("no_time_remaining")
        if self._role_tracking_active and self._role_tracking_start_time:
            time_elapsed = datetime.now() - self._role_tracking_start_time
            remaining_seconds = self.config["role_tracking_duration"] - time_elapsed.total_seconds()
            if remaining_seconds > 0:
                minutes, seconds = divmod(int(remaining_seconds), 60)
                time_remaining_display = self.strings("time_remaining_format").format(minutes=minutes, seconds=seconds)
            else:
                time_remaining_display = "Истекло"
        
        send_tracked_roles_chat_id_display = str(self.config["send_tracked_roles_chat_id"]) if self.config["send_tracked_roles_chat_id"] else self.strings("send_tracked_roles_chat_id_display")
        send_tracked_roles_delay_display = str(self.config["send_tracked_roles_delay"]) if self.config["send_tracked_roles_delay"] > 0 else self.strings("send_tracked_roles_delay_display")
        
        auto_track_roles_trigger_phrases_display = ", ".join(self.config["auto_track_roles_trigger_phrases"]) if self.config["auto_track_roles_trigger_phrases"] else self.strings("auto_track_roles_trigger_phrases_display")
        auto_track_roles_bot_ids_display = ", ".join(map(str, self.config["auto_track_roles_bot_ids"])) if self.config["auto_track_roles_bot_ids"] else self.strings("auto_track_roles_bot_ids_display")

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
            role_tracking_status,
            role_tracking_duration_display,
            tracked_roles_to_monitor_display,
            role_announcement_phrases_display,
            tracked_roles_count,
            time_remaining_display,
            send_tracked_roles_chat_id_display,
            send_tracked_roles_delay_display,
            auto_track_roles_trigger_phrases_display,
            auto_track_roles_bot_ids_display
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
                        break 
                if temp_player_nickname_for_test:
                    results.append(self.strings("ajgtest_player_nickname_used").format(nickname=temp_player_nickname_for_test))
                else:
                    results.append(self.strings("ajgtest_player_nickname_not_set_yet"))
            else:
                results.append(self.strings("ajgtest_player_lynch_disabled"))

            async for msg in self._client.iter_messages(current_chat_id, limit=500):
                count += 1

                if not getattr(msg, 'text', None):
                    continue

                sender = await msg.get_sender()
                sender_id = getattr(sender, 'id', None)

                is_general_bot_message = getattr(sender, 'bot', False) and (
                    not configured_bot_ids or sender_id in configured_bot_ids
                )

                is_player_voting_bot_message = getattr(sender, 'bot', False) and sender_id == self.config["lynch_voting_bot_id"]

                if not is_general_bot_message and not is_player_voting_bot_message:
                    continue
                
                msg_text_lower = msg.text.lower() 
                
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
                    
                    results.append(info_msg)

            if not results:
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

    @loader.watcher(incoming=True, outgoing=False)
    async def watcher(self, message: Message):
        """Обработчик всех входящих сообщений для автовхода в игру, автолинчевания, пересылки роли и отслеживания ролей."""
        try:
            if not self.config["enabled"]:
                logger.debug("AutoJoinGame: Модуль выключен. Пропускаю сообщение.")
                return

            if not getattr(message, 'text', None):
                logger.debug(f"AutoJoinGame: Сообщение {message.id} не содержит текста. Пропускаю.")
                return
            
            message_identifier = (message.chat_id, message.id)
            # Отсрочиваем проверку processed_messages до обработки логики автоотслеживания ролей

            sender = await message.get_sender()
            sender_id = getattr(sender, 'id', None)
            if sender_id is None:
                logger.warning(f"AutoJoinGame: Не удалось получить ID отправителя для сообщения {message.id} в чате {message.chat_id}. Пропускаю.")
                return

            allowed_chats = self.config["allowed_chats"]
            if allowed_chats and message.chat_id not in allowed_chats:
                logger.debug(f"AutoJoinGame: Чат {message.chat_id} не в списке разрешенных чатов ({allowed_chats}). Пропускаю сообщение {message.id}.")
                return

            msg_text = message.text
            msg_text_lower = msg_text.lower() 

            # --- Автоматическое включение отслеживания ролей ---
            auto_track_phrases = self.config["auto_track_roles_trigger_phrases"]
            auto_track_bot_ids = self.config["auto_track_roles_bot_ids"]

            if auto_track_phrases and not self.config["role_tracking_enabled"]:
                is_auto_track_trigger_bot = (
                    getattr(sender, 'bot', False) and
                    (not auto_track_bot_ids or sender_id in auto_track_bot_ids)
                )
                if is_auto_track_trigger_bot and any(p.lower() in msg_text_lower for p in auto_track_phrases):
                    logger.info(f"AutoJoinGame: Обнаружен триггер для автоматического включения отслеживания ролей в сообщении {message.id} от бота {sender_id}.")
                    
                    self.config["role_tracking_enabled"] = True
                    self._role_tracking_active = True
                    self._role_tracking_start_time = datetime.now()
                    self._tracked_roles_list = [] # Очищаем предыдущие отслеживаемые роли
                    self._processed_messages.clear() # Очищаем processed_messages при автоматическом включении отслеживания

                    send_chat_id = self.config["send_tracked_roles_chat_id"]
                    send_delay = self.config["send_tracked_roles_delay"]

                    if send_chat_id != 0 and send_delay > 0:
                        if self._send_tracked_roles_task:
                            self._send_tracked_roles_task.cancel()
                            self._send_tracked_roles_task = None
                        self._send_tracked_roles_task = asyncio.create_task(
                            self._send_tracked_roles_list_scheduled(send_delay, send_chat_id)
                        )
                        logger.info(f"AutoJoinGame: Автоматическое отслеживание ролей включено на {self.config['role_tracking_duration']} секунд. Список будет отправлен в чат {send_chat_id} через {send_delay} секунд.")
                        await self._client.send_message(message.chat_id, self.strings("auto_role_tracking_activated_with_send").format(
                            duration=self.config["role_tracking_duration"],
                            delay=send_delay,
                            chat_id=send_chat_id
                        ))
                    else:
                        logger.info(f"AutoJoinGame: Автоматическое отслеживание ролей включено на {self.config['role_tracking_duration']} секунд.")
                        await self._client.send_message(message.chat_id, self.strings("auto_role_tracking_activated").format(
                            duration=self.config["role_tracking_duration"]
                        ))
            
            # --- Логика отслеживания ролей ---
            # Эта часть должна выполняться до проверки _processed_messages,
            # чтобы новые роли отслеживались даже из уже обработанных сообщений.
            if self.config["role_tracking_enabled"] and self._role_tracking_active:
                if self._role_tracking_start_time and (datetime.now() - self._role_tracking_start_time).total_seconds() > self.config["role_tracking_duration"]:
                    logger.info(self.strings("role_tracking_expired"))
                    self._role_tracking_active = False
                    self._role_tracking_start_time = None
                    if self._send_tracked_roles_task: # <--- Исправлено: отмена задачи при истечении времени
                        self._send_tracked_roles_task.cancel()
                        self._send_tracked_roles_task = None
                elif not getattr(sender, 'bot', False) and sender_id != self._self_id: 
                    role_announcement_phrases_lower = [p.lower() for p in self.config["role_announcement_phrases"]]
                    
                    is_role_announcement = any(phrase in msg_text_lower for phrase in role_announcement_phrases_lower)
                    
                    if is_role_announcement:
                        found_tracked_role = None
                        for tracked_role_phrase_orig in self.config["tracked_roles_to_monitor"]:
                            # Check if the role phrase is present as a whole word or at the start/end
                            if (f" {tracked_role_phrase_orig.lower()}" in msg_text_lower or 
                                msg_text_lower.startswith(tracked_role_phrase_orig.lower() + " ") or # "Я - мирный житель"
                                msg_text_lower.endswith(" " + tracked_role_phrase_orig.lower()) or # "Моя роль: мирный житель"
                                msg_text_lower == tracked_role_phrase_orig.lower()): # "мирный житель"
                                found_tracked_role = tracked_role_phrase_orig 
                                break
                        
                        if found_tracked_role:
                            nickname = self._get_user_nickname(sender)
                            # Проверяем, был ли уже этот пользователь добавлен в текущей сессии отслеживания
                            if not any(entry[0] == sender_id for entry in self._tracked_roles_list): 
                                self._tracked_roles_list.append((sender_id, nickname, found_tracked_role)) 
                                logger.info(self.strings("role_tracked_success").format(nickname=nickname, role=found_tracked_role))
            
            # Теперь проверяем processed_messages для остальных функций модуля
            if message_identifier in self._processed_messages:
                logger.debug(f"AutoJoinGame: Сообщение {message.id} в чате {message.chat_id} уже было обработано. Пропускаю.")
                return
            
            self._processed_messages.add(message_identifier)

            # --- Обработка сообщения, устанавливающего ник игрока ---
            player_to_lynch_user_id = self.config["player_to_lynch_user_id"]
            if player_to_lynch_user_id != 0 and sender_id == player_to_lynch_user_id:
                nickname = message.text.strip()
                if nickname.startswith('!'):
                    nickname = nickname[1:].strip() 
                
                self._player_nickname_to_lynch = nickname
                logger.info(self.strings("player_nickname_set").format(nickname=self._player_nickname_to_lynch))
                return 

            # --- Обработка пересылки роли ---
            role_forward_chat_id = self.config["role_forward_chat_id"]
            role_trigger_phrases = self.config["role_trigger_phrases"]

            if (role_forward_chat_id != 0 and
                    message.is_private and
                    getattr(sender, 'bot', False) and 
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
                return 

            is_general_game_bot = getattr(sender, 'bot', False) and (
                not self.config["bot_ids"] or sender_id in self.config["bot_ids"]
            )
            is_lynch_player_voting_bot = getattr(sender, 'bot', False) and sender_id == self.config["lynch_voting_bot_id"]

            if not is_general_game_bot and not is_lynch_player_voting_bot:
                logger.debug(f"AutoJoinGame: Сообщение {message.id} от бота {sender_id}, но его ID не в списке разрешенных ботов для общих триггеров и не является ботом для голосования за игрока. Пропускаю.")
                return
            
            if (is_lynch_player_voting_bot and 
                self.config["lynch_voting_bot_id"] != 0 and 
                self._player_nickname_to_lynch and 
                any(phrase.lower() in msg_text_lower for phrase in self.config["lynch_player_voting_trigger_phrases"])):
                
                if not getattr(message, 'buttons', None):
                    logger.warning(f"⚠️ AutoJoinGame: Запрос на голосование за игрока найден (msg_id: {message.id}), но кнопок нет. Пропускаю.")
                    self._player_nickname_to_lynch = None 
                    return

                lynch_delays = self.config["lynch_delay"]
                chosen_lynch_delay = random.choice(lynch_delays)

                logger.info(self.strings("player_lynch_triggered").format(nickname=self._player_nickname_to_lynch))
                logger.info(f"⏳ AutoJoinGame: Ожидание {chosen_lynch_delay} секунд перед нажатием кнопки для голосования за игрока сообщения {message.id}...")
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
                                break 
                            except Exception as e:
                                logger.error(self.strings("player_lynch_error").format(nickname=self._player_nickname_to_lynch, error=e))
                                self._player_nickname_to_lynch = None 
                    if player_lynch_button_found:
                        break 
                
                if not player_lynch_button_found:
                    logger.warning(self.strings("player_lynch_button_not_found").format(nickname=self._player_nickname_to_lynch))
                    self._player_nickname_to_lynch = None 

                return 

            if is_general_game_bot:
                is_game_join = any(phrase.lower() in msg_text_lower for phrase in self.config["game_join_trigger_phrases"])
                all_lynch_trigger_phrases = self.config["lynch_trigger_phrases"] + self.config["lynch_hang_trigger_phrases"]
                is_general_lynch_message = any(phrase.lower() in msg_text_lower for phrase in all_lynch_trigger_phrases)

                if not (is_game_join or is_general_lynch_message):
                    logger.debug(f"AutoJoinGame: Сообщение {message.id} не содержит ни одну из фраз для активации (вход в игру, общее линчевание/повешение). Пропускаю.")
                    return
                
                if is_general_lynch_message:
                    if not getattr(message, 'buttons', None):
                        logger.warning(f"⚠️ AutoJoinGame: Запрос на линчевание/повешение найден (msg_id: {message.id}), но кнопок нет. Пропускаю.")
                        return

                    lynch_delays = self.config["lynch_delay"]
                    chosen_lynch_delay = random.choice(lynch_delays)

                    logger.info(f"⏳ AutoJoinGame: Ожидание {chosen_lynch_delay} секунд перед нажатием кнопки для линчевания/повешения сообщения {message.id}...")
                    await asyncio.sleep(chosen_lynch_delay)

                    lynch_marker = self.config["lynch_target_marker"]
                    target_emoji = "👍" 
                    success_log_message = f"🎉 AutoJoinGame: Успешно нажата кноп '{target_emoji}' для линчевания/повешения сообщения {message.id}."
                    not_found_log_message = self.strings("lynch_button_not_found_positive")
                    
                    if lynch_marker and lynch_marker in msg_text:
                        target_emoji = "👎"
                        success_log_message = f"🎉 AutoJoinGame: Успешно нажата кноп '{target_emoji}' для линчевания/повешения с маркером '{lynch_marker}' сообщения {message.id}."
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

                            if target_emoji in button_text: 
                                logger.info(f"✅ AutoJoinGame: Найдена кноп '{target_emoji}' для линчевания/повешения: '{button_text}'")
                                try:
                                    await button.click()
                                    logger.info(success_log_message)
                                    lynch_button_found = True
                                    break 
                                except Exception as e:
                                    logger.error(f"❌ AutoJoinGame: Ошибка при нажатии кнопки '{target_emoji}' для линчевания/повешения сообщения {message.id}: {e}")
                        if lynch_button_found:
                            break 
                    
                    if not lynch_button_found:
                        logger.warning(not_found_log_message)
                    
                    return 

                elif is_game_join: 
                    logger.info(f"🎮 AutoJoinGame: Найдено сообщение с набором/регистрацией! (msg_id: {message.id}, chat_id: {message.chat_id})")

                    if not getattr(message, 'buttons', None):
                        logger.warning(f"⚠️ AutoJoinGame: Сообщение с набором/регистрацией найдено (msg_id: {message.id}), но кнопок нет. Пропускаю.")
                        return

                    delays = self.config["delays"]
                    chosen_delay = random.choice(delays)

                    logger.info(f"⏳ AutoJoinGame: Ожидание {chosen_delay} секунд перед обработкой сообщения {message.id} (выбрано из {delays})...")
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

                            logger.debug(f"🔍 AutoJoinGame: Проверка кнопки: '{button_text}'")

                            if any(keyword in button_text.lower() for keyword in keywords_to_check):
                                logger.info(f"✅ AutoJoinGame: Найдена кнопка присоединения: '{button_text}'")

                                if getattr(button, 'url', None):
                                    button_url = button.url
                                    logger.info(f"🔗 AutoJoinGame: URL кнопки: {button_url}")

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
                                        logger.info(f"📤 AutoJoinGame: Режим Deep-Link активен. Отправка /start {start_param} боту @{bot_username}")

                                        try:
                                            await self._client.send_message(
                                                bot_username,
                                                f'/start {start_param}'
                                            )
                                            logger.info("🎉 AutoJoinGame: Успешно отправлена команда /start (уведомление в чат не отправлено).")
                                            button_found = True
                                            break 
                                        except Exception as e:
                                            logger.error(f"❌ AutoJoinGame: Ошибка при отправке Deep-Link команды /start для сообщения {message.id}: {e}")
                                    else:
                                        logger.warning(f"⚠️ AutoJoinGame: Найдена кнопка '{button_text}' с URL '{button_url}', но она не является Deep-Link или режим Deep-Link неактивен. Пропускаю.")
                                else: 
                                    logger.info(f"📤 AutoJoinGame: Найдена кнопка '{button_text}' (CallbackQuery). Нажимаю.")
                                    try:
                                        await button.click()
                                        logger.info(f"🎉 AutoJoinGame: Успешно нажата кноп '{button_text}' для присоединения к игре.")
                                        button_found = True
                                        break 
                                    except Exception as e:
                                        logger.error(f"❌ AutoJoinGame: Ошибка при нажатии кнопки '{button_text}' для присоединения к игре: {e}")
                        if button_found:
                            break 

                    if not button_found:
                        logger.warning(f"⚠️ AutoJoinGame: Кнопка присоединения не найдена под сообщением {message.id} после задержки.")
            
        except Exception as e:
            logger.exception(f"❌ AutoJoinGame: Критическая ошибка в watcher для сообщения {getattr(message, 'id', 'N/A')} в чате {getattr(message, 'chat_id', 'N/A')}: {e}")
