from typing import List, Union, Tuple, Optional

from .game import Rule, MoveResult

directions = ((-1, 0), (1, 0), (0, -1), (0, 1))


class Go(Rule):
    def __init__(self):
        super().__init__()
        self.name = "围棋"
        self.size = 19

    def find_eaten(self, x: int, y: int) -> bool:
        game = self.game
        value = game.get(x, y)
        if not value:
            return False
        found = 0

        def find_life(x: int, y: int) -> bool:
            nonlocal found
            found |= game.bit(x, y)
            points: List[Tuple[int, int]] = []
            for (dx, dy) in directions:
                i = x + dx
                j = y + dy
                if not game.in_range(i, j) or found & game.bit(i, j):
                    continue
                next = game.get(i, j)
                if not next:
                    return True
                if next == -value:
                    continue
                if next == value:
                    points.append((i, j))
            for (i, j) in points:
                result = find_life(i, j)
                if result:
                    return True
            return False

        return False if find_life(x, y) else bool(found)

    def update(self, x: int, y: int, value: int) -> Optional[Union[MoveResult, str]]:
        game = self.game
        b_board = game.b_board
        w_board = game.w_board

        if value == 1:
            game.b_board |= game.bit(x, y)
        else:
            game.w_board |= game.bit(x, y)

        diff = 0
        for (dx, dy) in directions:
            i = x + dx
            j = y + dy
            if not game.in_range(i, j):
                continue
            if game.get(i, j) == -value:
                diff |= self.find_eaten(i, j)

        if diff:
            if value == 1:
                game.w_board ^= diff
            else:
                game.b_board ^= diff
        elif self.find_eaten(x, y):
            game.b_board = b_board
            game.w_board = w_board
            return "不入子"

        if game.w_board << game.area + game.b_board in game.history:
            game.b_board = b_board
            game.w_board = w_board
            return "全局同形"
