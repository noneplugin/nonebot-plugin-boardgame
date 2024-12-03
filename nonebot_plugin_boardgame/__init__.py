import asyncio
from asyncio import TimerHandle
from typing import Annotated, Optional, Union

from nonebot import require
from nonebot.matcher import Matcher
from nonebot.params import Depends
from nonebot.plugin import PluginMetadata, inherit_supported_adapters
from nonebot.rule import to_me

require("nonebot_plugin_alconna")
require("nonebot_plugin_uninfo")
require("nonebot_plugin_orm")
require("nonebot_plugin_htmlrender")

from nonebot_plugin_alconna import (
    Alconna,
    AlconnaQuery,
    Args,
    Image,
    Option,
    Query,
    Text,
    UniMessage,
    on_alconna,
    store_true,
)
from nonebot_plugin_uninfo import Uninfo

from .game import Game, MoveResult, Player, Pos
from .go import Go
from .gomoku import Gomoku
from .othello import Othello

__plugin_meta__ = PluginMetadata(
    name="棋类游戏",
    description="五子棋、黑白棋、围棋",
    usage=(
        "@我 + “五子棋”、“黑白棋”、“围棋”开始一局游戏;\n"
        "再发送“落子 字母+数字”下棋，如“落子 A1”;\n"
        "发送“结束下棋”结束当前棋局；发送“显示棋盘”显示当前棋局"
    ),
    type="application",
    homepage="https://github.com/noneplugin/nonebot-plugin-boardgame",
    supported_adapters=inherit_supported_adapters(
        "nonebot_plugin_alconna", "nonebot_plugin_uninfo"
    ),
)


games: dict[str, Game] = {}
timers: dict[str, TimerHandle] = {}


def get_user_id(uninfo: Uninfo) -> str:
    return f"{uninfo.scope}_{uninfo.self_id}_{uninfo.scene_path}"


UserId = Annotated[str, Depends(get_user_id)]


def game_is_running(user_id: UserId) -> bool:
    return user_id in games


def game_not_running(user_id: UserId) -> bool:
    return user_id not in games


boardgame = on_alconna(
    Alconna(
        "boardgame",
        Option("-r|--rule", Args["rule", str], help_text="棋局规则"),
        Option("--white", default=False, action=store_true, help_text="执白，即后手"),
    ),
    rule=to_me() & game_not_running,
    use_cmd_start=True,
    block=True,
    priority=13,
)


def boardgame_wrapper(slot: Union[int, str], content: Optional[str]) -> str:
    if slot == "order" and content in ("后手", "执白"):
        return "--white"
    return ""


boardgame.shortcut(
    r"五子棋(?P<order>先手|执白|后手|执黑)?",
    {
        "prefix": True,
        "wrapper": boardgame_wrapper,
        "args": ["--rule", "gomoku", "{order}"],
    },
)
boardgame.shortcut(
    r"(?:黑白棋|奥赛罗)(?P<order>先手|执白|后手|执黑)?",
    {
        "prefix": True,
        "wrapper": boardgame_wrapper,
        "args": ["--rule", "othello", "{order}"],
    },
)
boardgame.shortcut(
    r"围棋(?P<order>先手|执白|后手|执黑)?",
    {
        "prefix": True,
        "wrapper": boardgame_wrapper,
        "args": ["--rule", "go", "{order}"],
    },
)

boardgame_show = on_alconna(
    "显示棋盘",
    aliases={"显示棋局", "查看棋盘", "查看棋局"},
    rule=game_is_running,
    use_cmd_start=True,
    block=True,
    priority=13,
)
boardgame_stop = on_alconna(
    "结束下棋",
    aliases={"结束游戏", "结束象棋"},
    rule=game_is_running,
    use_cmd_start=True,
    block=True,
    priority=13,
)
boardgame_repent = on_alconna(
    "悔棋",
    rule=game_is_running,
    use_cmd_start=True,
    block=True,
    priority=13,
)
boardgame_skip = on_alconna(
    "跳过",
    aliases={"跳过回合"},
    rule=game_is_running,
    use_cmd_start=True,
    block=True,
    priority=13,
)

