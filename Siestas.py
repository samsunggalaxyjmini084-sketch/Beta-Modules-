# meta developer: @Androfon_AI
# meta name: Управление папками
# meta version: 1.0.2

import os
import logging
from telethon import TelegramClient, events
from telethon.tl.functions.messages import UpdateDialogFilterRequest
from telethon.tl.types import DialogFilter, InputDialogPeer

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FolderManager:
    def __init__(self, client: TelegramClient):
        self.client = client
        self.setup_handlers()
        
    def setup_handlers(self):
        """Настройка обработчиков команд"""
        # Правильное использование декоратора events.register
        @self.client.on(events.NewMessage(pattern=r'^\.folder\s+\S+'))
        async def folder_handler(event):
            await self.handle_folder_command(event)

    async def handle_folder_command(self, event):
        """Обработчик команд для управления папками"""
        try:
            command_parts = event.message.text.split()
            if len(command_parts) < 2:
                await event.reply("❌ Используйте: .folder [create|delete|add|remove] [name]")
                return

            action = command_parts[1].lower()
            folder_name = " ".join(command_parts[2:]) if len(command_parts) > 2 else None

            if action == "create" and folder_name:
                await self.create_folder(folder_name)
                await event.reply(f"✅ Папка '{folder_name}' создана")
                
            elif action == "delete" and folder_name:
                await self.delete_folder(folder_name)
                await event.reply(f"✅ Папка '{folder_name}' удалена")
                
            elif action == "add" and folder_name:
                await self.add_chat_to_folder(event, folder_name)
                
            elif action == "remove" and folder_name:
                await self.remove_chat_from_folder(event, folder_name)
                
            else:
                await event.reply("❌ Неверная команда. Используйте: .folder [create|delete|add|remove] [name]")

        except Exception as e:
            logger.error(f"Error in folder command: {e}")
            await event.reply(f"❌ Ошибка: {str(e)}")

    async def create_folder(self, name: str):
        """Создание новой папки"""
        filters = await self.client.get_dialog_filters()
        
        # Проверяем, существует ли уже папка с таким именем
        for f in filters:
            if hasattr(f, 'title') and f.title == name:
                raise ValueError(f"Папка '{name}' уже существует")
        
        # Создаем новую папку
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
        """Удаление папки"""
        filters = await self.client.get_dialog_filters()
        folder_found = False
        
        for f in filters:
            if hasattr(f, 'title') and f.title == name:
                await self.client(UpdateDialogFilterRequest(id=f.id, filter=None))
                folder_found = True
                break
        
        if not folder_found:
            raise ValueError(f"Папка '{name}' не найдена")

    async def add_chat_to_folder(self, event, folder_name: str):
        """Добавление чата в папку"""
        chat_peer = await self.client.get_input_entity(event.chat_id)
        filters = await self.client.get_dialog_filters()
        folder_found = False
        
        for f in filters:
            if hasattr(f, 'title') and f.title == folder_name:
                include_peers = list(f.include_peers)
                
                # Проверяем, не добавлен ли уже чат
                if any(peer.channel_id == getattr(chat_peer, 'channel_id', None) or 
                       peer.user_id == getattr(chat_peer, 'user_id', None) for peer in include_peers):
                    await event.reply("✅ Чат уже находится в этой папке")
                    return
                
                include_peers.append(chat_peer)
                
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
                folder_found = True
                await event.reply(f"✅ Чат добавлен в папку '{folder_name}'")
                break
        
        if not folder_found:
            raise ValueError(f"Папка '{folder_name}' не найдена")

    async def remove_chat_from_folder(self, event, folder_name: str):
        """Удаление чата из папки"""
        chat_peer = await self.client.get_input_entity(event.chat_id)
        filters = await self.client.get_dialog_filters()
        folder_found = False
        
        for f in filters:
            if hasattr(f, 'title') and f.title == folder_name:
                include_peers = list(f.include_peers)
                peer_ids = [getattr(peer, 'channel_id', None) or getattr(peer, 'user_id', None) for peer in include_peers]
                chat_id = getattr(chat_peer, 'channel_id', None) or getattr(chat_peer, 'user_id', None)
                
                if chat_id not in peer_ids:
                    await event.reply("✅ Чат не находится в этой папке")
                    return
                
                # Удаляем чат из папки
                include_peers = [peer for peer in include_peers if 
                                getattr(peer, 'channel_id', None) != chat_id and 
                                getattr(peer, 'user_id', None) != chat_id]
                
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
                folder_found = True
                await event.reply(f"✅ Чат удален из папки '{folder_name}'")
                break
        
        if not folder_found:
            raise ValueError(f"Папка '{folder_name}' не найдена")

# Альтернативный способ инициализации модуля
def load_folder_manager(client):
    """Инициализация менеджера папок"""
    return FolderManager(client)

# Для использования в основном файле юзербота
if __name__ == "__main__":
    # Пример интеграции с юзерботом
    API_ID = int(os.getenv("API_ID", 12345))
    API_HASH = os.getenv("API_HASH", "your_api_hash_here")
    
    client = TelegramClient('session_name', API_ID, API_HASH)
    
    async def main():
        await client.start()
        folder_manager = FolderManager(client)
        print("Folder manager module is ready!")
        await client.run_until_disconnected()
    
    import asyncio
    asyncio.run(main())
