# meta developer: @hdjsfzbxm
# meta name: AutoJoinLink
# meta version: 1.0.2 # Версия обновлена

import logging
import re
import urllib.parse
import asyncio
from telethon.tl.types import Message, MessageEntityTextUrl, MessageEntityUrl
# ИСПРАВЛЕНО: Импортируем модуль errors из telethon
from telethon import errors
from telethon.tl.functions.messages import ImportChatInviteRequest

from .. import loader, utils

logger = logging.getLogger(__name__)

# Вспомогательная функция для разбора ссылок Telegram
def _parse_telegram_link(url: str):
    """
    Разбирает ссылку Telegram (t.me, telegram.me, tg://) и возвращает
    стандартизированную ссылку, такую как "invite:HASH" или "username:USERNAME".
    Возвращает None, если это не распознанная ссылка на чат/канал Telegram.
    """
    parsed_url = urllib.parse.urlparse(url)

    if parsed_url.scheme in ["http", "https"] and parsed_url.hostname in ["t.me", "telegram.me"]:
        path_parts = parsed_url.path.lstrip('/').split('/')
        if path_parts:
            if path_parts[0] == "joinchat" and len(path_parts) > 1:
                return f"invite:{path_parts[1]}"
            elif path_parts[0]:
                if re.fullmatch(r"[a-zA-Z0-9_]+", path_parts[0]):
                    return f"username:{path_parts[0]}"
    elif parsed_url.scheme == "tg":
        if parsed_url.hostname == "join":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            invite_hash = query_params.get('invite', [None])[0]
            if invite_hash:
                return f"invite:{invite_hash}"
        elif parsed_url.hostname == "resolve":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            domain = query_params.get('domain', [None])[0]
            if domain:
                if re.fullmatch(r"[a-zA-Z0-9_]+", domain):
                    return f"username:{domain}"
    return None