boardgame_reload = on_alconna(
    Alconna(
        "重载棋局",
        Option("-r|--rule", Args["rule", str], help_text="棋局规则"),
    ),
    aliases={"恢复棋局"},
    rule=game_not_running,
    use_cmd_start=True,
    block=True,
    priority=13,
)


def reload_wrapper(slot: Union[int, str], content: Optional[str]) -> str:
    if slot == "rule":
        if content in ("五子棋",):
            return "gomoku"
        if content in ("黑白棋", "奥赛罗"):
            return "othello"
        if content in ("围棋",):
            return "go"
    return ""


boardgame_reload.shortcut(
    r"(?:重载|恢复)(?P<rule>五子棋|黑白棋|奥赛罗|围棋)棋局",
    {
        "prefix": True,
        "wrapper": reload_wrapper,
        "args": ["--rule", "{rule}"],
    },
)

boardgame_position = on_alconna(
    Alconna("落子", Args["position", str]),
    rule=game_is_running,
    use_cmd_start=True,
    block=True,
    priority=14,
)


def stop_game(user_id: str):
    if timer := timers.pop(user_id, None):
        timer.cancel()
    games.pop(user_id, None)


async def stop_game_timeout(matcher: Matcher, user_id: str):
    game = games.get(user_id, None)
    stop_game(user_id)
    if game:
        msg = f"{game.name}下棋超时，游戏结束，可发送“重载{game.name}棋局”继续下棋"
        await matcher.finish(msg)


def set_timeout(matcher: Matcher, user_id: str, timeout: float = 600):
    if timer := timers.get(user_id, None):
        timer.cancel()
    loop = asyncio.get_running_loop()
    timer = loop.call_later(
        timeout, lambda: asyncio.ensure_future(stop_game_timeout(matcher, user_id))
    )
    timers[user_id] = timer


def current_player(uninfo: Uninfo) -> Player:
    user_id = uninfo.user.id
    user_name = (
        (uninfo.member.nick if uninfo.member else None)
        or uninfo.user.nick
        or uninfo.user.name
        or ""
    )
    return Player(user_id, user_name)


CurrentPlayer = Annotated[Player, Depends(current_player)]


@boardgame.handle()
async def _(
    matcher: Matcher,
    user_id: UserId,
    uninfo: Uninfo,
    player: CurrentPlayer,
    rule: Query[str] = AlconnaQuery("rule", ""),
    white: Query[bool] = AlconnaQuery("white.value", False),
):
    if uninfo.scene.is_private:
        await matcher.finish("棋类游戏暂不支持私聊")

    if rule.result == "go":
        Game = Go
    elif rule.result == "gomoku":
        Game = Gomoku
    elif rule.result == "othello":
        Game = Othello
    else:
        await matcher.finish(
            "当前支持的规则：go（围棋）、gomoku（五子棋）、othello（黑白棋）"
        )

    game = Game()
    if white.result:
        game.player_white = player
    else:
        game.player_black = player

    games[user_id] = game
    set_timeout(matcher, user_id)
    await game.save_record(user_id)

    msg = f"{player} 发起了游戏 {game.name}！\n发送“落子 字母+数字”下棋，如“落子 A1”"
    await (Text(msg) + Image(raw=await game.draw())).send()


@boardgame_show.handle()
async def _(matcher: Matcher, user_id: UserId):
    game = games[user_id]
    set_timeout(matcher, user_id)

    await UniMessage.image(raw=await game.draw()).send()


@boardgame_stop.handle()
async def _(matcher: Matcher, user_id: UserId, player: CurrentPlayer):
    game = games[user_id]

    if (not game.player_white or game.player_white != player) and (
        not game.player_black or game.player_black != player
    ):
        await matcher.finish("只有游戏参与者才能结束游戏")
    stop_game(user_id)
    await matcher.finish(f"游戏已结束，可发送“重载{game.name}棋局”继续下棋")


