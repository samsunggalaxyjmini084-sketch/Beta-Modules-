# meta developer: @Androfon_AI
# meta name: Шашки
# meta version: 1.3.0

import asyncio, html, random
from .. import loader, utils

EMPTY = 0
WHITE_MAN = 1
BLACK_MAN = 2
WHITE_KING = 3
BLACK_KING = 4

PIECE_EMOJIS = {
    EMPTY: ".",
    "light": " ",
    WHITE_MAN: "⚪",
    BLACK_MAN: "⚫",
    WHITE_KING: "🌝",
    BLACK_KING: "🌚",
    'selected': "🔘",
    'move_target': "🟢",
    'capture_target': "🔴",
}

class CheckersBoard:
    def __init__(self, mandatory_captures_enabled=True):
        self._board = [[EMPTY for _ in range(8)] for _ in range(8)]
        self._setup_initial_pieces()
        self.current_player = "white"
        self.mandatory_capture_from_pos = None
        self.mandatory_captures_enabled = mandatory_captures_enabled

    def _setup_initial_pieces(self):
        for r in range(8):
            for c in range(8):
                if (r + c) % 2 != 0:
                    if r < 3:
                        self._board[r][c] = BLACK_MAN
                    elif r > 4:
                        self._board[r][c] = WHITE_MAN

    def _is_valid_coord(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def get_piece_at(self, r, c):
        if not self._is_valid_coord(r, c):
            return None
        return self._board[r][c]

    def _set_piece_at(self, r, c, piece):
        if self._is_valid_coord(r, c):
            self._board[r][c] = piece

    def _get_player_color(self, piece):
        if piece in [WHITE_MAN, WHITE_KING]:
            return "white"
        if piece in [BLACK_MAN, BLACK_KING]:
            return "black"
        return None

    def _get_opponent_color(self, color):
        return "black" if color == "white" else "white"

    def _get_moves_for_piece(self, r, c):
        moves = []
        piece = self.get_piece_at(r, c)
        player_color = self._get_player_color(piece)
        opponent_color = self._get_opponent_color(player_color)

        if piece == EMPTY:
            return []

        all_diagonal_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        if piece in [WHITE_MAN, BLACK_MAN]:
            regular_move_directions = []
            if piece == WHITE_MAN:
                regular_move_directions = [(-1, -1), (-1, 1)]
            elif piece == BLACK_MAN:
                regular_move_directions = [(1, -1), (1, 1)]

            for dr, dc in regular_move_directions:
                new_r, new_c = r + dr, c + dc
                if self._is_valid_coord(new_r, new_c) and self.get_piece_at(new_r, new_c) == EMPTY:
                    moves.append((r, c, new_r, new_c, False))

            for dr, dc in all_diagonal_directions:
                captured_piece_r, captured_piece_c = r + dr, c + dc
                jump_r, jump_c = r + 2 * dr, c + 2 * dc
                
                captured_piece = self.get_piece_at(captured_piece_r, captured_piece_c)

                if (self._is_valid_coord(jump_r, jump_c) and
                    self.get_piece_at(jump_r, jump_c) == EMPTY and
                    self._get_player_color(captured_piece) == opponent_color):
                    
                    moves.append((r, c, jump_r, jump_c, True))

        elif piece in [WHITE_KING, BLACK_KING]:
            for dr, dc in all_diagonal_directions:
                current_r, current_c = r + dr, c + dc
                captured_piece_pos = None

                while self._is_valid_coord(current_r, current_c):
                    piece_on_path = self.get_piece_at(current_r, current_c)
                    piece_on_path_color = self._get_player_color(piece_on_path)

                    if piece_on_path == EMPTY:
                        if captured_piece_pos is None:
                            moves.append((r, c, current_r, current_c, False))
                        else:
                            moves.append((r, c, current_r, current_c, True))
                    elif piece_on_path_color == player_color:
                        break
                    elif piece_on_path_color == opponent_color:
                        if captured_piece_pos is None:
                            captured_piece_pos = (current_r, current_c)
                        else:
                            break
                    
                    current_r += dr
                    current_c += dc
        return moves

    def get_all_possible_moves(self, player_color):
        all_moves = []
        all_captures = []

        if self.mandatory_capture_from_pos:
            r, c = self.mandatory_capture_from_pos
            return [m for m in self._get_moves_for_piece(r, c) if m[4]]
            
        for r in range(8):
            for c in range(8):
                piece = self.get_piece_at(r, c)
                if self._get_player_color(piece) == player_color:
                    moves_for_piece = self._get_moves_for_piece(r, c)
                    for move in moves_for_piece:
                        if move[4]:
                            all_captures.append(move)
                        else:
                            all_moves.append(move)
        
        if self.mandatory_captures_enabled and all_captures: 
            return all_captures
        
        return all_moves + all_captures

    def _execute_move(self, start_r, start_c, end_r, end_c, is_capture_move):
        piece = self.get_piece_at(start_r, start_c)
        self._set_piece_at(end_r, end_c, piece)
        self._set_piece_at(start_r, start_c, EMPTY)

        if is_capture_move:
            dr_diff = end_r - start_r
            dc_diff = end_c - start_c
            
            dr_norm = 0
            if dr_diff != 0:
                dr_norm = dr_diff // abs(dr_diff)
            
            dc_norm = 0
            if dc_diff != 0:
                dc_norm = dc_diff // abs(dc_diff)

            current_r, current_c = start_r + dr_norm, start_c + dc_norm
            while self._is_valid_coord(current_r, current_c) and (current_r, current_c) != (end_r, end_c):
                if self.get_piece_at(current_r, current_c) != EMPTY:
                    self._set_piece_at(current_r, current_c, EMPTY)
                    break
                current_r += dr_norm
                current_c += dc_norm
        
        return is_capture_move

    def make_move(self, start_r, start_c, end_r, end_c, is_capture_move):
        self._execute_move(start_r, start_c, end_r, end_c, is_capture_move)
        
        piece_after_move = self.get_piece_at(end_r, end_c)
        if piece_after_move == WHITE_MAN and end_r == 0:
            self._set_piece_at(end_r, end_c, WHITE_KING)
            piece_after_move = WHITE_KING
        elif piece_after_move == BLACK_MAN and end_r == 7:
            self._set_piece_at(end_r, end_c, BLACK_KING)
            piece_after_move = BLACK_KING

        if is_capture_move:
            self.mandatory_capture_from_pos = (end_r, end_c)
            further_captures = [m for m in self._get_moves_for_piece(end_r, end_c) if m[4]]
            
            if further_captures:
                return True
            else:
                self.mandatory_capture_from_pos = None
                self.switch_turn()
                return False
        else:
            self.mandatory_capture_from_pos = None
            self.switch_turn()
            return False

    def switch_turn(self):
        self.current_player = self._get_opponent_color(self.current_player)

    def is_game_over(self):
        white_pieces = sum(1 for r in range(8) for c in range(8) if self._get_player_color(self.get_piece_at(r, c)) == "white")
        black_pieces = sum(1 for r in range(8) for c in range(8) if self._get_player_color(self.get_piece_at(r, c)) == "black")

        if white_pieces == 0:
            return "Победа черных"
        if black_pieces == 0:
            return "Победа белых"
        
        if not self.get_all_possible_moves(self.current_player):
            if self.current_player == "white":
                return "Победа черных (нет ходов у белых)"
            else:
                return "Победа белых (нет ходов у черных)"

        return None

    def to_list_of_emojis(self, selected_pos=None, possible_moves_with_info=None):
        board_emojis = []
        possible_moves_with_info = possible_moves_with_info if possible_moves_with_info else []
        
        possible_move_targets_map = {(move_info[0], move_info[1]): move_info[2] for move_info in possible_moves_with_info}

        for r in range(8):
            row_emojis = []
            for c in range(8):
                piece = self.get_piece_at(r, c)
                
                current_cell_emoji = PIECE_EMOJIS['light'] if (r + c) % 2 == 0 else PIECE_EMOJIS[piece]
                
                if (r, c) == selected_pos:
                    current_cell_emoji = PIECE_EMOJIS['selected']
                elif (r, c) in possible_move_targets_map:
                    is_capture_move = possible_move_targets_map[(r, c)]
                    current_cell_emoji = PIECE_EMOJIS['capture_target'] if is_capture_move else PIECE_EMOJIS['move_target']
                
                row_emojis.append(current_cell_emoji)
            board_emojis.append(row_emojis)
        return board_emojis
    
    def get_valid_moves_for_selection(self, current_r, current_c):
        piece = self.get_piece_at(current_r, current_c)
        if self._get_player_color(piece) != self.current_player:
            return []

        piece_moves_full_info = self._get_moves_for_piece(current_r, current_c)
        
        all_game_moves_full_info = self.get_all_possible_moves(self.current_player)
        
        valid_moves_for_selection = []

        if self.mandatory_capture_from_pos:
            if (current_r, current_c) == self.mandatory_capture_from_pos:
                valid_moves_for_selection = [(e_r, e_c, is_cap) for s_r, s_c, e_r, e_c, is_cap in piece_moves_full_info if is_cap]
            else:
                valid_moves_for_selection = []
        else:
            for s_r, s_c, e_r, e_c, is_cap in piece_moves_full_info:
                if (s_r, s_c, e_r, e_c, is_cap) in all_game_moves_full_info:
                    valid_moves_for_selection.append((e_r, e_c, is_cap))

        return valid_moves_for_selection


@loader.tds
class Checkers(loader.Module):
    """Шашки для игры вдвоём."""
    strings = {
        "name": "Шашки"
    }

    async def client_ready(self):
        self.games = {}
        await self.purgeSelf()

    async def purgeSelf(self):
        self.games = {}

    async def default_game_state(self, chat_id):
        return {
            'board_obj': None,
            'game_message': None,
            'selected_piece_pos': None,
            'possible_moves_for_selected': [],
            'colorName': "рандом",
            'host_color': None,
            'game_running': False,
            'game_reason_ended': None,
            'players_ids': [],
            'host_id': None,
            'opponent_id': None,
            'opponent_name': None,
            'player_white_id': None,
            'player_black_id': None,
            'game_board_call': None,
            'mandatory_captures_enabled': self.db.get("checkers_module", "mandatory_captures_enabled", True)
        }

    async def get_game_state(self, chat_id):
        if chat_id not in self.games:
            self.games[chat_id] = await self.default_game_state(chat_id)
        return self.games[chat_id]

    async def inline_handler(self, query):
        # Обработка inline-запросов
        if not hasattr(query, "data") or not query.data:
            return
        
        data = query.data
        if not isinstance(data, str) or not data.startswith("checkers_"):
            return

        parts = data.split('_')
        if len(parts) < 3:
            return

        method_name = parts[1]
        chat_id = int(parts[2])
        args = parts[3:]

        if chat_id not in self.games:
            await query.answer("Игра не найдена. Возможно, она была завершена.")
            return

        method = getattr(self, method_name, None)
        if method is None:
            return

        try:
            await method(query, chat_id, *args)
        except Exception as e:
            await query.answer(f"Ошибка: {str(e)}")

    async def checkerscmd(self, message):
        """Запустить игру в шашки. Использование: .checkers [@оппонент]"""
        chat_id = message.chat_id
        state = await self.get_game_state(chat_id)
        
        if state['game_running']:
            await utils.answer(message, "Игра уже запущена в этом чате!")
            return

        args = utils.get_args_raw(message)
        opponent_entity = None
        opponent_id = None
        opponent_name = "любой желающий"

        if args:
            try:
                opponent_entity = await message.client.get_entity(args)
                opponent_id = opponent_entity.id
                opponent_name = html.escape(opponent_entity.first_name)
            except Exception:
                opponent_name = "любой желающий"

        state['host_id'] = message.from_id
        state['opponent_id'] = opponent_id
        state['opponent_name'] = opponent_name
        state['players_ids'] = [message.from_id]
        if opponent_id:
            state['players_ids'].append(opponent_id)

        current_host_color_display = state['colorName']
        if state['host_color'] == "white":
            current_host_color_display = "белый"
        elif state['host_color'] == "black":
            current_host_color_display = "чёрный"

        invite_text_prefix = "Вас приглашают сыграть партию в шашки, примите?"
        if opponent_id:
            invite_text_prefix = f"<a href='tg://user?id={opponent_id}'>{opponent_name}</a>, вас пригласили сыграть партию в шашки, примите?"

        await self.inline.form(
            message=message,
            text=f"{invite_text_prefix}\n-- --\n"
                 f"Текущие настройки:\n"
                 f"| - > • Хост играет за {current_host_color_display} цвет\n"
                 f"| - > • Обязательные взятия: {'Включены' if state['mandatory_captures_enabled'] else 'Отключены'}",
            reply_markup=[
                [
                    {"text": "Принять вызов", "data": f"checkers_accept_game_{chat_id}"}
                ],
                [
                    {"text": "Настройки", "data": f"checkers_settings_menu_{chat_id}"}
                ],
                [
                    {"text": "Отклонить", "data": f"checkers_decline_game_{chat_id}"}
                ]
            ],
            ttl=60*60*24  # 24 часа
        )

    async def accept_game(self, call, chat_id):
        state = await self.get_game_state(chat_id)
        
        if call.from_user.id not in state['players_ids']:
            if state['opponent_id'] is None:
                state['opponent_id'] = call.from_user.id
                state['players_ids'].append(call.from_user.id)
                try:
                    opponent_entity = await self.client.get_entity(call.from_user.id)
                    state['opponent_name'] = html.escape(opponent_entity.first_name)
                except Exception:
                    state['opponent_name'] = "игрок"
            else:
                await call.answer("Вы не участник этой игры!")
                return

        if state['game_running']:
            await call.answer("Игра уже началась!")
            return

        if state['host_color'] is None:
            if state['colorName'] == "рандом":
                state['host_color'] = random.choice(["white", "black"])
            else:
                state['host_color'] = state['colorName']

        state['player_white_id'] = state['host_id'] if state['host_color'] == "white" else state['opponent_id']
        state['player_black_id'] = state['opponent_id'] if state['host_color'] == "white" else state['host_id']

        state['board_obj'] = CheckersBoard(mandatory_captures_enabled=state['mandatory_captures_enabled'])
        state['game_running'] = True
        state['game_reason_ended'] = None

        await self.display_board(call, chat_id)

