# meta developer: @NKDebra
# meta name: TagAll
# meta version: 2.5.2 

import asyncio
import contextlib
import logging
import random
import time
import re

# Используем telethon, как в предоставленном файле
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import Message

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
        self.last_timeout: float | None = None

    def stop(self):
        self.state = False


@loader.tds
class TagAllMod(loader.Module):
    """Отмечает всех участников чата через команды или триггеры в тексте.
    Включает/выключает работу триггеров командой .autotagall."""

    strings = {
        "name": "TagAll",
        "bot_error": "🚫 <b>Не получилось пригласить бота в чат или тип чата не поддерживается для приглашения бота.</b>",
        "_cfg_doc_delete": "Удалять сообщения после тега",
        "_cfg_doc_use_bot": "Использовать бота для тегов",
        "_cfg_doc_timeout": "Время между сообщениями (число, список или диапазон 0.1-1.0)",
        "_cfg_doc_silent": "Не отправлять сообщение с кнопкой отмены",
        "_cfg_doc_cycle_tagging": "Цикличный тег (пока не остановите)",
        "_cfg_doc_cycle_delay": "Задержка между циклами (сек)",
        "_cfg_doc_chunk_size": "Сколько пользователей в одном сообщении",
        "_cfg_doc_duration": "Длительность работы (0 = бесконечно)",
        "_cfg_doc_exclude_user_ids": "ID пользователей-исключений",
        "_cfg_doc_allowed_chat_ids": "ID разрешенных чатов для выполнения команд",
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
        "cmd_redirected": "➡️ <b>Команда перенаправлена в чат</b> <code>{target_chat_id}</code>, так как он единственный разрешенный.", # Эта строка останется для возможных будущих запросов, но не будет использоваться.
        "cmd_not_allowed_multiple": "🚫 <b>Чат не в белом списке. Разрешенные:</b> {allowed_chats}.",
        "trigger_not_allowed": "🚫 <b>Вам не разрешено использовать триггеры для TagAll.</b>",
        "autotagall_enabled": "✅ <b>Работа триггеров TagAll включена.</b>",
        "autotagall_disabled": "❌ <b>Работа триггеров TagAll выключена.</b>",
        "_cmd_tagall_doc": "[<номер чата>] [текст] - Отметить всех участников чата. [текст] будет отправлен вместе с тегами. Если текст не указан, будут отправлены только теги.",
        "_cmd_stoptagall_doc": "[<номер чата>] - Остановить запущенный процесс TagAll в <b>указанном или текущем чате</b>.",
        "_cmd_autotagall_doc": "Включить/выключить работу триггеров TagAll (установленных в .cfg)",
        "cmd_not_allowed": "🚫 <b>Эта команда не может быть использована в текущем чате, и нет единственного разрешенного чата для перенаправления.</b>",
        "cmd_not_allowed_current": "🚫 <b>Эта команда не может быть использована в текущем чате.</b>",
        "cmd_redirected_indexed": "➡️ <b>Команда перенаправлена в чат</b> <code>{target_chat_id}</code> (индекс <code>{index}</code>).",
        "invalid_chat_index": "🚫 <b>Неверный индекс чата</b> <code>{index}</code>. Разрешенные чаты: {allowed_chats}.",
        "tagall_stopped_silently": "✅ <b>TagAll в чате {chat_id} остановлен.</b>", # Сохраняем для возможного использования, но не выводим
    }

    strings_de = { 
        "bot_error": "🚫 <b>Einladung des Inline-bots in den Chat fehlgeschlagen oder der Chat-Typ wird für Bot-Einladungen nicht unterstützt.</b>",
        "_cfg_doc_delete": "Nachrichten nach Erwähnung löschen",
        "_cfg_doc_use_bot": "Inline-Bot verwenden, um Leute zu erwähnen",
        "_cfg_doc_timeout": (
            "Zeitintervall, in dem zwischen den Erwähnungen gewartet wird. Kann ein"
            " einzelner Wert (z. B. '0.1'), mehrere durch Komma getrennte Werte (z. B."
            " '0.1, 0.5, 1.0') oder ein Bereich (z. B. '0.1-1.0') sein."
        ),
        "_cfg_doc_silent": "Nachricht ohne Abbrechen-Button senden",
        "_cfg_doc_cycle_tagging": (
            "Alle Teilnehmer immer wieder erwähnen, bis du das Skript mit der"
            " Schaltfläche in der Nachricht stoppst"
        ),
        "_cfg_doc_cycle_delay": (
            "Verzögerung zwischen jedem Zyklus der Erwähnung in Sekunden"
        ),
        "_cfg_doc_chunk_size": "Wie viele Benutzer in einer Nachricht erwähnt werden sollen",
        "_cfg_doc_duration": "Wie lange (in Sekunden) der TagAll-Prozess laufen soll. Auf 0 für unbegrenzte Zeit einstellen.",
        "tagall_not_running": "🚫 <b>TagAll läuft derzeit nicht in Chat {chat_id}.</b>",
        "tagall_already_running": "🚫 <b>TagAll läuft bereits in Chat {chat_id}. Verwenden Sie <code>.stoptagall</code>, um es zu stoppen.</b>",
        "_cfg_doc_exclude_user_ids": "Benutzer-ID(s), die nicht erwähnt werden sollen. Kommagetrennt eingeben. Zum Beispiel: <code>123456789, 987654321</code>",
        "_cfg_doc_allowed_chat_ids": "Chat-ID(s), in denen die TagAll-Modulbefehle verwendet werden dürfen. Durch Kommas getrennt eingeben. Wenn nur eine ID angegeben ist, werden Befehle, die in anderen Chats ausgeführt werden, automatisch in diesen Chat umgeleitet. Wenn leer, sind Befehle in allen Chats erlaubt.",
        "_cmd_tagall_doc": "[<Chat-Nummer>] [Text] - Alle Chatteilnehmer erwähnen. [Text] wird zusammen mit den Erwähnungen gesendet. Wenn kein Text angegeben ist, werden nur die Erwähnungen gesendet.",
        "_cmd_stoptagall_doc": "[<Chat-Nummer>] - Den laufenden TagAll-Prozess im <b>angegebenen oder aktuellen Chat</b> stoppen.",
        "no_eligible_participants": "🚫 <b>In diesem Chat gibt es keine geeigneten Teilnehmer zum Taggen.</b>",
        "cmd_redirected": "➡️ <b>Befehl wurde in Chat</b> <code>{target_chat_id}</code> umgeleitet, da dies der einzige erlaubte ist.",
        "cmd_not_allowed": "🚫 <b>Dieser Befehl darf im aktuellen Chat nicht verwendet werden, und es gibt keinen einzigen erlaubten Chat zur Umleitung.</b>",
        "cmd_not_allowed_current": "🚫 <b>Dieser Befehl darf im aktuellen Chat nicht verwendet werden.</b>",
        "cmd_redirected_indexed": "➡️ <b>Befehl wurde in Chat</b> <code>{target_chat_id}</code> (Index <code>{index}</code>) umgeleitet.",
        "invalid_chat_index": "🚫 <b>Ungültiger Chat-Index</b> <code>{index}</code>. Erlaubte Chats: {allowed_chats}.",
        "cmd_not_allowed_multiple": "🚫 <b>Dieser Befehl darf im aktuellen Chat nicht verwendet werden. Geben Sie einen Chat-Index an oder verwenden Sie ihn in einem der erlaubten Chats:</b> {allowed_chats}.",
        "trigger_not_allowed": "🚫 <b>Ihnen ist es nicht gestattet, Trigger für TagAll zu verwenden.</b>",
        "autotagall_enabled": "✅ <b>Die TagAll-Triggerfunktion ist aktiviert.</b>",
        "autotagall_disabled": "❌ <b>Die TagAll-Triggerfunktion ist deaktiviert.</b>",
        "_cmd_autotagall_doc": "TagAll-Triggerfunktion (in .cfg eingestellt) aktivieren/deaktivieren",
        "tagall_stopped_silently": "✅ <b>TagAll in Chat {chat_id} gestoppt.</b>",
    }

    strings_tr = { 
        "bot_error": "🚫 <b>Inline botunu sohbete davet edilemedi veya sohbet türü bot davetleri için desteklenmiyor.</b>",
        "_cfg_doc_delete": "Etiketledikten sonra mesajları sil",
        "_cfg_doc_use_bot": "İnsanları etiketlemek için inline botu kullan",
        "_cfg_doc_timeout": (
            "Her etiket mesajı arasında ne kadar bekleneceği. Tek bir değer (örneğin,"
            " '0.1'), virgülle ayrılmış birden çok değer (örneğin, '0.1, 0.5, 1.0')"
            " veya bir aralık (örneğin, '0.1-1.0') belirtebilirsiniz."
        ),
        "_cfg_doc_silent": "İptal düğmesi olmadan mesaj gönderme",
        "_cfg_doc_cycle_tagging": (
            "Mesajdaki düğmeyi kullanarak betiği durdurana kadar tüm katılımcıları"
            " tekrar tekrar etiketle"
        ),
        "_cfg_doc_cycle_delay": "Etiketleme döngüsü arasındaki gecikme süresi (saniye)",
        "_cfg_doc_chunk_size": "Bir mesajda kaç kullanıcı etiketlenecek",
        "_cfg_doc_duration": "TagAll sürecinin ne kadar süre (saniye) çalışması gerektiği. Sınırsız süre için 0 olarak ayarlayın.",
        "_cfg_doc_exclude_user_ids": "Etiketlenmeyecek kullanıcı kimliği(leri). Virgülle ayırın. Örneğin: <code>123456789, 987654321</code>",
        "_cfg_doc_allowed_chat_ids": "TagAll modül komutlarının kullanılabileceği sohbet kimliği(leri). Virgülle ayırın. Yalnızca bir kimlik belirtilirse, diğer sohbetlerde başlatılan komutlar otomatik olarak bu sohbete yönlendirilecektir. Boş bırakılırsa, komutlara tüm sohbetlerde izin verilir.",
        "_cmd_tagall_doc": "[<Sohbet Numarası>] [metin] - Sohbet katılımcılarını etiketle. [metin] etiketlerle birlikte gönderilecektir. Metin belirtilmezse, sadece etiketler gönderilecektir.",
        "_cmd_stoptagall_doc": "[<Sohbet Numarası>] - Çalışan TagAll sürecini <b>belirtilen veya mevcut sohbette</b> durdur.",
        "tagall_not_running": "🚫 <b>TagAll şu anda {chat_id} sohbetinde çalışmıyor.</b>",
        "tagall_already_running": "🚫 <b>TagAll zaten {chat_id} sohbetinde çalışıyor. Durdurmak için <code>.stoptagall</code> komutunu kullanın.</b>",
        "no_eligible_participants": "🚫 <b>Bu sohbette etiketlenecek uygun katılımcı yok.</b>",
        "cmd_redirected": "➡️ <b>Komut, izin verilen tek sohbet olduğu için</b> <code>{target_chat_id}</code> sohbetine yönlendirildi.",
        "cmd_not_allowed": "🚫 <b>Bu komut mevcut sohbette kullanılamaz ve yönlendirmek için tek bir izin verilen sohbet yok.</b>",
        "cmd_not_allowed_current": "🚫 <b>Bu komut mevcut sohbette kullanılamaz.</b>",
        "cmd_redirected_indexed": "➡️ <b>Komut,</b> <code>{target_chat_id}</code> (dizin <code>{index}</code>) sohbetine yönlendirildi.",
        "invalid_chat_index": "🚫 <b>Geçersiz sohbet dizini</b> <code>{index}</code>. İzin verilen sohbetler: {allowed_chats}.",
        "cmd_not_allowed_multiple": "🚫 <b>Bu komut mevcut sohbette kullanılamaz. Bir sohbet dizini belirtin veya izin verilen sohbetlerden birinde kullanın:</b> {allowed_chats}.",
        "trigger_not_allowed": "🚫 <b>Size TagAll için tetikleyici kullanma izni verilmiyor.</b>",
        "autotagall_enabled": "✅ <b>TagAll tetikleyicileri etkinleştirildi.</b>",
        "autotagall_disabled": "❌ <b>TagAll tetikleyicileri devre dışı bırakıldı.</b>",
        "_cmd_autotagall_doc": "TagAll tetikleyicilerinin (yapılandırmada ayarlanmış) çalışmasını aç/kapat",
        "tagall_stopped_silently": "✅ <b>TagAll {chat_id} sohbetinde durduruldu.</b>",
    }

    strings_uz = { 
        "bot_error": (
            "🚫 <b>Inline botni chatga taklif qilish muvaffaqiyatsiz bo‘ldi yoki chat turi bot takliflari uchun qo‘llab-quvvatlanmaydi.</b>"
        ),
        "_cfg_doc_delete": "Etiketdan so‘ng xabarlarni o‘chirish",
        "_cfg_doc_use_bot": "Odamlarni etiketlash uchun inline botdan foydalanish",
        "_cfg_doc_timeout": (
            "Har bir etiket xabari orasida nechta kutish kerak. Bitta qiymat (masalan,"
            " '0.1'), vergul bilan ajratilgan bir nechta qiymatlar (masalan,"
            " '0.1, 0.5, 1.0') yoki diapazon (masalan, '0.1-1.0') ko'rsatishingiz mumkin."
        ),
        "_cfg_doc_silent": "Bekor tugmasi olmadan xabar jo‘natish",
        "_cfg_doc_cycle_tagging": (
            "Xabar bo‘yicha tugmani ishlatib, skriptni to‘xtatguncha barcha"
            " qatnashuvchilarni qayta-qayta etiketlash"
        ),
        "_cfg_doc_cycle_delay": "Har bir etiketlash tsikli orasida gecikma (soniya)",
        "_cfg_doc_chunk_size": "Bir xabarda nechta foydalanuvchi etiketlanadi",
        "_cfg_doc_duration": "TagAll jarayoni qancha vaqt (soniya) ishlashi kerak. Cheksiz vaqt uchun 0 ga o'rnating.",
        "_cfg_doc_exclude_user_ids": "Etiketlanmaydigan foydalanuvchi ID(lar)i. Vergul bilan ajrating. Misol uchun: <code>123456789, 987654321</code>",
        "_cfg_doc_allowed_chat_ids": "TagAll modul buyruqlaridan foydalanishga ruxsat berilgan chat ID(lar)i. Vergul bilan ajrating. Agar faqat bitta ID ko'rsatilgan bo'lsa, boshqa chatlarda ishga tushirilgan buyruqlar avtomatik ravishda ushbu chatga yo'naltiriladi. Bo'sh bo'lsa, buyruqlarga barcha chatlarda ruxsat beriladi.",
        "_cmd_tagall_doc": "[<Chat raqami>] [matn] - Chat qatnashuvchilarini tegish. [matn] teglar bilan birga yuboriladi. Agar matn ko'rsatilgan bo'lsa, teglar bilan birga yuboriladi. Matn ko'rsatilmagan bo'lsa, faqat teglar yuboriladi.",
        "_cmd_stoptagall_doc": "[<Chat raqami>] - Ishlayotgan TagAll jarayonini <b>ko'rsatilgan yoki joriy chatda</b> to'xtatish.",
        "tagall_not_running": "🚫 <b>TagAll hozirda {chat_id} chatida ishlamayapti.</b>",
        "tagall_already_running": "🚫 <b>TagAll {chat_id} chatida allaqachon ishlamoqda. Uni to'xtatish uchun <code>.stoptagall</code> dan foydalaning.</b>",
        "no_eligible_participants": "🚫 <b>Bu chatda tegish uchun mos ishtirokchilar topilmadi.</b>",
        "cmd_redirected": "➡️ <b>Buyruq, ruxsat berilgan yagona chat bo'lgani uchun</b> <code>{target_chat_id}</code> chatiga yo'naltirildi.",
        "cmd_not_allowed": "🚫 <b>Ushbu buyruq joriy chatda ishlatilmaydi va yo'naltirish uchun yagona ruxsat berilgan chat yo'q.</b>",
        "cmd_not_allowed_current": "🚫 <b>Ushbu buyruq joriy chatda ishlatilmaydi.</b>",
        "cmd_redirected_indexed": "➡️ <b>Buyruq,</b> <code>{target_chat_id}</code> (indeks <code>{index}</code>) chatiga yo'naltirildi.",
        "invalid_chat_index": "🚫 <b>Noto'g'ri chat indeksi</b> <code>{index}</code>. Ruxsat berilgan chatlar: {allowed_chats}.",
        "cmd_not_allowed_multiple": "🚫 <b>Ushbu buyruq joriy chatda ishlatilmaydi. Chat indeksini ko'rsating yoki ruxsat berilgan chatlardan birida foydalaning:</b> {allowed_chats}.",
        "trigger_not_allowed": "🚫 <b>Sizga TagAll uchun triggerlardan foydalanishga ruxsat berilmagan.</b>",
        "autotagall_enabled": "✅ <b>TagAll triggerlari yoqildi.</b>",
        "autotagall_disabled": "❌ <b>TagAll triggerlari o‘chirildi.</b>",
        "_cmd_autotagall_doc": "TagAll triggerlarining (konfiguratsiyada o'rnatilgan) ishlashini yoqish/o'chirish",
        "tagall_stopped_silently": "✅ <b>TagAll {chat_id} chatida to'xtatildi.</b>",
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
            # Восстанавливаем конфигурации триггеров
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

    async def client_ready(self, client, db):
        self._client = client
        self._db = db

    async def on_unload(self):
        for event in list(self._tagall_events.values()):
            event.stop()
        self._tagall_events.clear()
        logger.info("Все процессы TagAll остановлены из-за выгрузки модуля.")

    @loader.watcher()
    async def watcher(self, message: Message):
        if not self.config["enable_watcher"]: 
            return

        if not isinstance(message, Message) or not message.text:
            return

        # Проверяем allowed_chat_ids для триггеров
        allowed_chats_map = self._get_allowed_chat_ids_map()
        if allowed_chats_map: # Если список разрешенных чатов не пуст
            allowed_chat_ids_set = set(allowed_chats_map.values())
            if message.chat_id not in allowed_chat_ids_set:
                # Чат не в белом списке для триггеров, игнорируем
                return

        # Проверяем, разрешено ли отправителю использовать триггеры
        allowed_trigger_ids_raw = self.config["allowed_trigger_user_ids"]
        allowed_trigger_ids = {int(x.strip()) for x in allowed_trigger_ids_raw.split(",") if x.strip().isdigit()}

        # Если allowed_trigger_user_ids настроен и отправитель не в списке, игнорируем триггер
        if allowed_trigger_ids and message.sender_id not in allowed_trigger_ids:
            # Не отправляем сообщение "trigger_not_allowed", чтобы триггеры были бесшумными
            return

        message_text_lower = message.text.lower()
        
        # Разбираем множественные стоп-триггеры
        stop_triggers_raw = self.config["stop_trigger"]
        stop_triggers = [t.strip().lower() for t in stop_triggers_raw.split(',') if t.strip()]

        # Разбираем множественные старт-триггеры
        start_triggers_raw = self.config["start_trigger"]
        start_triggers = [t.strip().lower() for t in start_triggers_raw.split(',') if t.strip()]

        # Сначала проверяем стоп-триггер
        for trigger in stop_triggers:
            if trigger and trigger in message_text_lower:
                await self._stop_logic(message, "", send_confirmation=False) # Убрано подтверждение
                return

        # Затем старт-триггер
        for trigger in start_triggers:
            if trigger and trigger in message_text_lower:
                prefix = "" 
                await self._start_logic(message, prefix)
                return 

    def _get_allowed_chat_ids_map(self) -> dict[int, int]:
        allowed_ids_raw = self.config["allowed_chat_ids"]
        allowed_chats_map = {}
        # Оставляем цифры, запятые и минус для поддержки отрицательных ID чатов
        cleaned = re.sub(r"[^0-9,-]", "", allowed_ids_raw) 
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


    async def _resolve_target_chat(self, message: Message, raw_args: str) -> tuple[int | None, str | None]:
        original_chat_id = message.chat_id
        remaining_args = raw_args.strip()
        allowed_chats_map = self._get_allowed_chat_ids_map()
        allowed_chat_ids_set = set(allowed_chats_map.values())

        chat_index_match = re.match(r"^\s*(\d+)\s*(.*)$", remaining_args)
        if chat_index_match:
            try:
                index = int(chat_index_match.group(1))
                if index in allowed_chats_map:
                    target_id = allowed_chats_map[index]
                    if target_id != original_chat_id: 
                        await utils.answer(message, self.strings("cmd_redirected_indexed").format(target_chat_id=target_id, index=index))
                    return target_id, chat_index_match.group(2).strip()
                else:
                    await utils.answer(message, self.strings("invalid_chat_index").format(index=index, allowed_chats=self._format_allowed_chats_list(allowed_chats_map)))
                    return None, None
            except ValueError:
                pass 

        if not allowed_chat_ids_set: 
            return original_chat_id, remaining_args
        
        if original_chat_id in allowed_chat_ids_set:
            return original_chat_id, remaining_args
        
        if len(allowed_chat_ids_set) == 1:
            target_id = next(iter(allowed_chat_ids_set))
            # Удаляем сообщение о перенаправлении, так как оно не требуется пользователем
            # if target_id != original_chat_id: 
            #     await utils.answer(message, self.strings("cmd_redirected").format(target_chat_id=target_id))
            return target_id, remaining_args

        await utils.answer(message, self.strings("cmd_not_allowed_multiple").format(
            allowed_chats=self._format_allowed_chats_list(allowed_chats_map)
        ))
        return None, None

    async def _start_logic(self, message: Message, prefix: str):
        target_chat_id, message_prefix = await self._resolve_target_chat(message, prefix)
        if target_chat_id is None:
            return

        if target_chat_id in self._tagall_events and self._tagall_events[target_chat_id].state:
            await utils.answer(message, self.strings("tagall_already_running").format(chat_id=target_chat_id))
            # Сообщение не удаляется, так как это является запросом пользователя
            return

        # Исходное сообщение-триггер/команда больше не удаляется
        # if message.out:
        #     with contextlib.suppress(Exception): await message.delete()

        event = StopEvent(target_chat_id)
        self._tagall_events[target_chat_id] = event
        self._client.loop.create_task(self._run_tagall_process(target_chat_id, message_prefix, event))

    async def _stop_logic(self, message: Message, args: str, send_confirmation: bool = True):
        target_chat_id, _ = await self._resolve_target_chat(message, args)
        if target_chat_id is None:
            # Сообщение не удаляется, так как это является запросом пользователя
            # if message.out:
            #     with contextlib.suppress(Exception): await message.delete()
            return
        
        event = self._tagall_events.get(target_chat_id)
        if event and event.state:
            event.stop()
            logger.info(f"Команда stoptagall: процесс TagAll для чата {target_chat_id} был остановлен.")
            if send_confirmation: # Отправлять подтверждение только если send_confirmation=True
                await utils.answer(message, self.strings("tagall_stopped_silently").format(chat_id=target_chat_id))
            # Исходное сообщение-триггер/команда больше не удаляется
            # if message.out:
            #     with contextlib.suppress(Exception): await message.delete()
        else:
            if send_confirmation: # Отправлять сообщение, только если send_confirmation=True
                await utils.answer(message, self.strings("tagall_not_running").format(chat_id=target_chat_id))
            # Сообщение не удаляется, так как это является запросом пользователя
            # if message.out:
            #     with contextlib.suppress(Exception): await message.delete()

    @loader.command(
        groups=True,
        ru_doc=lambda self: self.strings("_cmd_tagall_doc"),
        de_doc=lambda self: self.strings("_cmd_tagall_doc"),
        tr_doc=lambda self: self.strings("_cmd_tagall_doc"),
        uz_doc=lambda self: self.strings("_cmd_tagall_doc"),
    )
    async def tagall(self, message: Message):
        """[<номер чата>] [текст] - Отметить всех участников чата. [текст] будет отправлен вместе с тегами. Если текст не указан, будут отправлены только теги."""
        await self._start_logic(message, utils.get_args_raw(message))

    @loader.command(
        ru_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
        de_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
        tr_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
        uz_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
    )
    async def stoptagall(self, message: Message):
        """[<номер чата>] - Остановить запущенный процесс TagAll в <b>указанном или текущем чате</b>."""
        await self._stop_logic(message, utils.get_args_raw(message), send_confirmation=False) # Теперь send_confirmation=False по умолчанию для команды

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
        # Исходное сообщение-команда больше не удаляется
        # if message.out:
        #     with contextlib.suppress(Exception): await message.delete()


    def _get_random_timeout(self, event: StopEvent) -> float:
        timeout_str = str(self.config["timeout"])
        default_timeout = 0.1
        current_timeout = default_timeout

        try:
            cleaned_timeout_str = re.sub(r"[^0-9.,-]", "", timeout_str).strip()

            if not cleaned_timeout_str:
                logger.warning(f"Пустая строка таймаута. Используется значение по умолчанию {default_timeout}.")
                event.last_timeout = default_timeout
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
                            logger.warning(f"Неверное значение в списке таймаутов: '{part}'. Игнорируется.")

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
                    logger.warning(f"Не удалось разобрать значения таймаута из '{timeout_str}'. Используется значение по умолчанию {default_timeout}.")

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
                    logger.warning(f"Не удалось разобрать диапазон таймаута из '{timeout_str}'. Используется значение по умолчанию {default_timeout}.")

            else:
                try:
                    current_timeout = max(0.0, float(cleaned_timeout_str))
                except ValueError:
                    logger.warning(f"Не удалось разобрать одиночное значение таймаута из '{timeout_str}'. Используется значение по умолчанию {default_timeout}.")

        except Exception as e:
            logger.error(f"Неожиданная ошибка при разборе таймаута '{timeout_str}': {e}. Используется значение по умолчанию {default_timeout}.")

        event.last_timeout = current_timeout
        return current_timeout

    async def _run_tagall_process(self, chat_id: int, message_prefix: str, event: StopEvent):
        """Внутренняя функция для обработки основной логики TagAll."""
        deleted_message_ids_telethon = []
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
                if not hasattr(self, 'inline') or not hasattr(self.inline, 'bot_username') or not getattr(self.inline, 'bot_client', None):
                    raise RuntimeError("Инлайн-бот не настроен или недоступен в текущей конфигурации.")

                bot_entity = await self._client.get_input_entity(self.inline.bot_username)
                with contextlib.suppress(Exception):  
                    await self._client(InviteToChannelRequest(chat_entity, [bot_entity]))
            except Exception as e:
                logger.error(f"Не удалось получить сущность бота или пригласить бота: {e}")
                await self._client.send_message(chat_id, self.strings("bot_error"))
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
            logger.warning(f"В чате {chat_id} не найдено подходящих участников для TagAll, останавливаем.")
            await self._client.send_message(chat_id, self.strings("no_eligible_participants"))
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

                if self.config["duration"] > 0 and (time.time() - start_time) > self.config["duration"]:
                    logger.info(f"TagAll process for chat {chat_id} finished due to duration limit.")
                    event.stop() 
                    break

                current_participants_for_cycle = []
                if self.config["cycle_tagging"] and not first_pass:
                    logger.debug(f"Повторный запрос участников для цикла в чате {chat_id}.")
                    async for user in self._client.iter_participants(chat_id):
                        if not user.bot and not user.deleted and user.id != owner_id and user.id not in excluded_user_ids:
                            current_participants_for_cycle.append(user)
                    random.shuffle(current_participants_for_cycle)
                    participants = current_participants_for_cycle

                if not participants:
                    logger.warning(f"В чате {chat_id} не найдено участников для TagAll, останавливаем цикл.")
                    break

                for chunk in utils.chunks(participants, self.config["chunk_size"]):
                    if not event.state: 
                        break

                    if self.config["duration"] > 0 and (time.time() - start_time) > self.config["duration"]:
                        logger.info(f"TagAll process for chat {chat_id} finished due to duration limit (mid-cycle).")
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
                                deleted_message_ids_telethon.append(m.id)
                    else:
                        m = await self._client.send_message(
                            chat_entity,
                            full_message_text,
                            parse_mode="HTML",
                        )
                        if self.config["delete"]:
                            deleted_message_ids_telethon.append(m.id)

                    await asyncio.sleep(self._get_random_timeout(event)) 

                first_pass = False
                if self.config["cycle_tagging"] and event.state:
                    await asyncio.sleep(self.config["cycle_delay"])
                elif not self.config["cycle_tagging"]:
                    break

        except Exception as e: 
            logger.error(f"Неожиданная ошибка в _run_tagall_process для чата {chat_id}: {e}", exc_info=True)
            with contextlib.suppress(Exception):
                await self._client.send_message(chat_id, f"🚫 <b>Произошла ошибка во время TagAll:</b> <code>{e}</code>")
        finally:
            if self.config["delete"]:
                with contextlib.suppress(Exception):
                    if deleted_message_ids_telethon:
                        for chunk_ids in utils.chunks(deleted_message_ids_telethon, 100):
                            await self._client.delete_messages(chat_entity, chunk_ids)

                    if deleted_message_ids_bot_client:
                        if hasattr(self, 'inline') and hasattr(self.inline, 'bot_client') and self.inline.bot_client:
                            for chunk_ids in utils.chunks(deleted_message_ids_bot_client, 100):
                                await self.inline.bot_client.delete_messages(chat_entity, chunk_ids)
                        else:
                            logger.warning("Клиент инлайн-бота недоступен для удаления своих сообщений.")

            if event.state: 
                logger.info(f"Процесс TagAll завершен естественным образом в чате {chat_id}.")
            
            if chat_id in self._tagall_events:
                del self._tagall_events[chat_id]
                logger.info(f"TagAll process for chat {chat_id} cleaned up from tracking dictionary.")
