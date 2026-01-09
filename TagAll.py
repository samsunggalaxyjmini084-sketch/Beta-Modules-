# meta developer: @yourhandle
# meta name: TagAll
# meta version: 2.0.5
#
# 01101110 01100101 01110110 01100101 01110010 00100000 01100111 01101001 01110110 01100101 00100000 01110101 01110000
# 01101110 01100101 01110110 01100101 01110010 00100000 01101100 01100101 01110100 00100000 01111001 01101111 01110101 00100000 01100100 01101111 01110111 01101110
# 01101110 01100101 01110110 01100101 01110010 00100000 01110010 01110101 01101110 00100000 01100001 01110010 01101111 01110101 01101110 01100100 00100000 01100001 01101110 01100100 00100000 01100100 01100101 01110011 01100101 01110010 01110100 00100000 01111001 01101111 01110101
# 01101110 01100101 01110110 01100101 01110010 00100000 01101101 01100001 01101011 01100101 00100000 01111001 01101111 01110101 00100000 01100011 01110010 01111001 00100000 01101110 01100101 01110110 01100101 01110010 00100000 01110011 01100001 01111001 00100000 01100111 01101111 01101111 01100100 01100010 01111001 01100101
# 01101110 01100101 01110110 01100101 01110010 00100000 01110100 01100101 01101100 01101100 00100000 01100001 01101100 01101100 00100000 01100001 00100000 01101100 01101001 01100101 00100000 01100001 01110010 01101111 01110101 01101110 01100100 00100000 01100001 01101110 01100100 00100000 01101000 01110101 01110010 01110100 00100000 01111001 01101111 01110101
# (Rick Astley - Never Gonna Give You Up)

import asyncio
import contextlib
import logging
import random
import re # Добавлено для работы с триггерами

from hikkatl.tl.types import Message
from hikkatl.tl.functions.channels import InviteToChannelRequest

from .. import loader, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


class StopEvent:
    def __init__(self):
        self.state = True

    def stop(self):
        self.state = False


