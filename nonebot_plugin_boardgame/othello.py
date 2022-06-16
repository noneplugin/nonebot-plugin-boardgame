from typing import Optional

from .game import Game, MoveResult, Placement, Pos


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
        self.set(Pos(mid - 1, mid - 1), -1)
        self.set(Pos(mid - 1, mid), 1)
        self.set(Pos(mid, mid - 1), 1)
        self.set(Pos(mid, mid), -1)

    def legal(self, pos: Pos, value: int) -> int:
        diff = 0
        for (dx, dy) in delta:
            p = Pos(pos.x + dx, Pos.y + dy)
            if not self.in_range(p) or self.get(p) != -value:
                continue
            temp = 0
            while True:
                temp |= self.bit(p)
                p.x += dx
                p.y += dy
                if not self.in_range(p) or self.get(p) != -value:
                    break
            if self.in_range(p) and self.get(p) == value:
                diff |= temp
        return diff

    def has_legal_move(self, value: int) -> bool:
        size = self.size
        for i in range(size):
            for j in range(size):
                p = Pos(i, j)
                if not self.get(p) and self.legal(p, value):
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

    def update(self, pos: Pos) -> Optional[MoveResult]:
        moveside = self.moveside
        diff = self.legal(pos, moveside)
        if not diff:
            return MoveResult.ILLEGAL
        self.w_board ^= diff
        self.b_board ^= diff
        self.push(pos)
        if self.is_full():
            return MoveResult(self.check())
        if not self.has_legal_move(-moveside):
            if not self.has_legal_move(moveside):
                return self.check()
            return MoveResult.SKIP
