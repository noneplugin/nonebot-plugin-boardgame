from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional
from nonebot_plugin_htmlrender import html_to_pic

from .svg import Svg, SvgOptions


class MoveResult(Enum):
    BLACK_WIN = 1
    WHITE_WIN = -1
    DRAW = -2
    SKIP = 2
    ILLEGAL = 3


class Placement(Enum):
    CROSS = 0
    GRID = 1


class Player:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

    def __eq__(self, player: "Player") -> bool:
        return self.id == player.id

    def __str__(self) -> str:
        return self.name


@dataclass
class History:
    b_board: int
    w_board: int
    moveside: int
    last_position: Optional[Tuple[int, int]]


class Game:
    def __init__(
        self,
        name: str,
        size: int,
        placement: Placement = Placement.CROSS,
        allow_skip: bool = False,
        allow_repent: bool = True,
    ):
        self.name: str = name
        self.size: int = size
        self.placement: Placement = placement
        self.allow_skip: bool = allow_skip
        self.allow_repent: bool = allow_repent

    def setup(self):
        self.player_white: Optional[Player] = None
        self.player_black: Optional[Player] = None
        self.moveside: int = 1
        """1 代表黑方，-1 代表白方"""
        self.last_position: Optional[Tuple[int, int]] = None
        self.history: List[History] = []
        self.b_board: int = 0
        self.w_board: int = 0
        self.area: int = self.size * self.size
        self.full: int = (1 << self.area) - 1
        self.save()

    def update(self, x: int, y: int) -> Optional[MoveResult]:
        raise NotImplementedError

    @property
    def player_next(self) -> Optional[Player]:
        return self.player_black if self.moveside == 1 else self.player_white

    @property
    def player_last(self) -> Optional[Player]:
        return self.player_white if self.moveside == 1 else self.player_black

    def is_full(self):
        return not ((self.b_board | self.w_board) ^ self.full)

    def bit(self, x: int, y: int) -> int:
        return 1 << (x * self.size + y)

    def in_range(self, x: int, y: int) -> bool:
        return x >= 0 and y >= 0 and x < self.size and y < self.size

    def get(self, x: int, y: int) -> int:
        bit = self.bit(x, y)
        if self.b_board & bit:
            return 1
        if self.w_board & bit:
            return -1
        return 0

    def set(self, x: int, y: int, value: int):
        bit = self.bit(x, y)
        if value == 1:
            self.w_board &= ~bit
            self.b_board |= bit
        elif value == -1:
            self.b_board &= ~bit
            self.w_board |= bit
        else:
            self.w_board &= ~bit
            self.b_board &= ~bit

    def push(self, x: int, y: int):
        self.set(x, y, self.moveside)
        self.moveside = -self.moveside
        self.last_position = (x, y)
        self.save()

    def save(self):
        history = History(self.b_board, self.w_board, self.moveside, self.last_position)
        self.history.append(history)

    def pop(self):
        self.history.pop()
        history = self.history[-1]
        self.b_board = history.b_board
        self.w_board = history.w_board
        self.moveside = history.moveside
        self.last_position = history.last_position

    def draw_svg(self):
        size = self.size
        placement = self.placement
        view_size = size + (3 if placement == Placement.CROSS else 4)
        svg = Svg(SvgOptions(view_size=view_size, size=view_size * 50)).fill("white")

        line_group = svg.g(
            {
                "stroke": "black",
                "stroke-width": 0.08,
                "stroke-linecap": "round",
            }
        )

        text_group = svg.g(
            {
                "font-size": "0.6",
                "font-weight": "normal",
                "style": "font-family: Sans; letter-spacing: 0",
            }
        )

        top_text_group = text_group.g({"text-anchor": "middle"})
        left_text_group = text_group.g({"text-anchor": "end"})
        bottom_text_group = text_group.g({"text-anchor": "middle"})
        right_text_group = text_group.g({"text-anchor": "start"})
        mask_group = svg.g({"fill": "white"})
        black_group = svg.g({"fill": "black"})
        white_group = svg.g(
            {
                "fill": "white",
                "stroke": "black",
                "stroke-width": 0.08,
            }
        )

        vertical_offset = 0.3 if placement == Placement.CROSS else 0.8
        horizontal_offset = 0 if placement == Placement.CROSS else 0.5
        for index in range(2, view_size - 1):
            line_group.line(index, 2, index, view_size - 2)
            line_group.line(2, index, view_size - 2, index)
            if index < size + 2:
                top_text_group.text(str(index - 1), index + horizontal_offset, 1.3)
                left_text_group.text(chr(index + 63), 1.3, index + vertical_offset)
                bottom_text_group.text(
                    str(index - 1), index + horizontal_offset, view_size - 0.8
                )
                right_text_group.text(
                    chr(index + 63), view_size - 1.3, index + vertical_offset
                )

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
                if placement == Placement.CROSS:
                    mask_group.rect(j + 1.48, i + 1.48, j + 2.52, i + 2.52)
                    offset = 2
                white_mark = 0.08
                black_mark = 0.12
                cx = j + offset
                cy = i + offset
                if value == 1:
                    black_group.circle(cx, cy, 0.36)
                    if self.last_position:
                        x, y = self.last_position
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
                    if self.last_position:
                        x, y = self.last_position
                        if x == i and y == j:
                            white_group.rect(
                                cx - white_mark,
                                cy - white_mark,
                                cx + white_mark,
                                cy + white_mark,
                                {"fill": "black"},
                            )
        return svg

    async def draw(self) -> bytes:
        svg = self.draw_svg()
        return await html_to_pic(
            f'<html><body style="margin: 0;">{svg.outer()}</body></html>',
            viewport={"width": 100, "height": 100},
        )
