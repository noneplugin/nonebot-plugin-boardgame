from enum import Enum
from typing import List, Union, Optional
from nonebot_plugin_htmlrender import get_new_page

from .svg import Svg, SvgOptions


class Rule:
    def __init__(self):
        self.name: str = ""
        self.size: int = 10
        self.placement: str = "cross"  # 'grid' or 'cross'
        self.allow_skip: bool = False
        self.allow_repent: bool = True

    def create(self, game: "Game") -> Optional[str]:
        self.game = game

    def update(self, x: int, y: int, value: int) -> Optional[Union["MoveResult", str]]:
        pass


class MoveResult(Enum):
    P1WIN = 1
    P2WIN = -1
    DRAW = -2
    SKIP = 2
    ILLEGAL = 3


class Player:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

    def __eq__(self, player: "Player") -> bool:
        return self.id == player.id

    def __str__(self) -> str:
        return self.name


class Game:
    def __init__(self, rule: Rule, size: int):
        self.p1: Optional[Player] = None
        self.p2: Optional[Player] = None
        self.next: Optional[Player] = None

        self.rule = rule
        self.name = rule.name
        self.size = size or rule.size
        self.placement = rule.placement
        self.allow_skip = rule.allow_skip
        self.allow_repent = rule.allow_repent

        self.b_board: int = 0
        self.w_board: int = 0
        self.area: int = size * size
        self.history: List[int] = []
        self.full: int = (1 << self.area) - 1

    def update(self, x: int, y: int, value: int) -> Optional[Union[MoveResult, str]]:
        return self.rule.update(x, y, value)

    def get_p_board(self):
        return self.w_board if self.next == self.p2 else self.b_board

    def set_p_board(self, value: int):
        if self.next == self.p2:
            self.w_board = value
        else:
            self.b_board = value

    def get_n_board(self):
        return self.b_board if self.next == self.p2 else self.w_board

    def set_n_board(self, value: int):
        if self.next == self.p2:
            self.b_board = value
        else:
            self.w_board = value

    def is_full(self):
        return not ((self.b_board | self.w_board) ^ self.full)

    def bit(self, x: int, y: int):
        return 1 << (x * self.size + y)

    def in_range(self, x: int, y: int) -> bool:
        return x >= 0 and y >= 0 and x < self.size and y < self.size

    def get(self, x: int, y: int) -> int:
        if not self.in_range(x, y):
            return 0
        p = 1 << (x * self.size + y)
        if p & self.b_board:
            return 1
        if p & self.w_board:
            return -1
        return 0

    def set(self, x: int, y: int, value: int) -> int:
        chess = self.bit(x, y)
        if value == 1:
            self.w_board &= ~chess
            self.b_board |= chess
            return self.b_board
        elif value == -1:
            self.b_board &= ~chess
            self.w_board |= chess
            return self.w_board
        else:
            self.w_board &= ~chess
            self.b_board &= ~chess
            return 0

    def save(self):
        board = (self.w_board << self.area) + self.b_board
        if board:
            self.history.append(board)

    def refresh(self):
        board = self.history[-1]
        self.w_board = board >> self.area
        self.b_board = board & self.full

    def draw_svg(self, x: Optional[int] = None, y: Optional[int] = None):
        size = self.size
        placement = self.placement
        view_size = size + (2 if placement == "cross" else 3)
        svg = Svg(SvgOptions(view_size=view_size, size=max(512, view_size * 32))).fill(
            "white"
        )

        line_group = svg.g(
            {
                "stroke": "black",
                "stroke-width": 0.08,
                "stroke-linecap": "round",
            }
        )

        text_group = svg.g(
            {
                "font-size": "0.75",
                "font-weight": "normal",
                "style": "font-family: Sans; letter-spacing: 0",
            }
        )

        top_text_group = text_group.g({"text-anchor": "middle"})
        left_text_group = text_group.g({"text-anchor": "right"})
        mask_group = svg.g({"fill": "white"})
        black_group = svg.g({"fill": "black"})
        white_group = svg.g(
            {
                "fill": "white",
                "stroke": "black",
                "stroke-width": 0.08,
            }
        )

        vertical_offset = 0.3 if placement == "cross" else 0.8
        horizontal_offset = 0 if placement == "cross" else 0.5
        for index in range(2, view_size):
            line_group.line(index, 2, index, view_size - 1)
            line_group.line(2, index, view_size - 1, index)
            if index < size + 2:
                top_text_group.text(str(index - 1), index + horizontal_offset, 1.3)
                left_text_group.text(chr(index + 63), 0.8, index + vertical_offset)

        for i in range(size):
            for j in range(size):
                value = self.get(i, j)
                if not value:
                    if (
                        size >= 13
                        and size % 2 == 1
                        and (i == 3 or i == size - 4 or i * 2 == size - 1)
                        and (j == 3 or j == size - 4 or j * 2 == size - 1)
                    ):
                        line_group.circle(j + 2, i + 2, 0.08)
                    continue

                offset = 2.5
                if placement == "cross":
                    mask_group.rect(j + 1.48, i + 1.48, j + 2.52, i + 2.52)
                    offset = 2
                white_mark = 0.08
                black_mark = 0.12
                cx = j + offset
                cy = i + offset
                if value == 1:
                    black_group.circle(cx, cy, 0.36)
                    if x == i and y == j:
                        black_group.rect(
                            cx - black_mark,
                            cy - black_mark,
                            cx + black_mark,
                            cy + black_mark,
                            {"fill": "white"},
                        )
                else:
                    white_group.circle(cx, cy, 0.32)
                    if x == i and y == j:
                        white_group.rect(
                            cx - white_mark,
                            cy - white_mark,
                            cx + white_mark,
                            cy + white_mark,
                            {"fill": "black"},
                        )
        return svg

    async def draw(self, x: Optional[int] = None, y: Optional[int] = None) -> bytes:
        svg = self.draw_svg(x, y)
        async with get_new_page() as page:
            html = f'<html><body style="margin: 0;">{svg.outer()}</body></html>'
            await page.set_content(html)
            return await page.screenshot(
                clip={"x": 0, "y": 0, "width": svg.width, "height": svg.height}
            )
