
Вот обновленный код модуля:

```python
# meta developer: @hdjsfzbxm
# meta name: AutoMafiaTournamentsGame 
# meta version: 2.5.0 # Версия обновлена для добавления функционала PinChatList
# 01000001010101000100111101001010010011100010000001000111010000010100110101000101
# 0100000101010100010011110100100101001110001000000100011101000001
# 0100110101000101001000000100110101000100010101010100110001000111
import logging
import asyncio
import random
import urllib.parse
from datetime import datetime, timedelta
from telethon.tl.types import Message, User, Channel, Chat, User # Added Channel, Chat for type hinting and correct entity handling
from telethon import events
import re
from collections import defaultdict
from typing import Optional, Union, List 
from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class AutoJoinGameMod(loader.Module): # Keep the class name as AutoJoinGameMod for now, as renaming the class itself could break some internal loader mechanisms if not handled carefully. The meta name is the user-facing name.
    """Модуль для автоматического нажатия кнопки при наборе в игру в ботах мафии, а также подтверждения линчевания и повешения, и голосования за конкретного игрока. Дополнительно: пересылка роли в мафии в указанный чат, отслеживание определенных ролей (с разделением на активные/неактивные) и автоматическая отправка списка отслеживаемых ролей в чат после активации. Поддерживает автоматическую активацию и деактивацию отслеживания ролей по ключевым словам. Также включает управление закрепленными чатами.""" # Updated _cls_doc to reflect new functionality

    strings = {
        "name": "AutoMafiaTournamentsGame", 
        "_cls_doc": "Модуль для автоматического нажатия кнопки при наборе в игру в ботах мафии, а также подтверждения линчевания и повешения, и голосования за конкретного игрока. Дополнительно: пересылка роли в мафии в указанный чат, отслеживание определенных ролей (с разделением на активные/неактивные) и автоматическая отправка списка отслеживаемых ролей в чат после активации. Поддерживает автоматическую активацию и деактивацию отслеживания ролей по ключевым словам. Также включает управление закрепленными чатами.", # Updated _cls_doc here as well
        "enabled": "✅ Автовход в игру и автолинчевание включены.",
        "disabled": "❌ Автовход в игру и автолинчевание выключены.",
        "status": "<emoji document_id=5875291072225087249>📊</emoji> Статус автовхода и автолинчевания:\n"
                  "Статус: {}\n"
                  "Задержка входа (секунды): {}\n"
                  "Задержка линчевания (секунды): {}\n"
                  "Боты для отслеживания: {}\n"
                  "Разрешенные чаты: {}\n"
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
                  "\n<emoji document_id=5944122171441618396>📌</emoji> Статус закрепленных чатов:\n" # New section for pinning status
                  "Управление папкой 'Все чаты': {}\n"
                  "Закрепленные чаты: {}",
        "error": "❌ Ошибка при нажатии кнопки: {}",
        "no_button": "⚠️ Кнопка не найдена под сообщением",
        "help_text": """<emoji document_id=5931415565955503486>🤖</emoji> AutoMafiaTournamentsGame - Помощь

<emoji document_id=5935847413859225147>🏀</emoji> Команды для мафии:
<code>.ajgon</code> - Включить автовход в игру и автолинчевание
<code>.ajgoff</code> - Выключить автовход в игру и автолинчевание
<code>.ajgstatus</code> - Показать статус
<code>.ajghelp</code> - Эта справка
<code>.ajgtest</code> - Проверить последнее сообщение с набором в текущем чате
<code>.ajgid</code> - Показать список ID ботов для мафии
<code>.ajgtournaments</code> - Показать информацию о регистрации на турниры
<code>.ajgshowtrackedroles</code> - Показать список найденных отслеживаемых ролей
<code>.ajgset &lt;ID_конфига&gt;</code> - Переключить активную конфигурацию ключевых слов для кнопок. Если <code>&lt;ID_конфига&gt;</code> не указан, покажет текущую активную конфигурацию и доступные ID.

<emoji document_id=5944122171441618396>📌</emoji> Команды для закрепления чатов:
<code>.pinit &lt;chat_id&gt; [&lt;pin_position&gt;]</code> - Закрепить чат по ID. Необязательно: укажите позицию (начиная с 1). Если позиция не указана, чат закрепится вверху.
<code>.unpinit &lt;chat_id&gt;</code> - Открепить чат по ID.
<code>.pinstatus</code> - Показать текущий статус закрепленных чатов.
<code>.pinsetallchats &lt;true/false&gt;</code> - Включить/выключить управление закреплением чатов в папке "Все чаты" (True/False). По умолчанию: False (управляется только в архиве).

<emoji document_id=5877260593901971030>⚙</emoji> Как работает:
Ждет сообщение о наборе в игру или о голосовании (линчевание/повешение) от указанных ботов (или от любого бота, если список пуст).
Автоматически переходит по URL кнопки и отправляет /start для входа в игру.
Если бот спрашивает "Вы точно хотите линчевать..." или "Вы точно хотите повесить...", модуль автоматически нажмет кнопку.
Если в сообщении присутствует настроенный <code>lynch_target_marker</code> (по умолчанию 𝓝𝓚), модуль автоматически нажмет кнопку с эмодзи '👎'. В противном случае, если маркера нет, нажмет '👍'.
Работает только когда включен.
Дополнительно, если настроен <code>player_to_lynch_user_id</code>, модуль будет ожидать сообщение с ником игрока от этого пользователя. Как только ник получен, модуль будет искать сообщение о голосовании от *одного из ботов из списка* <code>bot_ids</code>, содержащее <code>lynch_player_voting_trigger_phrases</code>, и затем автоматически нажмет кнопку с соответствующим ником игрока.
<b>Важное обновление:</b> Если сообщение от <code>player_to_lynch_user_id</code> начинается с символа <code>!</code>, этот символ будет автоматически удален из ника игрока перед использованием.
<b>Обновление 2.4.0:</b> При линчевании конкретного игрока, модуль теперь будет искать ник игрока как <b>подстроку</b> в тексте кнопки (регистронезависимо), а не только как точное совпадение. Это позволяет корректно обрабатывать кнопки, содержащие никнейм игрока вместе с дополнительными символами.
<b>Новая функция:</b> Модуль может автоматически пересылать сообщения с вашей ролью в мафии в указанный чат. Это работает, когда бот отправляет вам роль в приватном чате, и сообщение содержит одну из настроенных фраз-триггеров.
<b>Улучшенная функция:</b> Модуль может отслеживать сообщения пользователей, объявляющих свою роль, и сохранять их ники и <b>конкретную объявленную роль</b> в список, если эта роль соответствует одной из настроенных фраз.
Отслеживание включается/выключается автоматически по настроенным фразам-триггерам от ботов, а его длительность настраивается в конфиге.
<b>Новая функция:</b> Модуль может автоматически отправлять список отслеживаемых ролей в указанный чат через заданное время после активации отслеживания ролей.
<b>Новая функция:</b> Модуль может автоматически включать отслеживание ролей при получении сообщения, содержащего определенные фразы, от указанных ботов.
<b>Новая функция:</b> Модуль может автоматически <b>выключать</b> отслеживание ролей при получении сообщения, содержащего определенные фразы, от указанных ботов.
<b>Улучшение:</b> Теперь модуль более точно определяет роли, включая составные фразы, и позволяет помечать роли как 'неактивные' с помощью суффикса <code>(н)</code> для раздельного отображения.
<b>Приоритет кнопок:</b> Теперь модуль отдает предпочтение кнопкам, содержащим <b>другие ключевые слова</b> из активной конфигурации, если на кнопке также есть слово "присоединиться". Кнопка с только "присоединиться" будет нажата только в том случае, если других подходящих кнопок не найдено.
<b>Закрепление чатов:</b> Модуль может закреплять и откреплять чаты по их ID. Не-приватные чаты (группы, каналы) при закреплении перемещаются в папку "Архивные чаты" (или "Все чаты", если настроено).

<emoji document_id=5843843420468024653>⭐️</emoji> Настройки:
В конфиге модуля можно изменить задержку(и) перед нажатием. Если указано несколько значений, будет выбрано случайное.
Можно указать список ID ботов, от которых ожидать сообщение о наборе.
<b>Обновление:</b> Теперь параметр <code>bot_ids</code> включает в себя все боты, от которых ожидаются триггеры, включая ботов для голосования за игроков. Если список пуст, модуль будет работать со всеми ботами.
Можно указать список ID чатов, в которых модуль будет активен. Если список пуст, модуль будет работать во всех чатах.
<b>Настройка:</b> <code>button_keyword_configs_string</code> - строка с конфигурациями ключевых слов кнопок. Формат: <code>"Ключевое слово 1 (ID_конфига), Ключевое слово 2 (Другой_ID)"</code>. Например: <code>"присоединиться (1), играть (1), 🙋 (2), 🎮 (2)"</code>. Ключевые слова регистронезависимы. <b>Скобки с ID не учитываются при поиске кнопок.</b>
<b>Новая настройка:</b> <code>active_button_config_id</code> - ID активной конфигурации ключевых слов из <code>button_keyword_configs_string</code>. Например: <code>"1"</code> или <code>"default"</code>.
<b>Обновление: Если кнопка содержит URL вида <code>t.me/bot_username?start=param</code>, модуль автоматически отправит команду <code>/start &lt;param&gt;</code> соответствующему боту. Этот режим теперь активен для любого совпадения по <code>button_keywords</code> с Deep-Link URL.</b>
<b>Настройка:</b> <code>lynch_target_marker</code> - строка-маркер, которая, если присутствует в сообщении-триггере для голосования, заставит модуль нажать кнопку '👎'. Если отсутствует или маркер не указан (пустая строка), нажимается '👍'. По умолчанию: "" (пусто).
<b>Настройка:</b> <code>game_join_trigger_phrases</code> - список фраз, которые модуль будет искать в сообщениях для активации автовхода в игру. По умолчанию: <code>[\"Ведётся набор в игру\", \"Регистрация началась!\"]</code>.
<b>Настройка:</b> <code>lynch_trigger_phrases</code> - список фраз, которые модуль будет искать в сообщениях для активации автолинчевания. По умолчанию: <code>[\"Вы точно хотите линчевать\"]</code>.
<b>Настройка:</b> <code>lynch_hang_trigger_phrases</code> - список фраз, которые модуль будет искать в сообщениях для активации автоповешения. По умолчанию: <code>[\"Вы точно хотите повесить\"]</code>.
<b>Настройка:</b> <code>player_to_lynch_user_id</code> - ID пользователя, чье сообщение будет использоваться как ник игрока для линчевания. Если <code>0</code>, то функция отключена.
<b>Обновление:</b> <code>lynch_voting_bot_id</code> был объединен с <code>bot_ids</code>. Боты, отправляющие сообщения для голосования за конкретного игрока, теперь должны быть включены в список <code>bot_ids</code>.
<b>Настройка:</b> <code>lynch_player_voting_trigger_phrases</code> - список фраз, которые модуль будет искать в сообщениях от *любого бота из списка* <code>bot_ids</code> для активации голосования за конкретного игрока. По умолчанию: <code>[\"Пришло время искать виноватых!\", \"Кого ты хочешь повесить?\", \"Пришло время определить и наказать виновных\", \"Пришло время искать виноватых! Кого ты хочешь линчевать?\"]</code>.
<b>Настройка:</b> <code>role_forward_chat_id</code> - ID чата, куда будет пересылаться полученная роль в мафии. Если <code>0</code>, функция отключена.
<b>Настройка:</b> <code>role_trigger_phrases</code> - список фраз, которые модуль будет искать в сообщениях от бота в ЛС для определения роли. По умолчанию: <code>[\"Ваша роль:\", \"Ты - \", \"Твоя роль:\", \"Ты стал(а) \"]</code>.
<b>Настройка:</b> <code>role_tracking_enabled</code> - Включено ли отслеживание ролей. По умолчанию: <code>False</code>.
<b>Настройка:</b> <code>role_tracking_duration</code> - Длительность отслеживания ролей в секундах. По умолчанию: <code>300</code> (5 минут).
<b>Улучшенная настройка:</b> <code>tracked_roles_to_monitor</code> - Список фраз, указывающих на роли, которые нужно отслеживать. Модуль будет искать эти фразы в объявлениях ролей пользователей. Если роль должна быть "неактивной" (т.е. отображаться в отдельном списке), добавьте к ней суффикс <code>(н)</code>, например: <code>[\"мирный житель\", \"мафия (н)\", \"комиссар\"]</code>.
<b>Настройка:</b> <code>role_announcement_phrases</code> - Список фраз, которые пользователи могут использовать для объявления своей роли. По умолчанию: <code>[\"Моя роль:\", \"Я - \", \"Моя роль\", \"Я \", \"роль:\", \"моя роль\"]</code>.
<b>Новая настройка:</b> <code>send_tracked_roles_chat_id</code> - ID чата, куда будет отправлен список отслеживаемых ролей после активации. Если <code>0</code>, функция отключена.
<b>Новая настройка:</b> <code>send_tracked_roles_delay</code> - Задержка в секундах, через которую будет отправлен список отслеживаемых ролей после активации отслеживания.
<b>Новая настройка:</b> <code>auto_track_roles_trigger_phrases</code> - Список фраз, которые модуль будет искать в сообщениях для автоматического включения отслеживания ролей. По умолчанию: <code>[]</code>.
<b>Новая настройка:</b> <code>auto_track_roles_bot_ids</code> - Список ID ботов, от которых ожидается сообщение с фразами для автоматического включения отслеживания ролей. Если список пуст, сообщения будут отслеживаться от любого бота. По умолчанию: <code>[]</code>.
<b>Новая настройка:</b> <code>auto_disable_track_roles_trigger_phrases</code> - Список фраз, которые модуль будет искать в сообщениях для автоматического выключения отслеживания ролей. По умолчанию: <code>[]</code>.
<b>Новая настройка:</b> <code>auto_disable_track_roles_bot_ids</code> - Список ID ботов, от которых ожидается сообщение с фразами для автоматического выключения отслеживания ролей. Если список пуст, сообщения будут отслеживаться от любого бота. По умолчанию: <code>[]</code>.
<b>Новая настройка:</b> <code>pinned_chats_order</code> - Список закрепленных чатов и их позиций. Формат: <code>[{"chat_id": 12345, "pin_position": 1}, {"chat_id": 67890, "pin_position": 2}]</code>.
<b>Новая настройка:</b> <code>manage_all_chats_folder</code> - Включено ли управление закреплением чатов в папке "Все чаты". Если False, чаты закрепляются в архиве. По умолчанию: False.
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

.cfg AutoMafiaTournamentsGame button_keyword_configs_string""", 
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
        "time_remaining_format": "{minutes}м {seconds}s",
        "no_time_remaining": "N/A",
        "tracked_roles_send_success": "🎉 AutoMafiaTournamentsGame: Список отслеживаемых ролей успешно отправлен в чат <code>{chat_id}</code>.", 
        "tracked_roles_send_error": "❌ AutoMafiaTournamentsGame: Ошибка при отправке списка отслеживаемых ролей в чат <code>{chat_id}</code>: {error}", 
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
        "switch_keywords_no_configs": "⚠️ Нет настроенных конфигураций ключевых слов. Используйте <code>.cfg AutoMafiaTournamentsGame button_keyword_configs_string</code> для настройки.", 
        "switch_keywords_current": "ℹ️ Активная конфигурация уже <code>{config_id}</code>.",
        "switch_keywords_usage": "ℹ️ Текущая активная конфигурация: <code>{current_id}</code>. Ключевые слова: {current_keywords}\nДоступные ID: {available_ids}.\nИспользуйте <code>.ajgset &lt;ID_конфига&gt;</code> для переключения.",
        # New strings for PinChatList functionality
        "pin_chat_success": "✅ Чат <code>{chat_name}</code> (ID: <code>{chat_id}</code>) успешно закреплен на позиции {position}.",
        "pin_chat_success_archived": "✅ Чат <code>{chat_name}</code> (ID: <code>{chat_id}</code>) успешно закреплен на позиции {position} в архиве.",
        "pin_chat_already_pinned": "ℹ️ Чат <code>{chat_name}</code> (ID: <code>{chat_id}</code>) уже закреплен на позиции {position}.",
        "pin_chat_error": "❌ Ошибка при закреплении чата <code>{chat_id}</code>: {error}",
        "pin_chat_not_found": "⚠️ Чат с ID <code>{chat_id}</code> не найден или недоступен.",
        "unpin_chat_success": "✅ Чат <code>{chat_name}</code> (ID: <code>{chat_id}</code>) успешно откреплен.",
        "unpin_chat_not_found": "⚠️ Чат с ID <code>{chat_id}</code> не найден в списке закрепленных или недоступен.",
        "unpin_chat_error": "❌ Ошибка при откреплении чата <code>{chat_id}</code>: {error}",
        "no_pinned_chats": "ℹ️ Нет закрепленных чатов.",
        "pinned_chats_list_header": "<emoji document_id=5944122171441618396>📌</emoji> Текущие закрепленные чаты:\n",
        "pinned_chat_entry": "• <code>{chat_name}</code> (ID: <code>{chat_id}</code>) на позиции {position}",
        "pin_invalid_position": "⚠️ Неверный номер позиции. Позиция должна быть числом больше 0.",
        "manage_all_chats_set": "✅ Управление закреплением чатов в папке 'Все чаты' установлено на <code>{value}</code>.",
        "manage_all_chats_invalid_value": "⚠️ Неверное значение. Используйте 'true' или 'false'.",
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
                lambda: "Список фраз, указывающих на роли, которые нужно отслеживать. Модуль будет искать эти фразы в объявлениях ролей пользователей. Если роль должна быть 'неактивной', добавьте к ней суффикс '(н)', например: ['мирный житель', 'мафия (н)', 'комиссар'].",
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
            # New config for PinChatList functionality
            loader.ConfigValue(
                "pinned_chats_order",
                [],
                lambda: "Список закрепленных чатов и их позиций. Формат: [{'chat_id': 12345, 'pin_position': 1}, {'chat_id': 67890, 'pin_position': 2}].",
                validator=loader.validators.Series(
                    loader.validators.Dict(
                        dict_validator={
                            "chat_id": loader.validators.Integer(),
                            "pin_position": loader.validators.Integer(minimum=1),
                        }
                    )
                )
            ),
            loader.ConfigValue(
                "manage_all_chats_folder",
                False,
                lambda: "Включено ли управление закреплением чатов в папке 'Все чаты'. Если False, чаты закрепляются в архиве.",
                validator=loader.validators.Boolean()
            ),
        )

        self._player_nickname_to_lynch = None 
        self._role_tracking_active = False
        self._role_tracking_start_time = None
        self._tracked_roles_list = []
        self._self_id = None 
        self._processed_messages = set() 
        self._processed_messages_cleanup_task = None 
        self._send_tracked_roles_task = None
        self._pinned_chats_task = None # New task for initial pinning

        self._parsed_button_keywords: dict[str, list[str]] = {}
        self._current_button_keywords_to_use: list[str] = []

    async def client_ready(self, client, _):
        self._client = client
        self._self_id = (await self._client.get_me()).id 
        if self._processed_messages_cleanup_task is None:
            self._processed_messages_cleanup_task = asyncio.create_task(self._cleanup_processed_messages_loop())
        
        # Инициализация при запуске, важно, чтобы всегда были актуальные keywords
        self._update_button_keywords_from_config()
        
        # Initial pinning setup
        if self._pinned_chats_task is None:
            self._pinned_chats_task = asyncio.create_task(self._initial_pin_setup())


    async def _cleanup_processed_messages_loop(self):
        """Периодически очищает набор обработанных ID сообщений."""
        while True:
            await asyncio.sleep(300) 
            if self._processed_messages:
                logger.debug(f"AutoMafiaTournamentsGame: Очистка {len(self._processed_messages)} обработанных ID сообщений.") 
                self._processed_messages.clear()
            
    async def _on_unload(self):
        """Останавливает задачи при выгрузке модуля."""
        if self._processed_messages_cleanup_task:
            self._processed_messages_cleanup_task.cancel()
            try:
                await self._processed_messages_cleanup_task
            except asyncio.CancelledError:
                logger.debug("AutoMafiaTournamentsGame: Задача очистки обработанных сообщений отменена.") 
        
        if self._send_tracked_roles_task:
            self._send_tracked_roles_task.cancel()
            try:
                await self._send_tracked_roles_task
            except asyncio.CancelledError:
                logger.debug("AutoMafiaTournamentsGame: Задача отправки списка отслеживаемых ролей отменена при выгрузке.")

        if self._pinned_chats_task: # Cancel pinning task on unload
            self._pinned_chats_task.cancel()
            try:
                await self._pinned_chats_task
            except asyncio.CancelledError:
                logger.debug("AutoMafiaTournamentsGame: Задача инициализации закрепления чатов отменена при выгрузке.")


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
                logger.warning(f"AutoMafiaTournamentsGame: Не удалось разобрать часть конфига 'button_keyword_configs_string': '{entry}'. Ожидается формат 'Ключевое слово (ID_конфига)'. Пропускаю.") 
        return dict(parsed_configs)

    def _update_button_keywords_from_config(self):
        """Обновляет активные ключевые слова на основе конфига."""
        self._parsed_button_keywords = self._parse_button_keywords_string(self.config["button_keyword_configs_string"])
        
        active_id = self.config["active_button_config_id"]
        
        if active_id and active_id in self._parsed_button_keywords:
            self._current_button_keywords_to_use = self._parsed_button_keywords[active_id]
            logger.info(f"AutoMafiaTournamentsGame: Активная конфигурация ключевых слов кнопок установлена на '{active_id}'. Используются ключевые слова: {self._current_button_keywords_to_use}") 
        elif self._parsed_button_keywords:
            # Если активный ID не задан или не найден, пробуем использовать первый доступный
            first_id = next(iter(self._parsed_button_keywords))
            # Используем self.set() для сохранения изменения в конфиг, и обновляем self.config
            self.set("active_button_config_id", first_id) 
            self.config["active_button_config_id"] = first_id # Явно обновляем in-memory config
            self._current_button_keywords_to_use = self._parsed_button_keywords[first_id]
            logger.warning(f"AutoMafiaTournamentsGame: Активная конфигурация ключевых слов кнопок '{active_id}' не найдена или не установлена. Установлено на первую доступную: '{first_id}'.") 
        else:
            self._current_button_keywords_to_use = []
            self.set("active_button_config_id", "") # Очищаем, если нет конфигов
            self.config["active_button_config_id"] = "" # Явно обновляем in-memory config
            logger.warning("AutoMafiaTournamentsGame: Нет настроенных конфигураций ключевых слов кнопок. Модуль не будет активировать кнопки по ключевым словам.") 


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
                logger.debug("AutoMafiaTournamentsGame: Отправка списка отслеживаемых ролей отменена, так как отслеживание неактивно.") 
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
            logger.debug("AutoMafiaTournamentsGame: Задача по отправке списка отслеживаемых ролей отменена.") 
        except Exception as e:
            logger.error(self.strings("tracked_roles_send_error").format(chat_id=chat_id, error=e))

    # --- PinChatList functions start ---
    async def _initial_pin_setup(self):
        """Initial setup for pinning chats based on config."""
        try:
            logger.debug("AutoMafiaTournamentsGame: Выполняется начальная настройка закрепленных чатов.")
            for chat_data in self.config["pinned_chats_order"]:
                chat_id = chat_data["chat_id"]
                pin_position = chat_data["pin_position"]
                # Pass message=None for initial setup since there's no original message to reply to
                await self._pin_chat_list_actual(chat_id, pin_position, message=None, initial_setup=True)
            logger.debug("AutoMafiaTournamentsGame: Начальная настройка закрепленных чатов завершена.")
        except asyncio.CancelledError:
            logger.debug("AutoMafiaTournamentsGame: Задача начальной настройки закрепленных чатов отменена.")
        except Exception as e:
            logger.error(f"AutoMafiaTournamentsGame: Ошибка при начальной настройке закрепленных чатов: {e}")

    async def _pin_chat_list_actual(self, chat_id: int, pin_position: int, message: Optional[Message], initial_setup: bool = False):
        """Actual logic to pin a chat."""
        try:
            entity = await self._client.get_entity(chat_id)
            chat_name = getattr(entity, 'title', getattr(entity, 'first_name', str(chat_id)))

            # Determine if it's a private chat (User) vs. group/channel (Chat/Channel)
            is_private = isinstance(entity, User) and not getattr(entity, 'bot', False) and not getattr(entity, 'is_self', False)
            
            # If manage_all_chats_folder is False AND it's not a private chat, then pin to archive
            archive_mode = not self.config["manage_all_chats_folder"] and not is_private

            await self._client.pin_chat(
                entity=chat_id,
                pin_position=pin_position,
                archive=archive_mode,
                silent=True # Always pin silently
            )
            if not initial_setup and message: # Only send feedback if not initial setup and message is provided
                if archive_mode:
                    await utils.answer(message, self.strings("pin_chat_success_archived").format(chat_name=chat_name, chat_id=chat_id, position=pin_position))
                else:
                    await utils.answer(message, self.strings("pin_chat_success").format(chat_name=chat_name, chat_id=chat_id, position=pin_position))
            logger.info(f"AutoMafiaTournamentsGame: Чат {chat_id} успешно закреплен на позиции {pin_position} (архив: {archive_mode}).")

        except Exception as e:
            logger.error(f"AutoMafiaTournamentsGame: Ошибка при закреплении чата {chat_id}: {e}")
            if not initial_setup and message: # Only send feedback if not initial setup and message is provided
                await utils.answer(message, self.strings("pin_chat_error").format(chat_id=chat_id, error=e))

    async def _unpin_chat_list_actual(self, chat_id: int, message: Message): # Added message arg for feedback
        """Actual logic to unpin a chat."""
        try:
            entity = await self._client.get_entity(chat_id)
            chat_name = getattr(entity, 'title', getattr(entity, 'first_name', str(chat_id)))

            is_private = isinstance(entity, User) and not getattr(entity, 'bot', False) and not getattr(entity, 'is_self', False)
            archive_mode = not self.config["manage_all_chats_folder"] and not is_private

            await self._client.unpin_chat(
                entity=chat_id,
                archive=archive_mode
            )
            await utils.answer(message, self.strings("unpin_chat_success").format(chat_name=chat_name, chat_id=chat_id))
            logger.info(f"AutoMafiaTournamentsGame: Чат {chat_id} успешно откреплен.")
        except Exception as e:
            logger.error(f"AutoMafiaTournamentsGame: Ошибка при откреплении чата {chat_id}: {e}")
            await utils.answer(message, self.strings("unpin_chat_error").format(chat_id=chat_id, error=e))

    def _update_pinned_chats_config(self, chat_id: int, pin_position: Optional[int] = None, action: str = "add"):
        """Adds, updates, or removes chat from pinned_chats_order in config."""
        pinned_chats = list(self.config["pinned_chats_order"]) # Create a mutable copy

        if action == "add":
            # Remove existing entry for this chat_id if it exists, to prevent duplicates and handle updates
            pinned_chats = [c for c in pinned_chats if c["chat_id"] != chat_id]
            
            # Determine the actual insert position (0-based for list operations)
            if pin_position is not None and 1 <= pin_position <= len(pinned_chats) + 1:
                insert_index = pin_position - 1
            else:
                # If no position or invalid, add to the end
                insert_index = len(pinned_chats) 

            # Insert the new chat data
            new_chat_data = {"chat_id": chat_id, "pin_position": 0} # position will be re-numbered
            pinned_chats.insert(insert_index, new_chat_data)
            
            # Re-number all pins to ensure consecutive order
            for i, chat_data in enumerate(pinned_chats):
                chat_data["pin_position"] = i + 1

        elif action == "remove":
            # Filter out the chat to be removed
            pinned_chats = [c for c in pinned_chats if c["chat_id"] != chat_id]
            # Re-number remaining pins
            for i, chat_data in enumerate(pinned_chats):
                chat_data["pin_position"] = i + 1

        self.set("pinned_chats_order", pinned_chats)
        self.config["pinned_chats_order"] = pinned_chats # Update in-memory config

    # --- PinChatList commands start ---

    @loader.command(ru_doc="Закрепить чат по ID. Необязательно: укажите позицию (начиная с 1). Если позиция не указана, чат закрепится вверху.")
    async def pinit(self, message: Message):
        """Pin a chat by ID. Optional: specify pin_position (1-based)."""
        args = utils.get_args(message)
        if not args:
            await utils.answer(message, self.strings("pin_chat_error").format(chat_id="N/A", error="Не указан ID чата."))
            return

        try:
            chat_id = int(args[0])
        except ValueError:
            await utils.answer(message, self.strings("pin_chat_error").format(chat_id=args[0], error="Неверный формат ID чата. Ожидается число."))
            return

        pin_position = None
        if len(args) > 1:
            try:
                pin_position = int(args[1])
                if pin_position <= 0:
                    await utils.answer(message, self.strings("pin_invalid_position"))
                    return
            except ValueError:
                await utils.answer(message, self.strings("pin_invalid_position"))
                return

        try:
            entity = await self._client.get_entity(chat_id)
            chat_name = getattr(entity, 'title', getattr(entity, 'first_name', str(chat_id)))

            current_pinned = [c for c in self.config["pinned_chats_order"] if c["chat_id"] == chat_id]
            if current_pinned:
                # If already pinned, just update position if specified, otherwise inform
                if pin_position is not None and current_pinned[0]["pin_position"] != pin_position:
                    self._update_pinned_chats_config(chat_id, pin_position, "add") # "add" action re-inserts and re-numbers
                    await self._pin_chat_list_actual(chat_id, pin_position, message)
                    return # Exit after updating
                else:
                    await utils.answer(message, self.strings("pin_chat_already_pinned").format(chat_name=chat_name, chat_id=chat_id, position=current_pinned[0]["pin_position"]))
                    return
            
            # If not pinned, add it
            if pin_position is None:
                # Default to top if no position provided and it's a new pin
                pin_position = 1 

            self._update_pinned_chats_config(chat_id, pin_position, "add")
            # The actual pinning should happen *after* config is updated and position determined
            # The _pin_chat_list_actual handles sending success/error messages to the user
            await self._pin_chat_list_actual(chat_id, pin_position, message, initial_setup=False)
            
        except ValueError: # get_entity might raise ValueError if ID is invalid or not found
            await utils.answer(message, self.strings("pin_chat_not_found").format(chat_id=chat_id))
        except Exception as e:
            logger.error(f"AutoMafiaTournamentsGame: Ошибка при выполнении .pinit для чата {chat_id}: {e}")
            await utils.answer(message, self.strings("pin_chat_error").format(chat_id=chat_id, error=e))

    @loader.command(ru_doc="Открепить чат по ID.")
    async def unpinit(self, message: Message):
        """Unpin a chat by ID."""
        args = utils.get_args(message)
        if not args:
            await utils.answer(message, self.strings("unpin_chat_error").format(chat_id="N/A", error="Не указан ID чата."))
            return

        try:
            chat_id = int(args[0])
        except ValueError:
            await utils.answer(message, self.strings("unpin_chat_error").format(chat_id=args[0], error="Неверный формат ID чата. Ожидается число."))
            return

        found_in_config = any(c["chat_id"] == chat_id for c in self.config["pinned_chats_order"])
        if not found_in_config:
            await utils.answer(message, self.strings("unpin_chat_not_found").format(chat_id=chat_id))
            return
        
        self._update_pinned_chats_config(chat_id, action="remove")
        await self._unpin_chat_list_actual(chat_id, message) # Pass message here


    @loader.command(ru_doc="Показать текущий статус закрепленных чатов.")
    async def pinstatus(self, message: Message):
        """Show current pinned chats status."""
        manage_all_chats_display = "✅ Включено" if self.config["manage_all_chats_folder"] else "❌ Выключено"
        
        pinned_chats_display_list = []
        if self.config["pinned_chats_order"]:
            # Sort by pin_position before displaying
            sorted_pinned_chats = sorted(self.config["pinned_chats_order"], key=lambda x: x["pin_position"])
            for chat_data in sorted_pinned_chats:
                chat_id = chat_data["chat_id"]
                pin_position = chat_data["pin_position"]
                chat_name = str(chat_id) # Default name
                try:
                    entity = await self._client.get_entity(chat_id)
                    chat_name = getattr(entity, 'title', getattr(entity, 'first_name', str(chat_id)))
                except Exception as e:
                    logger.warning(f"AutoMafiaTournamentsGame: Не удалось получить сущность для чата ID {chat_id}: {e}")
                
                pinned_chats_display_list.append(self.strings("pinned_chat_entry").format(chat_name=chat_name, chat_id=chat_id, position=pin_position))
            
            pinned_chats_display = self.strings("pinned_chats_list_header") + "\n".join(pinned_chats_display_list)
        else:
            pinned_chats_display = self.strings("no_pinned_chats")

        # Construct the full status message, including all fields
        status_text = self.strings("status").format(
            "🟢 Включен" if self.config["enabled"] else "🔴 Выключен", 
            f"[{', '.join(map(str, self.config['delays']))}]" if len(self.config['delays']) > 1 else str(self.config['delays'][0]), 
            f"[{', '.join(map(str, self.config['lynch_delay']))}]" if len(self.config['lynch_delay']) > 1 else str(self.config['lynch_delay'][0]),
            ", ".join(map(str, self.config["bot_ids"])) if self.config["bot_ids"] else "Не указаны (любой бот)", 
            ", ".join(map(str, self.config["allowed_chats"])) if self.config["allowed_chats"] else "Все чаты", 
            self.config["button_keyword_configs_string"] if self.config["button_keyword_configs_string"] else "(пусто)",
            self.config["active_button_config_id"] if self.config["active_button_config_id"] else "(не задан)",
            ", ".join(self._current_button_keywords_to_use) if self._current_button_keywords_to_use else "(пусто)",
            ", ".join(self._parsed_button_keywords.keys()) if self._parsed_button_keywords else "(нет)",
            "🟢 Активен (автоматически обрабатывает Deep-Link URL, если они есть у подходящих кнопок)", 
            self.config["lynch_target_marker"] if self.config["lynch_target_marker"] else "(пусто)",
            ", ".join(self.config["game_join_trigger_phrases"]) if self.config["game_join_trigger_phrases"] else "(пусто)",
            ", ".join(self.config["lynch_trigger_phrases"]) if self.config["lynch_trigger_phrases"] else "(пусто)",
            ", ".join(self.config["lynch_hang_trigger_phrases"]) if self.config["lynch_hang_trigger_phrases"] else "(пусто)",
            str(self.config["player_to_lynch_user_id"]) if self.config["player_to_lynch_user_id"] else "Отключено (0)",
            ", ".join(self.config["lynch_player_voting_trigger_phrases"]) if self.config["lynch_player_voting_trigger_phrases"] else "(пусто)",
            self._player_nickname_to_lynch if self._player_nickname_to_lynch else "(нет)",
            str(self.config["role_forward_chat_id"]) if self.config["role_forward_chat_id"] else self.strings("role_forward_chat_id_display"),
            ", ".join(self.config["role_trigger_phrases"]) if self.config["role_trigger_phrases"] else self.strings("role_forward_trigger_phrases_display"),
            self.strings("role_tracking_status_active") if self.config["role_tracking_enabled"] and self._role_tracking_active else self.strings("role_tracking_status_inactive"),
            str(self.config["role_tracking_duration"]),
            ", ".join(self.config["tracked_roles_to_monitor"]) if self.config["tracked_roles_to_monitor"] else "(пусто)",
            ", ".join(self.config["role_announcement_phrases"]) if self.config["role_announcement_phrases"] else "(пусто)",
            len(self._tracked_roles_list),
            self._get_time_remaining_display(), # Helper function to format time
            str(self.config["send_tracked_roles_chat_id"]) if self.config["send_tracked_roles_chat_id"] else self.strings("send_tracked_roles_chat_id_display"),
            str(self.config["send_tracked_roles_delay"]) if self.config["send_tracked_roles_delay"] > 0 else self.strings("send_tracked_roles_delay_display"),
            ", ".join(self.config["auto_track_roles_trigger_phrases"]) if self.config["auto_track_roles_trigger_phrases"] else self.strings("auto_track_roles_trigger_phrases_display"),
            ", ".join(map(str, self.config["auto_track_roles_bot_ids"])) if self.config["auto_track_roles_bot_ids"] else self.strings("auto_track_roles_bot_ids_display"),
            ", ".join(self.config["auto_disable_track_roles_trigger_phrases"]) if self.config["auto_disable_track_roles_trigger_phrases"] else self.strings("auto_disable_track_roles_trigger_phrases_display"),
            ", ".join(map(str, self.config["auto_disable_track_roles_bot_ids"])) if self.config["auto_disable_track_roles_bot_ids"] else self.strings("auto_disable_track_roles_bot_ids_display"),
            manage_all_chats_display, # New arg
            pinned_chats_display # New arg
        )
        await utils.answer(message, status_text)

    # Helper function for status command to avoid repetition
    def _get_time_remaining_display(self) -> str:
        if self._role_tracking_active and self._role_tracking_start_time:
            time_elapsed = datetime.now() - self._role_tracking_start_time
            remaining_seconds = self.config["role_tracking_duration"] - time_elapsed.total_seconds()
            if remaining_seconds > 0:
                minutes, seconds = divmod(int(remaining_seconds), 60)
                return self.strings("time_remaining_format").format(minutes=minutes, seconds=seconds)
            else:
                return "Истекло"
        return self.strings("no_time_remaining")


    @loader.command(ru_doc="Включить/выключить управление закреплением чатов в папке 'Все чаты' (True/False). По умолчанию: False (управляется только в архиве).")
    async def pinsetallchats(self, message: Message):
        """Set whether to manage pinning in 'All Chats' folder."""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("manage_all_chats_invalid_value"))
            return
        
        value = args.lower()
        if value == "true":
            self.set("manage_all_chats_folder", True)
            self.config["manage_all_chats_folder"] = True # Update in-memory
            await utils.answer(message, self.strings("manage_all_chats_set").format(value="True"))
        elif value == "false":
            self.set("manage_all_chats_folder", False)
            self.config["manage_all_chats_folder"] = False # Update in-memory
            await utils.answer(message, self.strings("manage_all_chats_set").format(value="False"))
        else:
            await utils.answer(message, self.strings("manage_all_chats_invalid_value"))
    # --- PinChatList functions end ---


    @loader.command(ru_doc="Включить автовход в игру и автолинчевание")
    async def ajgon(self, message: Message):
        """Включить автовход в игру и автолинчевание"""
        self.set("enabled", True) 
        self.config["enabled"] = True 
        await utils.answer(message, self.strings("enabled"))

    @loader.command(ru_doc="Выключить автовход в игру и автолинчевание")
    async def ajgoff(self, message: Message):
        """Выключить автовход в игру и автолинчевание"""
        self.set("enabled", False) 
        self.config["enabled"] = False 
        self.set("role_tracking_enabled", False) 
        self.config["role_tracking_enabled"] = False 
        self._player_nickname_to_lynch = None 
        self._role_tracking_active = False 
        self._role_tracking_start_time = None
        self._tracked_roles_list = []
        self._processed_messages.clear() 
        if self._send_tracked_roles_task:
            self._send_tracked_roles_task.cancel()
            self._send_tracked_roles_task = None
        await utils.answer(message, self.strings("disabled"))

    @loader.command(ru_doc="Показать список найденных отслеживаемых ролей")
    async def ajgshowtrackedroles(self, message: Message):
        """Показать список найденных отслеживаемых ролей"""
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
        
        await utils.answer(message, message_text)

    @loader.command(ru_doc="Переключить активную конфигурацию ключевых слов для кнопок. Если ID_конфига не указан, покажет текущую активную конфигурацию и доступные ID.")
    async def ajgset(self, message: Message): 
        """Переключить активную конфигурацию ключевых слов для кнопок.
        Пример: .ajgset 1
        Используйте без аргументов, чтобы увидеть текущую активную конфигурацию и доступные ID."""
        
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
        # Delegating to pinstatus to avoid code duplication in status generation
        await self.pinstatus(message)


    @loader.command(ru_doc="Показать справку")
    async def ajghelp(self, message: Message):
        """Показать справку"""
        await utils.answer(message, self.strings("help_text"))

    @loader.command(ru_doc="Проверить последнее сообщение с набором")
    async def ajgtest(self, message: Message):
        """Проверить последнее сообщение с набором в текущем чате"""
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
            logger.exception(f"❌ AutoMafiaTournamentsGame: Критическая ошибка в ajgtest: {e}") # Updated module name
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
                logger.debug("AutoMafiaTournamentsGame: Модуль выключен. Пропускаю сообщение.") 
                return

            if not getattr(message, 'text', None):
                logger.debug(f"AutoMafiaTournamentsGame: Сообщение {message.id} не содержит текста. Пропускаю.") 
                return
            
            message_identifier = (message.chat_id, message.id)
            if message_identifier in self._processed_messages:
                logger.debug(f"AutoMafiaTournamentsGame: Сообщение {message.id} в чате {message.chat_id} уже было обработано. Пропускаю.") 
                return
            
            self._processed_messages.add(message_identifier)

            sender = await message.get_sender()
            sender_id = getattr(sender, 'id', None)
            if sender_id is None: # Corrected '===' to 'is'
                logger.warning(f"AutoMafiaTournamentsGame: Не удалось получить ID отправителя для сообщения {message.id} в чате {message.chat_id}. Пропускаю.") 
                return

            allowed_chats = self.config["allowed_chats"]
            if allowed_chats and message.chat_id not in allowed_chats:
                logger.debug(f"AutoMafiaTournamentsGame: Чат {message.chat_id} не в списке разрешенных чатов ({allowed_chats}). Пропускаю сообщение {message.id}.") 
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
                    logger.info(f"AutoMafiaTournamentsGame: Обнаружен триггер для автоматического включения отслеживания ролей в сообщении {message.id} от бота {sender_id}.") 
                    
                    self.set("role_tracking_enabled", True)
                    self.config["role_tracking_enabled"] = True 
                    self._role_tracking_active = True
                    self._role_tracking_start_time = datetime.now()
                    self._tracked_roles_list = []

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

            # --- Автоматическое выключение отслеживания ролей ---
            auto_disable_phrases = self.config["auto_disable_track_roles_trigger_phrases"]
            auto_disable_bot_ids = self.config["auto_disable_track_roles_bot_ids"]

            if auto_disable_phrases and self.config["role_tracking_enabled"]:
                is_auto_disable_trigger_bot = (
                    getattr(sender, 'bot', False) and
                    (not auto_disable_bot_ids or sender_id in auto_disable_bot_ids)
                )
                if is_auto_disable_trigger_bot and any(p.lower() in msg_text_lower for p in auto_disable_phrases):
                    logger.info(f"AutoMafiaTournamentsGame: Обнаружен триггер для автоматического выключения отслеживания ролей в сообщении {message.id} от бота {sender_id}.") 
                    
                    self.set("role_tracking_enabled", False)
                    self.config["role_tracking_enabled"] = False 
                    self._role_tracking_active = False
                    self._role_tracking_start_time = None
                    self._tracked_roles_list = []
                    if self._send_tracked_roles_task:
                        self._send_tracked_roles_task.cancel()
                        self._send_tracked_roles_task = None
                    
                    logger.info("AutoMafiaTournamentsGame: Автоматическое отслеживание ролей выключено.") 
                    await self._client.send_message(message.chat_id, self.strings("auto_role_tracking_deactivated"))
                    return
            
            # --- Логика отслеживания ролей ---
            if self.config["role_tracking_enabled"] and self._role_tracking_active:
                if self._role_tracking_start_time and (datetime.now() - self._role_tracking_start_time).total_seconds() > self.config["role_tracking_duration"]:
                    logger.info(self.strings("role_tracking_expired"))
                    self.set("role_tracking_enabled", False)
                    self.config["role_tracking_enabled"] = False 
                    self._role_tracking_active = False
                    self._role_tracking_start_time = None
                    if self._send_tracked_roles_task:
                        self._send_tracked_roles_task.cancel()
                        self._send_tracked_roles_task = None
                else:
                    role_announcement_phrases_lower = [p.lower() for p in self.config["role_announcement_phrases"]]
                    
                    is_role_announcement = any(phrase in msg_text_lower for phrase in role_announcement_phrases_lower)
                    
                    if is_role_announcement:
                        found_tracked_role_clean = None
                        is_role_active = True

                        for tracked_role_phrase_raw in self.config["tracked_roles_to_monitor"]:
                            role_to_match_lower = tracked_role_phrase_raw.lower()
                            current_is_active = True

                            if role_to_match_lower.endswith("(н)"):
                                current_is_active = False
                                role_to_match_lower = role_to_match_lower[:-3].strip()
                            
                            parts = role_to_match_lower.split()
                            escaped_parts = [re.escape(p) for p in parts]
                            internal_pattern = r"\s+".join(escaped_parts)
                            pattern = r"\b" + internal_pattern + r"\b"

                            if re.search(pattern, msg_text_lower):
                                found_tracked_role_clean = role_to_match_lower
                                is_role_active = current_is_active
                                break
                        
                        if found_tracked_role_clean:
                            nickname = self._get_user_nickname(sender)
                            if not any(entry[0] == sender_id and entry[2] == found_tracked_role_clean for entry in self._tracked_roles_list): 
                                self._tracked_roles_list.append((sender_id, nickname, found_tracked_role_clean, is_role_active)) 
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
                logger.debug(f"AutoMafiaTournamentsGame: Сообщение {message.id} от бота {sender_id}, но его ID не в списке разрешенных ботов. Пропускаю.") 
                return
            
            # Логика голосования за конкретного игрока
            if (self.config["player_to_lynch_user_id"] != 0 and 
                self._player_nickname_to_lynch and 
                any(phrase.lower() in msg_text_lower for phrase in self.config["lynch_player_voting_trigger_phrases"])): 
                
                if not getattr(message, 'buttons', None):
                    logger.warning(f"⚠️ AutoMafiaTournamentsGame: Запрос на голосование за игрока найден (msg_id: {message.id}), но кнопок нет. Пропускаю.") 
                    self._player_nickname_to_lynch = None 
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

                        if target_emoji in button_text: 
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

                keywords_to_check = self._current_button_keywords_to_use
                if not keywords_to_check:
                    logger.warning(f"⚠️ AutoMafiaTournamentsGame: Список активных ключевых слов для кнопок пуст. Ни одна кнопка не будет активирована для сообщения {message.id}.") 
                    return

                # Define the keyword to deprioritize as per user request
                deprioritized_keyword = "присоединиться"

                # Separate keywords into high-priority (any other) and low-priority (the deprioritized one)
                high_priority_keywords = [k for k in keywords_to_check if k.lower() != deprioritized_keyword.lower()]
                low_priority_keywords = [k for k in keywords_to_check if k.lower() == deprioritized_keyword.lower()]

                target_button = None
                
                # First pass: Try to find a button matching high-priority keywords
                # Iterate over buttons, if multiple high-priority match, the first one encountered will be selected.
                for row in message.buttons:
                    for button in row:
                        try:
                            button_text = str(getattr(button, 'text', ''))
                        except Exception as e:
                            logger.warning(f"Error getting button text for message {message.id}: {e}")
                            button_text = ''
                        
                        if any(keyword in button_text.lower() for keyword in high_priority_keywords):
                            target_button = button
                            logger.info(f"✅ AutoMafiaTournamentsGame: Найдена высокоприоритетная кнопка: '{button_text}'") 
                            break
                    if target_button:
                        break
                
                # Second pass: If no high-priority button found, try low-priority (deprioritized_keyword)
                # This ensures "присоединиться" is only chosen if no other matching keyword is present in *any* button.
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
                                logger.info(f"✅ AutoMafiaTournamentsGame: Найдена низкоприоритетная кнопка (только '{deprioritized_keyword}'): '{button_text}'") 
                                break
                        if target_button:
                            break

                if target_button:
                    button_text = str(getattr(target_button, 'text', ''))
                    if getattr(target_button, 'url', None):
                        button_url = target_button.url
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

                        if bot_username and start_param: 
                            logger.info(f"📤 AutoMafiaTournamentsGame: Deep-Link URL обнаружен. Отправка /start {start_param} боту @{bot_username}") 

                            try:
                                await self._client.send_message(
                                    bot_username,
                                    f'/start {start_param}'
                                )
                                logger.info("🎉 AutoMafiaTournamentsGame: Успешно отправлена команда /start (уведомление в чат не отправлено).") 
                            except Exception as e:
                                logger.error(f"❌ AutoMafiaTournamentsGame: Ошибка при отправке Deep-Link команды /start для сообщения {message.id}: {e}") 
                        else:
                            logger.warning(f"⚠️ AutoMafiaTournamentsGame: Найдена кнопка '{button_text}' с URL '{button_url}', но она не является Deep-Link. Пропускаю.") 
                    else: 
                        logger.info(f"📤 AutoMafiaTournamentsGame: Найдена кнопка '{button_text}' (CallbackQuery). Нажимаю.") 
                        try:
                            await target_button.click()
                            logger.info(f"🎉 AutoMafiaTournamentsGame: Успешно нажата кноп '{button_text}' для присоединения к игре.") 
                        except Exception as e:
                            logger.error(f"❌ AutoMafiaTournamentsGame: Ошибка при нажатии кнопки '{button_text}' для присоединения к игре: {e}") 
                else:
                    logger.warning(f"⚠️ AutoMafiaTournamentsGame: Кнопка присоединения не найдена под сообщением {message.id} после задержки.") 
            
        except Exception as e:
            logger.exception(f"❌ AutoMafiaTournamentsGame: Критическая ошибка в watcher для сообщения {getattr(message, 'id', 'N/A')} в чате {getattr(message, 'chat_id', 'N/A')}: {e}")
