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

from aiogram import Bot
from hikkatl.tl.functions.channels import InviteToChannelRequest
from hikkatl.tl.types import Message

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
        "bot_error": "🚫 <b>Unable to invite inline bot to chat</b>",
        "_cfg_doc_default_message": "Default message of mentions",
        "_cfg_doc_delete": "Delete messages after tagging",
        "_cfg_doc_use_bot": "Use inline bot to tag people",
        "_cfg_doc_timeout": "What time interval to sleep between each tag message",
        "_cfg_doc_silent": "Do not send message with cancel button",
        "_cfg_doc_cycle_tagging": (
            "Tag all participants over and over again until you stop the script using"
            " the button in the message"
        ),
        "_cfg_doc_cycle_delay": "Delay between each cycle of tagging in seconds",
        "_cfg_doc_chunk_size": "Number of users to tag in one message (max 5 for inline bot, higher for client)",
        "gathering": "🧚‍♀️ <b>Calling participants of this chat...</b>",
        "cancel": "🚫 Cancel",
        "cancelled": "🧚‍♀️ <b>TagAll cancelled!</b>",
        # New strings for triggers
        "_cfg_doc_trigger_system_enabled": "Enable or disable the trigger system for TagAll",
        "_cfg_doc_trigger_on_phrases": "List of phrases that activate TagAll (comma-separated)",
        "_cfg_doc_trigger_off_phrases": "List of phrases that deactivate TagAll (comma-separated)",
        "_cfg_doc_authorized_user_id": "User ID who can activate/deactivate triggers (0 or leave empty for any user)",
        "trigger_enabled": "✅ <b>TagAll trigger system enabled!</b>",
        "trigger_disabled": "❌ <b>TagAll trigger system disabled!</b>",
        "trigger_on_activated": "▶️ <b>TagAll activated by trigger in this chat!</b>",
        "trigger_off_deactivated": "⏸️ <b>TagAll deactivated by trigger in this chat!</b>",
        "trigger_already_on": "ℹ️ <b>TagAll is already running in this chat.</b>",
        "trigger_not_running": "ℹ️ <b>TagAll is not running in this chat.</b>",
        "not_authorized": "🚫 <b>You are not authorized to use TagAll triggers.</b>",
    }

    strings_ru = {
        "bot_error": "🚫 <b>Не получилось пригласить бота в чат</b>",
        "_cls_doc": (
            "Отмечает всех участников чата, используя инлайн бот или классическим"
            " методом"
        ),
        "_cfg_doc_default_message": "Сообщение по умолчанию для тегов",
        "_cfg_doc_delete": "Удалять сообщения после тега",
        "_cfg_doc_use_bot": "Использовать бота для тегов",
        "_cfg_doc_timeout": "Время между сообщениями с тегами",
        "_cfg_doc_silent": "Не отправлять сообщение с кнопкой отмены",
        "_cfg_doc_cycle_tagging": (
            "Тегать всех участников снова и снова, пока вы не остановите скрипт,"
            " используя кнопку в сообщении"
        ),
        "_cfg_doc_cycle_delay": "Задержка между циклами тегов в секундах",
        "_cfg_doc_chunk_size": "Количество пользователей для тега в одном сообщении (макс 5 для инлайн бота, больше для клиента)",
        "gathering": "🧚‍♀️ <b>Отмечаю участников чата...</b>",
        "cancel": "🚫 Отмена",
        "cancelled": "🧚‍♀️ <b>Сбор участников отменен!</b>",
        # New strings for triggers (Russian)
        "_cfg_doc_trigger_system_enabled": "Включить или выключить систему триггеров для TagAll",
        "_cfg_doc_trigger_on_phrases": "Список фраз, активирующих TagAll (через запятую)",
        "_cfg_doc_trigger_off_phrases": "Список фраз, деактивирующих TagAll (через запятую)",
        "_cfg_doc_authorized_user_id": "ID пользователя, который может активировать/деактивировать триггеры (0 или оставьте пустым для любого пользователя)",
        "trigger_enabled": "✅ <b>Система триггеров TagAll включена!</b>",
        "trigger_disabled": "❌ <b>Система триггеров TagAll выключена!</b>",
        "trigger_on_activated": "▶️ <b>TagAll активирован триггером в этом чате!</b>",
        "trigger_off_deactivated": "⏸️ <b>TagAll деактивирован триггером в этом чате!</b>",
        "trigger_already_on": "ℹ️ <b>TagAll уже запущен в этом чате.</b>",
        "trigger_not_running": "ℹ️ <b>TagAll не запущен в этом чате.</b>",
        "not_authorized": "🚫 <b>Вы не авторизованы для использования триггеров TagAll.</b>",
    }

    strings_de = {
        "bot_error": "🚫 <b>Einladung des Inline-Bots in den Chat fehlgeschlagen</b>",
        "_cfg_doc_default_message": "Standardnachricht für Erwähnungen",
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
        "_cfg_doc_chunk_size": "Anzahl der Benutzer, die in einer Nachricht erwähnt werden sollen (max. 5 für Inline-Bot, mehr für Client)",
        "gathering": "🧚‍♀️ <b>Erwähne Teilnehmer dieses Chats...</b>",
        "cancel": "🚫 Abbrechen",
        "cancelled": "🧚‍♀️ <b>TagAll abgebrochen!</b>",
        # New strings for triggers (German)
        "_cfg_doc_trigger_system_enabled": "Triggersystem für TagAll aktivieren oder deaktivieren",
        "_cfg_doc_trigger_on_phrases": "Liste der Phrasen, die TagAll aktivieren (kommagetrennt)",
        "_cfg_doc_trigger_off_phrases": "Liste der Phrasen, die TagAll deaktivieren (kommagetrennt)",
        "_cfg_doc_authorized_user_id": "Benutzer-ID, die Trigger aktivieren/deaktivieren kann (0 oder leer lassen für beliebigen Benutzer)",
        "trigger_enabled": "✅ <b>TagAll Triggersystem aktiviert!</b>",
        "trigger_disabled": "❌ <b>TagAll Triggersystem deaktiviert!</b>",
        "trigger_on_activated": "▶️ <b>TagAll durch Trigger in diesem Chat aktiviert!</b>",
        "trigger_off_deactivated": "⏸️ <b>TagAll durch Trigger in diesem Chat deaktiviert!</b>",
        "trigger_already_on": "ℹ️ <b>TagAll läuft bereits in diesem Chat.</b>",
        "trigger_not_running": "ℹ️ <b>TagAll läuft nicht in diesem Chat.</b>",
        "not_authorized": "🚫 <b>Du bist nicht berechtigt, TagAll-Trigger zu verwenden.</b>",
    }

    strings_tr = {
        "bot_error": "🚫 <b>Inline botunu sohbete davet edilemedi</b>",
        "_cfg_doc_default_message": "Varsayılan etiket mesajı",
        "_cfg_doc_delete": "Etiketledikten sonra mesajları sil",
        "_cfg_doc_use_bot": "İnsanları etiketlemek için inline botu kullan",
        "_cfg_doc_timeout": "Her etiket mesajı arasında ne kadar bekleneceği",
        "_cfg_doc_silent": "İptal düğmesi olmadan mesaj gönderme",
        "_cfg_doc_cycle_tagging": (
            "Mesajdaki düğmeyi kullanarak betiği durdurana kadar tüm katılımcıları"
            " tekrar tekrar etiketle"
        ),
        "_cfg_doc_cycle_delay": "Etiketleme döngüsü arasındaki gecikme süresi (saniye)",
        "_cfg_doc_chunk_size": "Tek mesajda etiketlenecek kullanıcı sayısı (inline bot için maks 5, client için daha fazla)",
        "gathering": "🧚‍♀️ <b>Bu sohbetteki katılımcıları çağırıyorum...</b>",
        "cancel": "🚫 İptal",
        "cancelled": "🧚‍♀️ <b>TagAll iptal edildi!</b>",
        # New strings for triggers (Turkish)
        "_cfg_doc_trigger_system_enabled": "TagAll için tetikleyici sistemi etkinleştir veya devre dışı bırak",
        "_cfg_doc_trigger_on_phrases": "TagAll'u etkinleştiren ifadeler listesi (virgülle ayrılmış)",
        "_cfg_doc_trigger_off_phrases": "TagAll'u devre dışı bırakan ifadeler listesi (virgülle ayrılmış)",
        "_cfg_doc_authorized_user_id": "Tetikleyicileri etkinleştirebilecek/devre dışı bırakabilecek kullanıcı kimliği (herhangi bir kullanıcı için 0 veya boş bırakın)",
        "trigger_enabled": "✅ <b>TagAll tetikleme sistemi etkinleştirildi!</b>",
        "trigger_disabled": "❌ <b>TagAll tetikleme sistemi devre dışı bırakıldı!</b>",
        "trigger_on_activated": "▶️ <b>TagAll bu sohbette tetikleyici tarafından etkinleştirildi!</b>",
        "trigger_off_deactivated": "⏸️ <b>TagAll bu sohbette tetikleyici tarafından devre dışı bırakıldı!</b>",
        "trigger_already_on": "ℹ️ <b>TagAll zaten bu sohbette çalışıyor.</b>",
        "trigger_not_running": "ℹ️ <b>TagAll bu sohbette çalışmıyor.</b>",
        "not_authorized": "🚫 <b>TagAll tetikleyicilerini kullanmaya yetkiniz yok.</b>",
    }

    strings_uz = {
        "bot_error": (
            "🚫 <b>Inline botni chatga taklif qilish muvaffaqiyatsiz bo‘ldi</b>"
        ),
        "_cls_doc": (
            "Отмечает всех участников чата, используя инлайн бот или классическим"
            " методом"
        ),
        "_cfg_doc_default_message": "Odatiy etiket xabari",
        "_cfg_doc_delete": "Etiketdan so‘ng xabarlarni o‘chirish",
        "_cfg_doc_use_bot": "Odamlarni etiketlash uchun inline botdan foydalanish",
        "_cfg_doc_timeout": "Har bir etiket xabari orasida nechta kutish kerak",
        "_cfg_doc_silent": "Bekor tugmasi olmadan xabar jo‘natish",
        "_cfg_doc_cycle_tagging": (
            "Xabar bo‘yicha tugmani ishlatib, skriptni to‘xtatguncha barcha"
            " qatnashuvchilarni qayta-qayta etiketlash"
        ),
        "_cfg_doc_cycle_delay": "Har bir etiketlash tsikli orasida gecikma (soniya)",
        "_cfg_doc_chunk_size": "Bitta xabarda belgilash uchun foydalanuvchilar soni (inline bot uchun maks 5, client uchun ko'proq)",
        "gathering": "🧚‍♀️ <b>Ushbu chatta qatnashganlarni chaqiraman...</b>",
        "cancel": "🚫 Bekor qilish",
        "cancelled": "🧚‍♀️ <b>TagAll bekor qilindi!</b>",
        # New strings for triggers (Uzbek)
        "_cfg_doc_trigger_system_enabled": "TagAll uchun trigger tizimini yoqish yoki o'chirish",
        "_cfg_doc_trigger_on_phrases": "TagAll'ni faollashtiradigan iboralar ro'yxati (vergul bilan ajratilgan)",
        "_cfg_doc_trigger_off_phrases": "TagAll'ni o'chiradigan iboralar ro'yxati (vergul bilan ajratilgan)",
        "_cfg_doc_authorized_user_id": "Triggerlarni faollashtirishi/o'chirishi mumkin bo'lgan foydalanuvchi IDsi (har qanday foydalanuvchi uchun 0 yoki bo'sh qoldirilsin)",
        "trigger_enabled": "✅ <b>TagAll trigger tizimi yoqildi!</b>",
        "trigger_disabled": "❌ <b>TagAll trigger tizimi o'chirildi!</b>",
        "trigger_on_activated": "▶️ <b>TagAll ushbu chatda trigger orqali faollashtirildi!</b>",
        "trigger_off_deactivated": "⏸️ <b>TagAll ushbu chatda trigger orqali o'chirildi!</b>",
        "trigger_already_on": "ℹ️ <b>TagAll bu chatda allaqachon ishlayapti.</b>",
        "trigger_not_running": "ℹ️ <b>TagAll bu chatda ishlamayapti.</b>",
        "not_authorized": "🚫 <b>Siz TagAll triggerlaridan foydalanishga ruxsat etilmagansiz.</b>",
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
                5, # Default to 5 users per message
                lambda: self.strings("_cfg_doc_chunk_size"),
                validator=loader.validators.Integer(minimum=1),
            ),
            # New config values for triggers
            loader.ConfigValue(
                "trigger_system_enabled",
                False,
                lambda: self.strings("_cfg_doc_trigger_system_enabled"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "trigger_on_phrases",
                "tagall on, start tagall",
                lambda: self.strings("_cfg_doc_trigger_on_phrases"),
                validator=loader.validators.Series(),
            ),
            loader.ConfigValue(
                "trigger_off_phrases",
                "tagall off, stop tagall",
                lambda: self.strings("_cfg_doc_trigger_off_phrases"),
                validator=loader.validators.Series(),
            ),
            loader.ConfigValue(
                "authorized_user_id",
                None,  # None means no specific user, 0 means any user.
                lambda: self.strings("_cfg_doc_authorized_user_id"),
                validator=loader.validators.Integer(minimum=0),
            ),
        )

        # Dictionary to store active triggered TagAll tasks: chat_id -> (asyncio.Task, StopEvent)
        self._active_tagall_tasks = {}

    async def client_ready(self, client, db):
        self._db = db

    async def cancel(self, call: InlineCall, event: StopEvent):
        event.stop()
        await call.answer(self.strings("cancelled"))

    @loader.command(
        ru_doc="Включить/выключить систему триггеров TagAll",
        de_doc="TagAll-Triggersystem ein-/ausschalten",
        tr_doc="TagAll tetikleme sistemini aç/kapat",
        uz_doc="TagAll trigger tizimini yoqish/o'chirish",
    )
    async def triggerall_toggle(self, message: Message):
        """Toggle TagAll trigger system"""
        self.config["trigger_system_enabled"] = not self.config["trigger_system_enabled"]
        if self.config["trigger_system_enabled"]:
            await utils.answer(message, self.strings("trigger_enabled"))
        else:
            await utils.answer(message, self.strings("trigger_disabled"))

    @loader.watcher(only_messages=True)
    async def _watcher(self, message: Message):
        if not message.text or not self.config["trigger_system_enabled"]:
            return

        # Check authorized user
        authorized_user_id = self.config["authorized_user_id"]
        # If authorized_user_id is None (empty config) or 0, any user can trigger.
        # If authorized_user_id is a positive integer, only that user can trigger.
        if authorized_user_id is not None and authorized_user_id != 0:
            if message.sender_id != authorized_user_id:
                await message.respond(self.strings("not_authorized"))
                return

        chat_id = utils.get_chat_id(message)
        message_text = message.text.lower().strip() # Normalize message text for comparison

        # Check for activation triggers
        for phrase in [p.strip().lower() for p in self.config["trigger_on_phrases"]]:
            if message_text == phrase:  # Exact match for trigger phrases
                if chat_id in self._active_tagall_tasks:
                    await message.respond(self.strings("trigger_already_on"))
                    return

                logger.info(f"TagAll triggered ON in chat {chat_id}")
                stop_event = StopEvent()
                tagall_task = asyncio.ensure_future(
                    self._run_triggered_tagall(message, stop_event)
                )
                self._active_tagall_tasks[chat_id] = (tagall_task, stop_event)
                await message.respond(self.strings("trigger_on_activated"))
                return

        # Check for deactivation triggers
        for phrase in [p.strip().lower() for p in self.config["trigger_off_phrases"]]:
            if message_text == phrase:  # Exact match for trigger phrases
                if chat_id in self._active_tagall_tasks:
                    logger.info(f"TagAll triggered OFF in chat {chat_id}")
                    _task, stop_event = self._active_tagall_tasks.pop(chat_id)
                    stop_event.stop()
                    with contextlib.suppress(asyncio.CancelledError):
                        await _task  # Await to ensure it's cancelled/finished
                    await message.respond(self.strings("trigger_off_deactivated"))
                else:
                    await message.respond(self.strings("trigger_not_running"))
                return

    async def _perform_tagging(self, message: Message, args: str, stop_event: StopEvent, silent: bool = False):
        """
        Core tagging logic, used by both manual command and triggered system.
        :param message: The original message object (for peer_id, chat_id).
        :param args: Arguments for the tagging message (from manual command).
        :param stop_event: An instance of StopEvent to control the tagging loop.
        :param silent: If True, do not send an inline cancel button message.
        """
        if self.config["use_bot"]:
            try:
                await self._client(
                    InviteToChannelRequest(message.peer_id, [self.inline.bot_username])
                )
            except Exception:
                # If bot cannot be invited, answer only if not silent
                if not silent:
                    await utils.answer(message, self.strings("bot_error"))
                return

            with contextlib.suppress(Exception):
                Bot.set_instance(self.inline.bot)

            chat_id = int(f"-100{utils.get_chat_id(message)}")
        else:
            chat_id = utils.get_chat_id(message)

        cancel_msg = None
        if not silent:
            cancel_msg = await self.inline.form(
                message=message,
                text=self.strings("gathering"),
                reply_markup={
                    "text": self.strings("cancel"),
                    "callback": self.cancel,
                    "args": (stop_event,),
                },
            )

        while True:
            if not stop_event.state:
                if cancel_msg:
                    await cancel_msg.edit(self.strings("cancelled"))
                break # Exit loop if stopped

            members = []
            try:
                async for user in self._client.iter_participants(message.peer_id):
                    if user.deleted:
                        continue # Skip deleted users

                    if user.username:
                        mention = f"@{user.username}"
                    else:
                        # Construct full_name manually
                        full_name_parts = []
                        if user.first_name:
                            full_name_parts.append(user.first_name)
                        if user.last_name:
                            full_name_parts.append(user.last_name)
                        
                        full_name = " ".join(full_name_parts).strip()
                        
                        # Fallback if full_name is still empty (e.g., user has no first/last name set)
                        if not full_name:
                            full_name = "Unknown User"
                        
                        mention = f'<a href="tg://user?id={user.id}">{utils.escape_html(full_name)}</a>'
                    members.append(mention)
            except Exception as e:
                logger.error(f"Error iterating participants: {e}")
                if not silent:
                    await utils.answer(message, f"🚫 <b>Error gathering participants:</b> {e}")
                break

            # The message to use will now always be args (if provided) or default_message
            message_text_to_use = args or self.config["default_message"]

            for chunk in utils.chunks(
                members,
                self.config["chunk_size"], # Use configurable chunk_size
            ):
                if not stop_event.state: # Check again before sending each chunk
                    break

                try:
                    m = await (
                        self.inline.bot.send_message
                        if self.config["use_bot"]
                        else self._client.send_message
                    )(
                        chat_id,
                        utils.escape_html(message_text_to_use)
                        + "\xad".join(chunk), # Still use soft hyphen for joining
                        parse_mode="HTML", # Explicitly set parse_mode for <a> tags and @mentions
                    )

                    if self.config["delete"]:
                        with contextlib.suppress(Exception):
                            await m.delete()
                except Exception as e:
                    logger.error(f"Error sending tag message in chat {chat_id}: {e}")
                    if "MESSAGE_TOO_LONG" in str(e):
                        logger.warning(f"Tag message too long in chat {chat_id}, consider reducing chunk size or message content.")
                    pass

                await asyncio.sleep(self.config["timeout"])

            if not stop_event.state:
                break

            if not self.config["cycle_tagging"]: # Break out of loop if not cycling after one pass
                break

            await asyncio.sleep(self.config["cycle_delay"])

        if cancel_msg and stop_event.state: # If not stopped by event but loop completed (e.g., no cycle)
             await cancel_msg.delete()

    @loader.command(
        groups=True,
        ru_doc="[текст] - Отметить всех участников чата",
        de_doc="[Text] - Alle Chatteilnehmer erwähnen",
        tr_doc="[metin] - Sohbet katılımcılarını etiketle",
        uz_doc="[matn] - Chat qatnashuvchilarini tegish",
    )
    async def tagall(self, message: Message):
        """[text] - Tag all users in chat"""
        args = utils.get_args_raw(message)
        if message.out:
            await message.delete()

        stop_event = StopEvent() # Local stop event for manual command
        await self._perform_tagging(message, args, stop_event, self.config["silent"])


    async def _run_triggered_tagall(self, message: Message, stop_event: StopEvent):
        """
        Runs the tagging logic for triggered activations.
        This runs as a background task and does not create its own cancel button.
        """
        try:
            # Pass an empty string for args; it will fall back to default_message
            await self._perform_tagging(message, "", stop_event, silent=True)
        except asyncio.CancelledError:
            logger.info(f"Triggered TagAll task for chat {utils.get_chat_id(message)} cancelled.")
        finally:
            chat_id = utils.get_chat_id(message)
            if chat_id in self._active_tagall_tasks:
                del self._active_tagall_tasks[chat_id]
            logger.info(f"Triggered TagAll task for chat {utils.get_chat_id(message)} finished/removed from tracking.")
