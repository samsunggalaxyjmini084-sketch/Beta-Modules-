# meta developer: @yourhandle
# meta name: Triggers
# meta version: 1.5.0
# meta lang: ru
# 01001001 01101110 01101001 01110100 01101001 01100001 01101100 01101001 01111000 01100101 01100100 00100000 01010100 01110010 01101001 01100111 01100111 01100101 01110010 01110011 00100000 01001101 01101111 01100100 01110101 01101100 01100101
# 01000111 01100101 01101110 01100101 01110010 01100001 01110100 01101111 01110010 00100000 01000001 01001001 00100000 01010010 01100101 01101100 01100101 01100001 01110011 01100101 00100000 00110001 00101110 00110001
# 01010101 01110000 01100100 01100001 01110100 01100101 01100100 00100000 01110111 01101001 01110100 01101000 00100000 01010011 01110100 01101111 01110000 00100000 01010111 01101111 01110010 01100100 00100000 01000110 01100101 01100001 01110100 01110101 01110010 01100101 00100000 00110001 00101110 00110010
# 01001001 01101101 01110000 01110010 01101111 01110110 01100101 01100100 00100000 01110111 01101001 01110100 01101000 00100000 01000101 01101101 01101111 01101010 01101001 01100101 01110011 00100000 01100001 01101110 01100100 00100000 01110011 01110100 01101111 01110000 00100000 01110111 01101111 01110010 01100100 00100000 01101110 01101111 00100000 01101110 01101111 01110100 01101001 01100110 01101001 01100011 01100001 01110100 01101001 01101111 01101110 00100000 00110001 00101110 00110011
# 01000110 01101001 01111000 01100101 01100100 00100000 01110011 01110100 01101111 01110000 00101101 01110111 01101111 01110010 01100100 00100000 01100011 01100001 01101110 01100011 01100101 01101100 01101100 01100001 01110100 01101001 01101111 01101110 00100000 01100001 01101110 01100100 00100000 01101101 01101001 01100111 01110010 01100001 01110100 01101001 01101111 01101110 00100000 01101100 01101111 01100111 01101001 01100011 00101110 00110001 00101110 00110011 00101110 00110001
# 01000100 01100101 01101100 01100001 01111001 00100000 01101100 01101111 01100111 01101001 01100011 00100000 01110101 01110000 01100100 01100001 01110100 01100101 01100100 00100000 01110100 01101111 00100000 01110011 01110101 01110000 01110000 01101111 01110010 01110100 00100000 01101101 01110101 01101100 01110100 01101001 01110000 01101100 01100101 00100000 01110010 01100001 01101110 01100100 01101111 01101101 00100000 01100100 01100101 01101100 01100001 01111001 01110011 00101110 00110001 00101110 00110100 00101110 00110000
# 01010101 01110000 01100100 01100001 01110100 01100101 01100100 00100000 01110111 01101001 01110100 01101000 00100000 01010011 01110100 01101111 01110000 00100000 01010111 01101111 01110010 01100100 00100000 01010100 01100001 01110010 01100111 01100101 01110100 00100000 01010101 01110011 01100101 01110010 00100000 01000110 01100101 01100001 01110100 01110101 01110010 01100101 00101110 00110001 00101110 00110101 00101110 00110000
# 01000001 01100100 01100100 01100101 01100100 00100000 01000100 01100101 01101100 01100001 01111001 00100000 01010010 01100001 01101110 01100111 01100101 00100000 01000110 01100101 01100001 01110100 01110101 01110010 01100101 00101110 00110001 00101110 00110101 00101110 00110001

import asyncio
import time
import random
from telethon.tl.types import (
    MessageMediaPhoto,
    MessageMediaDocument,
    DocumentAttributeSticker,
    DocumentAttributeVideo,
    DocumentAttributeAudio,
)

from .. import loader, utils

