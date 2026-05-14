# meta developer: @yourhandle
# meta name: PinChatList
# meta version: 1.0.1 # Версия обновлена
import logging
from telethon.tl.types import Message
from telethon.errors import RPCError
from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class PinChatListMod(loader.Module):
    """Модуль для закрепления (пиннинга) чатов в вашем списке чатов по их ID."""

    strings = {
        "name": "PinChatList",
        "_cls_doc": "Модуль для закрепления (пиннинга) чатов в вашем списке чатов по их ID.",
        "no_args": "⚠️ Укажите ID чата для закрепления. Пример: <code>.pinchatlist -1001234567890</code>",
        "invalid_chat_id": "❌ Неверный ID чата. Укажите числовой ID.",
        "chat_not_found": "❌ Чат с ID <code>{chat_id}</code> не найден или недоступен.",
        "pin_success": "✅ Чат <code>{chat_id}</code> успешно закреплен в вашем списке чатов.",
        "pin_already_pinned": "ℹ️ Чат <code>{chat_id}</code> уже закреплен в вашем списке чатов.",
        "pin_fail": "❌ Не удалось закрепить чат <code>{chat_id}</code>: {error}",
        "unpin_no_args": "⚠️ Укажите ID чата для открепления. Пример: <code>.unpinchatlist -1001234567890</code>",
        "unpin_success": "✅ Чат <code>{chat_id}</code> успешно откреплен из вашего списка чатов.",
        "unpin_not_pinned": "ℹ️ Чат <code>{chat_id}</code> не закреплен в вашем списке чатов.",
        "unpin_fail": "❌ Не удалось открепить чат <code>{chat_id}</code>: {error}",
    }

    def __init__(self):
        self.config = loader.ModuleConfig() # Настройки пока не требуются

    async def client_ready(self, client, _):
        self._client = client

    async def _process_pin_unpin(self, message: Message, pinned: bool):
        """Вспомогательная функция для логики закрепления/открепления чатов."""
        args = utils.get_args_raw(message)
        
        if not args:
            await utils.answer(message, self.strings("no_args") if pinned else self.strings("unpin_no_args"))
            return

        try:
            target_chat_id = int(args)
        except ValueError:
            await utils.answer(message, self.strings("invalid_chat_id"))
            return

        action_text = "закрепить" if pinned else "открепить"
        await utils.answer(message, f"⏳ Пытаюсь {action_text} чат <code>{target_chat_id}</code> в вашем списке чатов...")

        try:
            entity = await self._client.get_entity(target_chat_id)
        except (ValueError, TypeError):
            logger.error(f"PinChatList: Чат с ID {target_chat_id} не найден.")
            await utils.answer(message, self.strings("chat_not_found").format(chat_id=target_chat_id))
            return
        except Exception as e:
            logger.error(f"PinChatList: Ошибка при получении сущности чата {target_chat_id}: {e}", exc_info=True)
            await utils.answer(message, self.strings("chat_not_found").format(chat_id=target_chat_id))
            return

        try:
            # Ищем диалог, чтобы проверить его текущий статус закрепления
            target_dialog = None
            async for dialog in self._client.iter_dialogs():
                if dialog.id == target_chat_id:
                    target_dialog = dialog
                    break
            
            if not target_dialog:
                # Если диалог не найден в iter_dialogs, это означает, что чат либо не существует, либо
                # с ним никогда не было активной переписки и он не отображается в списке диалогов.
                # В этом случае get_entity уже должен был отработать с ошибкой, но если entity
                # был получен (например, по username, но диалог неактивен), то здесь нужно сообщить.
                await utils.answer(message, self.strings("chat_not_found").format(chat_id=target_chat_id))
                return

            is_currently_pinned = target_dialog.pinned

            if pinned: # Закрепляем
                if is_currently_pinned:
                    await utils.answer(message, self.strings("pin_already_pinned").format(chat_id=target_chat_id))
                    return
                await self._client.pin_peer(entity, pinned=True)
                await utils.answer(message, self.strings("pin_success").format(chat_id=target_chat_id))
                logger.info(f"PinChatList: Чат {target_chat_id} успешно закреплен.")
            else: # Открепляем
                if not is_currently_pinned:
                    await utils.answer(message, self.strings("unpin_not_pinned").format(chat_id=target_chat_id))
                    return
                await self._client.pin_peer(entity, pinned=False)
                await utils.answer(message, self.strings("unpin_success").format(chat_id=target_chat_id))
                logger.info(f"PinChatList: Чат {target_chat_id} успешно откреплен.")

        except RPCError as e:
            logger.error(f"PinChatList: Ошибка Telethon RPC при {action_text} чата {target_chat_id}: {e}", exc_info=True)
            await utils.answer(message, self.strings("pin_fail").format(chat_id=target_chat_id, error=e) if pinned else self.strings("unpin_fail").format(chat_id=target_chat_id, error=e))
        except Exception as e:
            logger.exception(f"PinChatList: Неожиданная ошибка при {action_text} чата {target_chat_id}: {e}")
            await utils.answer(message, self.strings("pin_fail").format(chat_id=target_chat_id, error=e) if pinned else self.strings("unpin_fail").format(chat_id=target_chat_id, error=e))


    @loader.command(ru_doc="Закрепить чат в вашем списке чатов по его ID.")
    async def pinchatlist(self, message: Message):
        """
        Закрепляет чат в вашем списке чатов.
        Использование: .pinchatlist <chat_id>
        Пример: .pinchatlist -1001234567890
        """
        await self._process_pin_unpin(message, True)

    @loader.command(ru_doc="Открепить чат из вашего списка чатов по его ID.")
    async def unpinchatlist(self, message: Message):
        """
        Открепляет чат из вашего списка чатов.
        Использование: .unpinchatlist <chat_id>
        Пример: .unpinchatlist -1001234567890
        """
        await self._process_pin_unpin(message, False)
