from typing import Optional

from .game import Game, MoveResult, Placement


delta = ((0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1))


class Othello(Game):
    def __init__(self, size: int = 8):
        super().__init__("黑白棋", size, placement=Placement.GRID, allow_skip=True)

    def setup(self):
        size = self.size
        if size % 2 != 0 or size == 2:
            raise ValueError("棋盘大小应为 2 的倍数且不小于 4")
        super().setup()
        mid = int(size / 2)
        self.set(mid - 1, mid - 1, -1)
        self.set(mid - 1, mid, 1)
        self.set(mid, mid - 1, 1)
        self.set(mid, mid, -1)

    def legal(self, x: int, y: int, value: int) -> int:
        diff = 0
        for (dx, dy) in delta:
            i = x + dx
            j = y + dy
            if not self.in_range(i, j) or self.get(i, j) != -value:
                continue
            temp = 0
            while True:
                temp |= self.bit(i, j)
                i += dx
                j += dy
                if not self.in_range(i, j) or self.get(i, j) != -value:
                    break
            if self.in_range(i, j) and self.get(i, j) == value:
                diff |= temp
        return diff

    def has_legal_move(self, value: int) -> bool:
        size = self.size
        for i in range(size):
            for j in range(size):
                if not self.get(i, j) and self.legal(i, j, value):
                    return True
        return False

    def check(self) -> MoveResult:
        def total(board: int) -> int:
            count = 0
            for i in range(self.area):
                count += 1 if board & 1 << i else 0
            return count

        b_count = total(self.b_board)
        w_count = total(self.w_board)
        sign = lambda a: 1 if a > 0 else -1 if a < 0 else 0
        return MoveResult(sign(b_count - w_count))

    def update(self, x: int, y: int) -> Optional[MoveResult]:
        moveside = self.moveside
        diff = self.legal(x, y, moveside)
        if not diff:
            return MoveResult.ILLEGAL
        self.w_board ^= diff
        self.b_board ^= diff
        self.push(x, y)
        if self.is_full():
            return MoveResult(self.check())
        if not self.has_legal_move(-moveside):
            if not self.has_legal_move(moveside):
                return self.check()
            return MoveResult.SKIP