@loader.tds
class TriggersMod(loader.Module):
    """
    Триггеры на сообщения (можно добавить фото, видео, файл и тд.).
    Поддерживает замену {NAME} на ник пользователя, активировавшего триггер.
    Добавлена возможность установки задержки (или нескольких случайных задержек, или диапазона задержек) для срабатывания триггера и стоп-слова для отмены.
    Теперь можно установить целевого пользователя для стоп-слова, чтобы оно срабатывало только для определённого пользователя.
    """
    strings = {
        "name": "Triggers",
        "chat_enabled": "<emoji document_id=5825794181183836432>✔️</emoji> Триггеры включены",
        "chat_disabled": "<emoji document_id=5778527486270770928>❌</emoji> Триггеры отключены",
        "chat_status_current": "<emoji document_id=5839200986022812209>🔄</emoji> Триггеры в этом чате: {}",
        "chat_status_other_chat": "<emoji document_id=5839200986022812209>🔄</emoji> Триггеры в чате <b>{}</b>: {}",
        "invalid_chat_id_arg": "<emoji document_id=5778527486270770928>❌</emoji> Укажи корректный ID чата (цифры) или не указывай ничего, чтобы управлять текущим чатом.",
        "need_reply": "<emoji document_id=5778527486270770928>❌</emoji> Ответь на сообщение для создания триггера. Например чтобы добавить триггер который на слово <b>привет</b> будет отвечать <b>Привет как дела</b>, то напиши сообщение <code>Привет как дела</code> и на него ответь командой <code>trigadd привет</code>",
        "trigger_added": "<emoji document_id=5825794181183836432>✔️</emoji> Триггер <code>{}</code> добавлен (ID: <code>{}</code>) в чат <b>{}</b>",
        "trigger_exists": "<emoji document_id=5881702736843511327>⚠️</emoji> Триггер <code>{}</code> уже есть в чате <b>{}</b>",
        "trigger_deleted": "<emoji document_id=5825794181183836432>✔️</emoji> Триггер с ID <code>{}</code> удалён из чата <b>{}</b>",
        "trigger_not_found": "<emoji document_id=5778527486270770928>❌</emoji> Триггер с ID <code>{}</code> не найден в чате <b>{}</b>",
        "mode_changed": "<emoji document_id=5825794181183836432>✔️</emoji> Режим триггеров изменён на: {}",
        "trigger_list": "<emoji document_id=5877316724830768997>🗃</emoji> Список триггеров ({}):\n\n{}\n\n🔒 - Строгий режим\n🔍 - Частичный режим\n🔐 - Приватный режим\n🎯 - Целевой пользователь установлен\n⏱ - Задержка установлена\n🛑 - Стоп-слово установлено\n👤🛑 - Целевой пользователь стоп-слова установлен\n\nℹ️ Изменить режим, задержку, стоп-слово или целевого пользователя можно командой <code>.trig</code> ID (<i>ID это цифра перед названием триггера</i>)",
        "trigger_list_in_chat": "<emoji document_id=5877316724830768997>🗃</emoji> Список триггеров ({} в чате <b>{}</b>):\n\n{}\n\n🔒 - Строгий режим\n🔍 - Частичный режим\n🔐 - Приватный режим\n🎯 - Целевой пользователь установлен\n⏱ - Задержка установлена\n🛑 - Стоп-слово установлено\n👤🛑 - Целевой пользователь стоп-слова установлен\n\nℹ️ Изменить режим, задержку, стоп-слово или целевого пользователя можно командой <code>.trig</code> ID (<i>ID это цифра перед названием триггера</i>)",
        "no_triggers": "<emoji document_id=5879785854284599288>ℹ️</emoji> В этом чате нет триггеров",
        "no_triggers_in_chat": "<emoji document_id=5879785854284599288>ℹ️</emoji> В чате <b>{}</b> нет триггеров",
        "mode_menu": "<emoji document_id=5875431869842985304>🎛</emoji> Выбери режим работы триггеров:\n\n🔒 Строгий - Срабатывает только при точном совпадении фразы или слова\n\n🔍 Частичный - Срабатывает при наличии слова/фразы в тексте\n\n🔐 Приватный - Срабатывает только на твои сообщения\n\nℹ️ Смена режима работает только на новые триггеры, чтобы изменить режим уже созданных триггеров пиши <code>.trig</code> ID триггера",
        "strict_mode": "Строгий",
        "partial_mode": "Частичный",
        "private_mode": "Приватный",
        "strict_desc": "Срабатывает только при точном совпадении фразы",
        "partial_desc": "Срабатывает при наличии фразы в тексте",
        "private_desc": "Срабатывает только на ваши собственные сообщения",
        "banned": "<emoji document_id=5825794181183836432>✔️</emoji> Пользователь добавлен в чёрный список триггеров",
        "unbanned": "<emoji document_id=5825794181183836432>✔️</emoji> Пользователь убран из чёрного списка триггеров",
        "already_banned": "<emoji document_id=5881702736843511327>⚠️</emoji> Пользователь уже в чёрном списке",
        "not_banned": "<emoji document_id=5881702736843511327>⚠️</emoji> Пользователя нет в чёрном списке",
        "ban_list": "<emoji document_id=5877316724830768997>🗃</emoji> Чёрный список пользователей:\n\n{}",
        "empty_ban_list": "<emoji document_id=5879785854284599288>ℹ️</emoji> Чёрный список пользователей пуст",
        "trigger_info": "<emoji document_id=5944940516754853337>📍</emoji> Триггер #{}\n\n📝 Реагирует на слово/фраза: <code>{}</code>\n\n💬 Текст к триггеру: {}{}\n📊 Тип триггера: {}\n{}\n{}\n{}\n{}",
        "trigger_mode_changed": "<emoji document_id=5825794181183836432>✔️</emoji> Режим триггера изменён на: {}",
        "change_trigger_mode": "<emoji document_id=5875431869842985304>🎛</emoji> Изменить тип триггера",
        "delete_trigger": "<emoji document_id=5879896690210639947>🗑</emoji> Удалить триггер",
        "back_to_trigger": "<emoji document_id=5877629862306385808>◀️</emoji> Назад",
        "invalid_trigger_id": "<emoji document_id=5778527486270770928>❌</emoji> Укажи корректный ID триггера (цифры).",
        "confirm_delete": "<emoji document_id=5881702736843511327>⚠️</emoji> Ты уверен что хочешь удалить этот триггер <code>{}</code>?\n\nПотом не вернешь обратно",
        "confirm_delete_yes": "<emoji document_id=5825794181183836432>✔️</emoji> Конечно",
        "confirm_delete_no": "<emoji document_id=5778527486270770928>❌</emoji> Отмена",
        "spam_warning": "<emoji document_id=5881702736843511327>⚠️</emoji> Обнаружен спам триггерами\n{}, если продолжишь спам, ты будешь автоматически заблокирован для использования триггеров",
        "spam_banned": "<emoji document_id=5872829476143894491>🚫</emoji> {} заблокирован за спам триггерами",
        "reply_mode_enabled": "<emoji document_id=5825794181183836432>✔️</emoji> Триггеры будут отвечать на сообщения",
        "reply_mode_disabled": "<emoji document_id=5778527486270770928>❌</emoji> Триггеры будут отправлять сообщения в чат",
        "reply_mode_status": "<emoji document_id=5839200986022812209>🔄</emoji> Режим ответа триггеров: {}",
        "target_user_info": "<emoji document_id=5771887475421090729>👤</emoji> Работает для: {} (<code>{}</code>)",
        "target_user_none": "<emoji document_id=5771887475421090729>👤</emoji> Работает для: Всех",
        "set_target_user_btn": "<emoji document_id=5944940516754853337>📍</emoji> Установить целевого пользователя",
        "remove_target_user_btn": "<emoji document_id=5872829476143894491>🚫</emoji> Удалить целевого пользователя",
        "target_user_set": "<emoji document_id=5825794181183836432>✔️</emoji> Целевой пользователь <b>{}</b> установлен для триггера <code>{}</code> в чате <b>{}</b>",
        "target_user_removed": "<emoji document_id=5825794181183836432>✔️</emoji> Целевой пользователь удалён для триггера <code>{}</code> из чата <b>{}</b>",
        "user_not_found": "<emoji document_id=5778527486270770928>❌</emoji> Не удалось найти пользователя по указанным данным.",
        "confirm_remove_target_user": "<emoji document_id=5881702736843511327>⚠️</emoji> Ты уверен что хочешь удалить целевого пользователя для триггера <code>{}</code>?",
        "set_target_user_instructions": "<emoji document_id=5879785854284599288>ℹ️</emoji> Чтобы установить целевого пользователя для триггера <code>{}</code> в чате <b>{}</b>, используй команду:\n\n<code>.trig {} {} ID_ПОЛЬЗОВАТЕЛЯ_ИЛИ_@ЮЗЕРНЕЙМ</code>\n\nИли ответь на сообщение пользователя этой же командой.\n\n(<i>ID триггера</i> - это цифра перед названием триггера в <code>.triglist</code>, <i>ID_чата</i> опционально, если триггер находится не в текущем чате)",
        "empty_trigger_name": "<emoji document_id=5778527486270770928>❌</emoji> Укажи слово или фразу для триггера.",
        "invalid_ban_args": "<emoji document_id=5778527486270770928>❌</emoji> Укажи ID/юзернейм пользователя или ответь на его сообщение.",
        "invalid_trig_args": "<emoji document_id=5778527486270770928>❌</emoji> Неверные аргументы. Используй: <code>.trig &lt;ID_триггера&gt; [ID_чата] [ID_пользователя/@username/clear | delay ЧИСЛО_СЕКУНД_1,ЧИСЛО_СЕКУНД_2,.../ЧИСЛО_МИН-ЧИСЛО_МАКС/0 | stopword СТОП_СЛОВО/clear | stopworduser ID_ПОЛЬЗОВАТЕЛЯ/@username/clear]</code>",
        "invalid_trigadd_args": "<emoji document_id=5778527486270770928>❌</emoji> Неверные аргументы. Используй: <code>.trigadd [ID_чата] &lt;фраза_триггера&gt;</code> (ответом на сообщение)",
        "invalid_trigdel_args": "<emoji document_id=5778527486270770928>❌</emoji> Неверные аргументы. Используй: <code>.trigdel &lt;ID_триггера&gt; [ID_чата]</code>",
        "triglist_instructions": "<emoji document_id=5879785854284599288>ℹ️</emoji> Используй: <code>.triglist [ID_чата]</code>",
        "trigger_source_msg_deleted": "<emoji document_id=5778527486270770928>❌</emoji> Исходное сообщение триггера (ID: <code>{}</code>) в чате <b>{}</b> было удалено или недоступно.",
        "trigger_source_msg_empty": "<emoji document_id=5778527486270770928>❌</emoji> Исходное сообщение триггера (ID: <code>{}</code>) в чате <b>{}</b> не содержит ни текста, ни медиа для отправки.",
        "delay_info_none": "<emoji document_id=5776213190387961618>🕓</emoji> Задержка: Нет",
        "delay_info_single": "<emoji document_id=5776213190387961618>🕓</emoji> Задержка: <b>{}</b> секунд",
        "delay_info_multiple": "<emoji document_id=5776213190387961618>🕓</emoji> Задержки: <b>{}</b> секунд (выбирается случайно)",
        "delay_info_range": "<emoji document_id=5776213190387961618>🕓</emoji> Задержка: <b>{} - {}</b> секунд (выбирается случайно)",
        "set_delay_btn": "<emoji document_id=5776213190387961618>🕓</emoji> Установить задержку",
        "delay_set_updated": "<emoji document_id=5825794181183836432>✔️</emoji> Задержка для триггера <code>{}</code> установлена на <b>{}</b> в чате <b>{}</b>",
        "delay_removed": "<emoji document_id=5825794181183836432>✔️</emoji> Задержка для триггера <code>{}</code> удалена из чата <b>{}</b>",
        "invalid_delay_value": "<emoji document_id=5778527486270770928>❌</emoji> Укажи корректное число, список чисел через запятую или диапазон ЧИСЛО_1-ЧИСЛО_2 для задержки (в секундах). Значения должны быть неотрицательными.",
        "set_delay_instructions": "<emoji document_id=5879785854284599288>ℹ️</emoji> Чтобы установить задержку (или несколько, или диапазон) для триггера <code>{}</code> в чате <b>{}</b>, используй команду:\n\n<code>.trig {} {} delay ЧИСЛО_СЕКУНД_1,ЧИСЛО_СЕКУНД_2,...</code>\nили <code>.trig {} {} delay ЧИСЛО_МИН-ЧИСЛО_МАКС</code>\n\nЧтобы удалить задержку, используй <code>.trig {} {} delay 0</code>\n\n(<i>ID триггера</i> - это цифра перед названием триггера в <code>.triglist</code>, <i>ID_чата</i> опционально, если триггер находится не в текущем чате)",
        "stop_word_info": "<emoji document_id=5872829476143894491>🚫</emoji> Стоп-слово: <b>{}</b>",
        "stop_word_info_none": "<emoji document_id=5872829476143894491>🚫</emoji> Стоп-слово: Нет",
        "set_stop_word_btn": "<emoji document_id=5872829476143894491>🚫</emoji> Установить стоп-слово",
        "remove_stop_word_btn": "<emoji document_id=5825794181183836432>✔️</emoji> Удалить стоп-слово",
        "stop_word_set": "<emoji document_id=5825794181183836432>✔️</emoji> Стоп-слово для триггера <code>{}</code> установлено на <b>{}</b> в чате <b>{}</b>",
        "stop_word_removed": "<emoji document_id=5825794181183836432>✔️</emoji> Стоп-слово удалено для триггера <code>{}</code> из чата <b>{}</b>",
        "invalid_stop_word_value": "<emoji document_id=5778527486270770928>❌</emoji> Укажи стоп-слово.",
        "set_stop_word_instructions": "<emoji document_id=5879785854284599288>ℹ️</emoji> Чтобы установить стоп-слово для триггера <code>{}</code> в чате <b>{}</b>, используй команду:\n\n<code>.trig {} {} stopword СТОП_СЛОВО</code>\n\n(<i>ID триггера</i> - это цифра перед названием триггера в <code>.triglist</code>, <i>ID_чата</i> опционально, если триггер находится не в текущем чате)",
        "stop_word_detected": "<emoji document_id=5872829476143894491>🚫</emoji> Срабатывание триггера <code>{}</code> отменено по стоп-слову.",
        "stop_word_target_user_info": "<emoji document_id=5771887475421090729>👤</emoji> Стоп-слово от: {} (<code>{}</code>)",
        "stop_word_target_user_none": "<emoji document_id=5771887475421090729>👤</emoji> Стоп-слово от: Всех",
        "set_stop_word_target_user_btn": "<emoji document_id=5771887475421090729>👤</emoji> Установить пользователя для стоп-слова",
        "remove_stop_word_target_user_btn": "<emoji document_id=5872829476143894491>🚫</emoji> Удалить пользователя для стоп-слова",
        "stop_word_target_user_set": "<emoji document_id=5825794181183836432>✔️</emoji> Целевой пользователь <b>{}</b> установлен для стоп-слова триггера <code>{}</code> в чате <b>{}</b>",
        "stop_word_target_user_removed": "<emoji document_id=5825794181183836432>✔️</emoji> Целевой пользователь для стоп-слова удалён для триггера <code>{}</code> из чата <b>{}</b>",
        "confirm_remove_stop_word_target_user": "<emoji document_id=5881702736843511327>⚠️</emoji> Ты уверен что хочешь удалить целевого пользователя для стоп-слова триггера <code>{}</code>?",
        "set_stop_word_target_user_instructions": "<emoji document_id=5879785854284599288>ℹ️</emoji> Чтобы установить целевого пользователя для стоп-слова триггера <code>{}</code> в чате <b>{}</b>, используй команду:\n\n<code>.trig {} {} stopworduser ID_ПОЛЬЗОВАТЕЛЯ_ИЛИ_@ЮЗЕРНЕЙМ</code>\n\nИли ответь на сообщение пользователя этой же командой.\n\n(<i>ID триггера</i> - это цифра перед названием триггера в <code>.triglist</code>, <i>ID_чата</i> опционально, если триггер находится не в текущем чате)",
    }

    def __init__(self):
        self.db = None
        self.triggers = {}
        self.modes = {}
        self.spam_tracker = {}
        self.next_trigger_id = 1
        self.reply_mode = True
        self.pending_triggers = {}

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self.triggers = {str(k): v for k, v in self.db.get("Triggers", "triggers", {}).items()}
        self.modes = {str(k): v for k, v in self.db.get("Triggers", "modes", {}).items()}
        self.reply_mode = self.db.get("Triggers", "reply_mode", True)

        max_existing_id_across_all = 0
        
        for chat_id_str in self.triggers.keys():
            for data in self.triggers[chat_id_str].values():
                if "id" in data:
                    max_existing_id_across_all = max(max_existing_id_across_all, data["id"])

        triggers_changed = False
        current_id_for_missing = max_existing_id_across_all + 1 

        for chat_id_str in list(self.triggers.keys()):
            for trigger_name, data in list(self.triggers[chat_id_str].items()):
                
                if "id" not in data:
                    data["id"] = current_id_for_missing
                    current_id_for_missing += 1
                    triggers_changed = True
                
                if "target_user_id" not in data:
                    data["target_user_id"] = None
                    triggers_changed = True
                
                # --- Delay migration logic start ---
                if "delay" not in data:
                    data["delay"] = [0]
                    triggers_changed = True
                
                current_delay_value = data.get("delay")
                normalized_delay = []

                if isinstance(current_delay_value, (int, float)):
                    val = int(current_delay_value)
                    normalized_delay = [val if val >= 0 else 0]
                elif isinstance(current_delay_value, str):
                    # Try to parse as a range X-Y
                    if '-' in current_delay_value:
                        parts = current_delay_value.split('-', 1)
                        if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
                            min_val = int(parts[0].strip())
                            max_val = int(parts[1].strip())
                            if min_val >= 0 and max_val >= 0:
                                normalized_delay = sorted([min_val, max_val]) # Ensure min, max order
                                if normalized_delay[0] == normalized_delay[1]:
                                    normalized_delay = [normalized_delay[0]] # Convert [X,X] to [X]
                    
                    # If not parsed as range or invalid, try as comma-separated or single digit
                    if not normalized_delay: # only if range parsing failed
                        parsed_values_str = [x.strip() for x in current_delay_value.split(',') if x.strip().isdigit()]
                        temp_discrete_delays = []
                        for val_str in parsed_values_str:
                            val = int(val_str)
                            if val >= 0:
                                temp_discrete_delays.append(val)
                        
                        if temp_discrete_delays:
                            normalized_delay = sorted(list(set(temp_discrete_delays)))
                        elif current_delay_value.strip().isdigit(): # Handle single digit string like "5"
                             val = int(current_delay_value.strip())
                             if val >= 0:
                                 normalized_delay = [val]

                elif isinstance(current_delay_value, list):
                    temp_list = []
                    for item in current_delay_value:
                        try:
                            val = int(item)
                            if val >= 0:
                                temp_list.append(val)
                        except (ValueError, TypeError):
                            pass
                    
                    if len(temp_list) == 2 and temp_list[0] <= temp_list[1]: # Could be a range or just two discrete. Normalize.
                        temp_list = sorted(temp_list)
                        if temp_list[0] == temp_list[1]:
                            normalized_delay = [temp_list[0]]
                        else:
                            normalized_delay = temp_list
                    elif len(temp_list) > 1: # Multiple discrete
                        normalized_delay = sorted(list(set(temp_list)))
                    else: # Single or empty
                        normalized_delay = temp_list
                
                # Final check: if still empty, default to [0]
                if not normalized_delay:
                    normalized_delay = [0]
                
                if data["delay"] != normalized_delay: # Check if a change actually occurred
                    data["delay"] = normalized_delay
                    triggers_changed = True
                # --- Delay migration logic end ---

                if "stop_word" not in data:
                    data["stop_word"] = None
                    triggers_changed = True
                
                if "stop_word_target_user_id" not in data:
                    data["stop_word_target_user_id"] = None
                    triggers_changed = True
                
                if "chat_id" in data and not isinstance(data["chat_id"], str):
                    data["chat_id"] = str(data["chat_id"])
                    triggers_changed = True

        stored_next_id = self.db.get("Triggers", "next_trigger_id", 1)
        self.next_trigger_id = max(stored_next_id, current_id_for_missing) 
        self.db.set("Triggers", "next_trigger_id", self.next_trigger_id)
        
        if triggers_changed:
            self.db.set("Triggers", "triggers", self.triggers)

    def check_spam(self, user_id, trigger_name):
        current_time = time.time()
        
        if user_id not in self.spam_tracker:
            self.spam_tracker[user_id] = {"triggers": [], "warned": False}
        
        self.spam_tracker[user_id]["triggers"] = [
            (timestamp, trig_name) for timestamp, trig_name in self.spam_tracker[user_id]["triggers"] 
            if current_time - timestamp < 5.0
        ]
        
        user_data = self.spam_tracker[user_id]
        user_data["triggers"].append((current_time, trigger_name))
        
        same_trigger_count = sum(1 for _, trig_name_in_list in user_data["triggers"] if trig_name_in_list == trigger_name)
        
        if same_trigger_count >= 3:
            if user_data["warned"]:
                return "ban"
            else:
                user_data["warned"] = True
                return "warn"
        
        return "continue"

    async def auto_ban_user(self, user_id):
        blacklist = self.db.get("Triggers", "blacklist", [])
        if user_id not in blacklist:
            blacklist.append(user_id)
            self.db.set("Triggers", "blacklist", blacklist)

    async def get_user_name(self, user_id):
        try:
            user = await self.client.get_entity(user_id)
            full_name = user.first_name or "Пользователь"
            if user.last_name:
                full_name += f" {user.last_name}"
            return full_name
        except Exception:
            return "Пользователь"
            
    async def _resolve_user_id(self, message, identifier_arg=None):
        target_id = None
        if identifier_arg:
            arg = identifier_arg
            if arg.isdigit():
                target_id = int(arg)
            else:
                username = arg.lstrip('@')
                if username:
                    try:
                        entity = await self.client.get_entity(username)
                        target_id = entity.id
                    except Exception:
                        pass
        elif message.is_reply:
            reply_msg = await message.get_reply_message()
            if reply_msg and reply_msg.sender_id:
                target_id = reply_msg.sender_id
        
        return target_id

    async def _get_chat_name(self, chat_id_str):
        try:
            entity = await self.client.get_entity(int(chat_id_str)) 
            if hasattr(entity, 'title') and entity.title:
                return entity.title
            elif hasattr(entity, 'first_name') and entity.first_name:
                name = entity.first_name
                if hasattr(entity, 'last_name') and entity.last_name:
                    name += f" {entity.last_name}"
                return name
            return f"ID {chat_id_str}"
        except Exception:
            return f"ID {chat_id_str}"

    def _is_chat_id_string(self, s):
        return isinstance(s, str) and (s.lstrip('-').isdigit())

    async def trigchatcmd(self, message):
        """Включить/выключить триггеры в текущем чате или в указанном по ID.
        Использование:
        .trigchat - для текущего чата
        .trigchat <chat_id> - для указанного чата"""
        
        args_raw = utils.get_args_raw(message)
        target_chat_id_str = str(message.chat_id)

        if args_raw:
            if self._is_chat_id_string(args_raw):
                target_chat_id_str = args_raw
            else:
                await utils.answer(message, self.strings["invalid_chat_id_arg"], link_preview=False)
                return
        
        chats = self.db.get("Triggers", "chats", {})
        new_status = not chats.get(target_chat_id_str, False)
        chats[target_chat_id_str] = new_status
        self.db.set("Triggers", "chats", chats)
        
        status_text = self.strings["chat_enabled"] if new_status else self.strings["chat_disabled"]
        
        if target_chat_id_str == str(message.chat_id):
            final_status_message = self.strings["chat_status_current"].format(status_text)
        else:
            chat_name = await self._get_chat_name(target_chat_id_str)
            final_status_message = self.strings["chat_status_other_chat"].format(chat_name, status_text)
        
        await utils.answer(message, final_status_message, link_preview=False)

    async def trigstatuscmd(self, message):
        """Узнать статус триггеров в текущем или указанном чате.
        Использование:
        .trigstatus - для текущего чата
        .trigstatus <chat_id> - для указанного чата"""
        
        args_raw = utils.get_args_raw(message)
        target_chat_id_str = str(message.chat_id)
        
        if args_raw:
            if self._is_chat_id_string(args_raw):
                target_chat_id_str = args_raw
            else:
                await utils.answer(message, self.strings["invalid_chat_id_arg"], link_preview=False)
                return
        
        chats = self.db.get("Triggers", "chats", {})
        current_status = chats.get(target_chat_id_str, False)
        
        status_text = self.strings["chat_enabled"] if current_status else self.strings["chat_disabled"]
        
        if target_chat_id_str == str(message.chat_id):
            final_status_message = self.strings["chat_status_current"].format(status_text)
        else:
            chat_name = await self._get_chat_name(target_chat_id_str)
            final_status_message = self.strings["chat_status_other_chat"].format(chat_name, status_text)
        
        await utils.answer(message, final_status_message, link_preview=False)


    async def trigaddcmd(self, message):
        """Добавить триггер (в ответ на сообщение, которое будет являться ответом).
        Использование: .trigadd [ID_чата] <фраза_триггера>
        Например: чтобы добавить триггер который на слово 'привет' будет отвечать 'Привет как дела',
        то напиши сообщение 'Привет как дела' и на него ответь командой .trigadd привет.
        Чтобы добавить в другой чат: .trigadd -1001234567890 привет"""
        if not message.is_reply:
            await utils.answer(message, self.strings["need_reply"], link_preview=False)
            return

        args_raw = utils.get_args_raw(message)
        parts = args_raw.split(maxsplit=1)

        target_chat_id_str = str(message.chat_id)
        trigger_name_raw = None

        if not parts:
            await utils.answer(message, self.strings["invalid_trigadd_args"], link_preview=False)
            return

        if self._is_chat_id_string(parts[0]):
            target_chat_id_str = parts[0]
            if len(parts) > 1:
                trigger_name_raw = parts[1]
            else:
                await utils.answer(message, self.strings["empty_trigger_name"], link_preview=False)
                return
        else:
            trigger_name_raw = parts[0]
        
        trigger_name = (trigger_name_raw or "").lower().strip()

        if not trigger_name:
            await utils.answer(message, self.strings["empty_trigger_name"], link_preview=False)
            return

        reply_msg = await message.get_reply_message()
        if not reply_msg:
             await utils.answer(message, self.strings["need_reply"], link_preview=False)
             return
        
        if target_chat_id_str not in self.triggers:
            self.triggers[target_chat_id_str] = {}
        if trigger_name in self.triggers[target_chat_id_str]:
            chat_name = await self._get_chat_name(target_chat_id_str)
            await utils.answer(message, self.strings["trigger_exists"].format(trigger_name, chat_name), link_preview=False)
            return
        
        trigger_id = self.next_trigger_id
        self.next_trigger_id += 1
        self.db.set("Triggers", "next_trigger_id", self.next_trigger_id)

        data = {
            "id": trigger_id, 
            "mode": self.modes.get(str(message.sender_id), "strict"),
            "chat_id": str(reply_msg.chat_id),
            "message_id": reply_msg.id,
            "target_user_id": None,
            "delay": [0], # Default to no delay
            "stop_word": None,
            "stop_word_target_user_id": None,
        }
        
        self.triggers[target_chat_id_str][trigger_name] = data
        self.db.set("Triggers", "triggers", self.triggers)
        chat_name = await self._get_chat_name(target_chat_id_str)
        await utils.answer(message, self.strings["trigger_added"].format(trigger_name, trigger_id, chat_name), link_preview=False)

    async def _get_trigger_info_data(self, chat_id_str, trigger_name, trigger_id):
        trigger_data = self.triggers.get(chat_id_str, {}).get(trigger_name)
        if not trigger_data:
            return None, None, None

        text_content = ""
        media_info = ""
        source_chat_id_for_get_messages = trigger_data.get("chat_id")
        source_message_id = trigger_data.get("message_id")

        try:
            msg = await self.client.get_messages(int(source_chat_id_for_get_messages), ids=source_message_id)
            if msg:
                text_content = msg.raw_text or ""
                if msg.media:
                    media_type = self.get_media_type_name(msg.media)
                    media_info = f"\n📋 Прикреплённый тип к триггеру: {media_type}\n\n"
                
                if not msg.raw_text and not msg.media:
                    text_content = self.strings["trigger_source_msg_empty"].format(source_message_id, await self._get_chat_name(source_chat_id_for_get_messages))
            else:
                text_content = self.strings["trigger_source_msg_deleted"].format(source_message_id, await self._get_chat_name(source_chat_id_for_get_messages))
        except Exception:
            text_content = self.strings["trigger_source_msg_deleted"].format(source_message_id, await self._get_chat_name(source_chat_id_for_get_messages))
        
        mode_name = {
            "strict": self.strings["strict_mode"],
            "partial": self.strings["partial_mode"], 
            "private": self.strings["private_mode"]
        }.get(trigger_data["mode"], trigger_data["mode"])
        
        target_user_id = trigger_data.get("target_user_id")
        target_user_info_str = self.strings["target_user_none"]
        if target_user_id:
            user_name = await self.get_user_name(target_user_id)
            target_user_info_str = self.strings["target_user_info"].format(user_name, target_user_id)

        delay_list = trigger_data.get("delay", [0])
        delay_info_str = self.strings["delay_info_none"]
        
        if len(delay_list) == 1 and delay_list[0] > 0:
            delay_info_str = self.strings["delay_info_single"].format(delay_list[0])
        elif len(delay_list) == 2 and delay_list[0] >= 0 and delay_list[1] >= 0 and delay_list[0] < delay_list[1]:
            delay_info_str = self.strings["delay_info_range"].format(delay_list[0], delay_list[1])
        elif any(d > 0 for d in delay_list): # For multiple discrete positive delays
            delay_info_str = self.strings["delay_info_multiple"].format(", ".join(map(str, sorted(list(set(d for d in delay_list if d > 0))))))

        stop_word_val = trigger_data.get("stop_word")
        stop_word_info_str = self.strings["stop_word_info_none"]
        if stop_word_val:
            stop_word_info_str = self.strings["stop_word_info"].format(stop_word_val)

        stop_word_target_user_id = trigger_data.get("stop_word_target_user_id")
        stop_word_target_user_info_str = self.strings["stop_word_target_user_none"]
        if stop_word_target_user_id:
            user_name = await self.get_user_name(stop_word_target_user_id)
            stop_word_target_user_info_str = self.strings["stop_word_target_user_info"].format(user_name, stop_word_target_user_id)

        info_text = self.strings["trigger_info"].format(
            trigger_id,
            trigger_name,
            text_content,
            media_info,
            mode_name,
            target_user_info_str,
            delay_info_str,
            stop_word_info_str,
            stop_word_target_user_info_str
        )
        
        reply_markup = [
            [{
                "text": self.strings["change_trigger_mode"],
                "callback": self.show_trigger_mode_menu,
                "args": (chat_id_str, trigger_name, trigger_id),
            }],
            [{
                "text": self.strings["set_target_user_btn"] if target_user_id is None else self.strings["remove_target_user_btn"],
                "callback": self.manage_target_user_inline,
                "args": (chat_id_str, trigger_name, trigger_id, target_user_id is not None),
            }],
            [{
                "text": self.strings["set_delay_btn"],
                "callback": self.show_set_delay_instructions,
                "args": (chat_id_str, trigger_name, trigger_id),
            }],
            [{
                "text": self.strings["set_stop_word_btn"] if stop_word_val is None else self.strings["remove_stop_word_btn"],
                "callback": self.manage_stop_word_inline,
                "args": (chat_id_str, trigger_name, trigger_id, stop_word_val is not None),
            }],
            [{
                "text": self.strings["set_stop_word_target_user_btn"] if stop_word_target_user_id is None else self.strings["remove_stop_word_target_user_btn"],
                "callback": self.manage_stop_word_target_user_inline,
                "args": (chat_id_str, trigger_name, trigger_id, stop_word_target_user_id is not None),
            }],
            [{
                "text": self.strings["delete_trigger"],
                "callback": self.confirm_trigger_delete,
                "args": (chat_id_str, trigger_name, trigger_id),
            }]
        ]
        return info_text, reply_markup, trigger_data

    async def trigcmd(self, message):
        """Показать информацию о триггере по ID или установить/удалить целевого пользователя/задержку/стоп-слово/целевого пользователя стоп-слова.
        Использование: .trig <ID_триггера> [ID_чата] [ID_пользователя/@username/clear | delay ЧИСЛО_СЕКУНД_1,ЧИСЛО_СЕКУНД_2,.../ЧИСЛО_МИН-ЧИСЛО_МАКС/0 | stopword СТОП_СЛОВО/clear | stopworduser ID_ПОЛЬЗОВАТЕЛЯ/@username/clear]
        Пример: .trig 10 (показать инфо о триггере 10 в текущем чате)
        Пример: .trig 10 -1001234567890 (показать инфо о триггере 10 в указанном чате)
        Установить целевого пользователя: .trig 10 @username / ID / (ответом на сообщение)
        Удалить целевого пользователя: .trig 10 clear
        Установить задержку: .trig 10 delay 5 (5 секунд задержки)
        Установить несколько задержек: .trig 10 delay 5,10,15
        Установить диапазон задержки: .trig 10 delay 5-240
        Удалить задержку: .trig 10 delay 0
        Установить стоп-слово: .trig 10 stopword отмена
        Удалить стоп-слово: .trig 10 stopword clear
        Установить целевого пользователя для стоп-слова: .trig 10 stopworduser @username / ID / (ответом на сообщение)
        Удалить целевого пользователя для стоп-слова: .trig 10 stopworduser clear"""
        
        args = utils.get_args_raw(message).split(maxsplit=3)
        
        target_chat_id_str = str(message.chat_id)
        trigger_id_str = None
        action_type = None
        action_value = None

        if not args:
            await utils.answer(message, self.strings["invalid_trig_args"], link_preview=False)
            return

        trigger_id_str = args[0]
        if not trigger_id_str.isdigit():
            await utils.answer(message, self.strings["invalid_trigger_id"], link_preview=False)
            return
        
        try:
            trigger_id = int(trigger_id_str)
        except ValueError:
            await utils.answer(message, self.strings["invalid_trigger_id"], link_preview=False)
            return

        if len(args) > 1 and self._is_chat_id_string(args[1]):
            target_chat_id_str = args[1]
            args_for_action = args[2:]
        else:
            args_for_action = args[1:]
        
        if len(args_for_action) >= 1:
            if args_for_action[0].lower() == "delay":
                action_type = "delay"
                if len(args_for_action) > 1:
                    action_value = args_for_action[1]
                else:
                    await utils.answer(message, self.strings["invalid_delay_value"], link_preview=False)
                    return
            elif args_for_action[0].lower() == "stopword":
                action_type = "stopword"
                if len(args_for_action) > 1:
                    action_value = args_for_action[1]
                else:
                    await utils.answer(message, self.strings["invalid_stop_word_value"], link_preview=False)
                    return
            elif args_for_action[0].lower() == "stopworduser":
                action_type = "stopworduser"
                if len(args_for_action) > 1:
                    action_value = args_for_action[1]
                else:
                    await utils.answer(message, self.strings["invalid_ban_args"], link_preview=False)
                    return
            else:
                action_type = "user"
                action_value = args_for_action[0]
        
        if target_chat_id_str not in self.triggers or not self.triggers[target_chat_id_str]:
            chat_name = await self._get_chat_name(target_chat_id_str)
            await utils.answer(message, self.strings["no_triggers_in_chat"].format(chat_name), link_preview=False)
            return
        
        trigger_name = None
        for name, data in self.triggers[target_chat_id_str].items():
            if data["id"] == trigger_id:
                trigger_name = name
                break
        
        if not trigger_name:
            chat_name = await self._get_chat_name(target_chat_id_str)
            await utils.answer(message, self.strings["trigger_not_found"].format(trigger_id, chat_name), link_preview=False)
            return

        if action_type == "user":
            chat_name = await self._get_chat_name(target_chat_id_str)
            if action_value.lower() == "clear":
                if self.triggers[target_chat_id_str][trigger_name].get("target_user_id") is None:
                    await utils.answer(message, self.strings["target_user_removed"].format(trigger_name, chat_name), link_preview=False) 
                    return
                self.triggers[target_chat_id_str][trigger_name]["target_user_id"] = None
                self.db.set("Triggers", "triggers", self.triggers)
                await utils.answer(message, self.strings["target_user_removed"].format(trigger_name, chat_name), link_preview=False)
                return
            
            target_user_id_to_set = await self._resolve_user_id(message, action_value)
            
            if target_user_id_to_set:
                self.triggers[target_chat_id_str][trigger_name]["target_user_id"] = target_user_id_to_set
                self.db.set("Triggers", "triggers", self.triggers)
                user_name = await self.get_user_name(target_user_id_to_set)
                await utils.answer(message, self.strings["target_user_set"].format(user_name, trigger_name, chat_name), link_preview=False)
            else:
                await utils.answer(message, self.strings["user_not_found"], link_preview=False)
            return
        elif action_type == "delay":
            chat_name = await self._get_chat_name(target_chat_id_str)
            try:
                final_delay_list = []
                action_value_lower = action_value.lower().strip()

                if action_value_lower == "0" or action_value_lower == "clear":
                    final_delay_list = [0]
                elif '-' in action_value_lower:
                    # Try to parse as a range X-Y
                    parts = action_value_lower.split('-', 1)
                    if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
                        min_val = int(parts[0].strip())
                        max_val = int(parts[1].strip())
                        if min_val < 0 or max_val < 0:
                            raise ValueError("Delay values must be non-negative.")
                        if min_val > max_val: # Swap if min > max
                            min_val, max_val = max_val, min_val
                        
                        if min_val == max_val:
                            final_delay_list = [min_val] # Treat as single fixed delay
                        else:
                            final_delay_list = [min_val, max_val]
                    else:
                        raise ValueError("Invalid delay range format. Use X-Y.")
                else:
                    # Try to parse as comma-separated values or a single value
                    delay_values_str_list = [v.strip() for v in action_value.split(',') if v.strip()]
                    
                    temp_parsed_delays = []
                    for val_str in delay_values_str_list:
                        if not val_str.isdigit():
                            raise ValueError("All discrete delay values must be digits.")
                        val = int(val_str)
                        if val < 0:
                            raise ValueError("Delay values must be non-negative.")
                        temp_parsed_delays.append(val)
                    
                    if not temp_parsed_delays:
                        final_delay_list = [0]
                    elif len(temp_parsed_delays) == 1:
                        final_delay_list = [temp_parsed_delays[0]]
                    else:
                        final_delay_list = sorted(list(set(temp_parsed_delays))) # Unique and sorted for consistency

                self.triggers[target_chat_id_str][trigger_name]["delay"] = final_delay_list
                self.db.set("Triggers", "triggers", self.triggers)
                
                delay_display = ""
                if len(final_delay_list) == 0 or (len(final_delay_list) == 1 and final_delay_list[0] == 0):
                    message_key = "delay_removed"
                    delay_display = self.strings["delay_info_none"].split(': ')[1] # "Нет"
                elif len(final_delay_list) == 1:
                    message_key = "delay_set_updated"
                    delay_display = f"{final_delay_list[0]} секунд"
                elif len(final_delay_list) == 2 and final_delay_list[0] < final_delay_list[1]:
                    message_key = "delay_set_updated"
                    delay_display = f"{final_delay_list[0]}-{final_delay_list[1]} секунд"
                else: # multiple discrete values
                    message_key = "delay_set_updated"
                    delay_display = f"{', '.join(map(str, final_delay_list))} секунд"
                
                await utils.answer(message, self.strings[message_key].format(trigger_name, delay_display, chat_name), link_preview=False)
            except ValueError as e:
                await utils.answer(message, self.strings["invalid_delay_value"] + f" ({e})", link_preview=False)
            return
        elif action_type == "stopword":
            chat_name = await self._get_chat_name(target_chat_id_str)
            if action_value.lower() == "clear":
                if self.triggers[target_chat_id_str][trigger_name].get("stop_word") is None:
                    await utils.answer(message, self.strings["stop_word_removed"].format(trigger_name, chat_name), link_preview=False)
                    return
                self.triggers[target_chat_id_str][trigger_name]["stop_word"] = None
                self.db.set("Triggers", "triggers", self.triggers)
                await utils.answer(message, self.strings["stop_word_removed"].format(trigger_name, chat_name), link_preview=False)
                return
            
            stop_word_to_set = action_value.lower().strip()
            if not stop_word_to_set:
                await utils.answer(message, self.strings["invalid_stop_word_value"], link_preview=False)
                return
            
            self.triggers[target_chat_id_str][trigger_name]["stop_word"] = stop_word_to_set
            self.db.set("Triggers", "triggers", self.triggers)
            await utils.answer(message, self.strings["stop_word_set"].format(trigger_name, stop_word_to_set, chat_name), link_preview=False)
            return
        elif action_type == "stopworduser":
            chat_name = await self._get_chat_name(target_chat_id_str)
            if action_value.lower() == "clear":
                if self.triggers[target_chat_id_str][trigger_name].get("stop_word_target_user_id") is None:
                    await utils.answer(message, self.strings["stop_word_target_user_removed"].format(trigger_name, chat_name), link_preview=False)
                    return
                self.triggers[target_chat_id_str][trigger_name]["stop_word_target_user_id"] = None
                self.db.set("Triggers", "triggers", self.triggers)
                await utils.answer(message, self.strings["stop_word_target_user_removed"].format(trigger_name, chat_name), link_preview=False)
                return
            
            target_user_id_to_set = await self._resolve_user_id(message, action_value)
            
            if target_user_id_to_set:
                self.triggers[target_chat_id_str][trigger_name]["stop_word_target_user_id"] = target_user_id_to_set
                self.db.set("Triggers", "triggers", self.triggers)
                user_name = await self.get_user_name(target_user_id_to_set)
                await utils.answer(message, self.strings["stop_word_target_user_set"].format(user_name, trigger_name, chat_name), link_preview=False)
            else:
                await utils.answer(message, self.strings["user_not_found"], link_preview=False)
            return

        info_text, reply_markup, _ = await self._get_trigger_info_data(target_chat_id_str, trigger_name, trigger_id)

        if info_text and reply_markup:
            await self.inline.form(
                message=message,
                text=info_text,
                reply_markup=reply_markup,
                silent=True
            )
        else:
            chat_name = await self._get_chat_name(target_chat_id_str)
            await utils.answer(message, self.strings["trigger_not_found"].format(trigger_id, chat_name), link_preview=False)

    async def manage_target_user_inline(self, call, chat_id_str, trigger_name, trigger_id, is_target_set):
        """Обработка нажатий на кнопки управления целевым пользователем."""
        chat_name = await self._get_chat_name(chat_id_str)
        if is_target_set:
            await call.edit(
                self.strings["confirm_remove_target_user"].format(trigger_name),
                reply_markup=[
                    [{
                        "text": self.strings["confirm_delete_yes"],
                        "callback": self.remove_target_user_confirmed,
                        "args": (chat_id_str, trigger_name, trigger_id),
                    }],
                    [{
                        "text": self.strings["confirm_delete_no"],
                        "callback": self.back_to_trigger_info,
                        "args": (chat_id_str, trigger_name, trigger_id),
                    }]
                ]
            )
        else:
            chat_id_arg_for_command = chat_id_str if chat_id_str != str(call.chat_id) else ""
            
            await call.edit(
                self.strings["set_target_user_instructions"].format(trigger_id, chat_name, trigger_id, chat_id_arg_for_command),
                reply_markup=[
                    [{
                        "text": self.strings["back_to_trigger"],
                        "callback": self.back_to_trigger_info,
                        "args": (chat_id_str, trigger_name, trigger_id),
                    }]
                ]
            )

    async def remove_target_user_confirmed(self, call, chat_id_str, trigger_name, trigger_id):
        """Подтвержденное удаление целевого пользователя."""
        chat_name = await self._get_chat_name(chat_id_str)
        if chat_id_str in self.triggers and trigger_name in self.triggers[chat_id_str]:
            self.triggers[chat_id_str][trigger_name]["target_user_id"] = None
            self.db.set("Triggers", "triggers", self.triggers)
            await call.answer(self.strings["target_user_removed"].format(trigger_name, chat_name), show_alert=True)
            await self.back_to_trigger_info(call, chat_id_str, trigger_name, trigger_id)
        else:
            await call.edit(self.strings["trigger_not_found"].format(trigger_id, chat_name), link_preview=False)

    async def show_set_delay_instructions(self, call, chat_id_str, trigger_name, trigger_id):
        """Показывает инструкции по установке задержки."""
        chat_name = await self._get_chat_name(chat_id_str)
        chat_id_arg_for_command = chat_id_str if chat_id_str != str(call.chat_id) else ""

        await call.edit(
            self.strings["set_delay_instructions"].format(trigger_id, chat_name, trigger_id, chat_id_arg_for_command, trigger_id, chat_id_arg_for_command, trigger_id, chat_id_arg_for_command),
            reply_markup=[
                [{
                    "text": self.strings["back_to_trigger"],
                    "callback": self.back_to_trigger_info,
                    "args": (chat_id_str, trigger_name, trigger_id),
                }]
            ]
        )

    async def manage_stop_word_inline(self, call, chat_id_str, trigger_name, trigger_id, is_stop_word_set):
        """Обработка нажатий на кнопки управления стоп-словом."""
        chat_name = await self._get_chat_name(chat_id_str)
        if is_stop_word_set:
            await call.edit(
                self.strings["confirm_remove_target_user"].format(trigger_name),
                reply_markup=[
                    [{
                        "text": self.strings["confirm_delete_yes"],
                        "callback": self.remove_stop_word_confirmed,
                        "args": (chat_id_str, trigger_name, trigger_id),
                    }],
                    [{
                        "text": self.strings["confirm_delete_no"],
                        "callback": self.back_to_trigger_info,
                        "args": (chat_id_str, trigger_name, trigger_id),
                    }]
                ]
            )
        else:
            chat_id_arg_for_command = chat_id_str if chat_id_str != str(call.chat_id) else ""
            
            await call.edit(
                self.strings["set_stop_word_instructions"].format(trigger_id, chat_name, trigger_id, chat_id_arg_for_command),
                reply_markup=[
                    [{
                        "text": self.strings["back_to_trigger"],
                        "callback": self.back_to_trigger_info,
                        "args": (chat_id_str, trigger_name, trigger_id),
                    }]
                ]
            )

    async def remove_stop_word_confirmed(self, call, chat_id_str, trigger_name, trigger_id):
        """Подтвержденное удаление стоп-слова."""
        chat_name = await self._get_chat_name(chat_id_str)
        if chat_id_str in self.triggers and trigger_name in self.triggers[chat_id_str]:
            self.triggers[chat_id_str][trigger_name]["stop_word"] = None
            self.db.set("Triggers", "triggers", self.triggers)
            await call.answer(self.strings["stop_word_removed"].format(trigger_name, chat_name), show_alert=True)
            await self.back_to_trigger_info(call, chat_id_str, trigger_name, trigger_id)
        else:
            await call.edit(self.strings["trigger_not_found"].format(trigger_id, chat_name), link_preview=False)

    async def manage_stop_word_target_user_inline(self, call, chat_id_str, trigger_name, trigger_id, is_target_set):
        """Обработка нажатий на кнопки управления целевым пользователем для стоп-слова."""
        chat_name = await self._get_chat_name(chat_id_str)
        if is_target_set:
            await call.edit(
                self.strings["confirm_remove_stop_word_target_user"].format(trigger_name),
                reply_markup=[
                    [{
                        "text": self.strings["confirm_delete_yes"],
                        "callback": self.remove_stop_word_target_user_confirmed,
                        "args": (chat_id_str, trigger_name, trigger_id),
                    }],
                    [{
                        "text": self.strings["confirm_delete_no"],
                        "callback": self.back_to_trigger_info,
                        "args": (chat_id_str, trigger_name, trigger_id),
                    }]
                ]
            )
        else:
            chat_id_arg_for_command = chat_id_str if chat_id_str != str(call.chat_id) else ""
            
            await call.edit(
                self.strings["set_stop_word_target_user_instructions"].format(trigger_id, chat_name, trigger_id, chat_id_arg_for_command),
                reply_markup=[
                    [{
                        "text": self.strings["back_to_trigger"],
                        "callback": self.back_to_trigger_info,
                        "args": (chat_id_str, trigger_name, trigger_id),
                    }]
                ]
            )

    async def remove_stop_word_target_user_confirmed(self, call, chat_id_str, trigger_name, trigger_id):
        """Подтвержденное удаление целевого пользователя для стоп-слова."""
        chat_name = await self._get_chat_name(chat_id_str)
        if chat_id_str in self.triggers and trigger_name in self.triggers[chat_id_str]:
            self.triggers[chat_id_str][trigger_name]["stop_word_target_user_id"] = None
            self.db.set("Triggers", "triggers", self.triggers)
            await call.answer(self.strings["stop_word_target_user_removed"].format(trigger_name, chat_name), show_alert=True)
            await self.back_to_trigger_info(call, chat_id_str, trigger_name, trigger_id)
        else:
            await call.edit(self.strings["trigger_not_found"].format(trigger_id, chat_name), link_preview=False)

    async def confirm_trigger_delete(self, call, chat_id_str, trigger_name, trigger_id):
        """Запрос подтверждения удаления триггера."""
        confirm_text = self.strings["confirm_delete"].format(trigger_name) 
        
        await call.edit(
            confirm_text,
            reply_markup=[
                [{
                    "text": self.strings["confirm_delete_yes"],
                    "callback": self.delete_trigger_confirmed,
                    "args": (chat_id_str, trigger_name, trigger_id),
                }],
                [{
                    "text": self.strings["confirm_delete_no"],
                    "callback": self.back_to_trigger_info,
                    "args": (chat_id_str, trigger_name, trigger_id),
                }]
            ]
        )

    async def delete_trigger_confirmed(self, call, chat_id_str, trigger_name, trigger_id):
        """Подтвержденное удаление триггера."""
        chat_name = await self._get_chat_name(chat_id_str)
        if chat_id_str in self.triggers and trigger_name in self.triggers[chat_id_str]:
            del self.triggers[chat_id_str][trigger_name]
            if not self.triggers[chat_id_str]:
                del self.triggers[chat_id_str]
            self.db.set("Triggers", "triggers", self.triggers)
            
            await call.edit(
                self.strings["trigger_deleted"].format(trigger_id, chat_name),
                reply_markup=[],
                link_preview=False
            )
        else:
            await call.edit(
                self.strings["trigger_not_found"].format(trigger_id, chat_name),
                reply_markup=[],
                link_preview=False
            )

    async def show_trigger_mode_menu(self, call, chat_id_str, trigger_name, trigger_id):
        """Показывает меню выбора режима для конкретного триггера."""
        current_mode = self.triggers[chat_id_str][trigger_name]["mode"]

        def btn_text(mode_key):
            check = "✅ " if mode_key == current_mode else ""
            return f"{check}{self.strings[mode_key + '_mode']}"

        await call.edit(
            self.strings["mode_menu"],
            reply_markup=[
                [{
                    "text": btn_text("strict"),
                    "callback": self.set_trigger_mode,
                    "args": (chat_id_str, trigger_name, trigger_id, "strict"),
                }],
                [{
                    "text": btn_text("partial"),
                    "callback": self.set_trigger_mode,
                    "args": (chat_id_str, trigger_name, trigger_id, "partial"),
                }],
                [{
                    "text": btn_text("private"),
                    "callback": self.set_trigger_mode,
                    "args": (chat_id_str, trigger_name, trigger_id, "private"),
                }],
                [{
                    "text": self.strings["back_to_trigger"],
                    "callback": self.back_to_trigger_info,
                    "args": (chat_id_str, trigger_name, trigger_id),
                }]
            ]
        )

    async def set_trigger_mode(self, call, chat_id_str, trigger_name, trigger_id, new_mode):
        """Устанавливает новый режим для конкретного триггера."""
        if chat_id_str in self.triggers and trigger_name in self.triggers[chat_id_str]:
            self.triggers[chat_id_str][trigger_name]["mode"] = new_mode
            self.db.set("Triggers", "triggers", self.triggers)
            
            mode_name = {
                "strict": self.strings["strict_mode"],
                "partial": self.strings["partial_mode"], 
                "private": self.strings["private_mode"]
            }.get(new_mode, new_mode)
            
            await call.answer(self.strings["trigger_mode_changed"].format(mode_name), show_alert=False)
            await self.back_to_trigger_info(call, chat_id_str, trigger_name, trigger_id)
        else:
            chat_name = await self._get_chat_name(chat_id_str)
            await call.edit(self.strings["trigger_not_found"].format(trigger_id, chat_name), link_preview=False)


    async def back_to_trigger_info(self, call, chat_id_str, trigger_name, trigger_id):
        """Возвращает к информации о триггере."""
        chat_name = await self._get_chat_name(chat_id_str)
        info_text, reply_markup, _ = await self._get_trigger_info_data(chat_id_str, trigger_name, trigger_id)
        
        if info_text and reply_markup:
            await call.edit(
                info_text,
                reply_markup=reply_markup
            )
        else:
            await call.edit(
                self.strings["trigger_not_found"].format(trigger_id, chat_name),
                reply_markup=[],
                link_preview=False
            )

    async def trigmodecmd(self, message):
        """Изменить режим работы триггеров по умолчанию (для новых триггеров)"""
        user_id = str(message.sender_id)
        current_mode = self.modes.get(user_id, "strict")

        def btn_text(mode_key):
            check = "✅ " if mode_key == current_mode else ""
            return f"{check}{self.strings[mode_key + '_mode']}"

        await self.inline.form(
            message=message,
            text=self.strings["mode_menu"],
            reply_markup=[
                [{
                    "text": btn_text("strict"),
                    "callback": self.set_default_mode,
                    "args": ("strict",),
                    "description": self.strings["strict_desc"]
                }],
                [{
                    "text": btn_text("partial"),
                    "callback": self.set_default_mode,
                    "args": ("partial",),
                    "description": self.strings["partial_desc"]
                }],
                [{
                    "text": btn_text("private"),
                    "callback": self.set_default_mode,
                    "args": ("private",),
                    "description": self.strings["private_desc"]
                }]
            ],
            silent=True
        )

    async def set_default_mode(self, call, mode):
        """Устанавливает режим работы триггеров по умолчанию для пользователя."""
        user_id = str(call.from_user.id)
        self.modes[user_id] = mode
        self.db.set("Triggers", "modes", self.modes)

        def btn_text(mode_key):
            check = "✅ " if mode_key == mode else ""
            return f"{check}{self.strings[mode_key + '_mode']}"

        await call.edit(
            self.strings["mode_menu"],
            reply_markup=[
                [{
                    "text": btn_text("strict"),
                    "callback": self.set_default_mode,
                    "args": ("strict",),
                    "description": self.strings["strict_desc"]
                }],
                [{
                    "text": btn_text("partial"),
                    "callback": self.set_default_mode,
                    "args": ("partial",),
                    "description": self.strings["partial_desc"]
                }],
                [{
                    "text": btn_text("private"),
                    "callback": self.set_default_mode,
                    "args": ("private",),
                    "description": self.strings["private_desc"]
                }]
            ]
        )
        mode_name = {
            "strict": self.strings["strict_mode"],
            "partial": self.strings["partial_mode"], 
            "private": self.strings["private_mode"]
        }.get(mode, mode)
        
        await call.answer(self.strings["mode_changed"].format(mode_name), show_alert=False)

    async def trigdelcmd(self, message):
        """Удалить триггер по ID.
        Использование: .trigdel <ID_триггера> [ID_чата]
        Если ID чата не указан, триггер удаляется из текущего чата."""
        args_raw = utils.get_args_raw(message)
        parts = args_raw.split(maxsplit=1)

        target_chat_id_str = str(message.chat_id)
        trigger_id_str = None

        if not parts:
            await utils.answer(message, self.strings["invalid_trigdel_args"], link_preview=False)
            return

        trigger_id_str = parts[0]
        
        if not trigger_id_str.isdigit():
            await utils.answer(message, self.strings["invalid_trigger_id"], link_preview=False)
            return
        
        trigger_id_to_delete = int(trigger_id_str)

        if len(parts) > 1:
            potential_chat_id_str = parts[1]
            if self._is_chat_id_string(potential_chat_id_str):
                target_chat_id_str = potential_chat_id_str
            else:
                await utils.answer(message, self.strings["invalid_trigdel_args"], link_preview=False)
                return

        chat_name = await self._get_chat_name(target_chat_id_str)
        if target_chat_id_str not in self.triggers or not self.triggers[target_chat_id_str]:
            await utils.answer(message, self.strings["no_triggers_in_chat"].format(chat_name), link_preview=False)
            return
        
        deleted = False
        for trigger_name, data in list(self.triggers[target_chat_id_str].items()): 
            if data["id"] == trigger_id_to_delete:
                del self.triggers[target_chat_id_str][trigger_name]
                deleted = True
                break
        if deleted:
            if not self.triggers[target_chat_id_str]:
                del self.triggers[target_chat_id_str]
            self.db.set("Triggers", "triggers", self.triggers)
            await utils.answer(message, self.strings["trigger_deleted"].format(trigger_id_to_delete, chat_name), link_preview=False)
        else:
            await utils.answer(message, self.strings["trigger_not_found"].format(trigger_id_to_delete, chat_name), link_preview=False)

    def get_media_emoji(self, media):
        """Возвращает эмодзи, соответствующий типу медиа."""
        if isinstance(media, MessageMediaPhoto):
            return "<emoji document_id=5888799736508454231>🖼</emoji>"
        if isinstance(media, MessageMediaDocument):
            for attr in media.document.attributes:
                if isinstance(attr, DocumentAttributeSticker):
                    return "<emoji document_id=5915480455603295660>🎶</emoji>"
                if isinstance(attr, DocumentAttributeVideo):
                    return "<emoji document_id=5882106094402147455>🎥</emoji>" if attr.round_message else "<emoji document_id=5882002216323125435>🎥</emoji>"
                if isinstance(attr, DocumentAttributeAudio):
                    return "<emoji document_id=5897853622057700958>🎙</emoji>" if attr.voice else "<emoji document_id=5891249688933305846>🎵</emoji>"
            if media.document.mime_type:
                if media.document.mime_type.startswith('image/'):
                    return "<emoji document_id=5888799736508454231>🖼</emoji>"
                if media.document.mime_type.startswith('video/'):
                    return "<emoji document_id=5882002216323125435>🎥</emoji>"
                if media.document.mime_type.startswith('audio/'):
                    return "<emoji document_id=5891249688933305846>🎵</emoji>"
            return "<emoji document_id=5877301185639091664>📄</emoji>"
        return "<emoji document_id=5877301185639091664>📄</emoji>"

    def get_media_type_name(self, media):
        """Возвращает человекочитаемое название типа медиа."""
        if isinstance(media, MessageMediaPhoto):
            return "Фото"
        if isinstance(media, MessageMediaDocument):
            for attr in media.document.attributes:
                if isinstance(attr, DocumentAttributeSticker):
                    return "Стикер"
                if isinstance(attr, DocumentAttributeVideo):
                    return "Видео сообщение" if attr.round_message else "Видео"
                if isinstance(attr, DocumentAttributeAudio):
                    return "Голосовое сообщение" if attr.voice else "Аудио"
            if media.document.mime_type:
                mime = media.document.mime_type
                if mime.startswith('image/'):
                    return "Изображение"
                if mime.startswith('video/'):
                    return "Видеофайл"
                if mime.startswith('audio/'):
                    return "Аудиофайл"
                if mime.startswith('text/'):
                    return "Текстовый файл"
            return "Документ"
        return "Медиафайл"

    async def triglistcmd(self, message):
        """Показать список всех триггеров.
        Использование: .triglist [ID_чата]"""
        args_raw = utils.get_args_raw(message)
        
        target_chat_id_str = str(message.chat_id)
        if args_raw:
            if self._is_chat_id_string(args_raw):
                target_chat_id_str = args_raw
            else:
                await utils.answer(message, self.strings["triglist_instructions"], link_preview=False)
                return

        chat_name = await self._get_chat_name(target_chat_id_str)
        if target_chat_id_str not in self.triggers or not self.triggers[target_chat_id_str]:
            await message.respond(self.strings["no_triggers_in_chat"].format(chat_name), parse_mode='html', link_preview=False)
            return
        
        triggers_sorted = sorted(self.triggers[target_chat_id_str].items(), key=lambda item: item[1].get("id", 0))
        
        count = len(triggers_sorted)
        trigger_list = []
        for trigger_name, data in triggers_sorted:
            mode_emoji = {
                "strict": "🔒",
                "partial": "🔍", 
                "private": "🔐"
            }.get(data["mode"], "🔒")

            target_user_emoji = ""
            if data.get("target_user_id"):
                target_user_emoji = "🎯 "
            
            delay_emoji = ""
            delay_list = data.get("delay", [0])
            if any(d > 0 for d in delay_list):
                delay_emoji = "⏱ "

            stop_word_emoji = ""
            if data.get("stop_word"):
                stop_word_emoji = "🛑 "

            stop_word_target_user_emoji = ""
            if data.get("stop_word_target_user_id"):
                stop_word_target_user_emoji = "👤🛑 "

            preview_parts = []
            source_chat_id_for_get_messages = data.get("chat_id")
            source_message_id = data.get("message_id")

            try:
                msg = await self.client.get_messages(int(source_chat_id_for_get_messages), ids=source_message_id)
                if msg:
                    if msg.media:
                        preview_parts.append(self.get_media_emoji(msg.media))
                    
                    if msg.raw_text:
                        text_preview = msg.raw_text.replace('\n', ' ')[:30]
                        if len(msg.raw_text) > 30:
                            text_preview += "..."
                        preview_parts.append(text_preview)
                    
                    if not preview_parts and not msg.raw_text and not msg.media: 
                        preview_parts.append("[пустое сообщение]")
                    elif not preview_parts and (msg.raw_text or msg.media):
                        preview_parts.append("[сообщение с контентом]")
                else:
                    preview_parts.append("[сообщение удалено или недоступно]")
            except Exception:
                preview_parts.append("[сообщение удалено или недоступно]")
            
            preview = " ".join(preview_parts).strip()
            
            trigger_list.append(
                f"<code>{data['id']}</code>. {mode_emoji} {target_user_emoji}{delay_emoji}{stop_word_emoji}{stop_word_target_user_emoji}<code>{trigger_name}</code> → {preview}"
            )
        
        if target_chat_id_str == str(message.chat_id):
            final_message = self.strings["trigger_list"].format(count, "\n".join(trigger_list))
        else:
            final_message = self.strings["trigger_list_in_chat"].format(count, chat_name, "\n".join(trigger_list))

        await message.respond(final_message, parse_mode='html', link_preview=False)

    async def trigbancmd(self, message):
        """Заблокировать пользователя (ID / @username / реплай)"""
        user_id = await self._resolve_user_id(message, utils.get_args_raw(message))
        if not user_id:
            await utils.answer(message, self.strings["invalid_ban_args"], link_preview=False)
            return
        blacklist = self.db.get("Triggers", "blacklist", [])
        if user_id in blacklist:
            await utils.answer(message, self.strings["already_banned"], link_preview=False)
            return
        blacklist.append(user_id)
        self.db.set("Triggers", "blacklist", blacklist)
        await utils.answer(message, self.strings["banned"], link_preview=False)

    async def trigunbancmd(self, message):
        """Разблокировать пользователя (ID / @username / реплай)"""
        user_id = await self._resolve_user_id(message, utils.get_args_raw(message))
        if not user_id:
            await utils.answer(message, self.strings["invalid_ban_args"], link_preview=False)
            return
        blacklist = self.db.get("Triggers", "blacklist", [])
        if user_id not in blacklist:
            await utils.answer(message, self.strings["not_banned"], link_preview=False)
            return
        blacklist.remove(user_id)
        self.db.set("Triggers", "blacklist", blacklist)
        await utils.answer(message, self.strings["unbanned"], link_preview=False)

    async def trigbanlistcmd(self, message):
        """Показать чёрный список"""
        blacklist = self.db.get("Triggers", "blacklist", [])
        if not blacklist:
            await utils.answer(message, self.strings["empty_ban_list"], link_preview=False)
            return
        
        ban_list = []
        for user_id in blacklist:
            try:
                user = await self.client.get_entity(user_id)
                name = user.first_name or "Без имени"
                if user.last_name:
                    name += f" {user.last_name}"
                
                if hasattr(user, 'username') and user.username:
                    user_link = f'<a href="https://t.me/{user.username}">{name}</a>'
                else:
                    user_link = f'<a href="tg://user?id={user_id}">{name}</a>'
                
                ban_list.append(f"{user_link} (ID <code>{user_id}</code>)")
            except Exception:
                user_link = f'<a href="tg://user?id={user_id}">Неизвестный аккаунт</a>'
                ban_list.append(f"{user_link} (ID <code>{user_id}</code>)")
        
        await utils.answer(message, self.strings["ban_list"].format("\n".join(ban_list)), parse_mode='html', link_preview=False)

    async def trigreplymodecmd(self, message):
        """Включить/выключить режим ответа триггеров (по умолчанию отвечают)"""
        new_status = not self.reply_mode
        self.reply_mode = new_status
        self.db.set("Triggers", "reply_mode", new_status)
        
        status_text = self.strings["reply_mode_enabled"] if new_status else self.strings["reply_mode_disabled"]
        await utils.answer(message, self.strings["reply_mode_status"].format(status_text), link_preview=False)

    async def _send_response(self, message, data, trigger_name, reply_to_id=None):
        """Вспомогательная функция для отправки ответа на триггер."""
        reply_to_id = reply_to_id if reply_to_id is not None else (message.id if self.reply_mode else None)
        source_chat_id_for_get_messages = data.get("chat_id")
        source_message_id = data.get("message_id")
        source_chat_name = await self._get_chat_name(source_chat_id_for_get_messages)

        try:
            original_msg = await self.client.get_messages(int(source_chat_id_for_get_messages), ids=source_message_id)

            if not original_msg:
                error_info = self.strings["trigger_source_msg_deleted"].format(
                    source_message_id, source_chat_name
                )
                await self.client.send_message(
                    message.chat_id,
                    error_info,
                    reply_to=reply_to_id,
                    link_preview=False
                )
                return

            content_to_send = original_msg.message or ""
            file_to_send = original_msg.media

            if not content_to_send and not file_to_send:
                error_info = self.strings["trigger_source_msg_empty"].format(
                    source_message_id, source_chat_name
                )
                await self.client.send_message(
                    message.chat_id,
                    error_info,
                    reply_to=reply_to_id,
                    link_preview=False
                )
                return

            if "{NAME}" in content_to_send:
                user_full_name = await self.get_user_name(message.sender_id)
                content_to_send = content_to_send.replace("{NAME}", user_full_name)

            await self.client.send_message(
                message.chat_id,
                content_to_send,
                reply_to=reply_to_id,
                file=file_to_send,
                link_preview=False
            )
        except Exception as e:
            error_info = (
                f"<emoji document_id=5778527486270770928>❌</emoji> Неизвестная ошибка при срабатывании триггера '{trigger_name}' (ID: {data.get('id', 'N/A')}):\n"
                f"Сохранённый chat_id: {source_chat_id_for_get_messages}\n"
                f"Сохранённый message_id: {source_message_id}\n"
                f"Ошибка: {str(e)}"
            )
            await self.client.send_message(
                message.chat_id,
                error_info,
                reply_to=reply_to_id,
                link_preview=False
            )

    async def _send_delayed_response(self, original_message, trigger_data, trigger_name, activation_id, cancel_event):
        """Отправляет ответ на триггер после задержки, если он не был отменен."""
        delay_list = trigger_data.get("delay", [0])
        selected_delay = 0
        
        if len(delay_list) == 2 and delay_list[0] >= 0 and delay_list[1] >= 0 and delay_list[0] < delay_list[1]:
            # Range delay: random integer between min and max (inclusive)
            selected_delay = random.randint(delay_list[0], delay_list[1])
        elif len(delay_list) >= 1 and delay_list[0] > 0:
            # Single fixed delay or multiple discrete delays
            positive_delays = [d for d in delay_list if d > 0]
            if positive_delays:
                selected_delay = random.choice(positive_delays)
            # else: selected_delay remains 0 (no positive delays found)
        # else: selected_delay remains 0 (delay_list is [0] or empty/invalid)
        
        if selected_delay > 0:
            await asyncio.sleep(selected_delay)

        if cancel_event.is_set():
            return

        await self._send_response(original_message, trigger_data, trigger_name)

        if activation_id in self.pending_triggers:
            del self.pending_triggers[activation_id]

    async def watcher(self, message):
        """Обработчик входящих сообщений для срабатывания триггеров."""
        if not message.text or message.text.startswith("."): 
            return
        
        chat_id_str = str(message.chat_id)
        incoming_text_lower = message.text.lower()

        for activation_id, pending_info in list(self.pending_triggers.items()):
            pending_chat_id_str, _, _ = activation_id
            
            if pending_chat_id_str == chat_id_str:
                stop_word = pending_info.get('stop_word')
                stop_word_target_user_id = pending_info.get('stop_word_target_user_id')

                if stop_word and stop_word.lower() in incoming_text_lower:
                    if stop_word_target_user_id is None or message.sender_id == stop_word_target_user_id:
                        pending_info['cancel_event'].set()
                        if activation_id in self.pending_triggers:
                            del self.pending_triggers[activation_id]
        
        chats = self.db.get("Triggers", "chats", {})
        if not chats.get(chat_id_str, False):
            return
        
        if chat_id_str not in self.triggers or not self.triggers[chat_id_str]:
            return
        
        blacklist = self.db.get("Triggers", "blacklist", [])
        if message.sender_id in blacklist:
            return
        
        for trigger_name, data in self.triggers[chat_id_str].items():
            match = False
            
            trigger_target_user_id = data.get("target_user_id")
            if trigger_target_user_id is not None and message.sender_id != trigger_target_user_id:
                continue
            
            if data["mode"] == "private":
                if message.sender_id != self.client.me.id: 
                    continue
                if incoming_text_lower.strip() == trigger_name.strip():
                    match = True
            elif data["mode"] == "strict":
                if incoming_text_lower.strip() == trigger_name.strip():
                    match = True
            else:
                if trigger_name in incoming_text_lower:
                    match = True
                    
            if match:
                spam_check = self.check_spam(message.sender_id, trigger_name)
                
                if spam_check == "warn":
                    user_name = await self.get_user_name(message.sender_id)
                    warning_text = self.strings["spam_warning"].format(user_name)
                    await self.client.send_message(
                        message.chat_id,
                        warning_text,
                        reply_to=message.id if self.reply_mode else None,
                        link_preview=False
                    )
                    return
                elif spam_check == "ban":
                    await self.auto_ban_user(message.sender_id)
                    user_name = await self.get_user_name(message.sender_id)
                    ban_text = self.strings["spam_banned"].format(user_name)
                    await self.client.send_message(
                        message.chat_id,
                        ban_text,
                        reply_to=message.id if self.reply_mode else None,
                        link_preview=False
                    )
                    return
                
                delay_list = data.get("delay", [0])
                stop_word_for_this_trigger = data.get("stop_word")
                stop_word_target_user_id_for_this_trigger = data.get("stop_word_target_user_id")

                if any(d > 0 for d in delay_list):
                    trigger_activation_id = (chat_id_str, data['id'], time.time())
                    cancel_event = asyncio.Event()
                    self.pending_triggers[trigger_activation_id] = {
                        'cancel_event': cancel_event,
                        'stop_word': stop_word_for_this_trigger,
                        'stop_word_target_user_id': stop_word_target_user_id_for_this_trigger,
                        'trigger_name': trigger_name,
                    }
                    asyncio.create_task(self._send_delayed_response(message, data, trigger_name, trigger_activation_id, cancel_event))
                else:
                    await self._send_response(message, data, trigger_name)
                
                break
