# meta version: 2.4
# meta name: 📊 Статистика Опросов
# meta developer: @Androfon_AI

from telethon import events
from .. import loader
from telethon.tl.types import MessageMediaPoll, User, TextWithEntities
from telethon.tl.functions.messages import GetPollVotesRequest
import telethon.utils as telethon_utils
import html


class PollStatsModule(loader.Module):
    """Модуль для просмотра статистики опросов, включая список не проголосовавших."""
    
    strings = {
        "name": "PollStats",
        "ru_doc": "Показывает статистику опросов и список не проголосовавших"
    }

    async def client_ready(self, client, db):
        self._client = client

    def __init__(self):
        self.config = loader.ModuleConfig()

    @loader.command(
        command="voters",
        ru_doc="Показывает количество проголосовавших в опросе и список тех, кто не проголосовал (если опрос публичный).\nИспользуйте: <code>.voters</code> ответив на сообщение с опросом.",
        en_doc="Shows the number of voters in a poll and a list of those who have not voted (if the poll is public).\nUsage: <code>.voters</code> by replying to a poll message."
    )
    async def voterscmd(self, message):
        """
        Показывает количество проголосовавших в опросе и список тех, кто не проголосовал.
        Используйте, ответив на сообщение с опросом.
        """
        reply = await message.get_reply_message()
        if not reply:
            await message.edit("<emoji document_id=5879813604068298387>❗️</emoji> Ответьте на сообщение с опросом.", parse_mode="HTML")
            return

        if reply.media and isinstance(reply.media, MessageMediaPoll):
            poll_question_text = reply.media.poll.question.text
            
            voters_count = reply.media.results.total_voters if reply.media.results and reply.media.results.total_voters is not None else 0
            
            is_public_poll = reply.media.poll.public_voters
            
            if is_public_poll:
                voted_user_ids = set()
                
                try:
                    # Get the InputPeer for the chat where the poll is located
                    peer = await self._client.get_input_entity(reply.peer_id)

                    if reply.media.poll.answers:
                        for answer_option in reply.media.poll.answers:
                            current_offset = ""
                            while True:
                                votes_list = await self._client(GetPollVotesRequest(
                                    peer=peer,
                                    id=reply.id,
                                    option=answer_option.option,
                                    limit=100, # Fetch up to 100 votes per request
                                    offset=current_offset
                                ))
                                
                                for user in votes_list.users:
                                    voted_user_ids.add(user.id)
                                
                                if not votes_list.next_offset:
                                    break
                                current_offset = votes_list.next_offset
                    
                    all_participant_ids = set()
                    all_participants_map = {}
                    # Iterate through all participants in the chat
                    async for participant in self._client.iter_participants(peer, aggressive=True):
                        # Only consider active users (not bots or deleted accounts)
                        if isinstance(participant, User) and not participant.bot and not participant.deleted:
                            all_participant_ids.add(participant.id)
                            all_participants_map[participant.id] = participant

                    non_voted_user_ids = all_participant_ids - voted_user_ids
                    
                    non_voters_list_text = ""
                    if non_voted_user_ids:
                        # Filter out any non-voted IDs that might not be in our current participant map (e.g., left the chat)
                        non_voters = [all_participants_map[uid] for uid in non_voted_user_ids if uid in all_participants_map]
                        
                        # Sort non-voters for consistent output
                        non_voters.sort(key=lambda u: (u.username.lower() if u.username else (telethon_utils.get_display_name(u) or '').lower()))
                        
                        non_voters_list_items = [
                            f"  <emoji document_id=5771887475421090729>👤</emoji> <a href='tg://user?id={user.id}'>"
                            f"{html.escape('@' + user.username) if user.username else html.escape(telethon_utils.get_display_name(user) or 'Неизвестный пользователь')}"
                            f"</a>"
                            for user in non_voters
                        ]
                        non_voters_list_text = f"\n<emoji document_id=5872829476143894491>🚫</emoji> <b>Не проголосовавшие:</b>\n" + "\n".join(non_voters_list_items)
                    else:
                        non_voters_list_text = "\n<emoji document_id=5825794181183836432>✔️</emoji> Все участники чата проголосовали (с учетом активных аккаунтов)."
                    
                    final_message = (
                        f"<emoji document_id=5877485980901971030>📊</emoji> В опросе \"<b>{html.escape(poll_question_text)}</b>\" проголосовало: <b>{voters_count}</b> человек(а)."
                        f"{non_voters_list_text}"
                    )
                    await message.edit(final_message, parse_mode="HTML")

                except Exception as e:
                    # Catch any exceptions during API calls or data processing
                    await message.edit(f"<emoji document_id=5879813604068298387>❗️</emoji> Произошла ошибка при получении данных: <i>{html.escape(str(e))}</i>", parse_mode="HTML")
            else:
                # Handle anonymous polls
                final_message = (
                    f"<emoji document_id=5877485980901971030>📊</emoji> В опросе \"<b>{html.escape(poll_question_text)}</b>\" проголосовало: <b>{voters_count}</b> человек(а)."
                    f"\n<emoji document_id=5832546462478635761>🔒</emoji> Опрос анонимный, список не проголосовавших недоступен."
                )
                await message.edit(final_message, parse_mode="HTML")
        else:
            await message.edit("<emoji document_id=5879813604068298387>❗️</emoji> Отвеченное сообщение не является опросом.", parse_mode="HTML")