@loader.tds
class AutoJoinLinkMod(loader.Module):
    """
    Модуль для автоматического входа в чаты/каналы Telegram по ссылкам,
    размещенным в определенных чатах.
    """

    strings = {
        "name": "AutoJoinLink",
        "_cls_doc": "Автоматически заходит по ссылкам на чаты/каналы Telegram.",
        "config_watch_chats_doc": "Список ID чатов, где модуль будет отслеживать ссылки. Если список пуст, отслеживание ведется во всех чатах.",
        "config_status": "<b><emoji document_id=5875291072225087249>📊</emoji> Статус AutoJoinLink:</b>\n"
                         "Статус: {}\n"
                         "Чаты для отслеживания ссылок: {}\n",
        "enabled": "✅ AutoJoinLink включен.",
        "disabled": "❌ AutoJoinLink выключен.",
        "watch_chats_display_all": "Все чаты",
        "watch_chats_display_ids": "<code>{}</code>",
        "link_found_prefix": "🔗 Обнаружена ссылка на чат/канал: ",
        "joining_chat": "➡️ Пытаюсь присоединиться к чату/каналу по ссылке: <code>{link_ref}</code>",
        "join_success": "✅ Успешно присоединился к: <code>{link_ref}</code>",
        "already_participant": "ℹ️ Уже являюсь участником чата/канала по ссылке: <code>{link_ref}</code>",
        "invite_expired_invalid": "❌ Ссылка устарела или недействительна: <code>{link_ref}</code>",
        "flood_wait": "⏳ Превышен лимит запросов, попробуйте позже. Ссылка: <code>{link_ref}</code> (Ожидайте {seconds}с)",
        "private_channel_error": "❌ Не удалось присоединиться к приватному чату/каналу по ссылке: <code>{link_ref}</code>. Возможно, нужна дополнительная инвайт-ссылка или это приватный канал без публичной ссылки.",
        "peer_invalid_error": "❌ Неверный Peer ID или недействительное имя пользователя для ссылки: <code>{link_ref}</code>.",
        "other_join_error": "❌ Неизвестная ошибка при присоединении к <code>{link_ref}</code>: <code>{error}</code>",
        "no_links_found": "ℹ️ В сообщении не найдено ссылок на Telegram чаты/каналы.",
        "error_parsing_link": "❌ Ошибка при разборе ссылки <code>{}</code>: {}",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "enabled",
                False,
                lambda: "Включен ли модуль автоматического входа в чаты по ссылкам",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "watch_chat_ids",
                [],
                lambda: self.strings("config_watch_chats_doc"),
                validator=loader.validators.Series(loader.validators.Integer())
            ),
        )

    async def client_ready(self, client, _):
        self._client = client
        self._self_id = (await self._client.get_me()).id


    @loader.command(ru_doc="Включить модуль AutoJoinLink")
    async def ajlon(self, message: Message):
        """Включить модуль AutoJoinLink"""
        self.config["enabled"] = True
        await utils.answer(message, self.strings("enabled"))

    @loader.command(ru_doc="Выключить модуль AutoJoinLink")
    async def ajloff(self, message: Message):
        """Выключить модуль AutoJoinLink"""
        self.config["enabled"] = False
        await utils.answer(message, self.strings("disabled"))

    @loader.command(ru_doc="Показать статус модуля AutoJoinLink")
    async def ajlstatus(self, message: Message):
        """Показать статус модуля AutoJoinLink"""
        status_text = "🟢 Включен" if self.config["enabled"] else "🔴 Выключен"
        watch_chats_display = self.strings("watch_chats_display_all")
        if self.config["watch_chat_ids"]:
            watch_chats_display = self.strings("watch_chats_display_ids").format(
                ", ".join(map(str, self.config["watch_chat_ids"]))
            )
        
        await utils.answer(message, self.strings("config_status").format(
            status_text,
            watch_chats_display
        ))

    @loader.watcher(incoming=True, outgoing=False)
    async def watcher(self, message: Message):
        """Слушает входящие сообщения на наличие ссылок на чаты/каналы."""
        if not self.config["enabled"]:
            return

        if message.sender_id == self._self_id:
            return

        if self.config["watch_chat_ids"] and message.chat_id not in self.config["watch_chat_ids"]:
            return

        if not message.text:
            return

        unique_chat_refs = set()

        if message.entities:
            for entity in message.entities:
                url_text = None
                if isinstance(entity, MessageEntityUrl):
                    url_text = message.text[entity.offset:entity.offset + entity.length]
                elif isinstance(entity, MessageEntityTextUrl):
                    url_text = entity.url

                if url_text:
                    try:
                        ref = _parse_telegram_link(url_text)
                        if ref:
                            unique_chat_refs.add(ref)
                    except Exception as e:
                        logger.warning(self.strings("error_parsing_link").format(url_text, e))


        telegram_link_regex = r"(?:https?://)?(?:t\.me|telegram\.me)/(?:joinchat/([a-zA-Z0-9_-]+)|([a-zA-Z0-9_]+))"
        tg_scheme_regex = r"tg://(?:join\?invite=([a-zA-Z0-9_-]+)|resolve\?domain=([a-zA-Z0-9_]+))"

        for match in re.finditer(telegram_link_regex, message.text, re.IGNORECASE):
            invite_hash = match.group(1)
            username = match.group(2)
            if invite_hash:
                unique_chat_refs.add(f"invite:{invite_hash}")
            elif username:
                unique_chat_refs.add(f"username:{username}")
        
        for match in re.finditer(tg_scheme_regex, message.text, re.IGNORECASE):
            invite_hash = match.group(1)
            username = match.group(2)
            if invite_hash:
                unique_chat_refs.add(f"invite:{invite_hash}")
            elif username:
                unique_chat_refs.add(f"username:{username}")

        if not unique_chat_refs:
            logger.debug(f"AutoJoinLink: В сообщении {message.id} в чате {message.chat_id} не найдено ссылок на чаты Telegram.")
            return

        response_messages = []
        for ref in unique_chat_refs:
            display_link_ref = ref
            if ref.startswith("invite:"):
                display_link_ref = f"t.me/joinchat/{ref.split(':')[1]}"
            elif ref.startswith("username:"):
                display_link_ref = f"t.me/{ref.split(':')[1]}"

            response_messages.append(self.strings("link_found_prefix") + f"<code>{display_link_ref}</code>")
            
            logger.info(self.strings("joining_chat").format(link_ref=display_link_ref))
            
            try:
                if ref.startswith("invite:"):
                    invite_hash = ref.split(":")[1]
                    await self._client(ImportChatInviteRequest(invite_hash))
                    response_messages.append(self.strings("join_success").format(link_ref=display_link_ref))
                elif ref.startswith("username:"):
                    username = ref.split(":")[1]
                    if not username.startswith('@'):
                        username = '@' + username
                    await self._client.join_chat(username)
                    response_messages.append(self.strings("join_success").format(link_ref=display_link_ref))
                else:
                    response_messages.append(self.strings("other_join_error").format(link_ref=display_link_ref, error="Неизвестный формат ссылки"))

            except errors.UserAlreadyParticipantError: # ИСПРАВЛЕНО: использование errors.
                response_messages.append(self.strings("already_participant").format(link_ref=display_link_ref))
            except (errors.InviteHashExpiredError, errors.InviteHashInvalidError): # ИСПРАВЛЕНО: использование errors.
                response_messages.append(self.strings("invite_expired_invalid").format(link_ref=display_link_ref))
            except errors.FloodWaitError as e: # ИСПРАВЛЕНО: использование errors.
                response_messages.append(self.strings("flood_wait").format(link_ref=display_link_ref, seconds=e.seconds))
            except errors.ChannelPrivateError: # ИСПРАВЛЕНО: использование errors.
                response_messages.append(self.strings("private_channel_error").format(link_ref=display_link_ref))
            except errors.PeerInvalidError: # ИСПРАВЛЕНО: использование errors.
                response_messages.append(self.strings("peer_invalid_error").format(link_ref=display_link_ref))
            except Exception as e:
                logger.error(f"AutoJoinLink: Ошибка при присоединении по ссылке {ref}: {e}", exc_info=True)
                response_messages.append(self.strings("other_join_error").format(link_ref=display_link_ref, error=e))
            
            await asyncio.sleep(1) 
        
        if response_messages:
            await self._client.send_message(message.chat_id, "\n".join(response_messages))