@boardgame_repent.handle()
async def _(matcher: Matcher, user_id: UserId, player: CurrentPlayer):
    game = games[user_id]
    set_timeout(matcher, user_id)

    if len(game.history) <= 1:
        await matcher.finish("对局尚未开始")
    if game.player_last and game.player_last != player:
        await matcher.finish("上一手棋不是你所下")
    game.pop()
    await game.save_record(user_id)
    msg = f"{player} 进行了悔棋"
    await (Text(msg) + Image(raw=await game.draw())).send()


@boardgame_skip.handle()
async def _(matcher: Matcher, user_id: UserId, player: CurrentPlayer):
    game = games[user_id]
    set_timeout(matcher, user_id)

    if not game.allow_skip:
        await matcher.finish("当前游戏不允许跳过回合")
    if game.player_next and game.player_next != player:
        await matcher.finish("当前不是你的回合")
    game.update(Pos.null())
    await game.save_record(user_id)
    msg = f"{player} 选择跳过其回合"
    if game.player_next:
        msg += f"，下一手轮到 {game.player_next}"
    await (Text(msg) + Image(raw=await game.draw())).send()


@boardgame_reload.handle()
async def _(
    matcher: Matcher,
    user_id: UserId,
    rule: Query[str] = AlconnaQuery("rule", ""),
):
    if rule.result == "go":
        Game = Go
    elif rule.result == "gomoku":
        Game = Gomoku
    elif rule.result == "othello":
        Game = Othello
    else:
        await matcher.finish(
            "当前支持的规则：go（围棋）、gomoku（五子棋）、othello（黑白棋）"
        )

    game = await Game.load_record(user_id)
    if not game:
        await matcher.finish("没有找到被中断的游戏")
    games[user_id] = game
    set_timeout(matcher, user_id)

    msg = (
        f"游戏发起时间：{game.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"黑方：{game.player_black}\n"
        f"白方：{game.player_white}\n"
        f"下一手轮到：{game.player_next}"
    )
    await (Text(msg) + Image(raw=await game.draw())).send()


@boardgame_position.handle()
async def _(
    matcher: Matcher,
    user_id: UserId,
    player: CurrentPlayer,
    position: Query[str] = AlconnaQuery("position", ""),
):
    game = games[user_id]
    set_timeout(matcher, user_id)

    if (
        game.player_black
        and game.player_white
        and game.player_black != player
        and game.player_white != player
    ):
        await matcher.finish("游戏已经开始，无法加入")

    if (game.player_next and game.player_next != player) or (
        game.player_last and game.player_last == player
    ):
        await matcher.finish("当前不是你的回合")

    try:
        pos = Pos.from_str(position.result)
    except ValueError:
        await matcher.finish("请发送正确的坐标")

    if not game.in_range(pos):
        await matcher.finish("落子超出边界")

    if game.get(pos):
        await matcher.finish("此处已有落子")

    try:
        result = game.update(pos)
    except ValueError as e:
        await matcher.finish(f"非法落子：{e}")

    msg = UniMessage()
    if game.player_last:
        msg += f"{player} 落子于 {pos}"
    else:
        if not game.player_black:
            game.player_black = player
        elif not game.player_white:
            game.player_white = player
        msg += f"{player} 加入了游戏并落子于 {pos}"

    if result == MoveResult.ILLEGAL:
        await matcher.finish("非法落子")
    elif result == MoveResult.SKIP:
        msg += f"，下一手依然轮到 {player}\n"
    elif result:
        game.is_game_over = True
        stop_game(user_id)
        if result == MoveResult.BLACK_WIN:
            msg += f"，恭喜 {game.player_black} 获胜！\n"
        elif result == MoveResult.WHITE_WIN:
            msg += f"，恭喜 {game.player_white} 获胜！\n"
        elif result == MoveResult.DRAW:
            msg += "，本局游戏平局\n"
    else:
        if game.player_next:
            msg += f"，下一手轮到 {game.player_next}\n"
    msg += Image(raw=await game.draw())

    await game.save_record(user_id)
    await msg.send()
