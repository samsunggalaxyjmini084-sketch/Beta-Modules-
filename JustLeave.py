# meta developer: @yourhandle
# meta name: Just leave
# meta version: 1.1.1 # Версия обновлена
import logging
from .. import loader, utils
from asyncio import sleep
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.errors.rpcerrorlist import (
    ChatAdminRequiredError,
    ChannelPrivateError,
    UserIsBlockedError,
    PeerIdInvalidError,
    ChatIdInvalidError,
    UserNotParticipantError,
)
from telethon.tl.types import User # Добавлен импорт User для проверки типа чата

logger = logging.getLogger(__name__)


@loader.tds
class LeaveMod(loader.Module):
    strings = {
        "name": "Just leave",
        "_cls_doc": "Модуль для выхода из текущего или указанного по ID чата, без последующих сообщений.",
        "no_chat": "<b>Невозможно выполнить команду: нет текущего чата.</b>",
        "leaving_current": "<b>Выхожу из текущего чата...</b>",
        "leaving_specified": "<b>Выхожу из чата <code>{chat_id}</code>...</b>",
        "leave_error": "❌ Не удалось покинуть чат <code>{chat_id}</code>: {error}",
        "chat_not_found": "❌ Чат <code>{chat_id}</code> не найден или недоступен.",
        "not_a_group_or_channel": "❌ Чат <code>{chat_id}</code> является личным чатом с пользователем или ботом. "
                                  "Для таких чатов нет команды 'покинуть'.",
        "help_text": ".leave [ID чата] [del]\n"
                     "Ливает из текущего чата или из указанного по ID.\n"
                     "Если указан 'del', удаляет сообщение команды перед уходом, иначе оставляет статус выхода."
                     "После выхода ничего не пишет."
    }

    @loader.sudo
    async def leavecmd(self, message):
        """
        .leave [ID чата] [del]
        Ливает из текущего чата или из указанного по ID.
        Если указан 'del', удаляет сообщение команды перед уходом, иначе оставляет статус выхода.
        После выхода ничего не пишет.
        """
        args_raw = utils.get_args_raw(message)
        
        target_chat_id = message.chat_id # По умолчанию выходим из текущего чата
        delete_command = False
        
        if not message.chat:
            await message.edit(self.strings("no_chat"))
            return

        # Разбираем аргументы: сначала пытаемся получить ID чата
        parts = args_raw.split(maxsplit=1)
        
        if parts:
            potential_chat_id_str = parts[0]
            remaining_args = parts[1] if len(parts) > 1 else None

            try:
                potential_chat_id = int(potential_chat_id_str)
                # Если это действительное целое число, используем его как ID целевого чата
                target_chat_id = potential_chat_id
                # Проверяем оставшиеся аргументы только на 'del'
                if remaining_args and remaining_args.lower() == "del":
                    delete_command = True
                
            except ValueError:
                # Если первая часть не число, то это не ID чата.
                # Проверяем, является ли вся строка 'del'
                if args_raw.lower() == "del":
                    delete_command = True
                # target_chat_id остается ID текущего чата
        
        # Первоначальное сообщение для отображения статуса перед выходом
        if delete_command:
            await message.delete()
        else:
            if target_chat_id == message.chat_id:
                await message.edit(self.strings("leaving_current"))
            else:
                await message.edit(self.strings("leaving_specified").format(chat_id=target_chat_id))
        
        await sleep(1) # Небольшая задержка перед выходом

        try:
            target_entity = await message.client.get_entity(target_chat_id)

            if isinstance(target_entity, User):
                # Нельзя "покинуть" личный чат с пользователем.
                error_msg = self.strings("not_a_group_or_channel").format(chat_id=target_chat_id)
                if not delete_command:
                    # Если команда не была удалена, отвечаем с ошибкой
                    if target_chat_id == message.chat_id: # Если пытались выйти из текущего личного чата
                        await message.edit(self.strings("leave_error").format(chat_id=target_chat_id, error=error_msg))
                    else: # Если пытались выйти из другого личного чата
                        await message.respond(self.strings("leave_error").format(chat_id=target_chat_id, error=error_msg))
                logger.warning(error_msg)
                return

            # Выполняем запрос на выход из чата
            await message.client(LeaveChannelRequest(target_chat_id))

            # Если успешно покинули, никаких сообщений больше не отправляем, как запрошено.
            logger.info(f"Successfully left chat {target_chat_id}")

        except UserNotParticipantError:
            error_msg = f"Я не состою в чате <code>{target_chat_id}</code>, чтобы его покинуть."
            if not delete_command:
                if target_chat_id == message.chat_id:
                    await message.edit(self.strings("leave_error").format(chat_id=target_chat_id, error=error_msg))
                else:
                    await message.respond(self.strings("leave_error").format(chat_id=target_chat_id, error=error_msg))
            logger.warning(error_msg)
        except (ChatAdminRequiredError, ChannelPrivateError, UserIsBlockedError, PeerIdInvalidError, ChatIdInvalidError, ValueError) as e:
            error_message = str(e)
            if isinstance(e, ChatAdminRequiredError):
                error_message = "У меня нет прав администратора для выхода из этого чата."
            elif isinstance(e, ChannelPrivateError):
                error_message = "Это приватный канал, я не могу из него выйти таким образом."
            elif isinstance(e, UserIsBlockedError):
                error_message = "Пользователь заблокирован, невозможно выполнить операцию."
            elif isinstance(e, (PeerIdInvalidError, ChatIdInvalidError, ValueError)):
                 error_message = "Указан неверный или недоступный ID чата."

            if not delete_command:
                if target_chat_id == message.chat_id:
                    await message.edit(self.strings("leave_error").format(chat_id=target_chat_id, error=error_message))
                else:
                    await message.respond(self.strings("leave_error").format(chat_id=target_chat_id, error=error_message))
            logger.error(f"Failed to leave chat {target_chat_id}: {error_message}")
        except Exception as e:
            logger.exception(f"An unexpected error occurred while trying to leave chat {target_chat_id}")
            if not delete_command:
                if target_chat_id == message.chat_id:
                    await message.edit(self.strings("leave_error").format(chat_id=target_chat_id, error=str(e)))
                else:
                    await message.respond(self.strings("leave_error").format(chat_id=target_chat_id, error=str(e)))
