# meta developer: @Androfon_AI
# meta name: PollStats
# meta version: 2.8
import html

from telethon import events
from telethon.tl.functions.messages import GetPollVotesRequest
from telethon.tl.types import MessageMediaPoll, TextWithEntities, User
import telethon.utils as telethon_utils

from .. import loader


class PollStatsModule(loader.Module):
    """Модуль для просмотра статистики опросов, включая список не проголосовавших или проголосовавших за определенный вариант."""

    strings = {
        "name": "PollStats",
        "ru_doc": "Показывает статистику опросов и список не проголосовавших. "
                  "Также можно указать вариант ответа, чтобы получить список проголосовавших за него.\n"
                  "Используйте: <code>.voters</code> (ответив на опрос) или <code>.voters [текст варианта]</code> (ответив на опрос).",
        "en_doc": "Shows poll statistics and a list of non-voters. "
                  "You can also specify an answer option to get a list of users who voted for it.\n"
                  "Usage: <code>.voters</code> (replying to a poll) or <code>.voters [option text]</code> (replying to a poll).",
        "poll_editable_status": "\n<emoji document_id=5828453479133800627>🔄</emoji> Изменение голоса: {status}",
        "poll_add_option_status": "\n➕ Добавление вариантов: {status}",
        "poll_setting_enabled": "Включено <emoji document_id=5832546462478635761>✅</emoji>",
        "poll_setting_disabled": "Выключено <emoji document_id=5879813604068298387>❌</emoji>",
    }

    async def client_ready(self, client, db):
        self._client = client

    def __init__(self):
        self.config = loader.ModuleConfig()

    @loader.command(
        command="voters",
        ru_doc="Показывает количество проголосовавших в опросе и список тех, кто не проголосовал (если опрос публичный). "
              "Также можно указать вариант ответа, чтобы получить список проголосовавших за него.\n"
              "Используйте: <code>.voters</code> (ответив на опрос) или <code>.voters [текст варианта]</code> (ответив на опрос).",
        en_doc="Shows the number of voters in a poll and a list of those who have not voted (if the poll is public). "
              "You can also specify an answer option to get a list of users who voted for it.\n"
              "Usage: <code>.voters</code> (replying to a poll) or <code>.voters [option text]</code> (replying to a poll)."
    )
    async def voterscmd(self, message: events.NewMessage.Event):
        """
        Показывает количество проголосовавших в опросе и список тех, кто не проголосовал.
        Также можно указать вариант ответа, чтобы получить список проголосовавших за него.
        Используйте, ответив на сообщение с опросом.
        """
        await message.edit("Загрузка статистики... <emoji document_id=5900104897885376843>🕓</emoji>")

        reply = await message.get_reply_message()
        if not reply:
            await message.edit("<emoji document_id=5879813604068298387>❗️</emoji> Ответьте на сообщение с опросом.", parse_mode="HTML")
            return

        # Разделяем текст сообщения, чтобы получить аргументы после команды
        args = message.text.split(None, 1) 
        option_text_arg = args[1] if len(args) > 1 else ""

        if reply.media and isinstance(reply.media, MessageMediaPoll):
            poll_question_text = reply.media.poll.question.text
            is_public_poll = reply.media.poll.public_voters

            if not is_public_poll:
                final_message = (
                    f"<emoji document_id=5877485980901971030>📊</emoji> В опросе \"<b>{html.escape(poll_question_text)}</b>\" проголосовало: <b>{reply.media.results.total_voters or 0}</b> человек(а)."
                    f"\n<emoji document_id=5832546462478635761>🔒</emoji> Опрос анонимный, списки проголосовавших/не проголосовавших недоступны."
                )
                await message.edit(final_message, parse_mode="HTML")
                return

            try:
                peer = await self._client.get_input_entity(reply.peer_id)

                if option_text_arg:
                    # Пользователь указал вариант ответа, выводим проголосовавших за него
                    target_option = None
                    for answer_option in reply.media.poll.answers:
                        # answer_option.text может быть TextWithEntities или str
                        decoded_text = answer_option.text.text if isinstance(answer_option.text, TextWithEntities) else str(answer_option.text)
                        if decoded_text.lower() == option_text_arg.lower():
                            target_option = answer_option
                            break

                    if not target_option:
                        await message.edit(f"<emoji document_id=5879813604068298387>❗️</emoji> Вариант ответа \"<b>{html.escape(option_text_arg)}</b>\" не найден в опросе.", parse_mode="HTML")
                        return

                    voters_for_option = []
                    current_offset = ""
                    while True:
                        votes_list = await self._client(GetPollVotesRequest(
                            peer=peer,
                            id=reply.id,
                            option=target_option.option,  # Используем байты конкретного варианта
                            limit=100,
                            offset=current_offset
                        ))

                        for user in votes_list.users:
                            if isinstance(user, User) and not user.bot and not user.deleted:
                                voters_for_option.append(user)

                        if not votes_list.next_offset:
                            break
                        current_offset = votes_list.next_offset

                    if voters_for_option:
                        voters_for_option.sort(key=lambda u: (u.username.lower() if u.username else (telethon_utils.get_display_name(u) or '').lower()))
                        voters_list_items = [
                            f"  <emoji document_id=5771887475421090729>👤</emoji> <a href='tg://user?id={user.id}'>"
                            f"{html.escape('@' + user.username) if user.username else html.escape(telethon_utils.get_display_name(user) or 'Неизвестный пользователь')}"
                            f"</a>"
                            for user in voters_for_option
                        ]
                        final_message = (
                            f"<emoji document_id=5877485980901971030>📊</emoji> Проголосовавшие за \"<b>{html.escape(option_text_arg)}</b>\" ({len(voters_for_option)} человек(а)):\n"
                            + "\n".join(voters_list_items)
                        )
                    else:
                        final_message = f"<emoji document_id=5879813604068298387>❗️</emoji> Никто не проголосовал за \"<b>{html.escape(option_text_arg)}</b>\"."

                    await message.edit(final_message, parse_mode="HTML")

                else:
                    # Аргумент не указан, выводим общую статистику и не проголосовавших
                    voters_count = reply.media.results.total_voters if reply.media.results and reply.media.results.total_voters is not None else 0

                    voted_user_ids = set()

                    if reply.media.poll.answers:
                        for answer_option in reply.media.poll.answers:
                            current_offset = ""
                            while True:
                                votes_list = await self._client(GetPollVotesRequest(
                                    peer=peer,
                                    id=reply.id,
                                    option=answer_option.option,  # Итерируем по всем вариантам, чтобы получить всех проголосовавших
                                    limit=100,
                                    offset=current_offset
                                ))

                                for user in votes_list.users:
                                    voted_user_ids.add(user.id)

                                if not votes_list.next_offset:
                                    break
                                current_offset = votes_list.next_offset

                    all_participant_ids = set()
                    all_participants_map = {}
                    async for participant in self._client.iter_participants(peer, aggressive=True):
                        if isinstance(participant, User) and not participant.bot and not participant.deleted:
                            all_participant_ids.add(participant.id)
                            all_participants_map[participant.id] = participant

                    non_voted_user_ids = all_participant_ids - voted_user_ids

                    non_voters_list_text = ""
                    if non_voted_user_ids:
                        non_voters = [all_participants_map[uid] for uid in non_voted_user_ids if uid in all_participants_map]
                        non_voters.sort(key=lambda u: (u.username.lower() if u.username else (telethon_utils.get_display_name(u) or '').lower()))

                        non_voters_list_items = [
                            f"  <emoji document_id=5771887475421090729>👤</emoji> <a href='tg://user?id={user.id}'>"
                            f"{html.escape('@' + user.username) if user.username else html.escape(telethon_utils.get_display_name(user) or 'Неизвестный пользователь')}"
                            f"</a>"
                            for user in non_voters
                        ]
                        non_voters_list_text = f"\n<emoji document_id=5872829476143894491>🚫</emoji> <b>Не проголосовавшие:</b>\n" + "\n".join(non_voters_list_items)
                    else:
                        non_voters_list_text = "\n<emoji document_id=5825794181183836432>✔️</emoji> Все активные участники чата проголосовали."

                    # Добавление информации о настройках опроса
                    poll_settings_info = ""
                    
                    # Статус "Изменение голоса"
                    editable_status_text = (
                        self.strings("poll_setting_enabled") if reply.media.poll.can_be_edited
                        else self.strings("poll_setting_disabled")
                    )
                    poll_settings_info += self.strings("poll_editable_status").format(status=editable_status_text)

                    # Статус "Добавление вариантов"
                    add_option_status_text = (
                        self.strings("poll_setting_enabled") if reply.media.poll.can_add_option
                        else self.strings("poll_setting_disabled")
                    )
                    poll_settings_info += self.strings("poll_add_option_status").format(status=add_option_status_text)


                    final_message = (
                        f"<emoji document_id=5877485980901971030>📊</emoji> В опросе \"<b>{html.escape(poll_question_text)}</b>\" проголосовало: <b>{voters_count}</b> человек(а)."
                        f"{poll_settings_info}"
                        f"{non_voters_list_text}"
                    )
                    await message.edit(final_message, parse_mode="HTML")

            except Exception as e:
                await message.edit(f"<emoji document_id=5879813604068298387>❗️</emoji> Произошла ошибка при получении данных: <i>{html.escape(str(e))}</i>", parse_mode="HTML")
        else:
            await message.edit("<emoji document_id=5879813604068298387>❗️</emoji> Отвеченное сообщение не является опросом.", parse_mode="HTML")
