# meta developer: @yourhandle
# meta name: UniversalMafiaTools
# meta version: 1.0.0
# Combined module for AutoJoinGame and TagAll functionalities

import logging
import asyncio
import random
import urllib.parse
from datetime import datetime, timedelta
from hikkatl.tl.functions.channels import InviteToChannelRequest # Specific for TagAll bot invite
from hikkatl.tl.types import Message, User
from hikkatl import events # Use hikkatl events for consistency
from hikkatl.tl.functions.messages import ToggleDialogPinRequest # Specific for pin/unpin commands
import re
from collections import defaultdict
from typing import Optional, List, Tuple
import contextlib # For TagAll's bot invite

from .. import loader, utils

logger = logging.getLogger(__name__)

# --- TagAll-specific classes and helpers ---
class StopEvent:
    """
    Event class to signal stopping the TagAll process.
    Stores the chat_id to ensure the trigger message comes from the correct chat.
    """
    def __init__(self, chat_id: int):
        self.state = True
        self.chat_id = chat_id
        self.last_timeout: float | None = None

    def stop(self):
        self.state = False

# --- End TagAll-specific classes and helpers ---


@loader.tds
class UniversalMafiaToolsMod(loader.Module):
    """
    Объединенный модуль для автовхода в игру, автолинчевания, пересылки ролей,
    отслеживания ролей и массового упоминания участников (TagAll).
    """

    strings = {
        "name": "UniversalMafiaTools",
        # --- AutoJoinGame Strings ---
        "enabled": "✅ Автовход в игру и автолинчевание включены.",
        "disabled": "❌ Автовход в игру и автолинчевание выключены.",
        "status": "<emoji document_id=5875291072225087249>📊</emoji> Статус автовхода и автолинчевания:\n"
                  "Статус: {}\n"
                  "Задержка входа (секунды): {}\n"
                  "Задержка линчевания (секунды): {}\n"
                  "Задержка выполнения команд (секунды): {}\n"
                  "Боты для отслеживания (и для автоотслеживания ролей): {}\n"
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
                  "Чат для отслеживания/вывода ролей: {}\n"
                  "Задержка отправки списка отслеживаемых ролей (секунды): {}\n"
                  "Автоматическое включение отслеживания ролей (фразы): {}\n"
                  "Автоматическое выключение отслеживания ролей (фразы): {}\n"
                  "Чат для триггеров автоотслеживания ролей: {}\n"
                  "\n<emoji document_id=5931415565955503486>👥</emoji> Статус TagAll:\n"
                  "Пользователей на сообщение: {}\n"
                  "Задержка между сообщениями (TagAll): {}\n"
                  "Удалять сообщения после тега (TagAll): {}\n"
                  "Использовать бота для тегов (TagAll): {}\n"
                  "Тихая отправка (TagAll): {}\n"
                  "Циклическое тегирование: {}\n"
                  "Задержка между циклами тегов: {}\n"
                  "Длительность тегирования (TagAll): {}\n"
                  "Триггерные сообщения остановки (TagAll): {}\n"
                  "Разрешенные юзеры для остановки (TagAll): {}\n"
                  "Триггерные сообщения активации (TagAll): {}\n"
                  "Разрешенные юзеры для активации (TagAll): {}\n"
                  "Исключенные юзеры (TagAll): {}\n"
                  "Разрешенные чаты для команд (TagAll): {}",
        "error": "❌ Ошибка при нажатии кнопки: {}",
        "no_button": "⚠️ Кнопка не найдена под сообщением",
        "help_text": """<emoji document_id=5931415565955503486>🤖</emoji> UniversalMafiaTools - Помощь

<emoji document_id=5935847413859225147>🏀</emoji> Команды AutoJoinGame:
<code>.ajgon</code> - Включить автовход в игру и автолинчевание
<code>.ajgoff</code> - Выключить автовход в игру и автолинчевание
<code>.ajgstatus</code> - Показать статус
<code>.ajghelp</code> - Эта справка
<code>.ajgtest</code> - Проверить последнее сообщение с набором в текущем чате
<code>.ajgid</code> - Показать список ID ботов для мафии
<code>.ajgtournaments</code> - Показать информацию о регистрации на турниры
<code>.ajgshowtrackedroles</code> - Показать список найденных отслеживаемых ролей. Если настроен <code>role_tracking_output_chat_id</code>, список будет отправлен туда, иначе - в текущий чат.
<code>.ajgset &lt;ID_конфига&gt;</code> - Переключить активную конфигурацию ключевых слов для кнопок. Если <code>&lt;ID_конфига&gt;</code> не указан, покажет текущую активную конфигурацию и доступные ID.
<code>.pinchat &lt;chat_id&gt;</code> - Закрепить чат в вашем списке диалогов И добавить его в разрешенные чаты модуля.
<code>.unpinchat &lt;chat_id&gt;</code> - Открепить чат из вашего списка диалогов И удалить его из разрешенных чатов модуля.
<code>.ajgpinchat &lt;chat_id&gt;</code> - Добавить ID чата только в список разрешенных чатов для модуля (<code>allowed_chats</code>).
<code>.ajgunpinchat &lt;chat_id&gt;</code> - Удалить ID чата только из списка разрешенных чатов для модуля (<code>allowed_chats</code>).

<emoji document_id=5877260593901971030>⚙</emoji> Как работает AutoJoinGame:
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
<b>Новая функция:</b> Настройка <code>role_tracking_output_chat_id</code> позволяет указать ID чата (положительное или отрицательное), в котором модуль будет отслеживать объявления ролей пользователей <b>И</b> куда будет отправлен список отслеживаемых ролей (автоматически после активации или по команде <code>.ajgshowtrackedroles</code>). Если <code>0</code>, отслеживание будет происходить во всех разрешенных чатах (<code>allowed_chats</code>), а списки будут отправляться в чат активации (для автоматической отправки) или в текущий чат (для команды).
<b>Новая функция:</b> Модуль может автоматически включать отслеживание ролей при получении сообщения, содержащего определенные фразы, от ботов, указанных в <code>bot_ids</code> (или от любого бота, если список <code>bot_ids</code> пуст).
<b>Новая функция:</b> Модуль может автоматически <b>выключать</b> отслеживание ролей при получении сообщения, содержащего определенные фразы, от ботов, указанных в <code>bot_ids</code> (или от любого бота, если список <code>bot_ids</code> пуст).
<b>Улучшение:</b> Теперь модуль более точно определяет роли, включая составные фразы, и позволяет помечать роли как 'неактивные' с помощью суффикса <code>(н)</code> для раздельного отображения.
<b>Приоритет кнопок:</b> Теперь модуль отдает предпочтение кнопкам, содержащим <b>другие ключевые слова</b> из активной конфигурации, если на кнопке также есть слово "присоединиться". Кнопка с только "присоединиться" будет нажата только в том случае, если других подходящих кнопок не найдено.
<b>Объединенные команды:</b> <code>.pinchat &lt;chat_id&gt;</code> и <code>.unpinchat &lt;chat_id&gt;</code> теперь управляют как закреплением/откреплением чатов в вашем списке диалогов, так и списком разрешенных чатов модуля.
<b>Дополнительные команды:</b> <code>.ajgpinchat &lt;chat_id&gt;</code> и <code>.ajgunpinchat &lt;chat_id&gt;</code> позволяют управлять ТОЛЬКО списком разрешенных чатов (<code>allowed_chats</code>) для модуля без изменения закрепления в Telegram. Эти команды, как и объединенные команды, могут быть ограничены для использования определенными пользователями через настройку <code>pin_unpin_allowed_user_ids</code>.
<b>Новая функция:</b> Настройка <code>command_delay</code> позволяет установить задержку перед выполнением всех команд модуля.
<b>Оптимизация отслеживания ролей:</b> Система отслеживания ролей теперь работает более быстро и стабильно, а также добавляет роли сразу после объявления.
<b>Новая функция:</b> Настройка <code>auto_role_tracking_trigger_chat_id</code> позволяет указать ID чата (положительное или отрицательное), в котором модуль будет слушать триггеры для автоматического включения/выключения отслеживания ролей. Если `0`, триггеры будут отслеживаться во всех разрешенных чатах.

<emoji document_id=5931415565955503486>👥</emoji> Команды TagAll:
<code>.tagall</code> [<номер чата>] [текст] - Отметить всех участников чата. [текст] будет отправлен вместе с тегами. Если текст не указан, будут отправлены только теги.
<code>.stoptagall</code> [<номер чата>] - Остановить запущенный процесс TagAll в <b>указанном или текущем чате</b>.
<code>.autotagall</code> [<номер чата>] [on|off] - Включить или выключить триггеры для запуска/остановки TagAll в <b>указанном или текущем чате</b>. Используйте `on` для включения, `off` для выключения. Без аргументов покажет статус триггеров.

<emoji document_id=5877260593901971030>⚙</emoji> Как работает TagAll:
Позволяет упомянуть всех участников чата, используя гибкие настройки.
Поддерживает указание текста перед упоминаниями.
Может быть остановлен командой <code>.stoptagall</code>.
Настраивается количество пользователей на сообщение и задержка между сообщениями.
Включает/выключает автоматическое упоминание по триггерам, настроенным в конфиге.
Поддерживает перенаправление команд в разрешенные чаты.
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

.cfg UniversalMafiaTools button_keyword_configs_string""",
        "lynch_triggered_positive": "<emoji document_id=5935968647901089910>🔫</emoji> Обнаружен запрос на линчевание/повешение. Нажимаю '👍'.",
        "lynch_button_not_found_positive": "⚠️ Запрос на линчевание/повешение обнаружен, но кнопка '👍' не найдена.",
        "lynch_triggered_negative": "<emoji document_id=5935968647901089910>🔫</emoji> Обнаружен запрос на линчевание/повешение с маркером '{marker}'. Нажимаю '👎'.",
        "lynch_button_not_found_negative": "⚠️ Запрос на линчевание/повешение с маркером '{marker}' обнаружен, но кнопка '👎' не найдена.",
        "player_nickname_set": "<emoji document_id=5839380580080293813>🖋</emoji> Установлен ник игрока для линчевания: <code>{nickname}</code>. Ожидаю голосования.",
        "player_lynch_triggered": "<emoji document_id=5935968647901089910>🔫</emoji> Обнаружен запрос на голосование за игрока. Ищу кнопку с ником <code>{nickname}</code>.",
        "player_lynch_button_found": "✅ UniversalMafiaTools: Найдена кнопка с ником <code>{nickname}</code>. Нажимаю.",
        "player_lynch_button_not_found": "⚠️ UniversalMafiaTools: Запрос на голосование за игрока найден, но кнопка с ником <code>{nickname}</code> не найдена.",
        "player_lynch_success": "🎉 UniversalMafiaTools: Успешно нажата кнопка с ником <code>{nickname}</code>. Ник сброшен.",
        "player_lynch_error": "❌ UniversalMafiaTools: Ошибка при нажатии кнопки с ником <code>{nickname}</code>: {error}",
        "ajgtest_player_nickname_would_be_set": "🔔 Сообщение ID <code>{msg_id}</code> от <code>{sender_id}</code> *установило бы* ник: <code>{nickname}</code>.",
        "ajgtest_player_nickname_not_set_yet": "ℹ️ Ник игрока для голосования не установлен в конфиге или не найден в последних 500 сообщениях.",
        "ajgtest_player_nickname_used": "ℹ️ Для последующих тестов используется ник: <code>{nickname}</code>.",
        "ajgtest_player_lynch_disabled": "ℹ️ ID пользователя для линчевания игрока не установлен в конфиге. Эта часть теста неактивна.",
        "ajgtest_no_matches": "❌ Сообщения с набором, запросом на линчевание или голосование за игрока от настроенных ботов/пользователя не найдено в текущем чате ID <code>{chat_id}</code>\n📊 Проверено сообщений: {count}",
        "ajgtest_error": "❌ Ошибка: <code>{error}</code>",
        "role_forward_chat_id_display": "Отключено (0)",
        "role_forward_trigger_phrases_display": "(пусто)",
        "role_forward_success": "🎉 UniversalMafiaTools: Роль успешно переслана в чат <code>{chat_id}</code>.",
        "role_forward_error": "❌ UniversalMafiaTools: Ошибка при пересылке роли в чат <code>{chat_id}</code>: {error}",
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
        "tracked_roles_send_success": "🎉 UniversalMafiaTools: Список отслеживаемых ролей успешно отправлен в чат <code>{chat_id}</code>.",
        "tracked_roles_send_error": "❌ UniversalMafiaTools: Ошибка при отправке списка отслеживаемых ролей в чат <code>{chat_id}</code>: {error}",
        "send_tracked_roles_delay_display": "Отключено (0)",
        "auto_track_roles_trigger_phrases_display": "(пусто)",
        "auto_role_tracking_activated": "<emoji document_id=5776375003280838798>✅</emoji> Автоматическое отслеживание ролей включено на {duration} секунд.",
        "auto_role_tracking_activated_with_send": "<emoji document_id=5776375003280838798>✅</emoji> Автоматическое отслеживание ролей включено на {duration} секунд. Список будет отправлен в чат <code>{chat_id}</code> через {delay} секунд.",
        "auto_disable_track_roles_trigger_phrases_display": "(пусто)",
        "auto_role_tracking_deactivated": "<emoji document_id=5944122171441618396>❌</emoji> Автоматическое отслеживание ролей выключено.",
        "switch_keywords_success": "✅ Активная конфигурация ключевых слов переключена на <code>{config_id}</code>. Теперь используются ключевые слова: {keywords}",
        "switch_keywords_not_found": "⚠️ Конфигурация с ID <code>{config_id}</code> не найдена. Доступные ID: {available_ids}.",
        "switch_keywords_no_configs": "⚠️ Нет настроенных конфигураций ключевых слов. Используйте <code>.cfg UniversalMafiaTools button_keyword_configs_string</code> для настройки.",
        "switch_keywords_current": "ℹ️ Активная конфигурация уже <code>{config_id}</code>.",
        "switch_keywords_usage": "ℹ️ Текущая активная конфигурация: <code>{current_id}</code>. Ключевые слова: {current_keywords}\nДоступные ID: {available_ids}.\nИспользуйте <code>.ajgset &lt;ID_конфига&gt;</code> для переключения.",
        "common_invalid_chat_id": "❌ Неверный ID чата. Пожалуйста, укажите числовой ID.",
        "not_allowed_to_configure_chats": "❌ У вас нет разрешения на изменение списка разрешенных чатов или управление закреплением/откреплением чатов.",
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
        "module_add_allowed_chat_success": "✅ Чат <code>{chat_id}</code> успешно добавлен в список разрешенных чатов модуля.",
        "module_add_allowed_chat_already_added": "⚠️ Чат <code>{chat_id}</code> уже находится в списке разрешенных чатов модуля.",
        "module_remove_allowed_chat_success": "✅ Чат <code>{chat_id}</code> успешно удален из списка разрешенных чатов модуля.",
        "module_remove_allowed_chat_not_found": "⚠️ Чат <code>{chat_id}</code> не найден в списке разрешенных чатов модуля.",
        "command_result_template": "Результаты для чата <code>{chat_id}</code>:\n• {dialog_action_result}\n• {module_action_result}",
        "ajg_only_action_start_msg": "⏳ Пытаюсь {action_text_verb} чат <code>{chat_id}</code> в списке разрешенных чатов модуля...",
        "role_tracking_output_chat_id_display_default": "По умолчанию (отслеживание в разрешенных чатах, отправка в чат активации/команды) (0)",
        "role_tracking_output_chat_id_display_specific": "ID чата: {}",
        "auto_role_tracking_trigger_chat_id_display_default": "Во всех разрешенных чатах (0)",
        "any_users": "Любые пользователи",

        # --- TagAll Strings ---
        "tagall_name": "TagAll", # Module name for TagAll
        "gathering": "<b>[TagAll]</b> Сбор участников чата...",
        "started": "<b>[TagAll]</b> Начинаю тегать участников...",
        "stopped": "<b>[TagAll]</b> *Тег остановлен.*",
        "no_group": "<b>[TagAll]</b> Эту команду можно использовать только в группах.",
        "done": "<b>[TagAll]</b> Все участники успешно отмечены!",
        "tagall_already_running": "В этом чате уже запущен тег!",
        "tagall_error": "<b>[TagAll] Произошла ошибка:</b> {e}",
        "tagall_not_running": "В этом чате сейчас нет активного тега.",
        "tagall_invalid_chat_index": "🚫 <b>Неверный индекс чата</b> <code>{index}</code>. Разрешенные чаты: {allowed_chats}.",
        "cmd_redirected_indexed": "➡️ <b>Команда перенаправлена в чат</b> <code>{target_chat_id}</code> (индекс <code>{index}</code>).",
        "cmd_redirected": "➡️ <b>Команда перенаправлена в чат</b> <code>{target_chat_id}</code>, так как он единственный разрешенный.",
        "cmd_not_allowed_multiple": "🚫 <b>Эта команда не может быть использована в текущем чате. Укажите индекс чата или используйте в одном из разрешенных чатов:</b> {allowed_chats}.",
        "triggers_state_enabled": "✅ <b>Триггеры TagAll включены в чате {chat_id}!</b>",
        "triggers_state_disabled": "❌ <b>Триггеры TagAll выключены в чате {chat_id}!</b>",
        "triggers_status_enabled": "✅ <b>Триггеры TagAll в чате {chat_id} включены.</b>",
        "triggers_status_disabled": "❌ <b>Триггеры TagAll в чате {chat_id} выключены.</b>",
        "tagall_no_eligible_participants": "Не удалось найти участников.",
        "tagall_chat_not_found": "🚫 <b>UniversalMafiaTools: TagAll: Не удалось найти чат с ID:</b> <code>{chat_id}</code>",
    }

    def __init__(self):
        super().__init__()
        # Initialize all configurations in a single ModuleConfig
        self.config = loader.ModuleConfig(
            # --- AutoJoinGame Configs ---
            loader.ConfigValue(
                option="enabled",
                default=False,
                doc="Включен ли автовход в игру и автолинчевание",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                option="delays",
                default=[0.5],
                doc="Список задержек перед нажатием кнопки входа в игру (секунды). Если указано несколько, будет выбрано случайное.",
                validator=loader.validators.Series(loader.validators.Float(minimum=0.1, maximum=10.0))
            ),
            loader.ConfigValue(
                option="lynch_delay",
                default=[0.5],
                doc="Список задержек перед нажатием кнопки '👍' или '👎' при линчевании (секунды). Если указано несколько, будет выбрано случайное.",
                validator=loader.validators.Series(loader.validators.Float(minimum=0.1, maximum=10.0))
            ),
            loader.ConfigValue(
                option="command_delay",
                default=0.0,
                doc="Задержка в секундах перед выполнением команды. Если 0, задержки нет. Поддерживает дробные значения.",
                validator=loader.validators.Float(minimum=0.0, maximum=10.0)
            ),
            loader.ConfigValue(
                option="bot_ids",
                default=[],
                doc="Список ID ботов, от которых ожидается сообщение о наборе в игру, линчевании, повешении, голосовании за игрока, а также триггеры для автоматического включения/выключения отслеживания ролей. Если список пуст, сообщения будут отслеживаться от любого бота.",
                validator=loader.validators.Series(loader.validators.Integer())
            ),
            loader.ConfigValue(
                option="allowed_chats",
                default=[],
                doc="Список ID чатов, в которых модуль будет активен (для автовхода, линчевания, пересылки ролей). Если список пуст, модуль будет работать во всех чатах.",
                validator=loader.validators.Series(loader.validators.Integer())
            ),
            loader.ConfigValue(
                option="pin_unpin_allowed_user_ids",
                default=[],
                doc="Список ID пользователей, которым разрешено использовать команды, связанные с изменением allowed_chats и закреплением/откреплением диалогов. Если список пуст, эти команды могут использовать все пользователи.",
                validator=loader.validators.Series(loader.validators.Integer())
            ),
            loader.ConfigValue(
                option="button_keyword_configs_string",
                default="присоединиться (default), играть (default), 🙋 (default), 🎮 (default), ✅ (default), 🌚 (default)",
                doc="Строка с конфигурациями ключевых слов для кнопок. Формат: 'Ключевое слово (ID_конфига), Другое слово (Другой_ID)'. Например: 'присоединиться (1), играть (1), 🙋 (2), 🎮 (2)'. Ключевые слова регистронезависимы. Скобки с ID не учитываются при поиске кнопок.",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                option="active_button_config_id",
                default="default",
                doc="ID активной конфигурации ключевых слов из 'button_keyword_configs_string'. Например: '1' или 'default'.",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                option="lynch_target_marker",
                default="",
                doc="Маркер (строка), который, если присутствует в сообщении-триггере для голосования, заставит модуль нажать кнопку '👎'. Если отсутствует или маркер не указан (пустая строка), нажимается '👍'.",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                option="game_join_trigger_phrases",
                default=["Ведётся набор в игру", "Регистрация началась!"],
                doc="Список фраз, которые модуль будет искать в сообщениях для активации автовхода в игру.",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                option="lynch_trigger_phrases",
                default=["Вы точно хотите линчевать"],
                doc="Список фраз, которые указывают на сообщение для голосования за линчевание (без маркера).",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                option="lynch_hang_trigger_phrases",
                default=["Вы точно хотите повесить"],
                doc="Список фраз, которые указывают на сообщение для голосования за повешение игрока (без маркера).",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                option="player_to_lynch_user_id",
                default=0,
                doc="ID пользователя, чье сообщение будет использоваться как ник игрока для линчевания. Если 0, то функция отключена.",
                validator=loader.validators.Integer(minimum=0)
            ),
            loader.ConfigValue(
                option="lynch_player_voting_trigger_phrases",
                default=["Пришло время искать виноватых!", "Кого ты хочешь повесить?", "Пришло время определить и наказать виновных", "Пришло время искать виноватых! Кого ты хочешь линчевать?"],
                doc="Список фраз, которые модуль будет искать в сообщениях от ботов (из bot_ids) для активации голосования за конкретного игрока.",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                option="role_forward_chat_id",
                default=0,
                doc="ID чата, куда будет пересылаться полученная роль в мафии. Если 0, функция отключена.",
                validator=loader.validators.Integer(minimum=0)
            ),
            loader.ConfigValue(
                option="role_trigger_phrases",
                default=["Ваша роль:", "Ты - ", "Твоя роль:", "Ты стал(а) "],
                doc="Список фраз, которые модуль будет искать в сообщениях от бота в ЛС для определения роли.",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                option="role_tracking_enabled",
                default=False,
                doc="Включено ли отслеживание ролей.",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                option="role_tracking_duration",
                default=300, # 5 минут
                doc="Длительность отслеживания ролей в секундах.",
                validator=loader.validators.Integer(minimum=10)
            ),
            loader.ConfigValue(
                option="tracked_roles_to_monitor",
                default=["мирный житель", "мафия (н)"],
                doc="Список фраз, указывающих на роли, которые нужно отслеживать. Модуль будет искать эти фразы в объявлениях ролей пользователей. Если роль должна быть 'неактивной', добавьте к ней суффикса '(н)', например: ['мирный житель', 'мафия (н)', 'комиссар'].",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                option="role_announcement_phrases",
                default=["Моя роль:", "Я - ", "Моя роль", "Я ", "роль:", "моя роль"],
                doc="Список фраз, которые пользователи могут использовать для объявления своей роли.",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                option="role_tracking_output_chat_id",
                default=0,
                doc="ID чата (положительное или отрицательное), в котором модуль будет отслеживать объявления ролей пользователей И куда будет отправлен список отслеживаемых ролей (автоматически после активации или по команде .ajgshowtrackedroles). Если 0, отслеживание будет происходить во всех разрешенных чатах ('allowed_chats'), а списки будут отправляться в чат активации (для автоматической отправки) или в текущий чат (для команды).",
                validator=loader.validators.Integer()
            ),
            loader.ConfigValue(
                option="send_tracked_roles_delay",
                default=30, # 30 секунд
                doc="Задержка в секундах, через которую будет отправлен список отслеживаемых ролей после активации отслеживания.",
                validator=loader.validators.Integer(minimum=0)
            ),
            loader.ConfigValue(
                option="auto_track_roles_trigger_phrases",
                default=[],
                doc="Список фраз, которые модуль будет искать в сообщениях для автоматического включения отслеживания ролей (от ботов из 'bot_ids').",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                option="auto_disable_track_roles_trigger_phrases",
                default=[],
                doc="Список фраз, которые модуль будет искать в сообщениях для автоматического выключения отслеживания ролей (от ботов из 'bot_ids').",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                option="auto_role_tracking_trigger_chat_id",
                default=0,
                doc="ID чата, в котором модуль будет слушать триггеры для автоматического включения/выключения отслеживания ролей. Если 0, триггеры будут отслеживаться во всех разрешенных чатах.",
                validator=loader.validators.Integer()
            ),

            # --- TagAll Configs ---
            loader.ConfigValue(
                option="USERS_PER_MESSAGE",
                default=5,
                doc="Количество пользователей, которых нужно тегать в одном сообщении (TagAll)",
                validator=loader.validators.Integer(minimum=1),
            ),
            loader.ConfigValue(
                option="DELAY",
                default=3.0,
                doc="Задержка между сообщениями в секундах для TagAll (не рекомендуется ставить меньше 2.0-3.0)",
                validator=loader.validators.Float(minimum=0.0),
            ),
            loader.ConfigValue(
                option="tagall_delete",
                default=False,
                doc="Удалять сообщения после тега (TagAll)",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                option="tagall_use_bot",
                default=False,
                doc="Использовать бота для тегов (TagAll)",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                option="tagall_timeout_str",
                default="0.1",
                doc=(
                    "Время между сообщениями с тегами (TagAll). Можно указать одно значение (например, '0.1'),"
                    " несколько значений через запятую (например, '0.1, 0.5, 1.0') или диапазон"
                    " (например, '0.1-1.0')."
                ),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                option="tagall_silent",
                default=False,
                doc="Не отправлять сообщение с кнопкой отмены (TagAll)",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                option="cycle_tagging",
                default=False,
                doc=(
                    "Тегать всех участников снова и снова, пока вы не остановите скрипт,"
                    " используя кнопку в сообщении (TagAll)"
                ),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                option="cycle_delay",
                default=0,
                doc="Задержка между циклами тегов в секундах (TagAll)",
                validator=loader.validators.Integer(minimum=0),
            ),
            loader.ConfigValue(
                option="tagall_duration",
                default=0,
                doc="Как долго (в секундах) должен работать процесс TagAll. Установите 0 для неограниченного времени.",
                validator=loader.validators.Integer(minimum=0),
            ),
            loader.ConfigValue(
                option="tagall_stop_trigger_message",
                default="",
                doc=(
                    "Сообщение(я)-триггер(ы) для остановки TagAll. Разделяйте запятыми."
                    " Можно указать индекс чата в скобках, например 'стоп(1)'. Если индекс"
                    " указан, триггер сработает только в соответствующем чате. Без индекса"
                    " триггер сработает в любом разрешенном чате."
                ),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                option="tagall_stop_trigger_user_id",
                default="",
                doc="ID пользователя(ей) или бота(ов), который(ые) может(могут) остановить TagAll сообщением-триггером. Разделяйте запятыми. Установите пустым, чтобы любой мог остановить.",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                option="tagall_activation_trigger_message",
                default="",
                doc=(
                    "Сообщение(я)-триггер(ы) для запуска TagAll. Разделяйте запятыми."
                    " Можно указать индекс чата в скобках, например 'запуск(1)'. Если индекс"
                    " указан, триггер сработает только в соответствующем чате. Без индекса"
                    " триггер сработает в любом разрешенном чате."
                ),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                option="tagall_activation_trigger_user_id",
                default="",
                doc="ID пользователя(ей) или бота(ов), который(ые) может(могут) запустить TagAll сообщением-триггером. Разделяйте запятыми. Установите пустым, чтобы любой мог запустить.",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                option="tagall_exclude_user_ids",
                default="",
                doc="ID пользователя(ей), которых не нужно тегать. Разделяйте запятыми. Например: <code>123456789, 987654321</code> (TagAll)",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                option="tagall_allowed_chat_ids",
                default="",
                doc="ID чата(ов), в которых разрешено использовать команды модуля TagAll. Разделяйте запятыми. Если указан только один ID, команды, запущенные в других чатах, будут автоматически перенаправлены в этот чат. Если пусто, команды разрешены во всех чатах.",
                validator=loader.validators.String(),
            ),
        )

        # --- AutoJoinGame State ---
        self._player_nickname_to_lynch = None
        self._role_tracking_active = False
        self._role_tracking_start_time = None
        self._tracked_roles_list = []
        self._tracked_roles_lookup_set: set[Tuple[int, str]] = set()
        self._compiled_tracked_role_patterns: List[Tuple[re.Pattern, str, bool]] = []
        self._self_id = None
        self._processed_messages = set()
        self._processed_messages_cleanup_task = None
        self._send_tracked_roles_task = None
        self._parsed_button_keywords: dict[str, list[str]] = {}
        self._current_button_keywords_to_use: list[str] = []

        # --- TagAll State ---
        self._tagall_events: dict[int, StopEvent] = {}

    async def client_ready(self, client, db):
        self._client = client
        self._db = db
        self._self_id = (await self._client.get_me()).id

        # AutoJoinGame setup
        if self._processed_messages_cleanup_task is None:
            self._processed_messages_cleanup_task = asyncio.create_task(self._cleanup_processed_messages_loop())
        self._update_button_keywords_from_config()
        self._update_tracked_roles_patterns()

    async def on_unload(self):
        # AutoJoinGame cleanup
        if self._processed_messages_cleanup_task:
            self._processed_messages_cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._processed_messages_cleanup_task
            logger.debug("UniversalMafiaTools: AJG: Задача очистки обработанных сообщений отменена.")

        if self._send_tracked_roles_task:
            self._send_tracked_roles_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._send_tracked_roles_task
            logger.debug("UniversalMafiaTools: AJG: Задача отправки списка отслеживаемых ролей отменена.")

        self._tracked_roles_lookup_set.clear()
        self._compiled_tracked_role_patterns.clear()

        # TagAll cleanup
        for event in list(self._tagall_events.values()):
            if event.state:
                event.stop()
        self._tagall_events.clear()
        logger.info("UniversalMafiaTools: TagAll: Все процессы TagAll остановлены из-за выгрузки модуля.")

    # --- AutoJoinGame Helper Methods (Copied as is) ---
    async def _cleanup_processed_messages_loop(self):
        """Периодически очищает набор обработанных ID сообщений."""
        while True:
            await asyncio.sleep(300)
            if self._processed_messages:
                logger.debug(f"UniversalMafiaTools: AJG: Очистка {len(self._processed_messages)} обработанных ID сообщений.")
                self._processed_messages.clear()

    def _update_tracked_roles_patterns(self):
        """Compiles regex patterns for tracked roles from config for faster lookup."""
        self._compiled_tracked_role_patterns = []
        for tracked_role_phrase_raw in self.config["tracked_roles_to_monitor"]:
            role_to_match_lower = tracked_role_phrase_raw.lower()
            current_is_active = True

            if role_to_match_lower.endswith("(н)"):
                current_is_active = False
                role_to_match_lower = role_to_match_lower[:-3].strip()

            parts = role_to_match_lower.split()
            escaped_parts = [re.escape(p) for p in parts]
            internal_pattern = r"\b" + r"\s+".join(escaped_parts) + r"\b"

            try:
                compiled_pattern = re.compile(internal_pattern, re.IGNORECASE)
                self._compiled_tracked_role_patterns.append((compiled_pattern, role_to_match_lower, current_is_active))
            except re.error as e:
                logger.error(f"UniversalMafiaTools: AJG: Ошибка компиляции регулярного выражения для роли '{tracked_role_phrase_raw}': {e}")

        logger.debug(f"UniversalMafiaTools: AJG: Обновлены шаблоны отслеживаемых ролей. Всего {len(self._compiled_tracked_role_patterns)} шаблонов.")

    def _parse_button_keywords_string(self, config_string: str) -> dict[str, list[str]]:
        """Парсит строку конфигурации ключевых слов кнопок в словарь."""
        parsed_configs = defaultdict(list)
        entries = [e.strip() for e in config_string.split(',')]

        for entry in entries:
            match = re.match(r"(.+?)\s*\(([\w\d]+)\)", entry)
            if match:
                keyword_part = match.group(1).strip()
                config_id = match.group(2).strip()
                parsed_configs[config_id].append(keyword_part.lower())
            elif entry:
                logger.warning(f"UniversalMafiaTools: AJG: Не удалось разобрать часть конфига 'button_keyword_configs_string': '{entry}'. Ожидается формат 'Ключевое слово (ID_конфига)'. Пропускаю.")
        return dict(parsed_configs)

    def _update_button_keywords_from_config(self):
        """Обновляет активные ключевые слова на основе конфига."""
        self._parsed_button_keywords = self._parse_button_keywords_string(self.config["button_keyword_configs_string"])

        active_id = self.config["active_button_config_id"]

        if active_id and active_id in self._parsed_button_keywords:
            self._current_button_keywords_to_use = self._parsed_button_keywords[active_id]
            logger.info(f"UniversalMafiaTools: AJG: Активная конфигурация ключевых слов кнопок установлена на '{active_id}'. Используются ключевые слова: {self._current_button_keywords_to_use}")
        elif self._parsed_button_keywords:
            first_id = next(iter(self._parsed_button_keywords))
            self.set("active_button_config_id", first_id)
            self.config["active_button_config_id"] = first_id
            self._current_button_keywords_to_use = self._parsed_button_keywords[first_id]
            logger.warning(f"UniversalMafiaTools: AJG: Активная конфигурация ключевых слов кнопок '{active_id}' не найдена или не установлена. Установлено на первую доступную: '{first_id}'.")
        else:
            self._current_button_keywords_to_use = []
            self.set("active_button_config_id", "")
            self.config["active_button_config_id"] = ""
            logger.warning("UniversalMafiaTools: AJG: Нет настроенных конфигураций ключевых слов кнопок. Модуль не будет активировать кнопки по ключевым словам.")

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
            if not self.config["role_tracking_enabled"] or not self._role_tracking_active:
                logger.debug("UniversalMafiaTools: AJG: Отправка списка отслеживаемых ролей отменена, так как отслеживание неактивно.")
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
            logger.debug("UniversalMafiaTools: AJG: Задача по отправке списка отслеживаемых ролей отменена.")
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
            logger.error(f"UniversalMafiaTools: AJG: Чат с ID {chat_id} не найден или недоступен для закрепления/открепления в Telegram.")
            return False, self.strings("dialog_chat_not_found_or_inaccessible").format(chat_id=chat_id)
        except Exception as e:
            logger.error(f"UniversalMafiaTools: AJG: Ошибка при получении сущности чата {chat_id} для Telegram pinning: {e}", exc_info=True)
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
                await self._client(ToggleDialogPinRequest(
                    peer=target_dialog.entity,
                    pinned=True
                ))
                return True, self.strings("dialog_pin_success").format(chat_id=chat_id)
            else:
                if not is_currently_pinned:
                    return False, self.strings("dialog_unpin_not_pinned").format(chat_id=chat_id)
                await self._client(ToggleDialogPinRequest(
                    peer=target_dialog.entity,
                    pinned=False
                ))
                return True, self.strings("dialog_unpin_success").format(chat_id=chat_id)

        except RPCError as e:
            logger.error(f"UniversalMafiaTools: AJG: Ошибка Telethon RPC при {action_text_verb} чата {chat_id} в Telegram: {e}", exc_info=True)
            return False, self.strings("dialog_pin_fail").format(chat_id=chat_id, error=e) if pin_action else self.strings("dialog_unpin_fail").format(chat_id=chat_id, error=e)
        except Exception as e:
            logger.exception(f"UniversalMafiaTools: AJG: Неожиданная ошибка при {action_text_verb} чата {chat_id} в Telegram: {e}")
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

    # --- End AutoJoinGame Helper Methods ---

    # --- TagAll Helper Methods (Copied as is) ---
    def _get_tagall_allowed_chat_ids_map(self) -> dict[int, int]:
        """
        Парсит строку tagall_allowed_chat_ids из конфига в словарь {index: chat_id}.
        Индексы 1-основанные.
        """
        allowed_ids_raw = self.config["tagall_allowed_chat_ids"]
        allowed_chats_map = {}
        cleaned_allowed_ids_raw = re.sub(r"[^0-9,]", "", allowed_ids_raw)
        for i, chat_id_str in enumerate(cleaned_allowed_ids_raw.split(',')):
            chat_id_str = chat_id_str.strip()
            if chat_id_str:
                try:
                    chat_id = int(chat_id_str)
                    allowed_chats_map[i + 1] = chat_id
                except ValueError:
                    logger.warning(f"UniversalMafiaTools: TagAll: Неверный ID чата в конфигурации 'tagall_allowed_chat_ids' после очистки: '{chat_id_str}'. Должен быть целым числом.")
        return allowed_chats_map

    def _format_tagall_allowed_chats_list(self, allowed_chats_map: dict[int, int]) -> str:
        """Форматирует список разрешенных чатов для вывода."""
        if not allowed_chats_map:
            return "<i>нет</i>"
        return ", ".join([f"<code>{idx}</code>: <code>{chat_id}</code>" for idx, chat_id in sorted(allowed_chats_map.items())])

    async def _resolve_tagall_target_chat(self, message: Message, raw_args: str) -> tuple[int | None, str | None]:
        """
        Определяет целевой chat_id для команды TagAll, применяя логику tagall_allowed_chat_ids и опциональный индекс.
        Возвращает (effective_target_chat_id: int | None, remaining_args: str | None).
        Возвращает None для effective_target_chat_id в случае ошибки.
        """
        original_chat_id = message.chat_id
        effective_target_chat_id = original_chat_id
        remaining_args = raw_args.strip()

        allowed_chats_map = self._get_tagall_allowed_chat_ids_map()
        allowed_chat_ids_set = set(allowed_chats_map.values())

        chat_index_match = re.match(r"^\s*(\d+)\s*(.*)$", remaining_args)
        if chat_index_match:
            try:
                chat_index = int(chat_index_match.group(1))
                if chat_index in allowed_chats_map:
                    effective_target_chat_id = allowed_chats_map[chat_index]
                    remaining_args = chat_index_match.group(2).strip()
                    if effective_target_chat_id != original_chat_id:
                        await utils.answer(message, self.strings("cmd_redirected_indexed").format(target_chat_id=effective_target_chat_id, index=chat_index))
                    return effective_target_chat_id, remaining_args
                else:
                    await utils.answer(message, self.strings("tagall_invalid_chat_index").format(index=chat_index, allowed_chats=self._format_tagall_allowed_chats_list(allowed_chats_map)))
                    return None, None
            except ValueError:
                pass

        if not allowed_chat_ids_set:
            return original_chat_id, remaining_args

        if original_chat_id in allowed_chat_ids_set:
            return original_chat_id, remaining_args
        else:
            if len(allowed_chat_ids_set) == 1:
                redirect_chat_id = next(iter(allowed_chat_ids_set))
                await utils.answer(message, self.strings("cmd_redirected").format(target_chat_id=redirect_chat_id))
                return redirect_chat_id, remaining_args
            else:
                await utils.answer(message, self.strings("cmd_not_allowed_multiple").format(allowed_chats=self._format_tagall_allowed_chats_list(allowed_chats_map)))
                return None, None

    def _parse_tagall_trigger_string(self, trigger_raw: str) -> tuple[str, int | None]:
        """Парсит необработанную строку триггера TagAll на базовое сообщение и необязательный индекс чата."""
        match = re.match(r"^(.*?)(?:\s*\((\d+)\))?$", trigger_raw.strip())
        if match:
            base_message = match.group(1).strip().lower()
            chat_index_str = match.group(2)
            chat_index = int(chat_index_str) if chat_index_str else None
            return base_message, chat_index
        return trigger_raw.strip().lower(), None

    def _get_random_tagall_timeout(self, event: StopEvent) -> float:
        """
        Разбирает конфигурацию таймаута TagAll и возвращает случайное значение таймаута.
        Поддерживает одно число с плавающей точкой, несколько чисел через запятую или диапазон чисел (например, "0.1-1.0").
        Гарантирует, что один и тот же таймаут не повторяется в двух последовательных вызовах,
        если указано несколько различных значений.
        """
        timeout_str = self.config["tagall_timeout_str"]
        default_timeout = 0.1
        current_timeout = default_timeout

        try:
            cleaned_timeout_str = re.sub(r"[^0-9.,-]", "", timeout_str).strip()

            if not cleaned_timeout_str:
                logger.warning(f"UniversalMafiaTools: TagAll: Пустая строка таймаута. Используется значение по умолчанию {default_timeout}.")
                return default_timeout

            if "," in cleaned_timeout_str:
                values = []
                for part in cleaned_timeout_str.split(','):
                    part = part.strip()
                    if part:
                        try:
                            val = float(part)
                            if val >= 0.0:
                                values.append(val)
                        except ValueError:
                            logger.warning(f"UniversalMafiaTools: TagAll: Неверное значение в списке таймаутов: '{part}'. Игнорируется.")

                if values:
                    if len(values) > 1 and event.last_timeout is not None and event.last_timeout in values:
                        available_values = [v for v in values if v != event.last_timeout]
                        if not available_values:
                            current_timeout = random.choice(values)
                        else:
                            current_timeout = random.choice(available_values)
                    else:
                        current_timeout = random.choice(values)
                else:
                    logger.warning(f"UniversalMafiaTools: TagAll: Не удалось разобрать значения таймаута из '{timeout_str}'. Используется значение по умолчанию {default_timeout}.")

            elif re.match(r"^\d*\.?\d*-\d*\.?\d*$", cleaned_timeout_str):
                parts = cleaned_timeout_str.split('-', 1)
                try:
                    min_val = float(parts[0].strip())
                    max_val = float(parts[1].strip())

                    min_val = max(0.0, min_val)
                    max_val = max(0.0, max_val)

                    if min_val > max_val:
                        min_val, max_val = max_val, min_val

                    current_timeout = random.uniform(min_val, max_val)
                except ValueError:
                    logger.warning(f"UniversalMafiaTools: TagAll: Не удалось разобрать диапазон таймаута из '{timeout_str}'. Используется значение по умолчанию {default_timeout}.")

            else:
                try:
                    current_timeout = max(0.0, float(cleaned_timeout_str))
                except ValueError:
                    logger.warning(f"UniversalMafiaTools: TagAll: Не удалось разобрать одиночное значение таймаута из '{timeout_str}'. Используется значение по умолчанию {default_timeout}.")

        except Exception as e:
            logger.error(f"UniversalMafiaTools: TagAll: Неожиданная ошибка при разборе таймаута '{timeout_str}': {e}. Используется значение по умолчанию {default_timeout}.")

        event.last_timeout = current_timeout
        return current_timeout

    async def _run_tagall_process(self, chat_id: int, message_prefix: str, event: StopEvent, silent_start: bool = False):
        """Внутренняя функция для обработки основной логики TagAll."""
        deleted_message_ids_hikkatl = []
        deleted_message_ids_bot_client = []

        is_bot_sender = self.config["tagall_use_bot"]

        try:
            chat_entity = await self._client.get_input_entity(chat_id)
        except Exception as e:
            logger.error(f"UniversalMafiaTools: TagAll: Не удалось получить сущность чата для ID {chat_id}: {e}")
            if not silent_start:
                await self._client.send_message(chat_id, self.strings("tagall_chat_not_found").format(chat_id=chat_id))
            event.stop()
            if chat_id in self._tagall_events:
                del self._tagall_events[chat_id]
            return

        excluded_user_ids = set()
        exclude_ids_raw = self.config["tagall_exclude_user_ids"]
        for uid_str in exclude_ids_raw.split(','):
            uid_str = uid_str.strip()
            if uid_str:
                try:
                    excluded_user_ids.add(int(uid_str))
                except ValueError:
                    logger.warning(f"UniversalMafiaTools: TagAll: Неверный ID пользователя в конфигурации 'tagall_exclude_user_ids': '{uid_str}'. Должен быть целым числом.")

        if is_bot_sender:
            try:
                if not hasattr(self, 'inline') or not hasattr(self.inline, 'bot_username') or not getattr(self.inline, 'bot_client', None):
                    raise RuntimeError("UniversalMafiaTools: TagAll: Инлайн-бот не настроен или недоступен.")

                bot_entity = await self._client.get_input_entity(self.inline.bot_username)
                with contextlib.suppress(Exception):
                    await self._client(InviteToChannelRequest(chat_entity, [bot_entity]))
            except Exception as e:
                logger.error(f"UniversalMafiaTools: TagAll: Не удалось получить сущность бота или пригласить бота: {e}")
                if not silent_start:
                    await self._client.send_message(chat_id, self.strings("bot_error")) # This uses AJG's bot_error string. Okay.
                event.stop()
                if chat_id in self._tagall_events:
                    del self._tagall_events[chat_id]
                return

        participants = []
        owner_id = self._client.tg_id
        async for user in self._client.iter_participants(chat_id):
            if not user.bot and not user.deleted and user.id != owner_id and user.id not in excluded_user_ids:
                participants.append(user)

        if not participants:
            logger.warning(f"UniversalMafiaTools: TagAll: В чате {chat_id} не найдено подходящих участников для TagAll, останавливаем.")
            if not silent_start:
                await self._client.send_message(chat_id, self.strings("tagall_no_eligible_participants"))
            event.stop()
            if chat_id in self._tagall_events:
                del self._tagall_events[chat_id]
            return

        random.shuffle(participants)

        start_time = time.time()

        try:
            first_pass = True
            while self.config["cycle_tagging"] or first_pass:
                if not event.state:
                    break

                if self.config["tagall_duration"] > 0 and (time.time() - start_time) > self.config["tagall_duration"]:
                    event.stop()
                    break

                current_participants_for_cycle = []
                if self.config["cycle_tagging"] and not first_pass:
                    logger.debug(f"UniversalMafiaTools: TagAll: Повторный запрос участников для цикла в чате {chat_id}.")
                    async for user in self._client.iter_participants(chat_id):
                        if not user.bot and not user.deleted and user.id != owner_id and user.id not in excluded_user_ids:
                            current_participants_for_cycle.append(user)
                    random.shuffle(current_participants_for_cycle)
                    participants = current_participants_for_cycle

                if not participants:
                    logger.warning(f"UniversalMafiaTools: TagAll: В чате {chat_id} не найдено участников для TagAll, останавливаем цикл.")
                    break

                for chunk in utils.chunks(participants, self.config["USERS_PER_MESSAGE"]):
                    if not event.state:
                        break

                    if self.config["tagall_duration"] > 0 and (time.time() - start_time) > self.config["tagall_duration"]:
                        event.stop()
                        break

                    tags = []
                    for user in chunk:
                        if user.username:
                            user_display_name = f"@{user.username}"
                        else:
                            display_name_parts = []
                            if user.first_name:
                                display_name_parts.append(user.first_name)
                            if user.last_name:
                                display_name_parts.append(user.last_name)

                            display_name = " ".join(display_name_parts)
                            user_display_name = utils.escape_html(display_name or "Пользователь")

                        tags.append(f'<a href="tg://user?id={user.id}">{user_display_name}</a>')

                    if message_prefix:
                        full_message_text = f"{message_prefix}\n{' '.join(tags)}"
                    else:
                        full_message_text = " ".join(tags)

                    if is_bot_sender:
                        if hasattr(self, 'inline') and hasattr(self.inline, 'bot_client') and self.inline.bot_client:
                            m = await self.inline.bot_client.send_message(
                                chat_id,
                                full_message_text,
                                parse_mode="HTML",
                            )
                            if self.config["tagall_delete"]:
                                deleted_message_ids_bot_client.append(m.id)
                        else:
                            logger.error("UniversalMafiaTools: TagAll: Клиент инлайн-бота недоступен или не настроен, переключаемся на юзербота для отправки сообщений.")
                            m = await self._client.send_message(
                                chat_entity,
                                full_message_text,
                                parse_mode="HTML",
                            )
                            if self.config["tagall_delete"]:
                                deleted_message_ids_hikkatl.append(m.id)
                    else:
                        m = await self._client.send_message(
                            chat_entity,
                            full_message_text,
                            parse_mode="HTML",
                        )
                        if self.config["tagall_delete"]:
                            deleted_message_ids_hikkatl.append(m.id)

                    await asyncio.sleep(self._get_random_tagall_timeout(event))

                first_pass = False
                if self.config["cycle_tagging"] and event.state:
                    await asyncio.sleep(self.config["cycle_delay"])
                elif not self.config["cycle_tagging"]:
                    break

        finally:
            if self.config["tagall_delete"]:
                with contextlib.suppress(Exception):
                    if deleted_message_ids_hikkatl:
                        for chunk_ids in utils.chunks(deleted_message_ids_hikkatl, 100):
                            await self._client.delete_messages(chat_entity, chunk_ids)

                    if deleted_message_ids_bot_client:
                        if hasattr(self, 'inline') and hasattr(self.inline, 'bot_client') and self.inline.bot_client:
                            for chunk_ids in utils.chunks(deleted_message_ids_bot_client, 100):
                                await self.inline.bot_client.delete_messages(chat_entity, chunk_ids)
                        else:
                            logger.warning("UniversalMafiaTools: TagAll: Клиент инлайн-бота недоступен для удаления своих сообщений.")

            if event.state:
                logger.info(f"UniversalMafiaTools: TagAll: Процесс TagAll завершен естественным образом в чате {chat_id}.")

            if chat_id in self._tagall_events:
                del self._tagall_events[chat_id]

    # --- End TagAll Helper Methods ---

    # --- Combined Message Watcher ---
    @loader.watcher(incoming=True, outgoing=False)
    async def watcher(self, message: Message):
        """Обработчик всех входящих сообщений для автовхода в игру, автолинчевания, пересылки роли, отслеживания ролей и триггеров TagAll."""
        try:
            if not getattr(message, 'text', None):
                logger.debug(f"UniversalMafiaTools: Сообщение {message.id} не содержит текста. Пропускаю.")
                return

            message_identifier = (message.chat_id, message.id)
            if message_identifier in self._processed_messages:
                logger.debug(f"UniversalMafiaTools: Сообщение {message.id} в чате {message.chat_id} уже было обработано. Пропускаю.")
                return

            self._processed_messages.add(message_identifier)

            sender = await message.get_sender()
            sender_id = getattr(sender, 'id', None)
            if sender_id is None:
                logger.warning(f"UniversalMafiaTools: Не удалось получить ID отправителя для сообщения {message.id} в чате {message.chat_id}. Пропускаю.")
                return

            chat_id = message.chat_id
            msg_text = message.text
            msg_text_lower = msg_text.lower()

            # --- TagAll Trigger Logic (Higher Priority) ---
            tagall_allowed_chats_map = self._get_tagall_allowed_chat_ids_map()
            tagall_allowed_chats_set = set(tagall_allowed_chats_map.values())

            is_chat_relevant_for_tagall_triggers = not tagall_allowed_chats_set or chat_id in tagall_allowed_chats_set

            if is_chat_relevant_for_tagall_triggers:
                current_tagall_event = self._tagall_events.get(chat_id)

                stop_triggers_enabled = self._db.get(self.name, f"stop_triggers_enabled_{chat_id}", False)
                activation_triggers_enabled = self._db.get(self.name, f"activation_triggers_enabled_{chat_id}", False)

                # --- Обработка триггера ОСТАНОВКИ TagAll ---
                if stop_triggers_enabled:
                    trigger_stop_messages_raw = self.config["tagall_stop_trigger_message"]
                    parsed_stop_triggers = []
                    for t_raw in trigger_stop_messages_raw.split(','):
                        if t_raw.strip():
                            parsed_stop_triggers.append(self._parse_tagall_trigger_string(t_raw))

                    has_stop_trigger_message = False
                    for base_trigger, config_chat_index in parsed_stop_triggers:
                        if base_trigger in msg_text_lower:
                            if config_chat_index is None:
                                has_stop_trigger_message = True
                                break
                            else:
                                trigger_target_chat_id = tagall_allowed_chats_map.get(config_chat_index)
                                if trigger_target_chat_id is not None and trigger_target_chat_id == chat_id:
                                    has_stop_trigger_message = True
                                    break

                    trigger_stop_user_ids_raw = self.config["tagall_stop_trigger_user_id"]
                    trigger_stop_user_ids = set()
                    for uid_str in trigger_stop_user_ids_raw.split(','):
                        uid_str = uid_str.strip()
                        if uid_str:
                            try:
                                uid = int(uid_str)
                                if uid > 0:
                                    trigger_stop_user_ids.add(uid)
                            except ValueError:
                                logger.warning(f"UniversalMafiaTools: TagAll: Неверный tagall_stop_trigger_user_id в конфигурации: '{uid_str}'. Должен быть целым числом.")

                    is_authorized_stop_user = not trigger_stop_user_ids or (message.sender and message.sender.id in trigger_stop_user_ids)

                    if current_tagall_event and current_tagall_event.state and has_stop_trigger_message and is_authorized_stop_user:
                        current_tagall_event.stop()
                        logger.info(f"UniversalMafiaTools: TagAll: Процесс остановлен триггером в чате {chat_id}.")
                        return

                # --- Обработка триггера АКТИВАЦИИ TagAll ---
                if activation_triggers_enabled:
                    activation_trigger_messages_raw = self.config["tagall_activation_trigger_message"]
                    parsed_activation_triggers = []
                    for t_raw in activation_trigger_messages_raw.split(','):
                        if t_raw.strip():
                            parsed_activation_triggers.append(self._parse_tagall_trigger_string(t_raw))

                    has_activation_trigger_message = False
                    for base_trigger, config_chat_index in parsed_activation_triggers:
                        if base_trigger in msg_text_lower:
                            if config_chat_index is None:
                                has_activation_trigger_message = True
                                break
                            else:
                                trigger_target_chat_id = tagall_allowed_chats_map.get(config_chat_index)
                                if trigger_target_chat_id is not None and trigger_target_chat_id == chat_id:
                                    has_activation_trigger_message = True
                                    break

                    activation_trigger_user_ids_raw = self.config["tagall_activation_trigger_user_id"]
                    activation_trigger_user_ids = set()
                    for uid_str in activation_trigger_user_ids_raw.split(','):
                        uid_str = uid_str.strip()
                        if uid_str:
                            try:
                                uid = int(uid_str)
                                if uid > 0:
                                    activation_trigger_user_ids.add(uid)
                            except ValueError:
                                logger.warning(f"UniversalMafiaTools: TagAll: Неверный tagall_activation_trigger_user_id в конфигурации: '{uid_str}'. Должен быть целым числом.")

                    is_authorized_activation_user = not activation_trigger_user_ids or (message.sender and message.sender.id in activation_trigger_user_ids)

                    if has_activation_trigger_message and is_authorized_activation_user:
                        if current_tagall_event and current_tagall_event.state:
                            logger.info(f"UniversalMafiaTools: TagAll: Уже запущен в чате {chat_id}, игнорируем триггер активации.")
                            return

                        logger.info(f"UniversalMafiaTools: TagAll: Активирован триггерным сообщением '{message.text}' от отправителя {message.sender.id if message.sender else 'unknown'} в чате {chat_id}")

                        event = StopEvent(chat_id)
                        self._tagall_events[chat_id] = event

                        self._client.loop.create_task(self._run_tagall_process(chat_id, "", event, True))
                        return

            # --- General AutoJoinGame Logic (Lower Priority) ---
            if not self.config["enabled"]:
                logger.debug("UniversalMafiaTools: AJG: Модуль выключен. Пропускаю сообщение для AJG функционала.")
                return

            allowed_chats_config = self.config["allowed_chats"]
            role_output_chat_config = self.config["role_tracking_output_chat_id"]
            auto_track_trigger_chat_config = self.config["auto_role_tracking_trigger_chat_id"]

            is_message_from_allowed_chat_ajg = not allowed_chats_config or chat_id in allowed_chats_config
            is_message_from_role_output_specific = role_output_chat_config != 0 and chat_id == role_output_chat_config
            is_message_from_auto_track_trigger_specific = auto_track_trigger_chat_config != 0 and chat_id == auto_track_trigger_chat_config

            if not (is_message_from_allowed_chat_ajg or is_message_from_role_output_specific or is_message_from_auto_track_trigger_specific):
                logger.debug(f"UniversalMafiaTools: AJG: Чат {chat_id} не соответствует никаким условиям активности модуля. Пропускаю сообщение {message.id}.")
                return

            # --- Автоматическое включение отслеживания ролей (AJG) ---
            auto_track_phrases = self.config["auto_track_roles_trigger_phrases"]
            is_trigger_chat_active_ajg = (auto_track_trigger_chat_config == 0 and is_message_from_allowed_chat_ajg) or \
                                         (auto_track_trigger_chat_config != 0 and chat_id == auto_track_trigger_chat_config)

            if (auto_track_phrases and not self.config["role_tracking_enabled"] and is_trigger_chat_active_ajg):
                is_auto_track_trigger_bot = (
                    getattr(sender, 'bot', False) and
                    (not self.config["bot_ids"] or sender_id in self.config["bot_ids"])
                )
                if is_auto_track_trigger_bot and any(p.lower() in msg_text_lower for p in auto_track_phrases):
                    logger.info(f"UniversalMafiaTools: AJG: Обнаружен триггер для автоматического включения отслеживания ролей в сообщении {message.id} от бота {sender_id} в чате {chat_id}.")

                    self.set("role_tracking_enabled", True)
                    self.config["role_tracking_enabled"] = True
                    self._role_tracking_active = True
                    self._role_tracking_start_time = datetime.now()
                    self._tracked_roles_list = []
                    self._tracked_roles_lookup_set.clear()
                    self._update_tracked_roles_patterns()

                    send_to_chat = self.config["role_tracking_output_chat_id"]
                    if send_to_chat == 0:
                        send_to_chat = chat_id

                    send_delay = self.config["send_tracked_roles_delay"]

                    if send_to_chat != 0 and send_delay > 0:
                        if self._send_tracked_roles_task:
                            self._send_tracked_roles_task.cancel()
                            self._send_tracked_roles_task = None
                        self._send_tracked_roles_task = asyncio.create_task(
                            self._send_tracked_roles_list_scheduled(send_delay, send_to_chat)
                        )
                        logger.info(self.strings("auto_role_tracking_activated_with_send").format(
                            duration=self.config["role_tracking_duration"],
                            delay=send_delay,
                            chat_id=send_to_chat
                        ))
                    else:
                        logger.info(self.strings("auto_role_tracking_activated").format(
                            duration=self.config["role_tracking_duration"]
                        ))
                    # Do not return here, AJG logic might still need to process the message if it's also a game join/lynch message.

            # --- Автоматическое выключение отслеживания ролей (AJG) ---
            auto_disable_phrases = self.config["auto_disable_track_roles_trigger_phrases"]
            if (auto_disable_phrases and self.config["role_tracking_enabled"] and is_trigger_chat_active_ajg):
                is_auto_disable_trigger_bot = (
                    getattr(sender, 'bot', False) and
                    (not self.config["bot_ids"] or sender_id in self.config["bot_ids"])
                )
                if is_auto_disable_trigger_bot and any(p.lower() in msg_text_lower for p in auto_disable_phrases):
                    logger.info(f"UniversalMafiaTools: AJG: Обнаружен триггер для автоматического выключения отслеживания ролей в сообщении {message.id} от бота {sender_id} в чате {chat_id}.")

                    self.set("role_tracking_enabled", False)
                    self.config["role_tracking_enabled"] = False
                    self._role_tracking_active = False
                    self._role_tracking_start_time = None
                    self._tracked_roles_list = []
                    self._tracked_roles_lookup_set.clear()
                    if self._send_tracked_roles_task:
                        self._send_tracked_roles_task.cancel()
                        self._send_tracked_roles_task = None

                    logger.info("UniversalMafiaTools: AJG: Автоматическое отслеживание ролей выключено.")
                    await self._client.send_message(chat_id, self.strings("auto_role_tracking_deactivated"))
                    # Do not return here, AJG logic might still need to process the message if it's also a game join/lynch message.

            # --- Логика отслеживания ролей (мониторинг) ---
            if self.config["role_tracking_enabled"] and self._role_tracking_active:
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
                    is_monitoring_active_in_this_chat = False
                    if role_output_chat_config == 0:
                        is_monitoring_active_in_this_chat = is_message_from_allowed_chat_ajg
                    else:
                        is_monitoring_active_in_this_chat = chat_id == role_output_chat_config

                    if is_monitoring_active_in_this_chat:
                        role_announcement_phrases_lower = [p.lower() for p in self.config["role_announcement_phrases"]]
                        is_role_announcement = any(phrase in msg_text_lower for phrase in role_announcement_phrases_lower)

                        if is_role_announcement:
                            found_tracked_role_clean = None
                            is_role_active = True

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
                nickname = msg_text.strip()
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
                    any(phrase.lower() in msg_text_lower for phrase in role_trigger_phrases) and
                    is_message_from_allowed_chat_ajg):
                try:
                    await self._client.forward_messages(
                        entity=role_forward_chat_id,
                        messages=message,
                        from_peer=chat_id
                    )
                    logger.info(self.strings("role_forward_success").format(chat_id=role_forward_chat_id))
                except Exception as e:
                    logger.error(self.strings("role_forward_error").format(chat_id=role_forward_chat_id, error=e))
                return

            # Continue only if message is from an allowed chat for general bot functions
            if not is_message_from_allowed_chat_ajg:
                logger.debug(f"UniversalMafiaTools: AJG: Сообщение {message.id} из чата {chat_id} не соответствует 'allowed_chats' для общих функций бота. Пропускаю.")
                return

            is_general_game_bot = getattr(sender, 'bot', False) and (
                not self.config["bot_ids"] or sender_id in self.config["bot_ids"]
            )

            if not is_general_game_bot:
                logger.debug(f"UniversalMafiaTools: AJG: Сообщение {message.id} от бота {sender_id}, но его ID не в списке разрешенных ботов. Пропускаю.")
                return

            # Логика голосования за конкретного игрока
            if (self.config["player_to_lynch_user_id"] != 0 and
                self._player_nickname_to_lynch and
                any(phrase.lower() in msg_text_lower for phrase in self.config["lynch_player_voting_trigger_phrases"])):

                if not getattr(message, 'buttons', None):
                    logger.warning(f"⚠️ UniversalMafiaTools: AJG: Запрос на голосование за игрока найден (msg_id: {message.id}), но кнопок нет. Пропускаю.")
                    self._player_nickname_to_lynch = None
                    return

                lynch_delays = self.config["lynch_delay"]
                chosen_lynch_delay = random.choice(lynch_delays)

                logger.info(self.strings("player_lynch_triggered").format(nickname=self._player_nickname_to_lynch))
                logger.info(f"⏳ UniversalMafiaTools: AJG: Ожидание {chosen_lynch_delay} секунд перед нажатием кнопки для голосования за игрока сообщения {message.id}...")
                await asyncio.sleep(chosen_lynch_delay)

                player_lynch_button_found = False
                for row in message.buttons:
                    for button in row:
                        try:
                            button_text = str(getattr(button, 'text', ''))
                        except Exception as e:
                            logger.warning(f"UniversalMafiaTools: AJG: Error getting button text for player lynch message {message.id}: {e}")
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
                logger.debug(f"UniversalMafiaTools: AJG: Сообщение {message.id} не содержит ни одну из фраз для активации (вход в игру, общее линчевание/повешение). Пропускаю.")
                return

            if is_general_lynch_message:
                if not getattr(message, 'buttons', None):
                    logger.warning(f"⚠️ UniversalMafiaTools: AJG: Запрос на линчевание/повешение найден (msg_id: {message.id}), но кнопок нет. Пропускаю.")
                    return

                lynch_delays = self.config["lynch_delay"]
                chosen_lynch_delay = random.choice(lynch_delays)

                logger.info(f"⏳ UniversalMafiaTools: AJG: Ожидание {chosen_lynch_delay} секунд перед нажатием кнопки для линчевания/повешения сообщения {message.id}...")
                await asyncio.sleep(chosen_lynch_delay)

                lynch_marker = self.config["lynch_target_marker"]
                target_emoji = "👍"
                success_log_message = f"🎉 UniversalMafiaTools: AJG: Успешно нажата кноп '{target_emoji}' для линчевания/повешения сообщения {message.id}."
                not_found_log_message = self.strings("lynch_button_not_found_positive")

                if lynch_marker and lynch_marker in msg_text:
                    target_emoji = "👎"
                    success_log_message = f"🎉 UniversalMafiaTools: AJG: Успешно нажата кноп '{target_emoji}' для линчевания/повешения с маркером '{lynch_marker}' сообщения {message.id}."
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
                            logger.warning(f"UniversalMafiaTools: AJG: Error getting button text for lynch message {message.id}: {e}")
                            button_text = ''

                        if target_emoji in button_text:
                            logger.info(f"✅ UniversalMafiaTools: AJG: Найдена кноп '{target_emoji}' для линчевания/повешения: '{button_text}'")
                            try:
                                await button.click()
                                logger.info(success_log_message)
                                lynch_button_found = True
                                break
                            except Exception as e:
                                logger.error(f"❌ UniversalMafiaTools: AJG: Ошибка при нажатии кнопки '{target_emoji}' для линчевания/повешения сообщения {message.id}: {e}")
                    if lynch_button_found:
                        break

                if not lynch_button_found:
                    logger.warning(not_found_log_message)

                return

            elif is_game_join:
                logger.info(f"🎮 UniversalMafiaTools: AJG: Найдено сообщение с набором/регистрацией! (msg_id: {message.id}, chat_id: {chat_id})")

                if not getattr(message, 'buttons', None):
                    logger.warning(f"⚠️ UniversalMafiaTools: AJG: Сообщение с набором/регистрацией найдено (msg_id: {message.id}), но кнопок нет. Пропускаю.")
                    return

                delays = self.config["delays"]
                chosen_delay = random.choice(delays)

                logger.info(f"⏳ UniversalMafiaTools: AJG: Ожидание {chosen_delay} секунд перед обработкой сообщения {message.id} (выбрано из {delays})...")
                await asyncio.sleep(chosen_delay)

                keywords_to_check = self._current_button_keywords_to_use
                if not keywords_to_check:
                    logger.warning(f"⚠️ UniversalMafiaTools: AJG: Список активных ключевых слов для кнопок пуст. Ни одна кнопка не будет активирована для сообщения {message.id}.")
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
                            logger.warning(f"UniversalMafiaTools: AJG: Error getting button text for message {message.id}: {e}")
                            button_text = ''

                        if any(keyword in button_text.lower() for keyword in high_priority_keywords):
                            target_button = button
                            logger.info(f"✅ UniversalMafiaTools: AJG: Найдена высокоприоритетная кнопка: '{button_text}'")
                            break
                    if target_button:
                        break

                if not target_button and low_priority_keywords:
                    for row in message.buttons:
                        for button in row:
                            try:
                                button_text = str(getattr(button, 'text', ''))
                            except Exception as e:
                                logger.warning(f"UniversalMafiaTools: AJG: Error getting button text for message {message.id}: {e}")
                                button_text = ''

                            if any(keyword in button_text.lower() for keyword in low_priority_keywords):
                                target_button = button
                                logger.info(f"✅ UniversalMafiaTools: AJG: Найдена низкоприоритетная кнопка (только '{deprioritized_keyword}'): '{button_text}'")
                                break
                        if target_button:
                            break

                if target_button:
                    button_text = str(getattr(target_button, 'text', ''))
                    if getattr(target_button, 'url', None):
                        button_url = target_button.url
                        logger.info(f"🔗 UniversalMafiaTools: AJG: URL кнопки: {button_url}")

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
                            logger.info(f"📤 UniversalMafiaTools: AJG: Deep-Link URL обнаружен. Отправка /start {start_param} боту @{bot_username}")

                            try:
                                await self._client.send_message(
                                    bot_username,
                                    f'/start {start_param}'
                                )
                                logger.info("🎉 UniversalMafiaTools: AJG: Успешно отправлена команда /start (уведомление в чат не отправлено).")
                            except Exception as e:
                                logger.error(f"❌ UniversalMafiaTools: AJG: Ошибка при отправке Deep-Link команды /start для сообщения {message.id}: {e}")
                        else:
                            logger.warning(f"⚠️ UniversalMafiaTools: AJG: Найдена кнопка '{button_text}' с URL '{button_url}', но она не является Deep-Link. Пропускаю.")
                    else:
                        logger.info(f"📤 UniversalMafiaTools: AJG: Найдена кнопка '{button_text}' (CallbackQuery). Нажимаю.")
                        try:
                            await target_button.click()
                            logger.info(f"🎉 UniversalMafiaTools: AJG: Успешно нажата кноп '{button_text}' для присоединения к игре.")
                        except Exception as e:
                            logger.error(f"❌ UniversalMafiaTools: AJG: Ошибка при нажатии кнопки '{button_text}' для присоединения к игре: {e}")
                else:
                    logger.warning(f"⚠️ UniversalMafiaTools: AJG: Кнопка присоединения не найдена под сообщением {message.id} после задержки.")

        except Exception as e:
            logger.exception(f"❌ UniversalMafiaTools: Критическая ошибка в watcher для сообщения {getattr(message, 'id', 'N/A')} в чате {getattr(message, 'chat_id', 'N/A')}: {e}")

    # --- AutoJoinGame Commands (Copied as is, with command_delay) ---

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

        await utils.answer(message, self.strings("dialog_pin_unpin_start_msg").format(action_text_verb="закрепить", chat_id=target_chat_id))
        dialog_pin_success, dialog_pin_msg = await self._toggle_telegram_dialog_pin(target_chat_id, True)

        module_add_success, module_add_msg = self._toggle_module_allowed_chat(target_chat_id, True)
