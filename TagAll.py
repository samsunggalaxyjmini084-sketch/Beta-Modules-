# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# Code is licensed under CC-BY-NC-ND 4.0 unless otherwise specified.
# 🌐 https://github.com/hikariatama/Hikka
# 🔑 https://creativecommons.org/licenses/by-nc-nd/4.0/
# + attribution
# + non-commercial
# + no-derivatives

# You CANNOT edit this file without direct permission from the author.
# You can redistribute this file without any changes.

# meta pic: https://static.dan.tatar/tagall_icon.png
# meta developer: @hikarimods
# meta banner: https://mods.hikariatama.ru/badges/tagall.jpg
# scope: hikka_min 1.6.3

import asyncio
import contextlib
import logging
import random
import time
import re
import unicodedata  # Импортируем unicodedata

from aiogram import Bot # Для использования inline.bot
from hikkatl.tl.functions.channels import InviteToChannelRequest
from hikkatl.tl.types import Message

from .. import loader, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


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


@loader.tds
class TagAllMod(loader.Module):
    """Отмечает всех участников чата через команды или триггеры в тексте.
    Включает/выключает работу триггеров командой .autotagall."""

    strings = {
        "name": "TagAll",
        "bot_error": "🚫 <b>Unable to invite inline bot to chat</b>",
        "_cfg_doc_default_message": "Default message of mentions",
        "_cfg_doc_delete": "Delete messages after tagging",
        "_cfg_doc_use_bot": "Use inline bot to tag people",
        "_cfg_doc_timeout": "What time interval to sleep between each tag message (number, list or range 0.1-1.0)",
        "_cfg_doc_silent": "Do not send message with cancel button",
        "_cfg_doc_cycle_tagging": "Tag all participants over and over again until you stop the script using the button in the message",
        "_cfg_doc_cycle_delay": "Delay between each cycle of tagging in seconds",
        "_cfg_doc_chunk_size": "How many users in one message",
        "_cfg_doc_duration": "Duration of work (0 = infinite)",
        "_cfg_doc_exclude_user_ids": "IDs of excluded users (comma separated)",
        "_cfg_doc_allowed_chat_ids": "IDs of allowed chats for commands (comma separated, use format 'index:chat_id' or just 'chat_id')",
        "_cfg_start_trigger": "Trigger(s) to start (if present in message text). Separate by commas.",
        "_cfg_stop_trigger": "Trigger(s) to stop (if present in message text). Separate by commas.",
        "_cfg_doc_allowed_trigger_user_ids": "IDs of users who can use triggers (via message text). Separate by commas. If empty, anyone can use triggers.",
        "_cfg_doc_enable_watcher": "Enable/disable trigger watcher ('.autotagall' command)",
        "gathering": "🧚‍♀️ <b>Calling participants of this chat...</b>",
        "cancel": "🚫 Cancel",
        "cancelled": "🧚‍♀️ <b>TagAll cancelled!</b>",
        "tagall_not_running": "🚫 <b>TagAll is not running in chat {chat_id}.</b>",
        "tagall_already_running": "🚫 <b>TagAll is already running in chat {chat_id}.</b>",
        "no_eligible_participants": "🚫 <b>No eligible participants found.</b>",
        "cmd_redirected": "➡️ <b>Command redirected to chat</b> <code>{target_chat_id}</code>, as it's the only allowed one.",
        "cmd_not_allowed_multiple": "🚫 <b>Chat is not in the whitelist. Allowed:</b> {allowed_chats}.",
        "invalid_chat_index": "🚫 <b>Invalid chat index {index}. Allowed:</b> {allowed_chats}.",
        "trigger_not_allowed": "🚫 <b>You are not allowed to use TagAll triggers.</b>",
        "autotagall_enabled": "✅ <b>TagAll triggers enabled.</b>",
        "autotagall_disabled": "❌ <b>TagAll triggers disabled.</b>",
        "_cmd_tagall_doc": "[<chat_index>] [text] - Tag all chat participants. [text] will be sent with tags. If no text is specified, only tags will be sent.",
        "_cmd_stoptagall_doc": "[<chat_index>] - Stop the running TagAll process in the <b>specified or current chat</b>.",
        "_cmd_autotagall_doc": "Enable/disable TagAll triggers (set in .cfg)",
    }

    strings_ru = {
        "bot_error": "🚫 <b>Не получилось пригласить бота в чат.</b>",
        "_cls_doc": (
            "Отмечает всех участников чата через команды или триггеры в тексте."
            " Включает/выключает работу триггеров командой .autotagall."
        ),
        "_cfg_doc_default_message": "Сообщение по умолчанию для тегов",
        "_cfg_doc_delete": "Удалять сообщения после тега",
        "_cfg_doc_use_bot": "Использовать бота для тегов",
        "_cfg_doc_timeout": "Время между сообщениями с тегами (число, список или диапазон 0.1-1.0)",
        "_cfg_doc_silent": "Не отправлять сообщение с кнопкой отмены",
        "_cfg_doc_cycle_tagging": (
            "Тегать всех участников снова и снова, пока вы не остановите скрипт,"
            " используя кнопку в сообщении"
        ),
        "_cfg_doc_cycle_delay": "Задержка между циклами тегов в секундах",
        "_cfg_doc_chunk_size": "Сколько пользователей в одном сообщении",
        "_cfg_doc_duration": "Длительность работы (0 = бесконечно)",
        "_cfg_doc_exclude_user_ids": "ID пользователей-исключений (через запятую)",
        "_cfg_doc_allowed_chat_ids": "ID разрешенных чатов для выполнения команд (через запятую, формат 'индекс:ID_чата' или просто 'ID_чата')",
        "_cfg_start_trigger": "Триггер(ы) для запуска (если есть в тексте сообщения). Разделяйте запятыми.",
        "_cfg_stop_trigger": "Триггер(ы) для остановки (если есть в тексте сообщения). Разделяйте запятыми.",
        "_cfg_doc_allowed_trigger_user_ids": (
            "ID пользователей, которые могут использовать триггеры (через текст сообщения). "
            "Разделяйте запятыми. Если пусто, любой может использовать триггеры."
        ),
        "_cfg_doc_enable_watcher": "Включить/выключить работу триггеров (команда .autotagall)",
        "gathering": "🧚‍♀️ <b>Отмечаю участников чата...</b>",
        "cancel": "🚫 Отмена",
        "cancelled": "🧚‍♀️ <b>Сбор участников отменен!</b>",
        "tagall_not_running": "🚫 <b>TagAll не запущен в чате {chat_id}.</b>",
        "tagall_already_running": "🚫 <b>TagAll уже запущен в чате {chat_id}.</b>",
        "no_eligible_participants": "🚫 <b>Нет подходящих участников.</b>",
        "cmd_redirected": "➡️ <b>Команда перенаправлена в чат</b> <code>{target_chat_id}</code>, так как он единственный разрешенный.",
        "cmd_not_allowed_multiple": "🚫 <b>Чат не в белом списке. Разрешенные:</b> {allowed_chats}.",
        "invalid_chat_index": "🚫 <b>Неверный индекс чата {index}. Разрешенные:</b> {allowed_chats}.",
        "trigger_not_allowed": "🚫 <b>Вам не разрешено использовать триггеры для TagAll.</b>",
        "autotagall_enabled": "✅ <b>Работа триггеров TagAll включена.</b>",
        "autotagall_disabled": "❌ <b>Работа триггеров TagAll выключена.</b>",
        "_cmd_tagall_doc": "[<номер чата>] [текст] - Отметить всех участников чата. [текст] будет отправлен вместе с тегами. Если текст не указан, будут отправлены только теги.",
        "_cmd_stoptagall_doc": "[<номер чата>] - Остановить запущенный процесс TagAll в <b>указанном или текущем чате</b>.",
        "_cmd_autotagall_doc": "Включить/выключить работу триггеров TagAll (установленных в .cfg)",
    }

    strings_de = {
        "bot_error": "🚫 <b>Einladung des Inline-Bots in den Chat fehlgeschlagen</b>",
        "_cfg_doc_default_message": "Standardnachricht für Erwähnungen",
        "_cfg_doc_delete": "Nachrichten nach Erwähnung löschen",
        "_cfg_doc_use_bot": "Inline-Bot verwenden, um Leute zu erwähnen",
        "_cfg_doc_timeout": (
            "Zeitintervall, in dem zwischen den Erwähnungen gewartet wird (Zahl, Liste oder Bereich 0.1-1.0)"
        ),
        "_cfg_doc_silent": "Nachricht ohne Abbrechen-Button senden",
        "_cfg_doc_cycle_tagging": (
            "Alle Teilnehmer immer wieder erwähnen, bis du das Skript mit der"
            " Schaltfläche in der Nachricht stoppst"
        ),
        "_cfg_doc_cycle_delay": (
            "Verzögerung zwischen jedem Zyklus der Erwähnung in Sekunden"
        ),
        "_cfg_doc_chunk_size": "Anzahl der Benutzer in einer Nachricht",
        "_cfg_doc_duration": "Dauer der Arbeit (0 = unendlich)",
        "_cfg_doc_exclude_user_ids": "IDs ausgeschlossener Benutzer (durch Komma getrennt)",
        "_cfg_doc_allowed_chat_ids": "IDs der erlaubten Chats für Befehle (durch Komma getrennt, Format 'Index:Chat_ID' oder nur 'Chat_ID')",
        "_cfg_start_trigger": "Trigger(s) zum Starten (wenn im Nachrichtentext vorhanden). Durch Kommas trennen.",
        "_cfg_stop_trigger": "Trigger(s) zum Stoppen (wenn im Nachrichtentext vorhanden). Durch Kommas trennen.",
        "_cfg_doc_allowed_trigger_user_ids": (
            "IDs von Benutzern, die Trigger verwenden dürfen (über Nachrichtentext). "
            "Durch Kommas trennen. Wenn leer, darf jeder Trigger verwenden."
        ),
        "_cfg_doc_enable_watcher": "Trigger-Watcher aktivieren/deaktivieren (Befehl '.autotagall')",
        "gathering": "🧚‍♀️ <b>Erwähne Teilnehmer dieses Chats...</b>",
        "cancel": "🚫 Abbrechen",
        "cancelled": "🧚‍♀️ <b>TagAll abgebrochen!</b>",
        "tagall_not_running": "🚫 <b>TagAll läuft nicht im Chat {chat_id}.</b>",
        "tagall_already_running": "🚫 <b>TagAll läuft bereits im Chat {chat_id}.</b>",
        "no_eligible_participants": "🚫 <b>Keine geeigneten Teilnehmer gefunden.</b>",
        "cmd_redirected": "➡️ <b>Befehl umgeleitet an Chat</b> <code>{target_chat_id}</code>, da dies der einzige erlaubte ist.",
        "cmd_not_allowed_multiple": "🚫 <b>Chat ist nicht auf der Whitelist. Erlaubt:</b> {allowed_chats}.",
        "invalid_chat_index": "🚫 <b>Ungültiger Chat-Index {index}. Erlaubt:</b> {allowed_chats}.",
        "trigger_not_allowed": "🚫 <b>Du darfst keine TagAll-Trigger verwenden.</b>",
        "autotagall_enabled": "✅ <b>TagAll-Trigger aktiviert.</b>",
        "autotagall_disabled": "❌ <b>TagAll-Trigger deaktiviert.</b>",
        "_cmd_tagall_doc": "[<Chat-Index>] [Text] - Alle Chatteilnehmer erwähnen. [Text] wird zusammen mit den Erwähnungen gesendet. Wenn kein Text angegeben ist, werden nur Erwähnungen gesendet.",
        "_cmd_stoptagall_doc": "[<Chat-Index>] - Den laufenden TagAll-Prozess im <b>angegebenen oder aktuellen Chat</b> stoppen.",
        "_cmd_autotagall_doc": "TagAll-Trigger aktivieren/deaktivieren (in .cfg festgelegt)",
    }

    strings_tr = {
        "bot_error": "🚫 <b>Inline botunu sohbete davet edilemedi</b>",
        "_cfg_doc_default_message": "Varsayılan etiket mesajı",
        "_cfg_doc_delete": "Etiketledikten sonra mesajları sil",
        "_cfg_doc_use_bot": "İnsanları etiketlemek için inline botu kullan",
        "_cfg_doc_timeout": "Her etiket mesajı arasında ne kadar bekleneceği (sayı, liste veya aralık 0.1-1.0)",
        "_cfg_doc_silent": "İptal düğmesi olmadan mesaj gönderme",
        "_cfg_doc_cycle_tagging": (
            "Mesajdaki düğmeyi kullanarak betiği durdurana kadar tüm katılımcıları"
            " tekrar tekrar etiketle"
        ),
        "_cfg_doc_cycle_delay": "Etiketleme döngüsü arasındaki gecikme süresi (saniye)",
        "_cfg_doc_chunk_size": "Tek mesajda kaç kullanıcı",
        "_cfg_doc_duration": "Çalışma süresi (0 = sonsuz)",
        "_cfg_doc_exclude_user_ids": "Hariç tutulan kullanıcı ID'leri (virgülle ayrılmış)",
        "_cfg_doc_allowed_chat_ids": "Komutlar için izin verilen sohbet ID'leri (virgülle ayrılmış, 'index:chat_id' veya sadece 'chat_id' formatını kullanın)",
        "_cfg_start_trigger": "Başlatma tetikleyicileri (mesaj metninde mevcutsa). Virgülle ayırın.",
        "_cfg_stop_trigger": "Durdurma tetikleyicileri (mesaj metninde mevcutsa). Virgülle ayırın.",
        "_cfg_doc_allowed_trigger_user_ids": (
            "Tetikleyicileri kullanabilecek kullanıcı ID'leri (mesaj metni aracılığıyla). "
            "Virgülle ayırın. Boşsa, herkes tetikleyicileri kullanabilir."
        ),
        "_cfg_doc_enable_watcher": "Tetikleyici izleyiciyi etkinleştir/devre dışı bırak ('.autotagall' komutu)",
        "gathering": "🧚‍♀️ <b>Bu sohbetteki katılımcıları çağırıyorum...</b>",
        "cancel": "🚫 İptal",
        "cancelled": "🧚‍♀️ <b>TagAll iptal edildi!</b>",
        "tagall_not_running": "🚫 <b>TagAll {chat_id} sohbetinde çalışmıyor.</b>",
        "tagall_already_running": "🚫 <b>TagAll {chat_id} sohbetinde zaten çalışıyor.</b>",
        "no_eligible_participants": "🚫 <b>Uygun katılımcı bulunamadı.</b>",
        "cmd_redirected": "➡️ <b>Komut sohbetine yönlendirildi</b> <code>{target_chat_id}</code>, çünkü tek izin verilen o.",
        "cmd_not_allowed_multiple": "🚫 <b>Sohbet beyaz listede değil. İzin verilenler:</b> {allowed_chats}.",
        "invalid_chat_index": "🚫 <b>Geçersiz sohbet dizini {index}. İzin verilenler:</b> {allowed_chats}.",
        "trigger_not_allowed": "🚫 <b>TagAll tetikleyicilerini kullanmanıza izin verilmiyor.</b>",
        "autotagall_enabled": "✅ <b>TagAll tetikleyicileri etkinleştirildi.</b>",
        "autotagall_disabled": "❌ <b>TagAll tetikleyicileri devre dışı bırakıldı.</b>",
        "_cmd_tagall_doc": "[<sohbet_indeksi>] [metin] - Tüm sohbet katılımcılarını etiketle. [metin] etiketlerle birlikte gönderilecektir. Metin belirtilmezse, sadece etiketler gönderilecektir.",
        "_cmd_stoptagall_doc": "[<sohbet_indeksi>] - <b>Belirtilen veya geçerli sohbetteki</b> çalışan TagAll işlemini durdur.",
        "_cmd_autotagall_doc": "TagAll tetikleyicilerini etkinleştir/devre dışı bırak (.cfg'de ayarlandı)",
    }

    strings_uz = {
        "bot_error": (
            "🚫 <b>Inline botni chatga taklif qilish muvaffaqiyatsiz bo‘ldi</b>"
        ),
        "_cfg_doc_default_message": "Odatiy etiket xabari",
        "_cfg_doc_delete": "Etiketdan so‘ng xabarlarni o‘chirish",
        "_cfg_doc_use_bot": "Odamlarni etiketlash uchun inline botdan foydalanish",
        "_cfg_doc_timeout": "Har bir etiket xabari orasida nechta kutish kerak (raqam, ro'yxat yoki oralik 0.1-1.0)",
        "_cfg_doc_silent": "Bekor tugmasi olmadan xabar jo‘natish",
        "_cfg_doc_cycle_tagging": (
            "Xabar bo‘yicha tugmani ishlatib, skriptni to‘xtatguncha barcha"
            " qatnashuvchilarni qayta-qayta etiketlash"
        ),
        "_cfg_doc_cycle_delay": "Har bir etiketlash tsikli orasida gecikma (soniya)",
        "_cfg_doc_chunk_size": "Bir xabarda nechta foydalanuvchi",
        "_cfg_doc_duration": "Ishlash muddati (0 = cheksiz)",
        "_cfg_doc_exclude_user_ids": "Istisno qilingan foydalanuvchilar ID'lari (vergul bilan ajratilgan)",
        "_cfg_doc_allowed_chat_ids": "Buyruqlar uchun ruxsat etilgan chat ID'lari (vergul bilan ajratilgan, 'index:chat_id' yoki faqat 'chat_id' formatidan foydalaning)",
        "_cfg_start_trigger": "Ishga tushirish uchun trigger(lar) (agar xabar matnida mavjud bo'lsa). Vergul bilan ajrating.",
        "_cfg_stop_trigger": "To'xtatish uchun trigger(lar) (agar xabar matnida mavjud bo'lsa). Vergul bilan ajrating.",
        "_cfg_doc_allowed_trigger_user_ids": (
            "Triggerlarni ishlata oladigan foydalanuvchilar ID'lari (xabar matni orqali). "
            "Vergul bilan ajrating. Agar bo'sh bo'lsa, har kim triggerlarni ishlata oladi."
        ),
        "_cfg_doc_enable_watcher": "Trigger kuzatuvchini yoqish/o'chirish ('.autotagall' buyrug'i)",
        "gathering": "🧚‍♀️ <b>Ushbu chatta qatnashganlarni chaqiraman...</b>",
        "cancel": "🚫 Bekor qilish",
        "cancelled": "🧚‍♀️ <b>TagAll bekor qilindi!</b>",
        "tagall_not_running": "🚫 <b>TagAll {chat_id} chatida ishlamayapti.</b>",
        "tagall_already_running": "🚫 <b>TagAll {chat_id} chatida allaqachon ishlayapti.</b>",
        "no_eligible_participants": "🚫 <b>Muvofiq ishtirokchi topilmadi.</b>",
        "cmd_redirected": "➡️ <b>Buyruq chatga yo'naltirildi</b> <code>{target_chat_id}</code>, chunki u yagona ruxsat etilgan.",
        "cmd_not_allowed_multiple": "🚫 <b>Chat oq ro'yxatda emas. Ruxsat etilganlar:</b> {allowed_chats}.",
        "invalid_chat_index": "🚫 <b>Noto'g'ri chat indeksi {index}. Ruxsat etilganlar:</b> {allowed_chats}.",
        "trigger_not_allowed": "🚫 <b>TagAll triggerlarini ishlatishga sizga ruxsat berilmagan.</b>",
        "autotagall_enabled": "✅ <b>TagAll triggerlari yoqildi.</b>",
        "autotagall_disabled": "❌ <b>TagAll triggerlari o'chirildi.</b>",
        "_cmd_tagall_doc": "[<chat_indeksi>] [matn] - Chatdagi barcha ishtirokchilarni tegish. [matn] teglar bilan birga yuboriladi. Agar matn ko'rsatilmagan bo'lsa, faqat teglar yuboriladi.",
        "_cmd_stoptagall_doc": "[<chat_indeksi>] - <b>Ko'rsatilgan yoki joriy chatda</b> ishlayotgan TagAll jarayonini to'xtatish.",
        "_cmd_autotagall_doc": "TagAll triggerlarini yoqish/o'chirish (.cfg'da o'rnatilgan)",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "default_message",
                "@all",
                lambda: self.strings("_cfg_doc_default_message"),
            ),
            loader.ConfigValue(
                "delete",
                False,
                lambda: self.strings("_cfg_doc_delete"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "use_bot",
                False,
                lambda: self.strings("_cfg_doc_use_bot"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "timeout",
                "0.1", # Изменено на string для поддержки списка/диапазона
                lambda: self.strings("_cfg_doc_timeout"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "silent",
                False,
                lambda: self.strings("_cfg_doc_silent"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "cycle_tagging",
                False,
                lambda: self.strings("_cfg_doc_cycle_tagging"), # Исправлено на _cfg_doc_cycle_tagging
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "cycle_delay",
                0,
                lambda: self.strings("_cfg_doc_cycle_delay"), # Исправлено на _cfg_doc_cycle_delay
                validator=loader.validators.Integer(minimum=0),
            ),
            loader.ConfigValue( # Добавлен chunk_size
                "chunk_size",
                5,
                lambda: self.strings("_cfg_doc_chunk_size"),
                validator=loader.validators.Integer(minimum=1),
            ),
            loader.ConfigValue( # Добавлен duration
                "duration",
                0,
                lambda: self.strings("_cfg_doc_duration"),
                validator=loader.validators.Integer(minimum=0),
            ),
            loader.ConfigValue( # Добавлен exclude_user_ids
                "exclude_user_ids",
                "",
                lambda: self.strings("_cfg_doc_exclude_user_ids"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue( # Добавлен allowed_chat_ids
                "allowed_chat_ids",
                "",
                lambda: self.strings("_cfg_doc_allowed_chat_ids"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue( # Добавлен start_trigger
                "start_trigger",
                "тагалл",
                lambda: self.strings("_cfg_start_trigger"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue( # Добавлен stop_trigger
                "stop_trigger",
                "стоп таг",
                lambda: self.strings("_cfg_stop_trigger"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue( # Добавлен allowed_trigger_user_ids
                "allowed_trigger_user_ids",
                "",
                lambda: self.strings("_cfg_doc_allowed_trigger_user_ids"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue( # Добавлен enable_watcher
                "enable_watcher",
                True,
                lambda: self.strings("_cfg_doc_enable_watcher"),
                validator=loader.validators.Boolean(),
            ),
        )
        self._tagall_events: dict[int, StopEvent] = {}
        self._translation_table = self._build_stylized_char_map() # Таблица для нормализации символов

    async def client_ready(self, client, db):
        self._client = client
        self._db = db

    async def on_unload(self):
        for event in list(self._tagall_events.values()):
            event.stop()
        self._tagall_events.clear()

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
                # Только добавляем в таблицу, если это не прямое отображение на себя
                if chr(stylized_char_code) != base_char_lower:
                    translation_table[stylized_char_code] = base_char_lower

        # Математические буквенно-цифровые символы (латиница)
        # Жирные (Bold)
        add_stylized_block('𝐀', 'A', 26) # Заглавные
        add_stylized_block('𝐚', 'a', 26) # Строчные
        # Курсивные (Italic)
        add_stylized_block('𝐴', 'A', 26)
        add_stylized_block('𝑎', 'a', 26)
        # Жирные курсивные (Bold Italic)
        add_stylized_block('𝑨', 'A', 26)
        add_stylized_block('𝒂', 'a', 26)
        # Моноширинные (Monospace)
        add_stylized_block('𝙰', 'A', 26)
        add_stylized_block('𝚊', 'a', 26)
        
        # Цифры различных стилей
        add_stylized_block('𝟎', '0', 10) # Жирные
        add_stylized_block('𝟘', '0', 10) # С двойным подчеркиванием
        add_stylized_block('𝟢', '0', 10) # Без засечек
        add_stylized_block('𝟬', '0', 10) # Жирные без засечек
        add_stylized_block('𝟶', '0', 10) # Моноширинные

        # Полноширинные ASCII символы (часто используются в азиатских шрифтах)
        add_stylized_block('Ａ', 'A', 26)
        add_stylized_block('ａ', 'a', 26)
        add_stylized_block('０', '0', 10)
        # Полноширинные знаки препинания и символы
        for char_code in range(ord('！'), ord('～') + 1):
            if chr(char_code) != unicodedata.normalize("NFKC", chr(char_code)).lower(): # Только если есть нормализация
                translation_table[char_code] = unicodedata.normalize("NFKC", chr(char_code)).lower()

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
            # Если allowed_trigger_user_ids настроен и отправитель не в списке, игнорируем триггер
            return

        # Нормализуем текст сообщения для сравнения с триггерами
        message_text_normalized = self._normalize_text_for_trigger(message.text)
        
        # Разбираем и нормализуем множественные стоп-триггеры из конфига
        stop_triggers_raw = self.config["stop_trigger"]
        stop_triggers = [self._normalize_text_for_trigger(t) for t in stop_triggers_raw.split(',') if t.strip()]

        # Разбираем и нормализуем множественные старт-триггеры из конфига
        start_triggers_raw = self.config["start_trigger"]
        start_triggers = [self._normalize_text_for_trigger(t) for t in start_triggers_raw.split(',') if t.strip()]

        # Сначала проверяем стоп-триггер
        for trigger in stop_triggers:
            if trigger and trigger in message_text_normalized:
                await self._stop_logic(message, "")
                return

        # Затем старт-триггер
        for trigger in start_triggers:
            if trigger and trigger in message_text_normalized:
                # Если триггер для запуска найден, весь остальной текст игнорируется.
                # Поэтому prefix устанавливается в пустую строку.
                prefix = "" 
                await self._start_logic(message, prefix)
                return

    def _get_allowed_chat_ids_map(self) -> dict[int, int]:
        allowed_ids_raw = self.config["allowed_chat_ids"]
        allowed_chats_map = {}
        # Удаляем все, кроме цифр, запятых и двоеточий
        cleaned = re.sub(r"[^0-9:,]", "", allowed_ids_raw)
        if not cleaned:
            return {}
        
        for item in cleaned.split(','):
            item = item.strip()
            if not item:
                continue
            
            if ':' in item:
                try:
                    index_str, chat_id_str = item.split(':', 1)
                    index = int(index_str)
                    chat_id = int(chat_id_str)
                    allowed_chats_map[index] = chat_id
                except ValueError:
                    logger.warning(f"Неверный формат ID чата в конфигурации 'allowed_chat_ids': '{item}'. Ожидается 'индекс:ID_чата' или 'ID_чата'.")
            else:
                try:
                    # Если формат без индекса, добавляем в список с авто-индексом (для удобства)
                    chat_id = int(item)
                    # Находим следующий доступный индекс
                    next_index = 1
                    while next_index in allowed_chats_map:
                        next_index += 1
                    allowed_chats_map[next_index] = chat_id
                except ValueError:
                    logger.warning(f"Неверный формат ID чата в конфигурации 'allowed_chat_ids': '{item}'. Ожидается 'индекс:ID_чата' или 'ID_чата'.")
        return allowed_chats_map

    def _format_allowed_chats_list(self, allowed_chats_map: dict[int, int]) -> str:
        """Форматирует список разрешенных чатов для вывода."""
        if not allowed_chats_map:
            return "<i>нет</i>"
        return ", ".join([f"<code>{idx}</code>: <code>{chat_id}</code>" for idx, chat_id in sorted(allowed_chats_map.items())])


    async def _resolve_target_chat(self, message: Message, raw_args: str) -> tuple[int | None, str]:
        original_chat_id = utils.get_chat_id(message)
        remaining_args = raw_args.strip()
        allowed_chats_map = self._get_allowed_chat_ids_map()
        allowed_chat_ids_set = set(allowed_chats_map.values())

        target_id = original_chat_id # По умолчанию - текущий чат

        # Проверяем, указан ли индекс чата в аргументах
        chat_index_match = re.match(r"^\s*(\d+)\s*(.*)$", remaining_args)
        if chat_index_match:
            try:
                index = int(chat_index_match.group(1))
                if index in allowed_chats_map:
                    target_id = allowed_chats_map[index]
                    remaining_args = chat_index_match.group(2).strip()
                else:
                    await utils.answer(message, self.strings("invalid_chat_index").format(index=index, allowed_chats=self._format_allowed_chats_list(allowed_chats_map)))
                    return None, ""
            except ValueError:
                pass # Невалидный индекс, продолжаем с обычным парсингом

        # Если allowed_chat_ids настроен
        if allowed_chat_ids_set:
            if target_id not in allowed_chat_ids_set: # Если текущий/выбранный по индексу чат не разрешен
                if len(allowed_chat_ids_set) == 1:
                    # Если только один чат разрешен, перенаправляем туда
                    target_id = next(iter(allowed_chat_ids_set))
                    await utils.answer(message, self.strings("cmd_redirected").format(target_chat_id=target_id))
                else:
                    # Если несколько чатов разрешены, но текущий не в списке, отказываем
                    await utils.answer(message, self.strings("cmd_not_allowed_multiple").format(
                        allowed_chats=self._format_allowed_chats_list(allowed_chats_map)
                    ))
                    return None, ""
        
        return target_id, remaining_args

    async def _start_logic(self, message: Message, prefix: str):
        target_chat_id, message_prefix = await self._resolve_target_chat(message, prefix)
        if target_chat_id is None:
            return

        if target_chat_id in self._tagall_events and self._tagall_events[target_chat_id].state:
            await utils.answer(message, self.strings("tagall_already_running").format(chat_id=target_chat_id))
            return

        if message.out:
            with contextlib.suppress(Exception): await message.delete()

        event = StopEvent(target_chat_id)
        self._tagall_events[target_chat_id] = event

        # Отправляем сообщение "gathering" с кнопкой отмены, если не silent
        cancel_message = None
        if not self.config["silent"]:
            try:
                cancel_message = await self.inline.form(
                    message=message, # Используем оригинальное сообщение для привязки inline-кнопки
                    text=self.strings("gathering"),
                    reply_markup={
                        "text": self.strings("cancel"),
                        "callback": self.cancel,
                        "args": (event,),
                    },
                    chat=target_chat_id # Отправляем сообщение в целевой чат
                )
            except Exception as e:
                logger.error(f"Не удалось отправить inline-сообщение с кнопкой отмены в чат {target_chat_id}: {e}")
                # Если не удалось отправить inline, то запускаем без кнопки
                self.config["silent"] = True # Временно отключаем silent для текущего запуска

        self._client.loop.create_task(self._run_tagall_process(target_chat_id, message_prefix, event, cancel_message))

    async def _stop_logic(self, message: Message, args: str):
        target_chat_id, _ = await self._resolve_target_chat(message, args)
        if target_chat_id is None: return
        
        event = self._tagall_events.get(target_chat_id)
        if event and event.state:
            event.stop()
            if message.out: 
                with contextlib.suppress(Exception): await message.delete()
        else:
            await utils.answer(message, self.strings("tagall_not_running").format(chat_id=target_chat_id))

    async def cancel(self, call: InlineCall, event: StopEvent):
        if event.state:
            event.stop()
            await call.edit(self.strings("cancelled"))
        else:
            await call.answer(self.strings("cancelled"))


    @loader.command(
        groups=True,
        ru_doc=lambda self: self.strings("_cmd_tagall_doc"),
        de_doc=lambda self: self.strings("_cmd_tagall_doc"),
        tr_doc=lambda self: self.strings("_cmd_tagall_doc"),
        uz_doc=lambda self: self.strings("_cmd_tagall_doc"),
    )
    async def tagall(self, message: Message):
        """[<chat_index>] [text] - Tag all users in chat"""
        await self._start_logic(message, utils.get_args_raw(message))

    @loader.command(
        ru_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
        de_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
        tr_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
        uz_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
    )
    async def stoptagall(self, message: Message):
        """[<chat_index>] - Stop the running TagAll process in the <b>specified or current chat</b>."""
        await self._stop_logic(message, utils.get_args_raw(message))

    @loader.command(
        ru_doc=lambda self: self.strings("_cmd_autotagall_doc"),
        de_doc=lambda self: self.strings("_cmd_autotagall_doc"),
        tr_doc=lambda self: self.strings("_cmd_autotagall_doc"),
        uz_doc=lambda self: self.strings("_cmd_autotagall_doc"),
    )
    async def autotagall(self, message: Message):
        """Включить/выключить работу триггеров TagAll (установленных в .cfg)"""
        self.config["enable_watcher"] = not self.config["enable_watcher"]
        if self.config["enable_watcher"]:
            await utils.answer(message, self.strings("autotagall_enabled"))
        else:
            await utils.answer(message, self.strings("autotagall_disabled"))
        if message.out:
            with contextlib.suppress(Exception): await message.delete()


    def _get_random_timeout(self, event: StopEvent) -> float:
        timeout_str = str(self.config["timeout"])
        try:
            cleaned = re.sub(r"[^0-9.,-]", "", timeout_str)
            if "-" in cleaned:
                parts = cleaned.split("-")
                min_val = max(0.0, float(parts[0]))
                max_val = max(0.0, float(parts[1]))
                if min_val > max_val: min_val, max_val = max_val, min_val
                return random.uniform(min_val, max_val)
            if "," in cleaned:
                vals = [float(x) for x in cleaned.split(",") if x and float(x) >= 0.0]
                # Избегаем повторения того же таймаута, если есть несколько значений
                if len(vals) > 1 and event.last_timeout is not None and event.last_timeout in vals:
                    available_values = [v for v in vals if v != event.last_timeout]
                    if available_values:
                        new_timeout = random.choice(available_values)
                    else: # Если все значения совпадают с last_timeout, повтор допустим
                        new_timeout = random.choice(vals)
                else:
                    new_timeout = random.choice(vals)
                event.last_timeout = new_timeout
                return new_timeout
            single_val = float(cleaned)
            event.last_timeout = max(0.0, single_val)
            return event.last_timeout
        except (ValueError, TypeError):
            logger.warning(f"Не удалось разобрать таймаут '{timeout_str}'. Используется значение по умолчанию 0.1.")
            event.last_timeout = 0.1
            return 0.1

    async def _run_tagall_process(self, chat_id: int, message_prefix: str, event: StopEvent, cancel_message: Message | None):
        """Внутренняя функция для обработки основной логики TagAll."""
        deleted_message_ids_hikkatl = []
        deleted_message_ids_bot_client = []

        is_bot_sender = self.config["use_bot"]

        try:
            chat_entity = await self._client.get_input_entity(chat_id)
        except Exception as e:
            logger.error(f"Не удалось получить сущность чата для ID {chat_id}: {e}")
            await self._client.send_message(chat_id, f"🚫 <b>Не удалось найти чат с ID:</b> <code>{chat_id}</code>")
            event.stop()
            if chat_id in self._tagall_events:
                del self._tagall_events[chat_id]
            if cancel_message and cancel_message.is_reply:
                with contextlib.suppress(Exception):
                    await cancel_message.edit(self.strings("cancelled"))
            return

        excluded_user_ids = set()
        exclude_ids_raw = self.config["exclude_user_ids"]
        for uid_str in exclude_ids_raw.split(','):
            uid_str = uid_str.strip()
            if uid_str:
                try:
                    excluded_user_ids.add(int(uid_str))
                except ValueError:
                    logger.warning(f"Неверный ID пользователя в конфигурации 'exclude_user_ids': '{uid_str}'. Должен быть целым числом.")

        if is_bot_sender:
            try:
                if not hasattr(self, 'inline') or not hasattr(self.inline, 'bot_client') or not getattr(self.inline, 'bot_client', None):
                    raise RuntimeError("Инлайн-бот не настроен или недоступен.")

                bot_entity = await self._client.get_input_entity(self.inline.bot_username)
                with contextlib.suppress(Exception):
                    await self._client(InviteToChannelRequest(chat_entity, [bot_entity]))
            except Exception as e:
                logger.error(f"Не удалось получить сущность бота или пригласить бота: {e}")
                await self._client.send_message(chat_id, self.strings("bot_error"))
                event.stop()
                if chat_id in self._tagall_events:
                    del self._tagall_events[chat_id]
                if cancel_message and cancel_message.is_reply:
                    with contextlib.suppress(Exception):
                        await cancel_message.edit(self.strings("cancelled"))
                return

        # Получаем список участников ОДИН РАЗ перед началом циклов
        participants = []
        owner_id = self._client.tg_id
        async for user in self._client.iter_participants(chat_id):
            if not user.bot and not user.deleted and user.id != owner_id and user.id not in excluded_user_ids:
                participants.append(user)

        if not participants:
            logger.warning(f"В чате {chat_id} не найдено подходящих участников для TagAll, останавливаем.")
            await self._client.send_message(chat_id, self.strings("no_eligible_participants"))
            event.stop()
            if chat_id in self._tagall_events:
                del self._tagall_events[chat_id]
            if cancel_message and cancel_message.is_reply:
                with contextlib.suppress(Exception):
                    await cancel_message.edit(self.strings("cancelled"))
            return

        random.shuffle(participants) # Перемешиваем список ОДИН РАЗ

        start_time = time.time()

        try:
            # Основной цикл работы: будет продолжаться до остановки или достижения лимита времени
            while event.state: 
                # Проверяем общую длительность работы
                if self.config["duration"] > 0 and (time.time() - start_time) > self.config["duration"]:
                    logger.info(f"TagAll достиг лимита длительности в чате {chat_id}. Остановка.")
                    event.stop()
                    break # Выход из основного цикла

                # Проходим по всем участникам в текущем списке (разбитым на чанки)
                for chunk in utils.chunks(participants, self.config["chunk_size"]):
                    if not event.state: # Проверяем, не был ли процесс остановлен во время обработки чанка
                        break # Выход из цикла по чанкам

                    if self.config["duration"] > 0 and (time.time() - start_time) > self.config["duration"]:
                        logger.info(f"TagAll достиг лимита длительности во время обработки чанка в чате {chat_id}. Остановка.")
                        event.stop()
                        break # Выход из цикла по чанкам

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

                    # message_prefix уже пустой, если сработал триггер, так что здесь все ок
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
                            if self.config["delete"]:
                                deleted_message_ids_bot_client.append(m.id)
                        else:
                            logger.error("Клиент инлайн-бота недоступен или не настроен, переключаемся на юзербота для отправки сообщений.")
                            m = await self._client.send_message(
                                chat_entity,
                                full_message_text,
                                parse_mode="HTML",
                            )
                            if self.config["delete"]:
                                deleted_message_ids_hikkatl.append(m.id)
                    else:
                        m = await self._client.send_message(
                            chat_entity,
                            full_message_text,
                            parse_mode="HTML",
                        )
                        if self.config["delete"]:
                            deleted_message_ids_hikkatl.append(m.id)

                    await asyncio.sleep(self._get_random_timeout(event)) # Задержка между отправкой чанков

                if not event.state: # Если процесс остановлен внутри цикла по чанкам, выходим и из основного цикла
                    break

                # После завершения одного полного прохода по всем участникам:
                if not self.config["cycle_tagging"]:
                    logger.info(f"TagAll завершил один полный проход без цикличного тегирования в чате {chat_id}. Остановка.")
                    break # Если циклическое тегирование отключено, завершаем работу

                # Если циклическое тегирование включено и процесс не остановлен, ждем задержку перед следующим циклом
                if self.config["cycle_tagging"] and event.state:
                    logger.debug(f"TagAll в чате {chat_id} ждет задержку ({self.config['cycle_delay']}с) перед следующим циклом.")
                    await asyncio.sleep(self.config["cycle_delay"])

        finally:
            if self.config["delete"]:
                with contextlib.suppress(Exception):
                    if deleted_message_ids_hikkatl:
                        for chunk_ids in utils.chunks(deleted_message_ids_hikkatl, 100):
                            await self._client.delete_messages(chat_entity, chunk_ids)

                    if deleted_message_ids_bot_client:
                        if hasattr(self, 'inline') and hasattr(self.inline, 'bot_client') and self.inline.bot_client:
                            for chunk_ids in utils.chunks(deleted_message_ids_bot_client, 100):
                                await self.inline.bot_client.delete_messages(chat_entity, chunk_ids)
                        else:
                            logger.warning("Клиент инлайн-бота недоступен для удаления своих сообщений.")

            if event.state:
                logger.info(f"Процесс TagAll завершен естественным образом в чате {chat_id}.")
                if cancel_message:
                    with contextlib.suppress(Exception):
                        await cancel_message.delete()

            if chat_id in self._tagall_events:
                del self._tagall_events[chat_id]
