# meta developer: @yourhandle
# meta name: TagAll
# meta version: 2.5.4 # Увеличиваем версию

import asyncio
import contextlib
import logging
import random
import time
import re
import unicodedata

from hikkatl.tl.functions.channels import InviteToChannelRequest
from hikkatl.tl.types import Message

from .. import loader, utils

logger = logging.getLogger(__name__)


class StopEvent:
    """
    Event class to signal stopping the TagAll process.
    Stores the chat_id to ensure the trigger message comes from the correct chat.
    """

    def __init__(self, chat_id: int):
        self.state = True
        self.chat_id = chat_id
        self.last_timeout: float | None = None # Хранит последний использованный таймаут для избежания повторов из списка

    def stop(self):
        self.state = False


@loader.tds
class TagAllMod(loader.Module):
    """Отмечает всех участников чата через команды или триггеры в тексте.
    Включает/выключает работу триггеров командой .autotagall."""

    strings = {
        "name": "TagAll",
        "bot_error": "🚫 <b>Не получилось пригласить бота в чат.</b>",
        "_cfg_doc_delete": "Удалять сообщения после тега",
        "_cfg_doc_use_bot": "Использовать бота для тегов",
        "_cfg_doc_timeout": "Время между сообщениями (число, список '0.1,0.5,1.0' или диапазон '0.1-1.0')",
        "_cfg_doc_silent": "Не отправлять сообщение с кнопкой отмены",
        "_cfg_doc_cycle_tagging": "Цикличный тег (пока не остановите)",
        "_cfg_doc_cycle_delay": "Задержка между циклами (сек)",
        "_cfg_doc_chunk_size": "Сколько пользователей в одном сообщении",
        "_cfg_doc_duration": "Длительность работы (0 = бесконечно)",
        "_cfg_doc_exclude_user_ids": "ID пользователей-исключений",
        "_cfg_doc_allowed_chat_ids": "ID разрешенных чатов для выполнения команд (через запятую)",
        "_cfg_start_trigger": "Триггер(ы) для запуска (если есть в тексте сообщения). Разделяйте запятыми.",
        "_cfg_stop_trigger": "Триггер(ы) для остановки (если есть в тексте сообщения). Разделяйте запятыми.",
        "_cfg_doc_allowed_trigger_user_ids": (
            "ID пользователей, которые могут использовать триггеры (через текст сообщения). "
            "Разделяйте запятыми. Если пусто, любой может использовать триггеры."
        ),
        "_cfg_doc_enable_watcher": "Включить/выключить работу триггеров (команда .autotagall)",
        "tagall_not_running": "🚫 <b>TagAll не запущен в чате {chat_id}.</b>",
        "tagall_already_running": "🚫 <b>TagAll уже запущен в чате {chat_id}.</b>",
        "no_eligible_participants": "🚫 <b>Нет подходящих участников.</b>",
        "cmd_redirected": "➡️ <b>Команда перенаправлена в чат</b> <code>{target_chat_id}</code>.",
        "cmd_redirected_default": "➡️ <b>Команда перенаправлена в чат</b> <code>{target_chat_id}</code> (выбран по умолчанию, т.к. несколько разрешенных чатов и не указан индекс).", # Новая строка
        "cmd_not_allowed_multiple": "🚫 <b>Чат не в белом списке. Разрешенные:</b> {allowed_chats}.",
        "trigger_not_allowed": "🚫 <b>Вам не разрешено использовать триггеры для TagAll.</b>",
        "autotagall_enabled": "✅ <b>Работа триггеров TagAll включена.</b>",
        "autotagall_disabled": "❌ <b>Работа триггеров TagAll выключена.</b>",
        "invalid_chat_index": "🚫 <b>Неверный индекс чата</b> <code>{index}</code>. Разрешенные чаты: {allowed_chats}.",
        "target_chat_not_found": "🚫 <b>Не удалось найти целевой чат с ID:</b> <code>{chat_id}</code> для выполнения тегирования.", # Новая строка
        "_cmd_tagall_doc": "[<номер чата>] [текст] - Отметить всех участников чата. [текст] будет отправлен вместе с тегами. Если текст не указан, будут отправлены только теги.",
        "_cmd_stoptagall_doc": "[<номер чата>] - Остановить запущенный процесс TagAll в <b>указанном или текущем чате</b>.",
        "_cmd_autotagall_doc": "Включить/выключить работу триггеров TagAll (установленных в .cfg)",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue("delete", False, lambda: self.strings("_cfg_doc_delete"), validator=loader.validators.Boolean()),
            loader.ConfigValue("use_bot", False, lambda: self.strings("_cfg_doc_use_bot"), validator=loader.validators.Boolean()),
            loader.ConfigValue("timeout", "0.1", lambda: self.strings("_cfg_doc_timeout"), validator=loader.validators.String()),
            loader.ConfigValue("silent", False, lambda: self.strings("_cfg_doc_silent"), validator=loader.validators.Boolean()),
            loader.ConfigValue("cycle_tagging", False, lambda: self.strings("_cfg_doc_cycle_tagging"), validator=loader.validators.Boolean()),
            loader.ConfigValue("cycle_delay", 0, lambda: self.strings("_cfg_doc_cycle_delay"), validator=loader.validators.Integer(minimum=0)),
            loader.ConfigValue("chunk_size", 3, lambda: self.strings("_cfg_doc_chunk_size"), validator=loader.validators.Integer(minimum=1)),
            loader.ConfigValue("duration", 0, lambda: self.strings("_cfg_doc_duration"), validator=loader.validators.Integer(minimum=0)),
            loader.ConfigValue("exclude_user_ids", "", lambda: self.strings("_cfg_doc_exclude_user_ids"), validator=loader.validators.String()),
            loader.ConfigValue("allowed_chat_ids", "", lambda: self.strings("_cfg_doc_allowed_chat_ids"), validator=loader.validators.String()),
            loader.ConfigValue("start_trigger", "тагалл", lambda: self.strings("_cfg_start_trigger"), validator=loader.validators.String()),
            loader.ConfigValue("stop_trigger", "стоп таг", lambda: self.strings("_cfg_stop_trigger"), validator=loader.validators.String()),
            loader.ConfigValue(
                "allowed_trigger_user_ids",
                "",
                lambda: self.strings("_cfg_doc_allowed_trigger_user_ids"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "enable_watcher",
                True,
                lambda: self.strings("_cfg_doc_enable_watcher"),
                validator=loader.validators.Boolean(),
            ),
        )
        self._tagall_events: dict[int, StopEvent] = {}
        self._translation_table = self._build_stylized_char_map()
        self._parsed_timeout_config = {}

    async def client_ready(self, client, db):
        self._client = client
        self._db = db
        self._parse_timeout_config()

    def on_config_update(self):
        """Вызывается при обновлении конфигурации, перепарсиваем таймаут."""
        self._parse_timeout_config()

    async def on_unload(self):
        for event in list(self._tagall_events.values()):
            event.stop()
        self._tagall_events.clear()

    async def _get_chat_entity_safe(self, chat_id: int):
        """Безопасно получает сущность чата."""
        try:
            return await self._client.get_input_entity(chat_id)
        except Exception as e:
            logger.error(f"TagAll: Не удалось получить сущность чата для ID {chat_id}: {e}")
            return None

    async def _send_feedback_message(self, chat_id: int, text: str):
        """Отправляет сообщение обратной связи в указанный чат."""
        entity = await self._get_chat_entity_safe(chat_id)
        if entity:
            with contextlib.suppress(Exception):
                await self._client.send_message(entity, text, parse_mode="HTML")
        else:
            logger.warning(f"TagAll: Не удалось отправить сообщение обратной связи в чат {chat_id} (сущность не найдена): {text[:100]}...")

    def _build_stylized_char_map(self) -> dict:
        """
        Строит таблицу для преобразования стилизованных Unicode-символов
        (например, жирные, курсивные из математических блоков)
        в их базовые строчные аналоги, а также для нормализации пробелов и дефисов.
        """
        translation_table = str.maketrans("", "")

        def add_stylized_block(start_stylized_char: str, start_base_char: str, length: int):
            for i in range(length):
                stylized_char_code = ord(start_stylized_char) + i
                base_char_lower = chr(ord(start_base_char) + i).lower()
                if chr(stylized_char_code) != base_char_lower:
                    translation_table[stylized_char_code] = base_char_lower

        # Математические буквенно-цифровые символы (латиница)
        add_stylized_block('𝐀', 'A', 26) # Bold Capitals
        add_stylized_block('𝐚', 'a', 26) # Bold Small
        add_stylized_block('𝐴', 'A', 26) # Italic Capitals
        add_stylized_block('𝑎', 'a', 26) # Italic Small
        add_stylized_block('𝑨', 'A', 26) # Bold Italic Capitals
        add_stylized_block('𝒂', 'a', 26) # Bold Italic Small
        add_stylized_block('𝙰', 'A', 26) # Monospace Capitals
        add_stylized_block('𝚊', 'a', 26) # Monospace Small
        
        # Цифры различных стилей
        add_stylized_block('𝟎', '0', 10) # Bold
        add_stylized_block('𝟘', '0', 10) # Double-struck
        add_stylized_block('𝟢', '0', 10) # Sans-serif
        add_stylized_block('𝟬', '0', 10) # Sans-serif Bold
        add_stylized_block('𝟶', '0', 10) # Monospace

        # Полноширинные ASCII символы (часто используются в азиатских шрифтах)
        for char_code in range(ord('！'), ord('～') + 1):
            normalized_char = unicodedata.normalize("NFKC", chr(char_code)).lower()
            if chr(char_code) != normalized_char and len(normalized_char) == 1:
                translation_table[char_code] = normalized_char

        # Удаляем невидимые символы (Zero-Width Space и т.д.)
        translation_table[0x200B] = None # Zero Width Space
        translation_table[0x200C] = None # Zero Width Non-Joiner
        translation_table[0x200D] = None # Zero Width Joiner

        # Нормализуем различные типы дефисов к стандартному
        translation_table[0x2010] = '-' # Hyphen
        translation_table[0x2011] = '-' # Non-breaking hyphen
        translation_table[0x2012] = '-' # Figure dash
        translation_table[0x2013] = '-' # En dash
        translation_table[0x2014] = '-' # Em dash
        translation_table[0x2015] = '-' # Horizontal bar

        # Нормализуем различные пробелы к стандартному
        translation_table[0x00A0] = ' ' # NO-BREAK SPACE
        translation_table[0x2000] = ' ' # EN QUAD
        translation_table[0x2001] = ' ' # EM QUAD
        translation_table[0x2002] = ' ' # EN SPACE
        translation_table[0x2003] = ' ' # EM SPACE
        translation_table[0x2004] = ' ' # THREE-PER-EM SPACE
        translation_table[0x2005] = ' ' # FOUR-PER-EM SPACE
        translation_table[0x2006] = ' ' # SIX-PER-EM SPACE
        translation_table[0x2007] = ' ' # FIGURE SPACE
        translation_table[0x2008] = ' ' # PUNCTUATION SPACE
        translation_table[0x2009] = ' ' # THIN SPACE
        translation_table[0x200A] = ' ' # HAIR SPACE
        translation_table[0x202F] = ' ' # NARROW NO-BREAK SPACE
        translation_table[0x205F] = ' ' # MEDIUM MATHEMATICAL SPACE
        translation_table[0x3000] = ' ' # IDEOGRAPHIC SPACE

        return translation_table

    def _normalize_text_for_trigger(self, text: str) -> str:
        """
        Нормализует текст для сравнения с триггерами.
        Преобразует стилизованные Unicode-символы в их стандартные строчные эквиваленты,
        удаляет нулевой ширины символы и нормализует различные пробелы/дефисы.
        """
        if not isinstance(text, str):
            return ""

        # Сначала применяем NFKC нормализацию для общей совместимости (например, лигатуры, полноширинные)
        normalized_text = unicodedata.normalize("NFKC", text)

        # Применяем предварительно построенную таблицу преобразований
        processed_text = normalized_text.translate(self._translation_table)

        # Переводим весь текст в нижний регистр
        processed_text = processed_text.lower()
        
        # Заменяем несколько пробелов на один и удаляем пробелы в начале/конце
        processed_text = re.sub(r'\s+', ' ', processed_text).strip()

        return processed_text

    def _parse_timeout_config(self):
        """
        Парсит строку конфигурации таймаута и сохраняет ее в структурированном виде.
        Вызывается при загрузке модуля и при изменении конфигурации.
        """
        timeout_str = str(self.config["timeout"])
        cleaned = re.sub(r"[^0-9.,-]", "", timeout_str)
        
        # Дефолтное значение
        self._parsed_timeout_config = {"type": "single", "value": 0.1}

        if not cleaned:
            return

        if "-" in cleaned:
            parts = cleaned.split("-")
            if len(parts) == 2:
                try:
                    min_val = max(0.0, float(parts[0]))
                    max_val = max(0.0, float(parts[1]))
                    if min_val > max_val: min_val, max_val = max_val, min_val
                    self._parsed_timeout_config = {"type": "range", "min": min_val, "max": max_val}
                    return
                except ValueError:
                    logger.warning(f"TagAll: Не удалось разобрать диапазон таймаута '{timeout_str}'. Используется значение по умолчанию 0.1.")
        elif "," in cleaned:
            try:
                vals = sorted([max(0.0, float(x)) for x in cleaned.split(",") if x.strip()])
                if vals:
                    self._parsed_timeout_config = {"type": "list", "values": vals}
                    return
                else:
                    logger.warning(f"TagAll: Не найдено валидных чисел в списке таймаутов '{timeout_str}'. Используется значение по умолчанию 0.1.")
            except ValueError:
                logger.warning(f"TagAll: Не удалось разобрать список таймаутов '{timeout_str}'. Используется значение по умолчанию 0.1.")
        else:
            try:
                single_val = max(0.0, float(cleaned))
                self._parsed_timeout_config = {"type": "single", "value": single_val}
                return
            except ValueError:
                logger.warning(f"TagAll: Не удалось разобрать одиночное значение таймаута '{timeout_str}'. Используется значение по умолчанию 0.1.")

    @loader.watcher()
    async def watcher(self, message: Message):
        if not self.config["enable_watcher"]:
            return

        if not isinstance(message, Message) or not message.text:
            return

        # Проверяем, разрешено ли отправителю использовать триггеры
        allowed_trigger_ids_raw = self.config["allowed_trigger_user_ids"]
        allowed_trigger_ids = {int(x.strip()) for x in allowed_trigger_ids_raw.split(",") if x.strip().isdigit()}

        if allowed_trigger_ids and message.sender_id not in allowed_trigger_ids:
            await self._send_feedback_message(message.chat_id, self.strings("trigger_not_allowed"))
            return

        # Нормализуем текст сообщения для сравнения с триггерами
        message_text_normalized = self._normalize_text_for_trigger(message.text)
        
        stop_triggers_raw = self.config["stop_trigger"]
        stop_triggers = [self._normalize_text_for_trigger(t) for t in stop_triggers_raw.split(',') if t.strip()]

        start_triggers_raw = self.config["start_trigger"]
        start_triggers = [self._normalize_text_for_trigger(t) for t in start_triggers_raw.split(',') if t.strip()]

        # Получаем целевой и обратный чаты. Для watcher, feedback_chat_id всегда message.chat_id
        target_chat_id, feedback_chat_id, _ = await self._resolve_target_chat_for_watcher(message)
        if target_chat_id is None: # Если не удалось определить целевой чат, то и триггер не сработает
            return

        # Сначала проверяем стоп-триггер
        for trigger in stop_triggers:
            if trigger and trigger in message_text_normalized:
                await self._stop_logic_internal(target_chat_id, feedback_chat_id)
                return

        # Затем старт-триггер
        for trigger in start_triggers:
            if trigger and trigger in message_text_normalized:
                # Для триггера, префикс сообщения всегда пустой, так как используется только наличие триггера
                await self._start_logic_internal(target_chat_id, "", feedback_chat_id)
                return

    def _get_allowed_chat_ids_map(self) -> dict[int, int]:
        allowed_ids_raw = self.config["allowed_chat_ids"]
        allowed_chats_map = {}
        cleaned = re.sub(r"[^0-9,]", "", allowed_ids_raw)
        if not cleaned: return {}
        for i, chat_id_str in enumerate(cleaned.split(',')):
            if chat_id_str:
                with contextlib.suppress(ValueError):
                    allowed_chats_map[i + 1] = int(chat_id_str)
        return allowed_chats_map

    def _format_allowed_chats_list(self, allowed_chats_map: dict[int, int]) -> str:
        """Форматирует список разрешенных чатов для вывода."""
        if not allowed_chats_map:
            return "<i>нет</i>"
        return ", ".join([f"<code>{idx}</code>: <code>{chat_id}</code>" for idx, chat_id in sorted(allowed_chats_map.items())])

    async def _resolve_target_chat(self, message: Message, raw_args: str) -> tuple[int | None, int, str | None]:
        """
        Определяет целевой чат для выполнения (тегирования) и чат для обратной связи.
        Возвращает (target_chat_id, feedback_chat_id, remaining_args).
        feedback_chat_id всегда равен chat_id оригинального сообщения.
        """
        original_chat_id = message.chat_id
        feedback_chat_id = original_chat_id # Сообщения обратной связи всегда в чат, откуда пришла команда
        remaining_args = raw_args.strip()

        allowed_chats_map = self._get_allowed_chat_ids_map()
        allowed_chat_ids_set = set(allowed_chats_map.values())
        target_chat_id = None

        # Если allowed_chat_ids не настроен, команды работают в текущем чате без ограничений.
        if not allowed_chat_ids_set:
            return original_chat_id, feedback_chat_id, remaining_args

        # Проверяем, указан ли явный индекс чата в аргументах команды
        chat_index_match = re.match(r"^\s*(\d+)\s*(.*)$", remaining_args)
        if chat_index_match:
            try:
                index = int(chat_index_match.group(1))
                if index in allowed_chats_map:
                    target_chat_id = allowed_chats_map[index]
                    # Сообщение о перенаправлении, если указан индекс и он отличается от текущего чата
                    if target_chat_id != original_chat_id:
                        await self._send_feedback_message(feedback_chat_id, self.strings("cmd_redirected").format(target_chat_id=target_chat_id))
                    return target_chat_id, feedback_chat_id, chat_index_match.group(2).strip()
                else:
                    await self._send_feedback_message(feedback_chat_id, self.strings("invalid_chat_index").format(index=index, allowed_chats=self._format_allowed_chats_list(allowed_chats_map)))
                    return None, feedback_chat_id, None
            except ValueError:
                pass # Невалидный индекс, продолжаем с обычной проверкой

        # Если текущий чат входит в список разрешенных
        if original_chat_id in allowed_chat_ids_set:
            return original_chat_id, feedback_chat_id, remaining_args
        
        # Если текущий чат НЕ входит в список разрешенных, но список разрешенных НЕ пуст.
        # Это сценарий перенаправления.
        if len(allowed_chat_ids_set) == 1:
            target_chat_id = next(iter(allowed_chat_ids_set))
            await self._send_feedback_message(feedback_chat_id, self.strings("cmd_redirected").format(target_chat_id=target_chat_id))
            return target_chat_id, feedback_chat_id, remaining_args
        else: # len(allowed_chat_ids_set) > 1
            # Если разрешенных чатов несколько и не указан индекс, выбираем первый из отсортированных.
            sorted_allowed_ids = sorted(list(allowed_chat_ids_set))
            target_chat_id = sorted_allowed_ids[0]
            await self._send_feedback_message(feedback_chat_id, self.strings("cmd_redirected_default").format(target_chat_id=target_chat_id))
            return target_chat_id, feedback_chat_id, remaining_args

    async def _resolve_target_chat_for_watcher(self, message: Message) -> tuple[int | None, int, str | None]:
        """
        Специальная версия _resolve_target_chat для watcher, где нет аргументов,
        и всегда происходит перенаправление в первый разрешенный чат, если текущий не разрешен.
        """
        original_chat_id = message.chat_id
        feedback_chat_id = original_chat_id
        
        allowed_chats_map = self._get_allowed_chat_ids_map()
        allowed_chat_ids_set = set(allowed_chats_map.values())
        
        # Если allowed_chat_ids не настроен, триггер работает в текущем чате.
        if not allowed_chat_ids_set:
            return original_chat_id, feedback_chat_id, ""

        # Если текущий чат входит в список разрешенных
        if original_chat_id in allowed_chat_ids_set:
            return original_chat_id, feedback_chat_id, ""
        
        # Если текущий чат НЕ входит в список разрешенных, но allowed_chat_ids НЕ пуст.
        # Триггеры перенаправляются в первый разрешенный чат.
        if allowed_chat_ids_set:
            sorted_allowed_ids = sorted(list(allowed_chat_ids_set))
            target_chat_id = sorted_allowed_ids[0]
            await self._send_feedback_message(feedback_chat_id, self.strings("cmd_redirected_default").format(target_chat_id=target_chat_id))
            return target_chat_id, feedback_chat_id, ""
        
        # Если allowed_chat_ids настроен, но ни один чат не подходит (чего быть не должно при правильной логике)
        await self._send_feedback_message(feedback_chat_id, self.strings("cmd_not_allowed_multiple").format(
            allowed_chats=self._format_allowed_chats_list(allowed_chats_map)
        ))
        return None, feedback_chat_id, ""


    async def _start_logic_internal(self, target_chat_id: int, message_prefix: str, feedback_chat_id: int):
        if target_chat_id in self._tagall_events and self._tagall_events[target_chat_id].state:
            await self._send_feedback_message(feedback_chat_id, self.strings("tagall_already_running").format(chat_id=target_chat_id))
            return

        event = StopEvent(target_chat_id)
        self._tagall_events[target_chat_id] = event
        self._client.loop.create_task(self._run_tagall_process(target_chat_id, message_prefix, event, feedback_chat_id))

    async def _stop_logic_internal(self, target_chat_id: int, feedback_chat_id: int):
        event = self._tagall_events.get(target_chat_id)
        if event and event.state:
            event.stop()
        else:
            await self._send_feedback_message(feedback_chat_id, self.strings("tagall_not_running").format(chat_id=target_chat_id))

    @loader.command(
        groups=True,
        ru_doc=lambda self: self.strings("_cmd_tagall_doc"),
    )
    async def tagall(self, message: Message):
        target_chat_id, feedback_chat_id, message_prefix = await self._resolve_target_chat(message, utils.get_args_raw(message))
        if message.out:
            with contextlib.suppress(Exception): await message.delete()
        
        if target_chat_id is None:
            return # _resolve_target_chat уже отправил сообщение об ошибке

        await self._start_logic_internal(target_chat_id, message_prefix, feedback_chat_id)

    @loader.command(
        ru_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
    )
    async def stoptagall(self, message: Message):
        target_chat_id, feedback_chat_id, _ = await self._resolve_target_chat(message, utils.get_args_raw(message))
        if message.out:
            with contextlib.suppress(Exception): await message.delete()

        if target_chat_id is None:
            return

        await self._stop_logic_internal(target_chat_id, feedback_chat_id)

    @loader.command(
        ru_doc=lambda self: self.strings("_cmd_autotagall_doc"),
    )
    async def autotagall(self, message: Message):
        if message.out:
            with contextlib.suppress(Exception): await message.delete()
            
        self.config["enable_watcher"] = not self.config["enable_watcher"]
        
        # Для autotagall не нужно разрешение чата, это глобальная настройка.
        # Сообщение всегда в текущий чат.
        if self.config["enable_watcher"]:
            await self._send_feedback_message(message.chat_id, self.strings("autotagall_enabled"))
        else:
            await self._send_feedback_message(message.chat_id, self.strings("autotagall_disabled"))

    def _get_random_timeout(self, event: StopEvent) -> float:
        """
        Возвращает случайный таймаут на основе предразобранной конфигурации.
        """
        timeout_cfg = self._parsed_timeout_config
        
        if timeout_cfg["type"] == "range":
            new_timeout = random.uniform(timeout_cfg["min"], timeout_cfg["max"])
        elif timeout_cfg["type"] == "list":
            vals = timeout_cfg["values"]
            # Избегаем повторения того же таймаута, если есть несколько значений
            if len(vals) > 1 and event.last_timeout is not None and event.last_timeout in vals:
                available_values = [v for v in vals if v != event.last_timeout]
                if available_values:
                    new_timeout = random.choice(available_values)
                else: # Если все значения совпадают с last_timeout, повтор допустим
                    new_timeout = random.choice(vals)
            else:
                new_timeout = random.choice(vals)
        else: # "single"
            new_timeout = timeout_cfg["value"]
        
        event.last_timeout = new_timeout
        return new_timeout

    async def _run_tagall_process(self, target_chat_id: int, message_prefix: str, event: StopEvent, feedback_chat_id: int):
        """Внутренняя функция для обработки основной логики TagAll."""
        deleted_message_ids_hikkatl = []
        deleted_message_ids_bot_client = []

        is_bot_sender = self.config["use_bot"]
        inline_bot_client_available = False
        if is_bot_sender:
            inline_bot_client_available = hasattr(self, 'inline') and getattr(self.inline, 'bot_client', None)

        target_chat_entity = await self._get_chat_entity_safe(target_chat_id)
        if not target_chat_entity:
            await self._send_feedback_message(feedback_chat_id, self.strings("target_chat_not_found").format(chat_id=target_chat_id))
            event.stop()
            if target_chat_id in self._tagall_events:
                del self._tagall_events[target_chat_id]
            return

        excluded_user_ids = set()
        exclude_ids_raw = self.config["exclude_user_ids"]
        for uid_str in exclude_ids_raw.split(','):
            uid_str = uid_str.strip()
            if uid_str:
                with contextlib.suppress(ValueError):
                    excluded_user_ids.add(int(uid_str))

        if is_bot_sender and not inline_bot_client_available:
            logger.error("TagAll: Клиент инлайн-бота не настроен или недоступен, не могу использовать его для тегов.")
            await self._send_feedback_message(feedback_chat_id, self.strings("bot_error"))
            event.stop()
            if target_chat_id in self._tagall_events:
                del self._tagall_events[target_chat_id]
            return

        if is_bot_sender and inline_bot_client_available:
            try:
                bot_entity = await self._client.get_input_entity(self.inline.bot_username)
                with contextlib.suppress(Exception):
                    await self._client(InviteToChannelRequest(target_chat_entity, [bot_entity]))
            except Exception as e:
                logger.error(f"TagAll: Не удалось получить сущность бота или пригласить бота: {e}")
                pass

        participants = []
        owner_id = self._client.tg_id
        async for user in self._client.iter_participants(target_chat_id):
            if not user.bot and not user.deleted and user.id != owner_id and user.id not in excluded_user_ids:
                participants.append(user)

        if not participants:
            logger.warning(f"TagAll: В чате {target_chat_id} не найдено подходящих участников для TagAll, останавливаем.")
            await self._send_feedback_message(feedback_chat_id, self.strings("no_eligible_participants"))
            event.stop()
            if target_chat_id in self._tagall_events:
                del self._tagall_events[target_chat_id]
            return

        random.shuffle(participants)

        start_time = time.time()

        try:
            first_pass = True
            while self.config["cycle_tagging"] or first_pass:
                if not event.state:
                    break

                if self.config["duration"] > 0 and (time.time() - start_time) > self.config["duration"]:
                    event.stop()
                    break

                current_cycle_participants = []
                if self.config["cycle_tagging"] and not first_pass: # Re-fetch participants if cycling
                    logger.debug(f"TagAll: Повторный запрос участников для цикла в чате {target_chat_id}.")
                    async for user in self._client.iter_participants(target_chat_id):
                        if not user.bot and not user.deleted and user.id != owner_id and user.id not in excluded_user_ids:
                            current_cycle_participants.append(user)
                    random.shuffle(current_cycle_participants)
                    participants = current_cycle_participants
                    if not participants:
                        logger.warning(f"TagAll: В чате {target_chat_id} не найдено участников для TagAll для следующего цикла, останавливаем.")
                        break

                for chunk in utils.chunks(participants, self.config["chunk_size"]):
                    if not event.state:
                        break

                    if self.config["duration"] > 0 and (time.time() - start_time) > self.config["duration"]:
                        event.stop()
                        break

                    tags = []
                    for user in chunk:
                        user_display_name = (
                            f"@{user.username}"
                            if user.username
                            else utils.escape_html(" ".join(filter(None, [user.first_name, user.last_name])) or "Пользователь")
                        )
                        tags.append(f'<a href="tg://user?id={user.id}">{user_display_name}</a>')

                    if message_prefix:
                        full_message_text = f"{message_prefix}\n{' '.join(tags)}"
                    else:
                        full_message_text = " ".join(tags)

                    # Отправка самих тегов всегда в target_chat_id
                    if is_bot_sender and inline_bot_client_available:
                        m = await self.inline.bot_client.send_message(
                            target_chat_id, # Отправляем теги в целевой чат
                            full_message_text,
                            parse_mode="HTML",
                        )
                        if self.config["delete"]:
                            deleted_message_ids_bot_client.append(m.id)
                    else:
                        m = await self._client.send_message(
                            target_chat_entity, # Отправляем теги в целевой чат
                            full_message_text,
                            parse_mode="HTML",
                        )
                        if self.config["delete"]:
                            deleted_message_ids_hikkatl.append(m.id)

                    await asyncio.sleep(self._get_random_timeout(event))

                first_pass = False
                if self.config["cycle_tagging"] and event.state:
                    await asyncio.sleep(self.config["cycle_delay"])
                elif not self.config["cycle_tagging"]:
                    break

        finally:
            if self.config["delete"]:
                with contextlib.suppress(Exception):
                    if deleted_message_ids_hikkatl:
                        for chunk_ids in utils.chunks(deleted_message_ids_hikkatl, 100):
                            await self._client.delete_messages(target_chat_entity, chunk_ids)

                    if deleted_message_ids_bot_client:
                        if inline_bot_client_available:
                            for chunk_ids in utils.chunks(deleted_message_ids_bot_client, 100):
                                await self.inline.bot_client.delete_messages(target_chat_entity, chunk_ids)
                        else:
                            logger.warning("TagAll: Клиент инлайн-бота недоступен для удаления своих сообщений.")

            if event.state:
                logger.info(f"TagAll: Процесс TagAll завершен естественным образом в чате {target_chat_id}.")

            if target_chat_id in self._tagall_events:
                del self._tagall_events[target_chat_id]
