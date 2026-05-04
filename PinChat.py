# meta developer: @yourhandle
# meta name: PinChat
# meta version: 1.0.0
import logging
from telethon.tl.functions.messages import UpdatePeerPinnedRequest # <-- Эта строка использует стандартную библиотеку Telethon, а не herokutl.
from telethon.tl.types import Message
from telethon.errors import PeerIdInvalidError, RPCError
from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class PinChatMod(loader.Module):
    """
    Модуль для закрепления и открепления чатов в вашем списке чатов.
    Используйте .pchat [ID_чата] для закрепления или .pchat -u [ID_чата] для открепления.
    """

    strings = {
        "name": "PinChat",
        "_cls_doc": "Модуль для закрепления и открепления чатов в вашем списке чатов.",
        "pin_success": "✅ Чат <b>{}</b> успешно <b>закреплен</b>.",
        "unpin_success": "✅ Чат <b>{}</b> успешно <b>откреплен</b>.",
        "already_pinned": "⚠️ Чат <b>{}</b> уже <b>закреплен</b>.",
        "not_pinned": "⚠️ Чат <b>{}</b> не <b>закреплен</b>.",
        "no_chat_specified": "⚠️ Укажите ID чата, ответьте на сообщение в чате, который хотите закрепить/открепить, или используйте команду в целевом чате.",
        "invalid_chat_id": "❌ Неверный ID чата или не удалось найти чат по ID: <code>{}</code>.",
        "error_action": "❌ Ошибка при выполнении действия с чатом <b>{}</b>: <code>{}</code>",
        "help_text": """<emoji document_id=5931415565955503486>🤖</emoji> <b>PinChat</b> - Помощь
        
        <emoji document_id=5935847413859225147>📌</emoji> <b>Команды:</b>
        <code>.pchat</code> [ID_чата] - Закрепить текущий чат или чат по ID.
        <code>.pchat -u</code> [ID_чата] - Открепить текущий чат или чат по ID.
        
        <emoji document_id=5877260593901971030>⚙</emoji> <b>Как работает:</b>
        Используйте команду <code>.pchat</code> в любом чате, чтобы закрепить его.
        Используйте <code>.pchat &lt;ID_чата&gt;</code>, чтобы закрепить чат по его ID.
        Для открепления используйте <code>.pchat -u</code> (открепить текущий чат) или <code>.pchat -u &lt;ID_чата&gt;</code> (открепить чат по ID).
        Вы можете получить ID чата, переслав сообщение из него в бота @ShowJsonBot или @userinfobot, или с помощью модуля .id.
        При указании ID для личных чатов с пользователями или ботами, используйте их обычный ID.
        """
    }

    async def client_ready(self, client, _):
        self._client = client

    @loader.command(ru_doc="Закрепляет или открепляет чат в списке чатов. Используйте .pchat -u [ID] для открепления.")
    async def pchatcmd(self, message: Message):
        """Закрепляет или открепляет чат в списке чатов."""
        args = utils.get_args_raw(message).split(maxsplit=1)
        
        target_entity = None
        entity_name = "неизвестный чат"
        pin_action = True  # По умолчанию: закрепить

        chat_id_str = None

        if args:
            if args[0].lower() == "-u":
                pin_action = False
                if len(args) > 1:  # .pchat -u <ID>
                    chat_id_str = args[1]
                else:  # .pchat -u (текущий чат)
                    target_entity = message.chat
            else:  # .pchat <ID>
                chat_id_str = args[0]
        else:  # .pchat (текущий чат)
            target_entity = message.chat

        if chat_id_str:
            try:
                target_entity = await self._client.get_entity(int(chat_id_str))
            except ValueError:
                await utils.answer(message, self.strings("invalid_chat_id").format(chat_id_str))
                return
            except Exception as e:
                logger.error(f"Ошибка при получении сущности для ID {chat_id_str}: {e}")
                await utils.answer(message, self.strings("invalid_chat_id").format(chat_id_str))
                return

        if not target_entity:
            # Если не удалось определить entity по аргументам, ищем в ответе
            if message.is_reply:
                reply_msg = await message.get_reply_message()
                target_entity = await reply_msg.get_chat() or await reply_msg.get_sender()
            
            if not target_entity:
                await utils.answer(message, self.strings("no_chat_specified"))
                return
        
        try:
            entity_name = await utils.get_chat_title(target_entity)
            
            # Получаем все диалоги, чтобы узнать текущий статус закрепления
            dialogs = await self._client.get_dialogs()
            target_dialog = next((d for d in dialogs if d.id == target_entity.id), None)

            current_pin_status = target_dialog.pinned if target_dialog else False

            if pin_action:  # Пользователь хочет закрепить
                if current_pin_status:
                    await utils.answer(message, self.strings("already_pinned").format(entity_name))
                    return
                await self._client(UpdatePeerPinnedRequest(peer=target_entity, pinned=True))
                await utils.answer(message, self.strings("pin_success").format(entity_name))
            else:  # Пользователь хочет открепить
                if not current_pin_status:
                    await utils.answer(message, self.strings("not_pinned").format(entity_name))
                    return
                await self._client(UpdatePeerPinnedRequest(peer=target_entity, pinned=False))
                await utils.answer(message, self.strings("unpin_success").format(entity_name))

        except PeerIdInvalidError:
            await utils.answer(message, self.strings("invalid_chat_id").format(chat_id_str if chat_id_str else "N/A"))
        except RPCError as e:
            logger.error(f"Ошибка RPC при закреплении/откреплении чата {entity_name} ({getattr(target_entity, 'id', 'N/A')}): {e}")
            await utils.answer(message, self.strings("error_action").format(entity_name, e))
        except Exception as e:
            logger.exception(f"Неожиданная ошибка в pchatcmd для {entity_name} ({getattr(target_entity, 'id', 'N/A')}): {e}")
            await utils.answer(message, self.strings("error_action").format(entity_name, e))
