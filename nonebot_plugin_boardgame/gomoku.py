from typing import Optional

from .game import Rule, MoveResult


class Gomoku(Rule):
    def __init__(self):
        super().__init__()
        self.name = "五子棋"
        self.size = 15

    def update(self, x: int, y: int, value: int) -> Optional[MoveResult]:
        game = self.game
        size = game.size
        board = game.set(x, y, value)
        v_count = 1
        h_count = 1
        m_count = 1
        p_count = 1

        for i in range(x - 1, -1, -1):
            if not (board & game.bit(i, y)):
                break
            v_count += 1
        for i in range(x + 1, size):
            if not (board & game.bit(i, y)):
                break
            v_count += 1
        if v_count >= 5:
            return MoveResult(value)

        for j in range(y - 1, -1, -1):
            if not (board & game.bit(x, j)):
                break
            h_count += 1
        for j in range(y + 1, size):
            if not (board & game.bit(x, j)):
                break
            h_count += 1
        if h_count >= 5:
            return MoveResult(value)

        i = x - 1
        j = y - 1
        while i >= 0 and j >= 0 and board & game.bit(i, j):
            m_count += 1
            i -= 1
            j -= 1
        i = x + 1
        j = y + 1
        while i < size and j < size and board & game.bit(i, j):
            m_count += 1
            i += 1
            j += 1
        if m_count >= 5:
            return MoveResult(value)

        i = x - 1
        j = y + 1
        while i >= 0 and j < size and board & game.bit(i, j):
            p_count += 1
            i -= 1
            j += 1
        i = x + 1
        j = y - 1
        while i < size and j >= 0 and board & game.bit(i, j):
            p_count += 1
            i += 1
            j -= 1
        if p_count >= 5:
            return MoveResult(value)

        if game.is_full():
            return MoveResult.DRAW