@loader.tds
class TagAllMod(loader.Module):
    """Tags all people in chat with either inline bot or client"""

    strings = {
        "name": "TagAll",
        "bot_error": "🚫 <b>Unable to invite inline bot to chat or chat type not supported for bot invites.</b>",
        "_cfg_doc_delete": "Delete messages after tagging",
        "_cfg_doc_use_bot": "Use inline bot to tag people",
        "_cfg_doc_timeout": "What time interval to sleep between each tag message",
        "_cfg_doc_silent": "Do not send message with cancel button",
        "_cfg_doc_cycle_tagging": (
            "Tag all participants over and over again until you stop the script using"
            " the button in the message"
        ),
        "_cfg_doc_cycle_delay": "Delay between each cycle of tagging in seconds",
        "_cfg_doc_chunk_size": "How many users to tag in one message",
        "_cfg_doc_delete_gathering_message": "Delete the gathering message immediately after sending",
        "_cfg_doc_start_triggers": "Comma-separated list of phrases that will start TagAll (e.g., .tagallstart, tagmeall). Case-insensitive. Text after trigger will be tagall prefix.",
        "_cfg_doc_stop_triggers": "Comma-separated list of phrases that will stop TagAll (e.g., .tagallstop, stoptag). Case-insensitive. Exact match.",
        "gathering": "🧚‍♀️ <b>Calling participants of this chat...</b>",
        "cancel": "🚫 Cancel",
        "cancelled": "🧚‍♀️ <b>TagAll cancelled!</b>",
        "tagall_stopped": "🧚‍♀️ <b>TagAll stopped!</b>",
        "tagall_not_running": "🚫 <b>TagAll is not currently running.</b>",
        "tagall_already_running": "🚫 <b>TagAll is already running. Please stop it first.</b>",
        "trigger_start_feedback": "🧚‍♀️ <b>TagAll started by trigger!</b>",
        "trigger_stop_feedback": "🧚‍♀️ <b>TagAll stopped by trigger!</b>",
    }

    strings_ru = {
        "bot_error": "🚫 <b>Не получилось пригласить бота в чат или тип чата не поддерживается для приглашения бота.</b>",
        "_cls_doc": (
            "Отмечает всех участников чата, используя инлайн бот или классическим"
            " методом"
        ),
        "_cfg_doc_delete": "Удалять сообщения после тега",
        "_cfg_doc_use_bot": "Использовать бота для тегов",
        "_cfg_doc_timeout": "Время между сообщениями с тегами",
        "_cfg_doc_silent": "Не отправлять сообщение с кнопкой отмены",
        "_cfg_doc_cycle_tagging": (
            "Тегать всех участников снова и снова, пока вы не остановите скрипт,"
            " используя кнопку в сообщении"
        ),
        "_cfg_doc_cycle_delay": "Задержка между циклами тегов в секундах",
        "_cfg_doc_chunk_size": "Сколько пользователей тегать в одном сообщении",
        "_cfg_doc_delete_gathering_message": "Удалять сообщение о сборе участников сразу после отправки",
        "_cfg_doc_start_triggers": "Список фраз (через запятую), которые запустят TagAll (например, .tagallstart, отметьвсех). Без учета регистра. Текст после триггера будет префиксом для тегов.",
        "_cfg_doc_stop_triggers": "Список фраз (через запятую), которые остановят TagAll (например, .tagallstop, хватит). Без учета регистра. Точное совпадение.",
        "gathering": "🧚‍♀️ <b>Отмечаю участников чата...</b>",
        "cancel": "🚫 Отмена",
        "cancelled": "🧚‍♀️ <b>Сбор участников отменен!</b>",
        "tagall_stopped": "🧚‍♀️ <b>TagAll остановлен!</b>",
        "tagall_not_running": "🚫 <b>TagAll сейчас не запущен.</b>",
        "tagall_already_running": "🚫 <b>TagAll уже запущен. Сначала остановите его.</b>",
        "trigger_start_feedback": "🧚‍♀️ <b>TagAll запущен по триггеру!</b>",
        "trigger_stop_feedback": "🧚‍♀️ <b>TagAll остановлен по триггеру!</b>",
    }

    strings_de = {
        "bot_error": "🚫 <b>Einladung des Inline-Bots in den Chat fehlgeschlagen oder der Chat-Typ wird für Bot-Einladungen nicht unterstützt.</b>",
        "_cfg_doc_delete": "Nachrichten nach Erwähnung löschen",
        "_cfg_doc_use_bot": "Inline-Bot verwenden, um Leute zu erwähnen",
        "_cfg_doc_timeout": (
            "Zeitintervall, in dem zwischen den Erwähnungen gewartet wird"
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
        "_cfg_doc_delete_gathering_message": "Die Sammelnachricht sofort nach dem Senden löschen",
        "_cfg_doc_start_triggers": "Kommagetrennte Liste von Phrasen, die TagAll starten (z.B. .tagallstart, allemarkieren). Groß-/Kleinschreibung wird ignoriert. Text nach dem Trigger wird zum Tagall-Präfix.",
        "_cfg_doc_stop_triggers": "Kommagetrennte Liste von Phrasen, die TagAll stoppen (z.B. .tagallstop, stoppmarkierung). Groß-/Kleinschreibung wird ignoriert. Exakte Übereinstimmung.",
        "gathering": "🧚‍♀️ <b>Erwähne Teilnehmer dieses Chats...</b>",
        "cancel": "🚫 Abbrechen",
        "cancelled": "🧚‍♀️ <b>TagAll abgebrochen!</b>",
        "tagall_stopped": "🧚‍♀️ <b>TagAll gestoppt!</b>",
        "tagall_not_running": "🚫 <b>TagAll läuft derzeit nicht.</b>",
        "tagall_already_running": "🚫 <b>TagAll läuft bereits. Bitte stoppe es zuerst.</b>",
        "trigger_start_feedback": "🧚‍♀️ <b>TagAll per Trigger gestartet!</b>",
        "trigger_stop_feedback": "🧚‍♀️ <b>TagAll per Trigger gestoppt!</b>",
    }

    strings_tr = {
        "bot_error": "🚫 <b>Inline botunu sohbete davet edilemedi veya sohbet türü bot davetleri için desteklenmiyor.</b>",
        "_cfg_doc_delete": "Etiketledikten sonra mesajları sil",
        "_cfg_doc_use_bot": "İnsanları etiketlemek için inline botu kullan",
        "_cfg_doc_timeout": "Her etiket mesajı arasında ne kadar bekleneceği",
        "_cfg_doc_silent": "İptal düğmesi olmadan mesaj gönderme",
        "_cfg_doc_cycle_tagging": (
            "Mesajdaki düğmeyi kullanarak betiği durdurana kadar tüm katılımcıları"
            " tekrar tekrar etiketle"
        ),
        "_cfg_doc_cycle_delay": "Etiketleme döngüsü arasındaki gecikme süresi (saniye)",
        "_cfg_doc_chunk_size": "Bir mesajda kaç kullanıcı etiketlenecek",
        "_cfg_doc_delete_gathering_message": "Toplama mesajını gönderdikten hemen sonra sil",
        "_cfg_doc_start_triggers": "TagAll'u başlatacak virgülle ayrılmış ifadeler listesi (örn. .tagallstart, hepsinietikle). Büyük/küçük harf duyarsız. Tetikleyici sonrası metin tagall ön eki olacaktır.",
        "_cfg_doc_stop_triggers": "TagAll'u durduracak virgülle ayrılmış ifadeler listesi (örn. .tagallstop, etiketidurdur). Büyük/küçük harf duyarsız. Tam eşleşme.",
        "gathering": "🧚‍♀️ <b>Bu sohbetteki katılımcıları çağırıyorum...</b>",
        "cancel": "🚫 İptal",
        "cancelled": "🧚‍♀️ <b>TagAll iptal edildi!</b>",
        "tagall_stopped": "🧚‍♀️ <b>TagAll durduruldu!</b>",
        "tagall_not_running": "🚫 <b>TagAll şu anda çalışmıyor.</b>",
        "tagall_already_running": "🚫 <b>TagAll zaten çalışıyor. Önce durdurun.</b>",
        "trigger_start_feedback": "🧚‍♀️ <b>TagAll tetikleyici ile başlatıldı!</b>",
        "trigger_stop_feedback": "🧚‍♀️ <b>TagAll tetikleyici ile durduruldu!</b>",
    }

    strings_uz = {
        "bot_error": (
            "🚫 <b>Inline botni chatga taklif qilish muvaffaqiyatsiz bo‘ldi yoki chat turi bot takliflari uchun qo‘llab-quvvatlanmaydi.</b>"
        ),
        "_cfg_doc_delete": "Etiketdan so‘ng xabarlarni o‘chirish",
        "_cfg_doc_use_bot": "Odamlarni etiketlash uchun inline botdan foydalanish",
        "_cfg_doc_timeout": "Har bir etiket xabari orasida nechta kutish kerak",
        "_cfg_doc_silent": "Bekor tugmasi olmadan xabar jo‘natish",
        "_cfg_doc_cycle_tagging": (
            "Xabar bo‘yicha tugmani ishlatib, skriptni to‘xtatguncha barcha"
            " qatnashuvchilarni qayta-qayta etiketlash"
        ),
        "_cfg_doc_cycle_delay": "Har bir etiketlash tsikli orasida gecikma (soniya)",
        "_cfg_doc_chunk_size": "Bir xabarda nechta foydalanuvchi etiketlanadi",
        "_cfg_doc_delete_gathering_message": "Yig'in xabarini yuborilgandan so'ng darhol o'chirish",
        "_cfg_doc_start_triggers": "TagAll'ni ishga tushiruvchi vergul bilan ajratilgan iboralar ro'yxati (masalan, .tagallstart, hammasini_belgilash). Katta/kichik harflarga ahamiyat berilmaydi. Triggerdan keyingi matn TagAll prefiksi bo'ladi.",
        "_cfg_doc_stop_triggers": "TagAll'ni to'xtatuvchi vergul bilan ajratilgan iboralar ro'yxati (masalan, .tagallstop, belgilashni_to'xtatish). Katta/kichik harflarga ahamiyat berilmaydi. Aniq mos kelishi kerak.",
        "gathering": "🧚‍♀️ <b>Ushbu chatta qatnashganlarni chaqiraman...</b>",
        "cancel": "🚫 Bekor qilish",
        "cancelled": "🧚‍♀️ <b>TagAll bekor qilindi!</b>",
        "tagall_stopped": "🧚‍♀️ <b>TagAll to'xtatildi!</b>",
        "tagall_not_running": "🚫 <b>TagAll hozirda ishlamayapti.</b>",
        "tagall_already_running": "🚫 <b>TagAll allaqachon ishlayapti. Avval uni to'xtating.</b>",
        "trigger_start_feedback": "🧚‍♀️ <b>TagAll trigger orqali ishga tushirildi!</b>",
        "trigger_stop_feedback": "🧚‍♀️ <b>TagAll trigger orqali to'xtatildi!</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
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
                0.1,
                lambda: self.strings("_cfg_doc_timeout"),
                validator=loader.validators.Float(minimum=0),
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
                lambda: self.strings("_cfg_doc_cycle_tagging"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "cycle_delay",
                0,
                lambda: self.strings("_cfg_doc_cycle_delay"),
                validator=loader.validators.Integer(minimum=0),
            ),
            loader.ConfigValue(
                "chunk_size",
                3,
                lambda: self.strings("_cfg_doc_chunk_size"),
                validator=loader.validators.Integer(minimum=1),
            ),
            loader.ConfigValue(
                "delete_gathering_message",
                False,
                lambda: self.strings("_cfg_doc_delete_gathering_message"),
                validator=loader.validators.Boolean(),
            ),
            # Новые конфиги для триггеров
            loader.ConfigValue(
                "start_triggers",
                "",
                lambda: self.strings("_cfg_doc_start_triggers"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "stop_triggers",
                "",
                lambda: self.strings("_cfg_doc_stop_triggers"),
                validator=loader.validators.String(),
            ),
        )
        self._tagall_event = None  # Инициализируем трекер события TagAll
        self._tagall_task = None # Для отслеживания запущенной задачи

    def _parse_triggers(self, trigger_string: str) -> list[str]:
        """Парсит строку триггеров, разделенных запятыми, возвращая список очищенных и приведенных к нижнему регистру триггеров."""
        return [t.strip().lower() for t in trigger_string.split(',') if t.strip()]

    async def cancel(self, call: InlineCall, event: StopEvent):
        """Обработчик кнопки отмены в инлайн-сообщении."""
        event.stop()
        await call.answer(self.strings("cancelled"))
        await call.edit(self.strings("cancelled")) # Обновляем сообщение с кнопкой

    async def _tagall_impl(self, message: Message, raw_args: str = ""):
        """Основная логика таггала, вызываемая командой или триггером."""
        deleted_message_ids_hikkatl = []
        deleted_message_ids_aiogram = []
        cancel_msg = None

        is_bot_sender = self.config["use_bot"]

        chat_entity = await self._client.get_input_entity(message.peer_id)
        chat_id_for_aiogram = message.chat_id

        if is_bot_sender:
            try:
                bot_entity = await self._client.get_input_entity(self.inline.bot_username)
                await self._client(InviteToChannelRequest(chat_entity, [bot_entity]))
            except Exception as e:
                logger.error(f"Failed to invite bot: {e}")
                await utils.answer(message, self.strings("bot_error"))
                # В случае ошибки приглашения бота, также очищаем состояние
                self._tagall_event = None
                self._tagall_task = None
                return

        event = StopEvent()
        self._tagall_event = event  # Сохраняем событие для возможной остановки извне

        # Отправляем сообщение с кнопкой отмены только если не "silent" и не настроено на немедленное удаление
        if not (self.config["silent"] or self.config["delete_gathering_message"]):
            cancel_msg = await self.inline.form(
                message=message,
                text=self.strings("gathering"),
                reply_markup={
                    "text": self.strings("cancel"),
                    "callback": self.cancel,
                    "args": (event,),
                },
            )
        elif self.config["delete_gathering_message"]:
            # Если настроено на немедленное удаление, отправляем обычное сообщение и удаляем его.
            # `utils.answer` здесь не удаляет, это просто отправка, так что нужно ручное удаление или просто не показывать
            # Если оно должно быть невидимым, то просто не отправляем его вообще.
            # Если цель - быстро показать и удалить, то:
            sent_gathering_msg = await utils.answer(message, self.strings("gathering"))
            if sent_gathering_msg and message.out: # Только если это наше сообщение и мы хотим его удалить
                await asyncio.sleep(0.5) # Дать время появиться
                await self._client.delete_messages(chat_entity, sent_gathering_msg)


        participants = []
        async for user in self._client.iter_participants(message.peer_id):
            if not user.bot and not user.deleted:
                participants.append(user)
        
        random.shuffle(participants)

        message_prefix = utils.escape_html(raw_args) if raw_args else ""

        try:
            first, br = True, False
            while True if self.config["cycle_tagging"] else first:
                for chunk in utils.chunks(participants, self.config["chunk_size"]):
                    if not event.state: # Проверяем, было ли событие остановлено
                        br = True
                        break

                    tags = []
                    for user in chunk:
                        if user.username:
                            user_display_name = f"@{user.username}"
                        else:
                            user_display_name = utils.escape_html(user.first_name or "Пользователь")
                            if user.last_name:
                                user_display_name += " " + utils.escape_html(user.last_name)
                    
                        tags.append(f'<a href="tg://user?id={user.id}">{user_display_name}</a>')

                    if message_prefix:
                        full_message_text = f"{message_prefix}\n{' '.join(tags)}"
                    else:
                        full_message_text = ' '.join(tags)

                    if is_bot_sender:
                        m = await self.inline.bot_client.send_message(
                            chat_id_for_aiogram,
                            full_message_text,
                            parse_mode="HTML",
                        )
                        if self.config["delete"]:
                            deleted_message_ids_aiogram.append(m.message_id)
                    else:
                        m = await self._client.send_message(
                            chat_entity,
                            full_message_text,
                            parse_mode="HTML",
                        )
                        if self.config["delete"]:
                            deleted_message_ids_hikkatl.append(m.id)

                    await asyncio.sleep(self.config["timeout"])

                if br: # Если вышли из внутреннего цикла из-за остановки
                    break

                first = False
                if self.config["cycle_tagging"]:
                    await asyncio.sleep(self.config["cycle_delay"])
        finally:
            self._tagall_event = None  # Очищаем событие независимо от исхода
            self._tagall_task = None # Очищаем задачу

            # Если сообщение с отменой было отправлено, удаляем его, или редактируем, если отменено пользователем
            if cancel_msg:
                if not event.state: # Было остановлено пользователем через кнопку
                    await cancel_msg.edit(self.strings("cancelled"))
                else: # Завершилось само, или остановлено триггером (тогда триггер пошлет свое сообщение, а это просто удаляем)
                    await cancel_msg.delete()

            if self.config["delete"]:  # Обрабатываем удаление помеченных сообщений
                with contextlib.suppress(Exception): # Подавляем любые ошибки при удалении
                    if deleted_message_ids_hikkatl:
                        # Удаляем сообщения большими пачками, если они были отправлены нашим клиентом
                        for chunk_ids in utils.chunks(deleted_message_ids_hikkatl, 100):
                            await self._client.delete_messages(chat_entity, chunk_ids)

                    if deleted_message_ids_aiogram:
                        # Удаляем сообщения по одному, если они были отправлены инлайн-ботом
                        for msg_id in deleted_message_ids_aiogram:
                            await self.inline.bot_client.delete_message(chat_id_for_aiogram, msg_id)


    async def _stoptagall_impl(self, message: Message, is_trigger: bool = False):
        """Основная логика остановки таггала, вызываемая командой или триггером."""
        if self._tagall_event and self._tagall_event.state:
            self._tagall_event.stop()
            # Дожидаемся завершения таска, чтобы убедиться, что _tagall_event и _tagall_task очищены
            if self._tagall_task:
                with contextlib.suppress(asyncio.CancelledError):
                    await self._tagall_task # Ждем завершения таска (его finally блока)
            
            if is_trigger:
                await utils.answer(message, self.strings("trigger_stop_feedback"))
            else:
                await utils.answer(message, self.strings("tagall_stopped"))
        else:
            if is_trigger:
                await utils.answer(message, self.strings("tagall_not_running")) # Используем общую строку
            else:
                await utils.answer(message, self.strings("tagall_not_running"))


    @loader.command(
        groups=True,
        ru_doc="[текст] - Отметить всех участников чата. [текст] будет отправлен вместе с тегами. Если текст не указан, будут отправлены только теги.",
        de_doc="[Text] - Alle Chatteilnehmer erwähnen. [Text] wird zusammen mit den Erwähnungen gesendet. Wenn kein Text angegeben ist, werden nur die Erwähnungen gesendet.",
        tr_doc="[metin] - Sohbet katılımcılarını etiketle. [metin] etiketlerle birlikte gönderilecektir. Metin belirtilmezse, sadece etiketler gönderilecektir.",
        uz_doc="[matn] - Chat qatnashuvchilarini tegish. [matn] teglar bilan birga yuboriladi. Agar matn ko'rsatilmagan bo'lsa, faqat teglar yuboriladi.",
    )
    async def tagall(self, message: Message):
        """[text] - Tag all users in chat. [text] will be sent along with tags. If no text is provided, only tags will be sent."""
        if self._tagall_event and self._tagall_event.state:
            await utils.answer(message, self.strings("tagall_already_running"))
            if message.out:
                await message.delete()
            return

        args = utils.get_args_raw(message)
        if message.out:
            await message.delete()
        
        # Запускаем таск и сохраняем его, чтобы можно было остановить
        self._tagall_task = asyncio.create_task(self._tagall_impl(message, raw_args=args))


    @loader.command(
        ru_doc="Остановить запущенный процесс TagAll.",
        de_doc="Den laufenden TagAll-Prozess stoppen.",
        tr_doc="Çalışan TagAll sürecini durdur.",
        uz_doc="Ishlayotgan TagAll jarayonini to'xtatish.",
    )
    async def stoptagall(self, message: Message):
        """Stop the currently running TagAll process."""
        await self._stoptagall_impl(message, is_trigger=False)
        if message.out:
            await message.delete()

    @loader.watcher(only_messages=True)
    async def _watcher(self, message: Message):
        """Проверяет сообщения на наличие триггеров для запуска/остановки TagAll."""
        # Реагируем только на наши исходящие текстовые сообщения
        if not message.text or not message.out:
            return

        message_text_lower = message.text.lower()

        # Проверка на триггеры запуска
        start_triggers = self._parse_triggers(self.config["start_triggers"])
        for trigger in start_triggers:
            if message_text_lower.startswith(trigger):
                if self._tagall_event and self._tagall_event.state:
                    await utils.answer(message, self.strings("tagall_already_running"))
                    await message.delete() # Удаляем сообщение с триггером, если уже запущено
                    return
                
                raw_args = message.text[len(trigger):].strip()
                await message.delete() # Удаляем сообщение с триггером перед запуском
                await utils.answer(message, self.strings("trigger_start_feedback"))
                
                # Запускаем таск и сохраняем его
                self._tagall_task = asyncio.create_task(self._tagall_impl(message, raw_args=raw_args))
                return # Реагируем только на один триггер

        # Проверка на триггеры остановки
        stop_triggers = self._parse_triggers(self.config["stop_triggers"])
        for trigger in stop_triggers:
            if message_text_lower == trigger: # Точное совпадение для остановки
                await message.delete() # Удаляем сообщение с триггером
                await self._stoptagall_impl(message, is_trigger=True)
                return # Реагируем только на один триггер
```
