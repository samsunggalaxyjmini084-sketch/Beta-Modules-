# meta developer: @yourhandle
# meta name: PinChat
# meta version: 1.0.5 # Обновлена версия модуля для обхода специфичной ошибки herokutl
import logging
import re
from telethon.tl.types import Message, User, Channel, Chat
from telethon.errors import PeerIdInvalidError, RPCError, TLMessageError # Добавлен TLMessageError
from telethon import functions # <- Импортируем общий объект functions
from .. import loader, utils # <- utils все еще нужно для utils.answer

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

    def _get_entity_name(self, entity):
        """Вспомогательная функция для получения читаемого имени сущности Telethon."""
        if isinstance(entity, User):
            if entity.first_name and entity.last_name:
                return f"{entity.first_name} {entity.last_name}"
            if entity.first_name:
                return entity.first_name
            if entity.username:
                return f"@{entity.username}"
            return f"User {entity.id}"
        elif isinstance(entity, (Channel, Chat)):
            return entity.title
        return f"Entity {entity.id}"

    @loader.command(ru_doc="Закрепляет или открепляет чат в списке чатов. Используйте .pchat -u [ID] для открепления.")
    async def pchatcmd(self, message: Message):
        """Закрепляет или открепляет чат в списке чатов."""
        
        # Ручной парсинг аргументов
        cmd_prefix = message.text.split(None, 1)[0]
        raw_args_text = message.text[len(cmd_prefix):].strip()
        args = re.split(r'\s+', raw_args_text, maxsplit=1)

        target_entity = None
        pin_action = True
        chat_id_str = None

        if args and args[0]:
            if args[0].lower() == "-u":
                pin_action = False
                if len(args) > 1 and args[1]:
                    chat_id_str = args[1]
                else:
                    target_entity = message.chat
            else:
                chat_id_str = args[0]
        else:
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
            if message.is_reply:
                reply_msg = await message.get_reply_message()
                target_entity = await reply_msg.get_chat() or await reply_msg.get_sender()
            
            if not target_entity:
                await utils.answer(message, self.strings("no_chat_specified"))
                return
        
        try:
            entity_name = self._get_entity_name(target_entity)
            input_peer = await self._client.get_input_entity(target_entity)

            dialogs = await self._client.get_dialogs()
            target_dialog_from_dialogs = next((d for d in dialogs if d.id == target_entity.id), None)
            current_pin_status = target_dialog_from_dialogs.pinned if target_dialog_from_dialogs else False

            rpc_call_successful = False
            
            if pin_action:
                if current_pin_status:
                    await utils.answer(message, self.strings("already_pinned").format(entity_name))
                    return
            else:
                if not current_pin_status:
                    await utils.answer(message, self.strings("not_pinned").format(entity_name))
                    return

            try:
                # Попытка 1: Используем стандартное имя запроса Telethon (UpdatePeerPinnedRequest)
                await self._client(functions.messages.UpdatePeerPinnedRequest(
                    peer=input_peer, pinned=pin_action
                ))
                rpc_call_successful = True
            except AttributeError as e:
                logger.warning(
                    f"PinChat: Стандартный вызов UpdatePeerPinnedRequest не удался ({e}). "
                    "Попытка использовать альтернативное имя 'UpdatePeerPinned'. "
                    "Это может указывать на нестандартный форк Telethon (например, herokutl)."
                )
                try:
                    # Попытка 2: Используем альтернативное имя запроса (UpdatePeerPinned)
                    # Это обходной путь для нестандартных форков, если они переименовали RPC-вызов
                    alternative_rpc_call = getattr(functions.messages, 'UpdatePeerPinned', None)
                    if alternative_rpc_call:
                        await self._client(alternative_rpc_call(peer=input_peer, pinned=pin_action))
                        rpc_call_successful = True
                    else:
                        logger.error(
                            "PinChat: Ни UpdatePeerPinnedRequest, ни UpdatePeerPinned не найдены "
                            "в functions.messages. Ваша среда Telethon/Herokutl может быть несовместима."
                        )
                        raise e # Перебрасываем исходную ошибку, если альтернатива не найдена
                except AttributeError as e_alt:
                    logger.error(f"PinChat: Альтернативный вызов UpdatePeerPinned также не удался ({e_alt}).")
                    raise e # Перебрасываем исходную ошибку

            if rpc_call_successful:
                if pin_action:
                    await utils.answer(message, self.strings("pin_success").format(entity_name))
                else:
                    await utils.answer(message, self.strings("unpin_success").format(entity_name))
            else:
                # Этот блок должен быть достигнут только в случае, если rpc_call_successful остается False
                # после всех попыток, но исключение не было перехвачено.
                # Теоретически не должно быть достигнуто, так как исключения должны быть перехвачены.
                await utils.answer(message, self.strings("error_action").format(entity_name, "Не удалось выполнить действие (неизвестная ошибка)."))

        except PeerIdInvalidError:
            await utils.answer(message, self.strings("invalid_chat_id").format(chat_id_str if chat_id_str else "N/A"))
        except (RPCError, TLMessageError) as e:
            logger.error(f"Ошибка RPC при закреплении/откреплении чата {entity_name} ({getattr(target_entity, 'id', 'N/A')}): {e}")
            await utils.answer(message, self.strings("error_action").format(entity_name, e))
        except Exception as e:
            logger.exception(f"Неожиданная ошибка в pchatcmd для {entity_name} ({getattr(target_entity, 'id', 'N/A')}): {e}")
            await utils.answer(message, self.strings("error_action").format(entity_name, e))
