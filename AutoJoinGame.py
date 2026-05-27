# meta developer: @yourhandle
# meta name: AutoJoinGame
# meta version: 2.4.17 # Версия обновлена для восстановления функций отслеживания ролей
# 01000001010101000100111101001010010011100010000001000111010000010100110101000101
# 0100000101010100010011110100100101001110001000000100011101000001
# 010011010100011001001110001000000100110101000100010101010100110001000111
import logging
import asyncio
import random
import urllib.parse
from datetime import datetime, timedelta
from telethon.tl.types import Message, User
from telethon.errors import RPCError
from telethon import events, functions
import re
from collections import defaultdict
from typing import Optional, List, Tuple
from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class AutoJoinGameMod(loader.Module):
    """Модуль для автоматического нажатия кнопки при наборе в игру в ботах мафии, а также подтверждения линчевания и повешения, и голосования за конкретного игрока. Дополнительно: пересылка роли в мафии в указанный чат, отслеживание определенных ролей (с разделением на активные/неактивные) и автоматическая отправка списка отслеживаемых ролей в чат после активации. Поддерживает автоматическую активацию и деактивацию отслеживания ролей по ключевым словам. Добавлены объединенные команды для управления закреплением/откреплением чатов и списком разрешенных чатов для модуля. Оптимизирована система отслеживания ролей для повышения стабильности и скорости. Добавлена возможность отправки списка отслеживаемых ролей в заранее указанный чат по команде, а также возможность указать конкретный чат для отслеживания ролей.""" # Restored _cls_doc

    strings = {
        "name": "AutoJoinGame",
        "_cls_doc": "Модуль для автоматического нажатия кнопки при наборе в игру в ботах мафии, а также подтверждения линчевания и повешения, и голосования за конкретного игрока. Дополнительно: пересылка роли в мафии в указанный чат, отслеживание определенных ролей (с разделением на активные/неактивные) и автоматическая отправка списка отслеживаемых ролей в чат после активации. Поддерживает автоматическую активацию и деактивацию отслеживания ролей по ключевым словам. Добавлены объединенные команды для управления закреплением/откреплением чатов и списком разрешенных чатов для модуля. Оптимизирована система отслеживания ролей для повышения стабильности и скорости. Добавлена возможность отправки списка отслеживаемых ролей в заранее указанный чат по команде, а также возможность указать конкретный чат для отслеживания ролей.", # Restored _cls_doc
        "enabled": "✅ Автовход в игру и автолинчевание включены.",
        "disabled": "❌ Автовход в игру и автолинчевание выключены.",
        "status": "<emoji document_id=5875291072225087249>📊</emoji> Статус автовхода и автолинчевания:\n"
                  "Статус: {}\n"
                  "Задержка входа (секунды): {}\n"
                  "Задержка линчевания (секунды): {}\n"
                  "Задержка выполнения команд (секунды): {}\n"
                  "Боты для отслеживания: {}\n"
                  "Разрешенные чаты для модуля: {}\n"
                  "Пользователи, разрешенные для настройки чатов и закрепления: {}\n"
                  "Конфигурации ключевых слов кнопок (сырые): {}\n"
                  "Активная конфигурация ключевых слов: {} (Ключевые слова: {})\n"
                  "Доступные ID конфигураций: {}\n"
                  "Режим Deep-Link: {}\n"
                  "Маркер линчевания для '👎': {}\n"
                  "Фразы-триггеры входа в игру: {}\n"
                  "Фразы-триггеры линчевания: {}\n"
                  "Фразы-триггеры повешения: {}\n"
                  "ID пользователя для линчевания игрока: {}\n"
                  "Фразы-триггеры голосования за игрока: {}\n"
                  "Последний ник игрока для линчевания: {}\n"
                  "\n<emoji document_id=5877485980901971030>📊</emoji> Статус пересылки роли:\n"
                  "Чат для пересылки роли: {}\n"
                  "Фразы-триггеры роли: {}\n"
                  "\n<emoji document_id=5771887475421090729>👤</emoji> Статус отслеживания ролей:\n"
                  "Отслеживание ролей: {}\n"
                  "Длительность отслеживания (секунды): {}\n"
                  "Фразы для отслеживаемых ролей: {} (Добавьте '(н)' в конце для неактивных ролей)\n"
                  "Фразы-триггеры объявления роли: {}\n"
                  "Отслеживаемых ролей найдено: {}\n"
                  "Время до окончания отслеживания: {}\n"
                  "Чат для отправки списка отслеживаемых ролей: {}\n"
                  "Задержка отправки списка отслеживаемых ролей (секунды): {}\n"
                  "Автоматическое включение отслеживания ролей (фразы): {}\n"
                  "Автоматическое включение отслеживания ролей (боты): {}\n"
                  "Автоматическое выключение отслеживания ролей (фразы): {}\n"
                  "Автоматическое выключение отслеживания ролей (боты): {}\n"
                  "Чат для вывода списка отслеживаемых ролей по команде: {}\n"
                  "Чат для отслеживания ролей: {}", # Restored from 2.4.15
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
<code>.ajgshowtrackedroles</code> - Показать список найденных отслеживаемых ролей. Если настроен <code>tracked_roles_display_chat_id</code>, список будет отправлен туда.
<code>.ajgset &lt;ID_конфига&gt;</code> - Переключить активную конфигурацию ключевых слов для кнопок. Если <code>&lt;ID_конфига&gt;</code> не указан, покажет текущую активную конфигурацию и доступные ID.
<code>.pinchat &lt;chat_id&gt;</code> - Закрепить чат в вашем списке диалогов И добавить его в разрешенные чаты модуля.
<code>.unpinchat &lt;chat_id&gt;</code> - Открепить чат из вашего списка диалогов И удалить его из разрешенных чатов модуля.
<code>.ajgpinchat &lt;chat_id&gt;</code> - Добавить ID чата только в список разрешенных чатов для модуля (<code>allowed_chats</code>).
<code>.ajgunpinchat &lt;chat_id&gt;</code> - Удалить ID чата только из списка разрешенных чатов для модуля (<code>allowed_chats</code>).

<emoji document_id=5877260593901971030>⚙</emoji> Как работает:
Ждет сообщение о наборе в игру или о голосовании (линчевание/повешение) от указанных ботов (или от любого бота, если список пуст).
Автоматически переходит по URL кнопки и отправляет /start для входа в игру.
Если бот спрашивает "Вы точно хотите линчевать..." или "Вы точно хотите повесить...", модуль автоматически нажмет кнопку.
Если в сообщении присутствует настроенный <code>lynch_target_marker</code> (по умолчанию 𝓝𝓚), модуль автоматически нажмет кнопку с эмодзи '👎'. В противном случае, если маркера нет, нажмет '👍'.
Работает только когда включен.
Дополнительно, если настроен <code>player_to_lynch_user_id</code>, модуль будет ожидать сообщение с ником игрока от этого пользователя. Как только ник получен, модуль будет искать сообщение о голосовании от *одного из ботов из списка* <code>bot_ids</code>, содержащее <code>lynch_player_voting_trigger_phrases</code>, и затем автоматически нажмет кнопку с соответствующим ником игрока.
<b>Важное обновление:</b> Если сообщение от <code>player_to_lynch_user_id</code> начинается с символа <code>!</code>, этот символ будет автоматически удален из ника игрока перед использованием.
<b>Обновление 2.4.0:</b> При линчевании конкретного игрока, модуль теперь будет искать ник игрока как <b>подстробу</b> в тексте кнопки (регистронезависимо), а не только как точное совпадение. Это позволяет корректно обрабатывать кнопки, содержащие никнейм игрока вместе с дополнительными символами.
<b>Новая функция:</b> Модуль может автоматически пересылать сообщения с вашей ролью в мафии в указанный чат. Это работает, когда бот отправляет вам роль в приватном чате, и сообщение содержит одну из настроенных фраз-триггеров.
<b>Улучшенная функция:</b> Модуль может отслеживать сообщения пользователей, объявляющих свою роль, и сохранять их ники и <b>конкретную объявленную роль</b> в список, если эта роль соответствует одной из настроенных фраз.
Отслеживание включается/выключается автоматически по настроенным фразам-триггерам от ботов, а его длительность настраивается в конфиге.
<b>Новая функция:</b> Модуль может автоматически отправлять список отслеживаемых ролей в указанный чат через заданное время после активации отслеживания ролей.
<b>Новая функция:</b> Модуль может автоматически включать отслеживание ролей при получении сообщения, содержащего определенные фразы, от указанных ботов.
<b>Новая функция:</b> Модуль может автоматически <b>выключать</b> отслеживание ролей при получении сообщения, содержащего определенные фразы, от указанных ботов.
<b>Улучшение:</b> Теперь модуль более точно определяет роли, включая составные фразы, и позволяет помечать роли как 'неактивные' с помощью суффикса <code>(н)</code> для раздельного отображения.
<b>Приоритет кнопок:</b> Теперь модуль отдает предпочтение кнопкам, содержащим <b>другие ключевые слова</b> из активной конфигурации, если на кнопке также есть слово "присоединиться". Кнопка с только "присоединиться" будет нажата только в том случае, если других подходящих кнопок не найдено.
<b>Объединенные команды:</b> <code>.pinchat &lt;chat_id&gt;</code> и <code>.unpinchat &lt;chat_id&gt;</code> теперь управляют как закреплением/откреплением чатов в вашем списке диалогов, так и списком разрешенных чатов модуля.
<b>Дополнительные команды:</b> <code>.ajgpinchat &lt;chat_id&gt;</code> и <code>.ajgunpinchat &lt;chat_id&gt;</code> позволяют управлять ТОЛЬКО списком разрешенных чатов (<code>allowed_chats</code>) для модуля без изменения закрепления в Telegram. Эти команды, как и объединенные команды, могут быть ограничены для использования определенными пользователями через настройку <code>pin_unpin_allowed_user_ids</code>.
<b>Новая функция:</b> Настройка <code>command_delay</code> позволяет установить задержку перед выполнением всех команд модуля.
<b>Оптимизация отслеживания ролей:</b> Система отслеживания ролей теперь работает более быстро и стабильно, а также добавляет роли сразу после объявления.
<b>Новая функция:</b> Настройка <code>tracked_roles_display_chat_id</code> позволяет указать ID чата, куда будет отправлен список отслеживаемых ролей по команде <code>.ajgshowtrackedroles</code>, независимо от того, в каком чате была вызвана команда.
<b>Новая функция:</b> Настройка <code>role_tracking_monitor_chat_id</code> позволяет указать ID чата, в котором модуль будет отслеживать объявления ролей пользователей. Если 0, отслеживание будет происходить во всех разрешенных чатах.
""", # Restored help_text
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

.cfg AutoJoinGame button_keyword_configs_string""",
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
        "tracked_roles_list": "<emoji document_id=5771887475421090729>👤</emoji> Список отслеживаемых ролей ({total_count} всего):\n\n{active_roles_section}\n\n{inactive_roles_section}",
        "active_roles_header": "🟢 Активные роли (найдено {count}):",
        "inactive_roles_header": "🔴 Неактивные роли (найдено {count}):",
        "no_active_roles": "🟢 Активные роли: Пока не найдено ни одной активной роли.",
        "no_inactive_roles": "🔴 Неактивные роли: Пока не найдено ни одной неактивной роли.",
        "role_tracked_success_with_status": "✅ Отслеживание ролей: Пользователь <code>{nickname}</code> (Роль: {role}, Статус: {status}) добавлен в список отслеживаемых ролей.",
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
        "auto_disable_track_roles_trigger_phrases_display": "(пусто)",
        "auto_disable_track_roles_bot_ids_display": "Не указаны (любой бот)",
        "auto_role_tracking_deactivated": "<emoji document_id=5944122171441618396>❌</emoji> Автоматическое отслеживание ролей выключено.",
        "switch_keywords_success": "✅ Активная конфигурация ключевых слов переключена на <code>{config_id}</code>. Теперь используются ключевые слова: {keywords}",
        "switch_keywords_not_found": "⚠️ Конфигурация с ID <code>{config_id}</code> не найдена. Доступные ID: {available_ids}.",
        "switch_keywords_no_configs": "⚠️ Нет настроенных конфигураций ключевых слов. Используйте <code>.cfg AutoJoinGame button_keyword_configs_string</code> для настройки.",
        "switch_keywords_current": "ℹ️ Активная конфигурация уже <code>{config_id}</code>.",
        "switch_keywords_usage": "ℹ️ Текущая активная конфигурация: <code>{current_id}</code>. Ключевые слова: {current_keywords}\nДоступные ID: {available_ids}.\nИспользуйте <code>.ajgset &lt;ID_конфига&gt;</code> для переключения.",

        # --- NEW/UPDATED Strings for unified pin/unpin commands ---
        "common_invalid_chat_id": "❌ Неверный ID чата. Пожалуйста, укажите числовой ID.",
        "not_allowed_to_configure_chats": "❌ У вас нет разрешения на изменение списка разрешенных чатов или управление закреплением/откреплением чатов.",

        # Для закрепления/открепления чатов в Telegram (как в PinChat.py)
        "dialog_pin_unpin_start_msg": "⏳ Пытаюсь {action_text_verb} чат <code>{chat_id}</code> в вашем списке диалогов...",
        "dialog_chat_not_found_or_inaccessible": "❌ Чат с ID <code>{chat_id}</code> не найден или недоступен для закрепления/открепления в вашем списке диалогов.",
        "dialog_pin_success": "✅ Чат <code>{chat_id}</code> успешно закреплен в вашем списке диалогов.",
        "dialog_pin_already_pinned": "ℹ️ Чат <code>{chat_id}</code> уже закреплен в вашем списке диалогов.",
        "dialog_pin_fail": "❌ Не удалось закрепить чат <code>{chat_id}</code> в диалогах: {error}",
        "dialog_unpin_success": "✅ Чат <code>{chat_id}</code> успешно откреплен из вашего списка диалогов.",
        "dialog_unpin_not_pinned": "ℹ️ Чат <code>{chat_id}</code> не закреплен в вашем списке диалогов.",
        "dialog_unpin_fail": "❌ Не удалось открепить чат <code>{chat_id}</code> из диалогов: {error}",
        "dialog_pin_no_args": "⚠️ Укажите ID чата для закрепления. Пример: <code>.pinchat -1001234567890</code>",
        "dialog_unpin_no_args": "⚠️ Укажите ID чата для открепления. Пример: <code>.unpinchat -1001234567890</code>",

        # Для параметра allowed_chats модуля
        "module_add_allowed_chat_success": "✅ Чат <code>{chat_id}</code> успешно добавлен в список разрешенных чатов модуля.",
        "module_add_allowed_chat_already_added": "⚠️ Чат <code>{chat_id}</code> уже находится в списке разрешенных чатов модуля.",
        "module_remove_allowed_chat_success": "✅ Чат <code>{chat_id}</code> успешно удален из списка разрешенных чатов модуля.",
        "module_remove_allowed_chat_not_found": "⚠️ Чат <code>{chat_id}</code> не найден в списке разрешенных чатов модуля.",

        # Комбинированные результаты для команд .pinchat / .unpinchat
        "command_result_template": "Результаты для чата <code>{chat_id}</code>:\n• {dialog_action_result}\n• {module_action_result}",
        "ajg_only_action_start_msg": "⏳ Пытаюсь {action_text_verb} чат <code>{chat_id}</code> в списке разрешенных чатов модуля...",
        "pin_unpin_allowed_user_ids_display": "Не указаны (любой пользователь)",

        # NEW: Strings for tracked_roles_display_chat_id
        "tracked_roles_display_chat_id_display": "Отключено (0)",
        "tracked_roles_sent_to_configured_chat": "✅ Список отслеживаемых ролей отправлен в чат <code>{chat_id}</code>.",
        "tracked_roles_send_error_to_configured_chat": "❌ Ошибка при отправке списка отслеживаемых ролей в настроенный чат <code>{chat_id}</code>: {error}. Отправляю сюда.",
        "tracked_roles_sent_to_current_chat_fallback": "ℹ️ Отправляю список в текущий чат из-за ошибки или неактивной настройки.",

        # NEW: Strings for role_tracking_monitor_chat_id
        "role_tracking_monitor_chat_id_display": "Во всех разрешенных чатах (0)",
    }

    def __init__(self):
        super().__init__()
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
                "command_delay",
                0.0,
                lambda: "Задержка в секундах перед выполнением команды. Если 0, задержки нет. Поддерживает дробные значения.",
                validator=loader.validators.Float(minimum=0.0, maximum=10.0)
            ),
            loader.ConfigValue(
                "bot_ids",
                [],
                lambda: "Список ID ботов, от которых ожидается сообщение о наборе в игру, линчевании, повешении или голосовании за игрока. Если список пуст, сообщения будут отслеживаться от любого бота.",
                validator=loader.validators.Series(loader.validators.Integer())
            ),
            loader.ConfigValue(
                "allowed_chats",
                [],
                lambda: "Список ID чатов, в которых модуль будет активен. Если список пуст, модуль будет работать во всех чатах.",
                validator=loader.validators.Series(loader.validators.Integer())
            ),
            loader.ConfigValue(
                "pin_unpin_allowed_user_ids",
                [],
                lambda: "Список ID пользователей, которым разрешено использовать команды, связанные с изменением allowed_chats и закреплением/откреплением диалогов. Если список пуст, эти команды могут использовать все пользователи.",
                validator=loader.validators.Series(loader.validators.Integer())
            ),
            loader.ConfigValue(
                "button_keyword_configs_string",
                "присоединиться (default), играть (default), 🙋 (default), 🎮 (default), ✅ (default), 🌚 (default)",
                lambda: "Строка с конфигурациями ключевых слов для кнопок. Формат: 'Ключевое слово (ID_конфига), Другое слово (Другой_ID)'. Например: 'присоединиться (1), играть (1), 🙋 (2), 🎮 (2)'. Ключевые слова регистронезависимы. Скобки с ID не учитываются при поиске кнопок.",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "active_button_config_id",
                "default",
                lambda: "ID активной конфигурации ключевых слов из 'button_keyword_configs_string'. Например: '1' или 'default'.",
                validator=loader.validators.String()
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
                lambda: "Список фраз, которые модуль будет искать в сообщениях для активации автовхода в игру.",
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
                "lynch_player_voting_trigger_phrases",
                ["Пришло время искать виноватых!", "Кого ты хочешь повесить?", "Пришло время определить и наказать виновных", "Пришло время искать виноватых! Кого ты хочешь линчевать?"],
                lambda: "Список фраз, которые модуль будет искать в сообщениях от ботов (из bot_ids) для активации голосования за конкретного игрока.",
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
            # --- Re-added Role Tracking Configs from 2.4.15 ---
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
                ["мирный житель", "мафия (н)"],
                lambda: "Список фраз, указывающих на роли, которые нужно отслеживать. Модуль будет искать эти фразы в объявлениях ролей пользователей. Если роль должна быть 'неактивной', добавьте к ней суффикса '(н)', например: ['мирный житель', 'мафия (н)', 'комиссар'].",
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
            loader.ConfigValue(
                "auto_disable_track_roles_trigger_phrases",
                [],
                lambda: "Список фраз, которые модуль будет искать в сообщениях для автоматического выключения отслеживания ролей.",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                "auto_disable_track_roles_bot_ids",
                [],
                lambda: "Список ID ботов, от которых ожидается сообщение с фразами для автоматического выключения отслеживания ролей. Если список пуст, сообщения будут отслеживаться от любого бота.",
                validator=loader.validators.Series(loader.validators.Integer())
            ),
            loader.ConfigValue(
                "tracked_roles_display_chat_id",
                0,
                lambda: "ID чата, куда будет отправляться список найденных отслеживаемых ролей по команде .ajgshowtrackedroles. Если 0, список будет отправлен в текущий чат.",
                validator=loader.validators.Integer(minimum=0)
            ),
            loader.ConfigValue(
                "role_tracking_monitor_chat_id",
                0, # Default to 0 (monitor in any allowed chat)
                lambda: "ID чата, в котором модуль будет отслеживать объявления ролей пользователей. Если 0, отслеживание будет происходить во всех разрешенных чатах.",
                validator=loader.validators.Integer(minimum=0)
            ),
        )

        self._player_nickname_to_lynch = None
        self._role_tracking_active = False # Re-added
        self._role_tracking_start_time = None # Re-added
        self._tracked_roles_list = [] # Stores (sender_id, nickname, role_text, is_active) for display # Re-added
        self._tracked_roles_lookup_set: set[Tuple[int, str]] = set() # Stores (sender_id, role_text) for quick duplicate checks # Re-added
        self._compiled_tracked_role_patterns: List[Tuple[re.Pattern, str, bool]] = [] # (compiled_regex, clean_role_text, is_active) # Re-added
        self._self_id = None
        self._processed_messages = set()
        self._processed_messages_cleanup_task = None
        self._send_tracked_roles_task = None # Re-added

        self._parsed_button_keywords: dict[str, list[str]] = {}
        self._current_button_keywords_to_use: list[str] = []

    async def client_ready(self, client, _):
        self._client = client
        self._self_id = (await self._client.get_me()).id
        if self._processed_messages_cleanup_task is None:
            self._processed_messages_cleanup_task = asyncio.create_task(self._cleanup_processed_messages_loop())

        # Инициализация при запуске, важно, чтобы всегда были актуальные keywords
        self._update_button_keywords_from_config()
        self._update_tracked_roles_patterns() # Re-added: Initialize/update role patterns

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

        if self._send_tracked_roles_task: # Re-added
            self._send_tracked_roles_task.cancel()
            try:
                await self._send_tracked_roles_task
            except asyncio.CancelledError:
                logger.debug("AutoJoinGame: Задача отправки списка отслеживаемых ролей отменена при выгрузке.")

        self._tracked_roles_lookup_set.clear() # Re-added
        self._compiled_tracked_role_patterns.clear() # Re-added

    def _update_tracked_roles_patterns(self): # Re-added
        """Compiles regex patterns for tracked roles from config for faster lookup."""
        self._compiled_tracked_role_patterns = []
        for tracked_role_phrase_raw in self.config["tracked_roles_to_monitor"]:
            role_to_match_lower = tracked_role_phrase_raw.lower()
            current_is_active = True

            if role_to_match_lower.endswith("(н)"):
                current_is_active = False
                role_to_match_lower = role_to_match_lower[:-3].strip()

            parts = role_to_match_lower.split()
            # Use \s+ to match one or more whitespace characters, consistent with original implicit behavior
            escaped_parts = [re.escape(p) for p in parts]
            internal_pattern = r"\b" + r"\s+".join(escaped_parts) + r"\b"

            try:
                # Compile once, case-insensitive for robustness
                compiled_pattern = re.compile(internal_pattern, re.IGNORECASE)
                self._compiled_tracked_role_patterns.append((compiled_pattern, role_to_match_lower, current_is_active))
            except re.error as e:
                logger.error(f"AutoJoinGame: Ошибка компиляции регулярного выражения для роли '{tracked_role_phrase_raw}': {e}")

        logger.debug(f"AutoJoinGame: Обновлены шаблоны отслеживаемых ролей. Всего {len(self._compiled_tracked_role_patterns)} шаблонов.")

    def _parse_button_keywords_string(self, config_string: str) -> dict[str, list[str]]:
        """Парсит строку конфигурации ключевых слов кнопок в словарь."""
        parsed_configs = defaultdict(list)
        entries = [e.strip() for e in config_string.split(',')]

        for entry in entries:
            # Убеждаемся, что парсим только ключевое слово и ID, игнорируя остальное
            match = re.match(r"(.+?)\s*\(([\w\d]+)\)", entry)
            if match:
                keyword_part = match.group(1).strip()
                config_id = match.group(2).strip()
                parsed_configs[config_id].append(keyword_part.lower())
            elif entry:
                logger.warning(f"AutoJoinGame: Не удалось разобрать часть конфига 'button_keyword_configs_string': '{entry}'. Ожидается формат 'Ключевое слово (ID_конфига)'. Пропускаю.")
        return dict(parsed_configs)

    def _update_button_keywords_from_config(self):
        """Обновляет активные ключевые слова на основе конфига."""
        self._parsed_button_keywords = self._parse_button_keywords_string(self.config["button_keyword_configs_string"])

        active_id = self.config["active_button_config_id"]

        if active_id and active_id in self._parsed_button_keywords:
            self._current_button_keywords_to_use = self._parsed_button_keywords[active_id]
            logger.info(f"AutoJoinGame: Активная конфигурация ключевых слов кнопок установлена на '{active_id}'. Используются ключевые слова: {self._current_button_keywords_to_use}")
        elif self._parsed_button_keywords:
            # Если активный ID не задан или не найден, пробуем использовать первый доступный
            first_id = next(iter(self._parsed_button_keywords))
            # Используем self.set() для сохранения изменения в конфиг, и обновляем self.config
            self.set("active_button_config_id", first_id)
            self.config["active_button_config_id"] = first_id # Явно обновляем in-memory config
            self._current_button_keywords_to_use = self._parsed_button_keywords[first_id]
            logger.warning(f"AutoJoinGame: Активная конфигурация ключевых слов кнопок '{active_id}' не найдена или не установлена. Установлено на первую доступную: '{first_id}'.")
        else:
            self._current_button_keywords_to_use = []
            self.set("active_button_config_id", "") # Очищаем, если нет конфигов
            self.config["active_button_config_id"] = "" # Явно обновляем in-memory config
            logger.warning("AutoJoinGame: Нет настроенных конфигураций ключевых слов кнопок. Модуль не будет активировать кнопки по ключевым словам.")


    def _get_user_nickname(self, user: User) -> str: # Re-added
        """Получает никнейм пользователя, предпочитая имя и фамилию."""
        if user.first_name and user.last_name:
            return f"{user.first_name} {user.last_name}"
        if user.first_name:
            return user.first_name
        if user.username:
            return user.username
        return f"Неизвестный пользователь"

    async def _send_tracked_roles_list_scheduled(self, delay: int, chat_id: int): # Re-added
        """Задача для отправки списка отслеживаемых ролей через заданное время."""
        try:
            await asyncio.sleep(delay)
            if not self.config["role_tracking_enabled"] or not self._role_tracking_active:
                logger.debug("AutoJoinGame: Отправка списка отслеживаемых ролей отменена, так как отслеживание неактивно.")
                return

            active_roles_display = []
            inactive_roles_display = []

            for _, nickname, role_text, is_active in self._tracked_roles_list:
                if is_active:
                    active_roles_display.append(f"• <code>{nickname}</code> (Роль: {role_text})")
                else:
                    inactive_roles_display.append(f"• <code>{nickname}</code> (Роль: {role_text})")

            active_section = self.strings("no_active_roles")
            if active_roles_display:
                active_section = self.strings("active_roles_header").format(count=len(active_roles_display)) + "\n" + "\n".join(active_roles_display)

            inactive_section = self.strings("no_inactive_roles")
            if inactive_roles_display:
                inactive_section = self.strings("inactive_roles_header").format(count=len(inactive_roles_display)) + "\n" + "\n".join(inactive_roles_display)

            message_text = self.strings("tracked_roles_list").format(
                total_count=len(self._tracked_roles_list),
                active_roles_section=active_section,
                inactive_roles_section=inactive_section
            )

            await self._client.send_message(chat_id, message_text)
            logger.info(self.strings("tracked_roles_send_success").format(chat_id=chat_id))

        except asyncio.CancelledError:
            logger.debug("AutoJoinGame: Задача по отправке списка отслеживаемых ролей отменена.")
        except Exception as e:
            logger.error(self.strings("tracked_roles_send_error").format(chat_id=chat_id, error=e))

    async def _toggle_telegram_dialog_pin(self, chat_id: int, pin_action: bool) -> tuple[bool, str]:
        """
        Toggles the pin status of a Telegram dialog.
        Returns (success_status: bool, result_message: str).
        """
        action_text_verb = "закрепить" if pin_action else "открепить"

        try:
            entity = await self._client.get_entity(chat_id)
        except (ValueError, TypeError):
            logger.error(f"AutoJoinGame: Чат с ID {chat_id} не найден или недоступен для закрепления/открепления в Telegram.")
            return False, self.strings("dialog_chat_not_found_or_inaccessible").format(chat_id=chat_id)
        except Exception as e:
            logger.error(f"AutoJoinGame: Ошибка при получении сущности чата {chat_id} для Telegram pinning: {e}", exc_info=True)
            return False, self.strings("dialog_chat_not_found_or_inaccessible").format(chat_id=chat_id)

        try:
            target_dialog = None
            async for dialog in self._client.iter_dialogs():
                if dialog.id == chat_id:
                    target_dialog = dialog
                    break

            if not target_dialog:
                return False, self.strings("dialog_chat_not_found_or_inaccessible").format(chat_id=chat_id)

            is_currently_pinned = target_dialog.pinned

            if pin_action:
                if is_currently_pinned:
                    return False, self.strings("dialog_pin_already_pinned").format(chat_id=chat_id)
                await self._client(functions.messages.ToggleDialogPinRequest(
                    peer=target_dialog.entity,
                    pinned=True
                ))
                return True, self.strings("dialog_pin_success").format(chat_id=chat_id)
            else:
                if not is_currently_pinned:
                    return False, self.strings("dialog_unpin_not_pinned").format(chat_id=chat_id)
                await self._client(functions.messages.ToggleDialogPinRequest(
                    peer=target_dialog.entity,
                    pinned=False
                ))
                return True, self.strings("dialog_unpin_success").format(chat_id=chat_id)

        except RPCError as e:
            logger.error(f"AutoJoinGame: Ошибка Telethon RPC при {action_text_verb} чата {chat_id} в Telegram: {e}", exc_info=True)
            return False, self.strings("dialog_pin_fail").format(chat_id=chat_id, error=e) if pin_action else self.strings("dialog_unpin_fail").format(chat_id=chat_id, error=e)
        except Exception as e:
            logger.exception(f"AutoJoinGame: Неожиданная ошибка при {action_text_verb} чата {chat_id} в Telegram: {e}")
            return False, self.strings("dialog_pin_fail").format(chat_id=chat_id, error=e) if pin_action else self.strings("dialog_unpin_fail").format(chat_id=chat_id, error=e)

    def _toggle_module_allowed_chat(self, chat_id: int, add_action: bool) -> tuple[bool, str]:
        """
        Adds or removes a chat ID from the module's allowed_chats configuration.
        Returns (success_status: bool, result_message: str).
        """
        current_allowed_chats = self.config["allowed_chats"].copy()

        if add_action:
            if chat_id in current_allowed_chats:
                return False, self.strings("module_add_allowed_chat_already_added").format(chat_id=chat_id)

            current_allowed_chats.append(chat_id)
            self.set("allowed_chats", current_allowed_chats)
            self.config["allowed_chats"] = current_allowed_chats
            return True, self.strings("module_add_allowed_chat_success").format(chat_id=chat_id)
        else:
            if chat_id not in current_allowed_chats:
                return False, self.strings("module_remove_allowed_chat_not_found").format(chat_id=chat_id)

            current_allowed_chats.remove(chat_id)
            self.set("allowed_chats", current_allowed_chats)
            self.config["allowed_chats"] = current_allowed_chats
            return True, self.strings("module_remove_allowed_chat_success").format(chat_id=chat_id)

    @loader.command(ru_doc="Закрепить чат в вашем списке диалогов И добавить его в разрешенные чаты модуля.")
    async def pinchat(self, message: Message):
        """
        Закрепляет чат в вашем списке диалогов И добавляет его в разрешенные чаты модуля.
        Использование: .pinchat <chat_id>
        Пример: .pinchat -1001234567890
        """
        if self.config["command_delay"] > 0:
            await asyncio.sleep(self.config["command_delay"])

        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("dialog_pin_no_args"))
            return

        try:
            target_chat_id = int(args)
        except ValueError:
            await utils.answer(message, self.strings("common_invalid_chat_id"))
            return

        sender = await message.get_sender()
        sender_id = getattr(sender, 'id', None)
        allowed_users = self.config["pin_unpin_allowed_user_ids"]
        if allowed_users and sender_id not in allowed_users:
            await utils.answer(message, self.strings("not_allowed_to_configure_chats"))
            return

        # 1. Выполняем действие по закреплению чата в Telegram
        # Сначала показываем сообщение о попытке
        await utils.answer(message, self.strings("dialog_pin_unpin_start_msg").format(action_text_verb="закрепить", chat_id=target_chat_id))
        dialog_pin_success, dialog_pin_msg = await self._toggle_telegram_dialog_pin(target_chat_id, True)

        # 2. Выполняем действие по добавлению чата в allowed_chats модуля
        module_add_success, module_add_msg = self._toggle_module_allowed_chat(target_chat_id, True)

        # Комбинируем результаты
        final_message = self.strings("command_result_template").format(
            chat_id=target_chat_id,
            dialog_action_result=dialog_pin_msg,
            module_action_result=module_add_msg
        )
        await utils.answer(message, final_message)

    @loader.command(ru_doc="Открепить чат из вашего списка диалогов И удалить его из разрешенных чатов модуля.")
    async def unpinchat(self, message: Message):
        """
        Открепляет чат из вашего списка диалогов И удаляет его из разрешенных чатов модуля.
        Использование: .unpinchat <chat_id>
        Пример: .unpinchat -1001234567890
        """
        if self.config["command_delay"] > 0:
            await asyncio.sleep(self.config["command_delay"])

        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("dialog_unpin_no_args"))
            return

        try:
            target_chat_id = int(args)
        except ValueError:
            await utils.answer(message, self.strings("common_invalid_chat_id"))
            return

        sender = await message.get_sender()
        sender_id = getattr(sender, 'id', None)
        allowed_users = self.config["pin_unpin_allowed_user_ids"]
        if allowed_users and sender_id not in allowed_users:
            await utils.answer(message, self.strings("not_allowed_to_configure_chats"))
            return

        # 1. Выполняем действие по откреплению чата из Telegram
        # Сначала показываем сообщение о попытке
        await utils.answer(message, self.strings("dialog_pin_unpin_start_msg").format(action_text_verb="открепить", chat_id=target_chat_id))
        dialog_unpin_success, dialog_unpin_msg = await self._toggle_telegram_dialog_pin(target_chat_id, False)

        # 2. Выполняем действие по удалению чата из allowed_chats модуля
        module_remove_success, module_remove_msg = self._toggle_module_allowed_chat(target_chat_id, False)

        # Комбинируем результаты
        final_message = self.strings("command_result_template").format(
            chat_id=target_chat_id,
            dialog_action_result=dialog_unpin_msg,
            module_action_result=module_remove_msg
        )
        await utils.answer(message, final_message)

    # --- Команды для управления ТОЛЬКО allowed_chats модуля (переименованы и уточнены) ---
    @loader.command(ru_doc="Добавить ID чата только в список разрешенных чатов для модуля (allowed_chats).")
    async def ajgpinchat(self, message: Message):
        """Добавить ID чата только в список разрешенных чатов модуля (без изменения закрепления в Telegram)."""
        if self.config["command_delay"] > 0:
            await asyncio.sleep(self.config["command_delay"])

        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("common_invalid_chat_id"))
            return

        try:
            target_chat_id = int(args)
        except ValueError:
            await utils.answer(message, self.strings("common_invalid_chat_id"))
            return

        sender = await message.get_sender()
        sender_id = getattr(sender, 'id', None)
        allowed_users = self.config["pin_unpin_allowed_user_ids"]
        if allowed_users and sender_id not in allowed_users:
            await utils.answer(message, self.strings("not_allowed_to_configure_chats"))
            return

        await utils.answer(message, self.strings("ajg_only_action_start_msg").format(action_text_verb="добавить", chat_id=target_chat_id))
        _, result_msg = self._toggle_module_allowed_chat(target_chat_id, True)
        await utils.answer(message, result_msg)

    @loader.command(ru_doc="Удалить ID чата только из списка разрешенных чатов для модуля (allowed_chats).")
    async def ajgunpinchat(self, message: Message):
        """Удалить ID чата только из списка разрешенных чатов модуля (без изменения закрепления в Telegram)."""
        if self.config["command_delay"] > 0:
            await asyncio.sleep(self.config["command_delay"])

        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("common_invalid_chat_id"))
            return

        try:
            target_chat_id = int(args)
        except ValueError:
            await utils.answer(message, self.strings("common_invalid_chat_id"))
            return

        sender = await message.get_sender()
        sender_id = getattr(sender, 'id', None)
        allowed_users = self.config["pin_unpin_allowed_user_ids"]
        if allowed_users and sender_id not in allowed_users:
            await utils.answer(message, self.strings("not_allowed_to_configure_chats"))
            return

        await utils.answer(message, self.strings("ajg_only_action_start_msg").format(action_text_verb="удалить", chat_id=target_chat_id))
        _, result_msg = self._toggle_module_allowed_chat(target_chat_id, False)
        await utils.answer(message, result_msg)


    @loader.command(ru_doc="Включить автовход в игру и автолинчевание")
    async def ajgon(self, message: Message):
        """Включить автовход в игру и автолинчевание"""
        if self.config["command_delay"] > 0:
            await asyncio.sleep(self.config["command_delay"])
        self.set("enabled", True)
        self.config["enabled"] = True
        await utils.answer(message, self.strings("enabled"))

    @loader.command(ru_doc="Выключить автовход в игру и автолинчевание")
    async def ajgoff(self, message: Message):
        """Выключить автовход в игру и автолинчевание"""
        if self.config["command_delay"] > 0:
            await asyncio.sleep(self.config["command_delay"])
        self.set("enabled", False)
        self.config["enabled"] = False
        self._player_nickname_to_lynch = None
        self.set("role_tracking_enabled", False) # Re-added
        self.config["role_tracking_enabled"] = False # Re-added
        self._role_tracking_active = False # Re-added
        self._role_tracking_start_time = None # Re-added
        self._tracked_roles_list = [] # Re-added
        self._tracked_roles_lookup_set.clear() # Re-added
        self._processed_messages.clear()
        if self._send_tracked_roles_task: # Re-added
            self._send_tracked_roles_task.cancel()
            self._send_tracked_roles_task = None
        await utils.answer(message, self.strings("disabled"))

    @loader.command(ru_doc="Показать список найденных отслеживаемых ролей") # Re-added command
    async def ajgshowtrackedroles(self, message: Message):
        """Показать список найденных отслеживаемых ролей. Если настроен tracked_roles_display_chat_id, список будет отправлен туда."""
        if self.config["command_delay"] > 0:
            await asyncio.sleep(self.config["command_delay"])
        active_roles_display = []
        inactive_roles_display = []

        for _, nickname, role_text, is_active in self._tracked_roles_list:
            if is_active:
                active_roles_display.append(f"• <code>{nickname}</code> (Роль: {role_text})")
            else:
                inactive_roles_display.append(f"• <code>{nickname}</code> (Роль: {role_text})")

        active_section = self.strings("no_active_roles")
        if active_roles_display:
            active_section = self.strings("active_roles_header").format(count=len(active_roles_display)) + "\n" + "\n".join(active_roles_display)

        inactive_section = self.strings("no_inactive_roles")
        if inactive_roles_display:
            inactive_section = self.strings("inactive_roles_header").format(count=len(inactive_roles_display)) + "\n" + "\n".join(inactive_roles_display)

        message_text = self.strings("tracked_roles_list").format(
            total_count=len(self._tracked_roles_list),
            active_roles_section=active_section,
            inactive_roles_section=inactive_section
        )

        display_chat_id = self.config["tracked_roles_display_chat_id"]
        if display_chat_id != 0:
            try:
                await self._client.send_message(display_chat_id, message_text)
                await utils.answer(message, self.strings("tracked_roles_sent_to_configured_chat").format(chat_id=display_chat_id))
            except Exception as e:
                logger.error(f"AutoJoinGame: Ошибка при отправке списка отслеживаемых ролей в настроенный чат {display_chat_id}: {e}")
                await utils.answer(message, self.strings("tracked_roles_send_error_to_configured_chat").format(chat_id=display_chat_id, error=e))
                await utils.answer(message, self.strings("tracked_roles_sent_to_current_chat_fallback"))
                await utils.answer(message, message_text) # Fallback to current chat
        else:
            await utils.answer(message, message_text)


    @loader.command(ru_doc="Переключить активную конфигурацию ключевых слов для кнопок. Если ID_конфига не указан, покажет текущую активную конфигурацию и доступные ID.")
    async def ajgset(self, message: Message):
        """Переключить активную конфигурацию ключевых слов для кнопок.
        Пример: .ajgset 1
        Используйте без аргументов, чтобы увидеть текущую активную конфигурацию и доступные ID."""
        if self.config["command_delay"] > 0:
            await asyncio.sleep(self.config["command_delay"])

        config_id = utils.get_args_raw(message)

        if not self._parsed_button_keywords:
            await utils.answer(message, self.strings("switch_keywords_no_configs"))
            return

        available_ids = ", ".join(self._parsed_button_keywords.keys())

        if not config_id:
            current_active_id = self.config["active_button_config_id"]
            current_keywords = ", ".join(self._current_button_keywords_to_use)
            await utils.answer(message, self.strings("switch_keywords_usage").format(
                current_id=current_active_id,
                current_keywords=current_keywords,
                available_ids=available_ids
            ))
            return

        if config_id == self.config["active_button_config_id"]:
            await utils.answer(message, self.strings("switch_keywords_current").format(config_id=config_id))
            return

        if config_id in self._parsed_button_keywords:
            self.set("active_button_config_id", config_id)
            self.config["active_button_config_id"] = config_id
            self._update_button_keywords_from_config()
            await utils.answer(message, self.strings("switch_keywords_success").format(
                config_id=config_id,
                keywords=", ".join(self._current_button_keywords_to_use)
            ))
        else:
            await utils.answer(message, self.strings("switch_keywords_not_found").format(
                config_id=config_id,
                available_ids=available_ids if available_ids else "нет"
            ))

    @loader.command(ru_doc="Показать статус автовхода и автолинчевания")
    async def ajgstatus(self, message: Message):
        """Показать статус автовхода и автолинчевания"""
        if self.config["command_delay"] > 0:
            await asyncio.sleep(self.config["command_delay"])
        status = "🟢 Включен" if self.config["enabled"] else "🔴 Выключен"

        delays = self.config["delays"]
        delay_display = f"[{', '.join(map(str, delays))}]" if len(delays) > 1 else str(delays[0])

        lynch_delays = self.config["lynch_delay"]
        lynch_delay_display = f"[{', '.join(map(str, lynch_delays))}]" if len(lynch_delays) > 1 else str(lynch_delays[0])

        command_delay_display = str(self.config["command_delay"])

        bot_ids_display = ", ".join(map(str, self.config["bot_ids"])) if self.config["bot_ids"] else "Не указаны (любой бот)"

        allowed_chats = self.config["allowed_chats"]
        allowed_chats_display = ", ".join(map(str, allowed_chats)) if allowed_chats else "Все чаты"

        pin_unpin_allowed_user_ids_display = ", ".join(map(str, self.config["pin_unpin_allowed_user_ids"])) if self.config["pin_unpin_allowed_user_ids"] else self.strings("pin_unpin_allowed_user_ids_display")

        button_keyword_configs_string_display = self.config["button_keyword_configs_string"] if self.config["button_keyword_configs_string"] else "(пусто)"
        active_button_config_id_display = self.config["active_button_config_id"] if self.config["active_button_config_id"] else "(не задан)"
        current_button_keywords_display = ", ".join(self._current_button_keywords_to_use) if self._current_button_keywords_to_use else "(пусто)"
        available_config_ids_display = ", ".join(self._parsed_button_keywords.keys()) if self._parsed_button_keywords else "(нет)"

        deep_link_status_display = "🟢 Активен (автоматически обрабатывает Deep-Link URL, если они есть у подходящих кнопок)"

        lynch_target_marker_display = self.config["lynch_target_marker"] if self.config["lynch_target_marker"] else "(пусто)"

        game_join_trigger_phrases_display = ", ".join(self.config["game_join_trigger_phrases"]) if self.config["game_join_trigger_phrases"] else "(пусто)"
        lynch_trigger_phrases_display = ", ".join(self.config["lynch_trigger_phrases"]) if self.config["lynch_trigger_phrases"] else "(пусто)"
        lynch_hang_trigger_phrases_display = ", ".join(self.config["lynch_hang_trigger_phrases"]) if self.config["lynch_hang_trigger_phrases"] else "(пусто)"

        player_to_lynch_user_id_display = str(self.config["player_to_lynch_user_id"]) if self.config["player_to_lynch_user_id"] else "Отключено (0)"
        lynch_player_voting_trigger_phrases_display = ", ".join(self.config["lynch_player_voting_trigger_phrases"]) if self.config["lynch_player_voting_trigger_phrases"] else "(пусто)"
        current_player_nickname_display = self._player_nickname_to_lynch if self._player_nickname_to_lynch else "(нет)"

        role_forward_chat_id_display = str(self.config["role_forward_chat_id"]) if self.config["role_forward_chat_id"] else self.strings("role_forward_chat_id_display")
        role_trigger_phrases_display = ", ".join(self.config["role_trigger_phrases"]) if self.config["role_trigger_phrases"] else self.strings("role_forward_trigger_phrases_display")

        # --- Re-added Role Tracking Status Display from 2.4.15 ---
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

        auto_disable_track_roles_trigger_phrases_display = ", ".join(self.config["auto_disable_track_roles_trigger_phrases"]) if self.config["auto_disable_track_roles_trigger_phrases"] else self.strings("auto_disable_track_roles_trigger_phrases_display")
        auto_disable_track_roles_bot_ids_display = ", ".join(map(str, self.config["auto_disable_track_roles_bot_ids"])) if self.config["auto_disable_track_roles_bot_ids"] else self.strings("auto_disable_track_roles_bot_ids_display")

        tracked_roles_display_chat_id_formatted = str(self.config["tracked_roles_display_chat_id"]) if self.config["tracked_roles_display_chat_id"] else self.strings("tracked_roles_display_chat_id_display")

        role_tracking_monitor_chat_id_formatted = str(self.config["role_tracking_monitor_chat_id"]) if self.config["role_tracking_monitor_chat_id"] else self.strings("role_tracking_monitor_chat_id_display")


        await utils.answer(message, self.strings("status").format(
            status,
            delay_display,
            lynch_delay_display,
            command_delay_display,
            bot_ids_display,
            allowed_chats_display,
            pin_unpin_allowed_user_ids_display,
            button_keyword_configs_string_display,
            active_button_config_id_display,
            current_button_keywords_display,
            available_config_ids_display,
            deep_link_status_display,
            lynch_target_marker_display,
            game_join_trigger_phrases_display,
            lynch_trigger_phrases_display,
            lynch_hang_trigger_phrases_display,
            player_to_lynch_user_id_display,
            lynch_player_voting_trigger_phrases_display,
            current_player_nickname_display,
            role_forward_chat_id_display,
            role_trigger_phrases_display,
            # --- Re-added Role Tracking Status fields ---
            role_tracking_status,
            role_tracking_duration_display,
            tracked_roles_to_monitor_display,
            role_announcement_phrases_display,
            tracked_roles_count,
            time_remaining_display,
            send_tracked_roles_chat_id_display,
            send_tracked_roles_delay_display,
            auto_track_roles_trigger_phrases_display,
            auto_track_roles_bot_ids_display,
            auto_disable_track_roles_trigger_phrases_display,
            auto_disable_track_roles_bot_ids_display,
            tracked_roles_display_chat_id_formatted,
            role_tracking_monitor_chat_id_formatted,
        ))

    @loader.command(ru_doc="Показать справку")
    async def ajghelp(self, message: Message):
        """Показать справку"""
        if self.config["command_delay"] > 0:
            await asyncio.sleep(self.config["command_delay"])
        await utils.answer(message, self.strings("help_text"))

    @loader.command(ru_doc="Проверить последнее сообщение с набором")
    async def ajgtest(self, message: Message):
        """Проверить последнее сообщение с набором в текущем чате"""
        if self.config["command_delay"] > 0:
            await asyncio.sleep(self.config["command_delay"])
        current_chat_id = message.chat_id
        configured_bot_ids = self.config["bot_ids"]

        keywords_to_check_for_test = self._current_button_keywords_to_use

        deep_link_status_test_display = "🟢 Активен (автоматически обрабатывает Deep-Link URL, если они есть у подходящих кнопок)"

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

                if not is_general_bot_message:
                    continue

                msg_text_lower = msg.text.lower()

                is_game_join_test_message = any(phrase.lower() in msg_text_lower for phrase in game_join_phrases_for_test)
                is_general_lynch_test_message = any(phrase.lower() in msg_text_lower for phrase in lynch_phrases_for_test)
                is_player_voting_test_message = (
                    self.config["player_to_lynch_user_id"] != 0 and
                    is_general_bot_message and
                    any(phrase.lower() in msg_text_lower for phrase in player_lynch_phrases_for_test)
                )


                if is_game_join_test_message or is_general_lynch_test_message or is_player_voting_test_message:
                    info_msg = f"✅ Найдено сообщение ID <code>{msg.id}</code> от <code>{sender_id if sender_id is not None else 'Неизвестно'}</code>:\n"
                    text_preview = msg.text[:100] + "..." if len(msg.text) > 100 else msg.text
                    info_msg += f"💬 Текст: <code>{text_preview}</code>\n"

                    if getattr(msg, 'buttons', None):
                        info_msg += "🔘 Есть кнопки: Да\n"
                        info_msg += "Список кнопок:\n"
                        button_matched_in_test = False

                        if is_player_voting_test_message:
                            if temp_player_nickname_for_test:
                                info_msg += f"  <emoji document_id=5935968647901089910>🔫</emoji> (Режим голосования за игрока: ищу ник <code>{temp_player_nickname_for_test}</code>)\n"
                                for row_idx, row in enumerate(msg.buttons):
                                    for btn_idx, btn in enumerate(row):
                                        btn_text = str(getattr(btn, 'text', f'Кнопка {btn_idx}'))
                                        if temp_player_nickname_for_test.lower() in btn_text.lower():
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
                            info_msg += "  <emoji document_id=5935847413859225147>🏀</emoji> (Режим входа в игру: ищу ключевые слова с приоритетом)\n"

                            deprioritized_keyword_test = "присоединиться"
                            high_priority_keywords_test = [k for k in keywords_to_check_for_test if k.lower() != deprioritized_keyword_test.lower()]
                            low_priority_keywords_test = [k for k in keywords_to_check_for_test if k.lower() == deprioritized_keyword_test.lower()]

                            temp_target_button_text = None
                            temp_target_button_url = None

                            all_buttons_info = []

                            # Simulate priority check for testing
                            found_high_priority = False
                            for row in msg.buttons:
                                for btn in row:
                                    btn_text_test = str(getattr(btn, 'text', ''))
                                    btn_url_test = getattr(btn, 'url', None)

                                    button_info = {
                                        "text": btn_text_test,
                                        "url": btn_url_test,
                                        "match_type": "нет",
                                        "action": ""
                                    }

                                    if any(keyword in btn_text_test.lower() for keyword in high_priority_keywords_test):
                                        button_info["match_type"] = "✅ ВЫСОКИЙ ПРИОРИТЕТ!"
                                        if not found_high_priority: # Capture the first high-priority match
                                            temp_target_button_text = btn_text_test
                                            temp_target_button_url = btn_url_test
                                            found_high_priority = True
                                            button_matched_in_test = True # Overall match for the test

                                    all_buttons_info.append(button_info)

                            if not found_high_priority and low_priority_keywords_test:
                                for btn_info in all_buttons_info:
                                    if any(keyword in btn_info["text"].lower() for keyword in low_priority_keywords_test):
                                        btn_info["match_type"] = "✅ НИЗКИЙ ПРИОРИТЕТ (присоединиться)"
                                        if not temp_target_button_text: # Capture the first low-priority match if no high-priority was found
                                            temp_target_button_text = btn_info["text"]
                                            temp_target_button_url = btn_info["url"]
                                            button_matched_in_test = True # Overall match for the test


                            for btn_info in all_buttons_info:
                                url_display = f" (URL: <code>{btn_info['url'][:50]}...</code>)" if btn_info['url'] and len(btn_info['url']) > 50 else (f" (URL: <code>{btn_info['url']}</code>)" if btn_info['url'] else " (URL: Нет, Callback кнопка)")

                                action_suffix = ""
                                if btn_info['text'] == temp_target_button_text and btn_info['url'] == temp_target_button_url and button_matched_in_test:
                                    # This is the button that would be clicked
                                    if btn_info['url']:
                                        parsed_url = urllib.parse.urlparse(btn_info['url'])
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

                                        if bot_username and start_param:
                                            action_suffix = f" (Действие Deep-Link: *была бы* отправлена <code>/start {start_param}</code> боту @{bot_username})"
                                        else:
                                            action_suffix = " (Действие: *была бы* нажата URL кнопка)"
                                    else:
                                        action_suffix = " (Действие: *была бы* нажата Callback кнопка)"

                                info_msg += f"  • <code>{btn_info['text']}</code>{url_display} ({btn_info['match_type']}){action_suffix}\n"

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
        if self.config["command_delay"] > 0:
            await asyncio.sleep(self.config["command_delay"])
        await utils.answer(message, self.strings("ajgid_bots_list"))

    @loader.command(ru_doc="Показать информацию о регистрации на турниры")
    async def ajgtournaments(self, message: Message):
        """Показать информацию о регистрации на турниры"""
        if self.config["command_delay"] > 0:
            await asyncio.sleep(self.config["command_delay"])
        await utils.answer(message, self.strings("ajgtournaments_text"))

    @loader.watcher(incoming=True, outgoing=False)
    async def watcher(self, message: Message):
        """Обработчик всех входящих сообщений для автовхода в игру, автолинчевания, пересылки роли."""
        try:
            if not self.config["enabled"]:
                logger.debug("AutoJoinGame: Модуль выключен. Пропускаю сообщение.")
                return

            if not getattr(message, 'text', None):
                logger.debug(f"AutoJoinGame: Сообщение {message.id} не содержит текста. Пропускаю.")
                return

            message_identifier = (message.chat_id, message.id)
            if message_identifier in self._processed_messages:
                logger.debug(f"AutoJoinGame: Сообщение {message.id} в чате {message.chat_id} уже было обработано. Пропускаю.")
                return

            self._processed_messages.add(message_identifier)

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

            # --- Автоматическое включение отслеживания ролей --- # Re-added
            auto_track_phrases = self.config["auto_track_roles_trigger_phrases"]
            auto_track_bot_ids = self.config["auto_track_roles_bot_ids"]

            if auto_track_phrases and not self.config["role_tracking_enabled"]:
                is_auto_track_trigger_bot = (
                    getattr(sender, 'bot', False) and
                    (not auto_track_bot_ids or sender_id in auto_track_bot_ids)
                )
                if is_auto_track_trigger_bot and any(p.lower() in msg_text_lower for p in auto_track_phrases):
                    logger.info(f"AutoJoinGame: Обнаружен триггер для автоматического включения отслеживания ролей в сообщении {message.id} от бота {sender_id}.")

                    self.set("role_tracking_enabled", True)
                    self.config["role_tracking_enabled"] = True
                    self._role_tracking_active = True
                    self._role_tracking_start_time = datetime.now()
                    self._tracked_roles_list = []
                    self._tracked_roles_lookup_set.clear()
                    self._update_tracked_roles_patterns()

                    send_chat_id = self.config["send_tracked_roles_chat_id"]
                    send_delay = self.config["send_tracked_roles_delay"]

                    if send_chat_id != 0 and send_delay > 0:
                        if self._send_tracked_roles_task:
                            self._send_tracked_roles_task.cancel()
                            self._send_tracked_roles_task = None
                        self._send_tracked_roles_task = asyncio.create_task(
                            self._send_tracked_roles_list_scheduled(send_delay, send_chat_id)
                        )
                        logger.info(self.strings("auto_role_tracking_activated_with_send").format(
                            duration=self.config["role_tracking_duration"],
                            delay=send_delay,
                            chat_id=send_chat_id
                        ))
                    else:
                        logger.info(self.strings("auto_role_tracking_activated").format(
                            duration=self.config["role_tracking_duration"]
                        ))
                    return

            # --- Автоматическое выключение отслеживания ролей --- # Re-added
            auto_disable_phrases = self.config["auto_disable_track_roles_trigger_phrases"]
            auto_disable_bot_ids = self.config["auto_disable_track_roles_bot_ids"]

            if auto_disable_phrases and self.config["role_tracking_enabled"]:
                is_auto_disable_trigger_bot = (
                    getattr(sender, 'bot', False) and
                    (not auto_disable_bot_ids or sender_id in auto_disable_bot_ids)
                )
                if is_auto_disable_trigger_bot and any(p.lower() in msg_text_lower for p in auto_disable_phrases):
                    logger.info(f"AutoJoinGame: Обнаружен триггер для автоматического выключения отслеживания ролей в сообщении {message.id} от бота {sender_id}.")

                    self.set("role_tracking_enabled", False)
                    self.config["role_tracking_enabled"] = False
                    self._role_tracking_active = False
                    self._role_tracking_start_time = None
                    self._tracked_roles_list = []
                    self._tracked_roles_lookup_set.clear()
                    if self._send_tracked_roles_task:
                        self._send_tracked_roles_task.cancel()
                        self._send_tracked_roles_task = None

                    logger.info("AutoJoinGame: Автоматическое отслеживание ролей выключено.")
                    await self._client.send_message(message.chat_id, self.strings("auto_role_tracking_deactivated"))
                    return

            # --- Логика отслеживания ролей --- # Re-added
            if self.config["role_tracking_enabled"] and self._role_tracking_active:
                # Проверка на истечение времени
                if self._role_tracking_start_time and (datetime.now() - self._role_tracking_start_time).total_seconds() > self.config["role_tracking_duration"]:
                    logger.info(self.strings("role_tracking_expired"))
                    self.set("role_tracking_enabled", False)
                    self.config["role_tracking_enabled"] = False
                    self._role_tracking_active = False
                    self._role_tracking_start_time = None
                    self._tracked_roles_list = []
                    self._tracked_roles_lookup_set.clear()
                    if self._send_tracked_roles_task:
                        self._send_tracked_roles_task.cancel()
                        self._send_tracked_roles_task = None
                else:
                    # Проверка на чат мониторинга ролей
                    monitor_chat_id = self.config["role_tracking_monitor_chat_id"]
                    if monitor_chat_id != 0 and message.chat_id != monitor_chat_id:
                        logger.debug(f"AutoJoinGame: Отслеживание ролей активно, но сообщение {message.id} не из настроенного чата для мониторинга ({monitor_chat_id}). Пропускаю.")
                        # Если не совпадает, то дальнейшая логика отслеживания ролей для этого сообщения не выполняется.
                    else:
                        role_announcement_phrases_lower = [p.lower() for p in self.config["role_announcement_phrases"]]

                        is_role_announcement = any(phrase in msg_text_lower for phrase in role_announcement_phrases_lower)

                        if is_role_announcement:
                            found_tracked_role_clean = None
                            is_role_active = True

                            # Iterate through pre-compiled patterns for faster role matching
                            for compiled_pattern, clean_role_text, active_status in self._compiled_tracked_role_patterns:
                                if compiled_pattern.search(msg_text_lower):
                                    found_tracked_role_clean = clean_role_text
                                    is_role_active = active_status
                                    break

                            if found_tracked_role_clean:
                                nickname = self._get_user_nickname(sender)
                                if (sender_id, found_tracked_role_clean) not in self._tracked_roles_lookup_set:
                                    self._tracked_roles_list.append((sender_id, nickname, found_tracked_role_clean, is_role_active))
                                    self._tracked_roles_lookup_set.add((sender_id, found_tracked_role_clean))
                                    status_text = "Активная" if is_role_active else "Неактивная"
                                    logger.info(self.strings("role_tracked_success_with_status").format(nickname=nickname, role=found_tracked_role_clean, status=status_text))

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

            if not is_general_game_bot:
                logger.debug(f"AutoJoinGame: Сообщение {message.id} от бота {sender_id}, но его ID не в списке разрешенных ботов. Пропускаю.")
                return

            # Логика голосования за конкретного игрока
            if (self.config["player_to_lynch_user_id"] != 0 and
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

                        if self._player_nickname_to_lynch.lower() in button_text.lower():
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

            # Логика общего линчевания/повешения и входа в игру
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

                keywords_to_check = self._current_button_keywords_to_use
                if not keywords_to_check:
                    logger.warning(f"⚠️ AutoJoinGame: Список активных ключевых слов для кнопок пуст. Ни одна кнопка не будет активирована для сообщения {message.id}.")
                    return

                deprioritized_keyword = "присоединиться"

                high_priority_keywords = [k for k in keywords_to_check if k.lower() != deprioritized_keyword.lower()]
                low_priority_keywords = [k for k in keywords_to_check if k.lower() == deprioritized_keyword.lower()]

                target_button = None

                for row in message.buttons:
                    for button in row:
                        try:
                            button_text = str(getattr(button, 'text', ''))
                        except Exception as e:
                            logger.warning(f"Error getting button text for message {message.id}: {e}")
                            button_text = ''

                        if any(keyword in button_text.lower() for keyword in high_priority_keywords):
                            target_button = button
                            logger.info(f"✅ AutoJoinGame: Найдена высокоприоритетная кнопка: '{button_text}'")
                            break
                    if target_button:
                        break

                if not target_button and low_priority_keywords:
                    for row in message.buttons:
                        for button in row:
                            try:
                                button_text = str(getattr(button, 'text', ''))
                            except Exception as e:
                                logger.warning(f"Error getting button text for message {message.id}: {e}")
                                button_text = ''

                            if any(keyword in button_text.lower() for keyword in low_priority_keywords):
                                target_button = button
                                logger.info(f"✅ AutoJoinGame: Найдена низкоприоритетная кнопка (только '{deprioritized_keyword}'): '{button_text}'")
                                break
                        if target_button:
                            break

                if target_button:
                    button_text = str(getattr(target_button, 'text', ''))
                    if getattr(target_button, 'url', None):
                        button_url = target_button.url
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

                        if bot_username and start_param:
                            logger.info(f"📤 AutoJoinGame: Deep-Link URL обнаружен. Отправка /start {start_param} боту @{bot_username}")

                            try:
                                await self._client.send_message(
                                    bot_username,
                                    f'/start {start_param}'
                                )
                                logger.info("🎉 AutoJoinGame: Успешно отправлена команда /start (уведомление в чат не отправлено).")
                            except Exception as e:
                                logger.error(f"❌ AutoJoinGame: Ошибка при отправке Deep-Link команды /start для сообщения {message.id}: {e}")
                        else:
                            logger.warning(f"⚠️ AutoJoinGame: Найдена кнопка '{button_text}' с URL '{button_url}', но она не является Deep-Link. Пропускаю.")
                    else:
                        logger.info(f"📤 AutoJoinGame: Найдена кнопка '{button_text}' (CallbackQuery). Нажимаю.")
                        try:
                            await target_button.click()
                            logger.info(f"🎉 AutoJoinGame: Успешно нажата кноп '{button_text}' для присоединения к игре.")
                        except Exception as e:
                            logger.error(f"❌ AutoJoinGame: Ошибка при нажатии кнопки '{button_text}' для присоединения к игре: {e}")
                else:
                    logger.warning(f"⚠️ AutoJoinGame: Кнопка присоединения не найдена под сообщением {message.id} после задержки.")

        except Exception as e:
            logger.exception(f"❌ AutoJoinGame: Критическая ошибка в watcher для сообщения {getattr(message, 'id', 'N/A')} в чате {getattr(message, 'chat_id', 'N/A')}: {e}")
