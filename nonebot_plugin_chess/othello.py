from typing import Optional

from .game import Rule, Game, MoveResult


delta = ((0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1))


class Othello(Rule):
    def __init__(self):
        super().__init__()
        self.name = "黑白棋"
        self.size = 8
        self.placement = "grid"
        self.allow_skip = True

    def create(self, game: Game) -> Optional[str]:
        super().create(game)
        size = game.size
        if size % 2 != 0 or size == 2:
            return "棋盘大小应为 2 的倍数且不小于 4"
        mid = int(size / 2)
        game.set(mid - 1, mid - 1, -1)
        game.set(mid - 1, mid, 1)
        game.set(mid, mid - 1, 1)
        game.set(mid, mid, -1)

    def legal(self, x: int, y: int, value: int) -> int:
        game = self.game
        diff = 0
        for (dx, dy) in delta:
            i = x + dx
            j = y + dy
            if not game.in_range(i, j) or game.get(i, j) != -value:
                continue
            temp = 0
            while True:
                temp |= game.bit(i, j)
                i += dx
                j += dy
                if not game.in_range(i, j) or game.get(i, j) != -value:
                    break
            if game.in_range(i, j) and game.get(i, j) == value:
                diff |= temp
        return diff

    def has_legal_move(self, value: int) -> bool:
        game = self.game
        size = game.size
        for i in range(size):
            for j in range(size):
                if not game.get(i, j) and self.legal(i, j, value):
                    return True
        return False

    def total(self, length: int, board: int) -> int:
        count = 0
        for i in range(length):
            count += 1 if board & 1 << i else 0
        return count

    def check(self) -> MoveResult:
        game = self.game
        length = game.area
        b_count = self.total(length, game.b_board)
        w_count = self.total(length, game.w_board)
        sign = lambda a: 1 if a > 0 else -1 if a < 0 else 0
        return MoveResult(sign(b_count - w_count))

    def update(self, x: int, y: int, value: int) -> Optional[MoveResult]:
        game = self.game
        diff = self.legal(x, y, value)
        if not diff:
            return MoveResult.ILLEGAL
        game.w_board ^= diff
        game.b_board ^= diff
        game.set(x, y, value)
        if game.is_full():
            return MoveResult(self.check())
        if not self.has_legal_move(-value):
            if not self.has_legal_move(value):
                return self.check()
            return MoveResult.SKIP
