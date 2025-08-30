# meta developer: @Androfon_AI
# meta name: Управление папками
# meta version: 1.0.1

from telethon import TelegramClient, events
from telethon.tl.functions.messages import UpdateDialogFilterRequest
from telethon.tl.types import DialogFilter, InputDialogPeer

class FolderManager:
    def __init__(self, client: TelegramClient):
        self.client = client

    async def create_folder(self, name: str):
        filters = await self.client.get_dialog_filters()
        new_filter = DialogFilter(
            id=len(filters) + 1,
            title=name,
            pinned_peers=[],
            include_peers=[],
            exclude_peers=[],
            contacts=False,
            non_contacts=False,
            groups=False,
            broadcasts=False,
            bots=False,
            exclude_muted=False,
            exclude_read=False,
            exclude_archived=False
        )
        await self.client(UpdateDialogFilterRequest(id=new_filter.id, filter=new_filter))

    async def delete_folder(self, name: str):
        filters = await self.client.get_dialog_filters()
        for f in filters:
            if hasattr(f, 'title') and f.title == name:
                await self.client(UpdateDialogFilterRequest(id=f.id, filter=None))
                return
        raise ValueError("Папка не найдена")

    async def _manage_chat_in_folder(self, event, folder_name: str, action: str):
        chat_peer = await self.client.get_input_entity(event.chat_id)
        filters = await self.client.get_dialog_filters()
        
        for f in filters:
            if hasattr(f, 'title') and f.title == folder_name:
                include_peers = list(f.include_peers)
                
                if action == "add":
                    if chat_peer not in include_peers:
                        include_peers.append(chat_peer)
                    else:
                        await event.reply("Чат уже в папке")
                        return

                elif action == "remove":
                    if chat_peer in include_peers:
                        include_peers.remove(chat_peer)
                    else:
                        await event.reply("Чата нет в папке")
                        return

                updated_filter = DialogFilter(
                    id=f.id,
                    title=f.title,
                    pinned_peers=f.pinned_peers,
                    include_peers=include_peers,
                    exclude_peers=f.exclude_peers,
                    contacts=f.contacts,
                    non_contacts=f.non_contacts,
                    groups=f.groups,
                    broadcasts=f.broadcasts,
                    bots=f.bots,
                    exclude_muted=f.exclude_muted,
                    exclude_read=f.exclude_read,
                    exclude_archived=f.exclude_archived
                )

                await self.client(UpdateDialogFilterRequest(id=f.id, filter=updated_filter))
                await event.reply(f"Чат {'добавлен в' if action == 'add' else 'удален из'} папку '{folder_name}'")
                return

        raise ValueError("Папка не найдена")

    async def _handle_folder_command(self, event):
        try:
            args = event.message.text.split()[1:]
            if not args:
                await event.reply("Используйте: .folder [create|delete|add|remove] [name]")
                return

            command = args[0].lower()
            folder_name = args[1] if len(args) > 1 else None

            if command == "create":
                await self.create_folder(folder_name)
                await event.reply(f"Папка '{folder_name}' создана")

            elif command == "delete":
                await self.delete_folder(folder_name)
                await event.reply(f"Папка '{folder_name}' удалена")

            elif command in ["add", "remove"]:
                if len(args) < 2:
                    await event.reply("Укажите название папки")
                    return
                await self._manage_chat_in_folder(event, folder_name, command)

            else:
                await event.reply("Неизвестная команда")

        except Exception as e:
            await event.reply(f"Ошибка: {str(e)}")

def register(client):
    manager = FolderManager(client)
    
    # Регистрируем обработчик команды .folder
    @client.on(events.NewMessage(pattern=r'^\.folder\s+\S+'))
    async def handler(event):
        await manager._handle_folder_command(event)
    
    return manager

# Если модуль запускается отдельно
if __name__ == "__main__":
    import os
    API_ID = int(os.getenv("API_ID", 12345))
    API_HASH = os.getenv("API_HASH", "your_api_hash")
    
    client = TelegramClient('session_name', API_ID, API_HASH)
    register(client)
    client.start()
    client.run_until_disconnected()
