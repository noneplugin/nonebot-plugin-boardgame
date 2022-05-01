from typing import List, Tuple, Optional

from .game import Game, MoveResult

directions = ((-1, 0), (1, 0), (0, -1), (0, 1))


class Go(Game):
    def __init__(self, size: int = 19):
        super().__init__("围棋", size)

    def find_eaten(self, x: int, y: int) -> int:
        value = self.get(x, y)
        if not value:
            return False
        found = 0

        def find_life(x: int, y: int) -> bool:
            nonlocal found
            found |= self.bit(x, y)
            points: List[Tuple[int, int]] = []
            for (dx, dy) in directions:
                i = x + dx
                j = y + dy
                if not self.in_range(i, j) or (found & self.bit(i, j)):
                    continue
                next = self.get(i, j)
                if not next:
                    return True
                if next == -value:
                    continue
                if next == value:
                    points.append((i, j))
            for (i, j) in points:
                if find_life(i, j):
                    return True
            return False

        return 0 if find_life(x, y) else found

    def update(self, x: int, y: int) -> Optional[MoveResult]:
        moveside = self.moveside
        self.push(x, y)

        diff = 0
        for (dx, dy) in directions:
            i = x + dx
            j = y + dy
            if not self.in_range(i, j):
                continue
            if self.get(i, j) == -moveside:
                diff |= self.find_eaten(i, j)

        if diff:
            if moveside == 1:
                self.w_board ^= diff
            else:
                self.b_board ^= diff
        elif self.find_eaten(x, y):
            self.pop()
            raise ValueError("不入子")

        for history in self.history[1:-1]:
            if (
                history.b_board
                and self.b_board == history.b_board
                and history.w_board
                and self.w_board == history.w_board
            ):
                self.pop()
                raise ValueError("全局同形")
