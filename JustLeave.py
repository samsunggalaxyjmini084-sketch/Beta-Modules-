# meta developer: @hdjsfzbxm
# meta name: Just leave
# meta version: 1.1.3 # Версия обновлена
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
from telethon.tl.types import Message, User # ИСПРАВЛЕНО: Добавлен импорт Message

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
                     "После выхода ничего не пишет (в случае успеха)."
    }

    @loader.sudo
    async def leavecmd(self, message):
        """
        .leave [ID чата] [del]
        Ливает из текущего чата или из указанного по ID.
        Если указан 'del', удаляет сообщение команды перед уходом, иначе оставляет статус выхода.
        После выхода ничего не пишет (в случае успеха).
        """
        args_raw = utils.get_args_raw(message)
        
        target_chat_id = message.chat_id
        original_message_chat_id = message.chat_id # Сохраняем ID оригинального чата для отчета об ошибках
        delete_command = False
        
        # Обработка случая, когда нет контекста чата (например, команда в "Избранном")
        if not message.chat:
            await message.respond(self.strings("no_chat"))
            return

        # Разбираем аргументы: сначала пытаемся получить ID чата
        parts = args_raw.split(maxsplit=1)
        
        if parts:
            potential_chat_id_str = parts[0]
            remaining_args = parts[1] if len(parts) > 1 else None

            try:
                potential_chat_id = int(potential_chat_id_str)
                target_chat_id = potential_chat_id
                if remaining_args and remaining_args.lower() == "del":
                    delete_command = True
            except ValueError:
                # Если первая часть не число, то это не ID чата.
                # Проверяем, является ли вся строка 'del'
                if args_raw.lower() == "del":
                    delete_command = True
                # target_chat_id остается ID текущего чата
        
        # Подготавливаем начальное сообщение статуса
        initial_status_text = ""
        if target_chat_id == message.chat_id:
            initial_status_text = self.strings("leaving_current")
        else:
            initial_status_text = self.strings("leaving_specified").format(chat_id=target_chat_id)

        status_message_to_update = None

        if delete_command:
            await message.delete()
        else:
            try:
                status_message_to_update = await message.edit(initial_status_text)
            except Exception as e:
                logger.warning(f"Не удалось изменить сообщение {message.id} из-за {type(e).__name__}: {e}. Отправляю новое сообщение вместо этого.")
                status_message_to_update = await message.respond(initial_status_text)
        
        await sleep(1)

        try:
            target_entity = await message.client.get_entity(target_chat_id)

            if isinstance(target_entity, User):
                error_msg = self.strings("not_a_group_or_channel").format(chat_id=target_chat_id)
                await self._report_error_status(status_message_to_update, original_message_chat_id, target_chat_id, error_msg, delete_command)
                logger.warning(error_msg)
                return

            await message.client(LeaveChannelRequest(target_chat_id))

            logger.info(f"Успешно покинул чат {target_chat_id}")
            # После успешного выхода никаких дополнительных сообщений не отправляем.

        except UserNotParticipantError:
            error_msg = f"Я не состою в чате <code>{target_chat_id}</code>, чтобы его покинуть."
            await self._report_error_status(status_message_to_update, original_message_chat_id, target_chat_id, error_msg, delete_command)
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

            await self._report_error_status(status_message_to_update, original_message_chat_id, target_chat_id, error_message, delete_command)
            logger.error(f"Не удалось покинуть чат {target_chat_id}: {error_message}")
        except Exception as e:
            logger.exception(f"Произошла непредвиденная ошибка при попытке покинуть чат {target_chat_id}")
            await self._report_error_status(status_message_to_update, original_message_chat_id, target_chat_id, str(e), delete_command)

    async def _report_error_status(self, status_message: Message, original_chat_id: int, target_chat_id: int, error_text: str, delete_command_used: bool):
        """
        Вспомогательная функция для обновления сообщения статуса с ошибкой или отправки нового сообщения при сбое.
        Принимает original_chat_id для надежного ответа в чат, если все остальное не удалось.
        """
        if delete_command_used:
            logger.error(f"Произошла ошибка после команды 'del' для чата {target_chat_id}: {error_text}. Пользователю сообщение не отправлено.")
            return

        full_error_text = self.strings("leave_error").format(chat_id=target_chat_id, error=error_text)
        
        if status_message:
            try:
                await status_message.edit(full_error_text)
            except Exception as e:
                logger.warning(f"Не удалось изменить сообщение статуса {status_message.id} с ошибкой {type(e).__name__}: {e}. Пытаюсь ответить в оригинальный чат.")
                try:
                    await self._client.send_message(original_chat_id, full_error_text)
                except Exception as e2:
                    logger.error(f"Двойной откат не удался, не удалось сообщить об ошибке в чат {original_chat_id}: {e2}", exc_info=True)
        else:
            # Этот блок выполняется, если status_message изначально был None (т.е. message.edit/respond не удалось),
            # и delete_command_used == False.
            try:
                await self._client.send_message(original_chat_id, full_error_text) 
            except Exception as e:
                logger.error(f"Откат на send_message не удался, не удалось сообщить об ошибке в чат {original_chat_id}: {e}", exc_info=True)
