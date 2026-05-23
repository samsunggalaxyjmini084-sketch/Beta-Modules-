# meta developer: @hdjsfzbxm
# meta name: PinChat 
# meta version: 1.0.5 # Версия обновлена: убрано сообщение о задержке
import logging
import asyncio 
from telethon.tl.types import Message
from telethon.errors import RPCError
from telethon import functions
from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class PinChatMod(loader.Module): 
    """Модуль для закрепления (пиннинга) чатов в вашем списке чатов по их ID. Поддерживает настраиваемую задержку перед выполнением действия.""" 

    strings = {
        "name": "PinChat", 
        "_cls_doc": "Модуль для закрепления (пиннинга) чатов в вашем списке чатов по их ID. Поддерживает настраиваемую задержку перед выполнением действия.", 
        "no_args": "⚠️ Укажите ID чата для закрепления. Пример: <code>.pinchat -1001234567890</code>", 
        "invalid_chat_id": "❌ Неверный ID чата. Укажите числовой ID.",
        "chat_not_found": "❌ Чат с ID <code>{chat_id}</code> не найден или недоступен.",
        "pin_success": "✅ Чат <code>{chat_id}</code> успешно закреплен в вашем списке чатов.",
        "pin_already_pinned": "ℹ️ Чат <code>{chat_id}</code> уже закреплен в вашем списке чатов.",
        "pin_fail": "❌ Не удалось закрепить чат <code>{chat_id}</code>: {error}",
        "unpin_no_args": "⚠️ Укажите ID чата для открепления. Пример: <code>.unpinchat -1001234567890</code>", 
        "unpin_success": "✅ Чат <code>{chat_id}</code> успешно откреплен из вашего списка чатов.",
        "unpin_not_pinned": "ℹ️ Чат <code>{chat_id}</code> не закреплен в вашем списке чатов.",
        "unpin_fail": "❌ Не удалось открепить чат <code>{chat_id}</code>: {error}",
        # "delay_message": "⏳ Ожидание {delay} секунд перед попыткой {action_text} чата <code>{chat_id}</code>..." # Эта строка удалена/закомментирована
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "action_delay",
                0.0, # По умолчанию 0 секунд (без задержки)
                lambda: "Задержка в секундах перед выполнением действия закрепления/открепления чата. Если 0, то без задержки.",
                validator=loader.validators.Float(minimum=0.0, maximum=10.0)
            )
        )

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

        action_text_verb = "закрепить" if pinned else "открепить"

        # --- Применение задержки ---
        delay = self.config["action_delay"]
        if delay > 0:
            logger.debug(f"PinChat: Ожидание {delay} секунд перед попыткой {action_text_verb} чата {target_chat_id}...")
            await asyncio.sleep(delay)
        # --- Конец применения задержки ---

        # Это сообщение останется, так как оно информирует о начале попытки после задержки
        await utils.answer(message, f"⏳ Пытаюсь {action_text_verb} чат <code>{target_chat_id}</code> в вашем списке чатов...")

        try:
            # get_entity может вернуть Channel, User, Chat, но ToggleDialogPin ожидает InputPeer
            # Для надежности, получаем InputPeer из dialog.entity
            entity = await self._client.get_entity(target_chat_id)
        except (ValueError, TypeError):
            logger.error(f"PinChat: Чат с ID {target_chat_id} не найден.") 
            await utils.answer(message, self.strings("chat_not_found").format(chat_id=target_chat_id))
            return
        except Exception as e:
            logger.error(f"PinChat: Ошибка при получении сущности чата {target_chat_id}: {e}", exc_info=True) 
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
                await utils.answer(message, self.strings("chat_not_found").format(chat_id=target_chat_id))
                return

            is_currently_pinned = target_dialog.pinned

            if pinned: # Закрепляем
                if is_currently_pinned:
                    await utils.answer(message, self.strings("pin_already_pinned").format(chat_id=target_chat_id))
                    return
                # Используем низкоуровневый RPC-вызов для закрепления
                await self._client(functions.messages.ToggleDialogPinRequest(
                    peer=target_dialog.entity,
                    pinned=True
                ))
                await utils.answer(message, self.strings("pin_success").format(chat_id=target_chat_id))
                logger.info(f"PinChat: Чат {target_chat_id} успешно закреплен.") 
            else: # Открепляем
                if not is_currently_pinned:
                    await utils.answer(message, self.strings("unpin_not_pinned").format(chat_id=target_chat_id))
                    return
                # Используем низкоуровневый RPC-вызов для открепления
                await self._client(functions.messages.ToggleDialogPinRequest(
                    peer=target_dialog.entity,
                    pinned=False
                ))
                await utils.answer(message, self.strings("unpin_success").format(chat_id=target_chat_id))
                logger.info(f"PinChat: Чат {target_chat_id} успешно откреплен.") 

        except RPCError as e:
            logger.error(f"PinChat: Ошибка Telethon RPC при {action_text_verb} чата {target_chat_id}: {e}", exc_info=True) 
            await utils.answer(message, self.strings("pin_fail").format(chat_id=target_chat_id, error=e) if pinned else self.strings("unpin_fail").format(chat_id=target_chat_id, error=e))
        except Exception as e:
            logger.exception(f"PinChat: Неожиданная ошибка при {action_text_verb} чата {target_chat_id}: {e}") 
            await utils.answer(message, self.strings("pin_fail").format(chat_id=target_chat_id, error=e) if pinned else self.strings("unpin_fail").format(chat_id=target_chat_id, error=e))


    @loader.command(ru_doc="Закрепить чат в вашем списке чатов по его ID.")
    async def pinchat(self, message: Message): 
        """
        Закрепляет чат в вашем списке чатов.
        Использование: .pinchat <chat_id>
        Пример: .pinchat -1001234567890
        """
        await self._process_pin_unpin(message, True)

    @loader.command(ru_doc="Открепить чат из вашего списка чатов по его ID.")
    async def unpinchat(self, message: Message): 
        """
        Открепляет чат из вашего списка чатов.
        Использование: .unpinchat <chat_id>
        Пример: .unpinchat -1001234567890
        """
        await self._process_pin_unpin(message, False)
