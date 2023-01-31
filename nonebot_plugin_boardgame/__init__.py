import shlex
import asyncio
from asyncio import TimerHandle
from dataclasses import dataclass
from typing import Dict, List, Optional, NoReturn, Union

from nonebot.matcher import Matcher
from nonebot.exception import ParserExit
from nonebot.plugin import PluginMetadata
from nonebot.rule import Rule, ArgumentParser
from nonebot import on_command, on_shell_command, require
from nonebot.params import EventToMe, CommandArg, CommandStart, ShellCommandArgv

from nonebot.adapters.onebot.v11 import Bot as V11Bot
from nonebot.adapters.onebot.v11 import Message as V11Msg
from nonebot.adapters.onebot.v11 import MessageSegment as V11MsgSeg
from nonebot.adapters.onebot.v11 import MessageEvent as V11MEvent
from nonebot.adapters.onebot.v11 import GroupMessageEvent as V11GMEvent
from nonebot.adapters.onebot.v11 import PrivateMessageEvent as V11PMEvent

from nonebot.adapters.onebot.v12 import Bot as V12Bot
from nonebot.adapters.onebot.v12 import Message as V12Msg
from nonebot.adapters.onebot.v12 import MessageSegment as V12MsgSeg
from nonebot.adapters.onebot.v12 import MessageEvent as V12MEvent
from nonebot.adapters.onebot.v12 import GroupMessageEvent as V12GMEvent
from nonebot.adapters.onebot.v12 import PrivateMessageEvent as V12PMEvent
from nonebot.adapters.onebot.v12 import ChannelMessageEvent as V12CMEvent

require("nonebot_plugin_datastore")
require("nonebot_plugin_htmlrender")

from .go import Go
from .gomoku import Gomoku
from .othello import Othello
from .game import Game, MoveResult, Player, Pos

__plugin_meta__ = PluginMetadata(
    name="棋类游戏",
    description="五子棋、黑白棋、围棋",
    usage=(
        "@我 + “五子棋”、“黑白棋”、“围棋”开始一局游戏;\n"
        "再发送“落子 字母+数字”下棋，如“落子 A1”;\n"
        "发送“结束下棋”结束当前棋局；发送“显示棋盘”显示当前棋局"
    ),
    extra={
        "unique_name": "boardgame",
        "example": "@小Q 五子棋\n落子 G8\n结束下棋",
        "author": "meetwq <meetwq@gmail.com>",
        "version": "0.2.0",
    },
)


parser = ArgumentParser("boardgame", description="棋类游戏")
parser.add_argument("-r", "--rule", help="棋局规则")
group = parser.add_mutually_exclusive_group()
group.add_argument("-e", "--stop", "--end", action="store_true", help="停止下棋")
group.add_argument("-v", "--show", "--view", action="store_true", help="显示棋盘")
group.add_argument("--skip", action="store_true", help="跳过回合")
group.add_argument("--repent", action="store_true", help="悔棋")
group.add_argument("--reload", action="store_true", help="重新加载已停止的游戏")
parser.add_argument("--white", action="store_true", help="后手")
parser.add_argument("position", nargs="?", help="落子位置")


boardgame = on_shell_command("boardgame", parser=parser, block=True, priority=13)


@boardgame.handle()
async def _(
    bot: Union[V11Bot, V12Bot],
    matcher: Matcher,
    event: Union[V11MEvent, V12MEvent],
    argv: List[str] = ShellCommandArgv(),
):
    await handle_boardgame(bot, matcher, event, argv)


def shortcut(cmd: str, argv: List[str] = [], **kwargs):
    command = on_command(cmd, **kwargs, block=True, priority=13)

    @command.handle()
    async def _(
        bot: Union[V11Bot, V12Bot],
        matcher: Matcher,
        event: Union[V11MEvent, V12MEvent],
        msg: Union[V11Msg, V12Msg] = CommandArg(),
    ):
        try:
            args = shlex.split(msg.extract_plain_text().strip())
        except:
            args = []
        await handle_boardgame(bot, matcher, event, argv + args)


def get_cid(bot: Union[V11Bot, V12Bot], event: Union[V11MEvent, V12MEvent]):
    if isinstance(event, V11MEvent):
        cid = f"{bot.self_id}_{event.sub_type}_"
    else:
        cid = f"{bot.self_id}_{event.detail_type}_"

    if isinstance(event, V11GMEvent) or isinstance(event, V12GMEvent):
        cid += str(event.group_id)
    elif isinstance(event, V12CMEvent):
        cid += f"{event.guild_id}_{event.channel_id}"
    else:
        cid += str(event.user_id)

    return cid


def game_running(
    bot: Union[V11Bot, V12Bot], event: Union[V11MEvent, V12MEvent]
) -> bool:
    cid = get_cid(bot, event)
    return bool(games.get(cid, None))


# 命令前缀为空则需要to_me，否则不需要
def smart_to_me(command_start: str = CommandStart(), to_me: bool = EventToMe()) -> bool:
    return bool(command_start) or to_me


def not_private(event: Union[V11MEvent, V12MEvent]) -> bool:
    return not (isinstance(event, V11PMEvent) or isinstance(event, V12PMEvent))


shortcut("五子棋", ["--rule", "gomoku"], rule=Rule(smart_to_me) & not_private)
shortcut(
    "黑白棋", ["--rule", "othello"], aliases={"奥赛罗"}, rule=Rule(smart_to_me) & not_private
)
shortcut("围棋", ["--rule", "go"], rule=Rule(smart_to_me) & not_private)
shortcut("停止下棋", ["--stop"], aliases={"结束下棋", "停止游戏", "结束游戏"}, rule=game_running)
shortcut("查看棋盘", ["--show"], aliases={"查看棋局", "显示棋盘", "显示棋局"}, rule=game_running)
shortcut("跳过回合", ["--skip"], rule=game_running)
shortcut("悔棋", ["--repent"], rule=game_running)
shortcut("落子", rule=game_running)
shortcut("重载五子棋棋局", ["--rule", "gomoku", "--reload"], aliases={"恢复五子棋棋局"})
shortcut("重载黑白棋棋局", ["--rule", "othello", "--reload"], aliases={"恢复黑白棋棋局"})
shortcut("重载围棋棋局", ["--rule", "go", "--reload"], aliases={"恢复围棋棋局"})


@dataclass
class Options:
    rule: str = ""
    stop: bool = False
    show: bool = False
    skip: bool = False
    repent: bool = False
    reload: bool = False
    white: bool = False
    position: str = ""


games: Dict[str, Game] = {}
timers: Dict[str, TimerHandle] = {}


async def stop_game(matcher: Matcher, cid: str):
    timers.pop(cid, None)
    if games.get(cid, None):
        game = games.pop(cid)
        await matcher.finish(f"{game.name}下棋超时，游戏结束，可发送“重载{game.name}棋局”继续下棋")


def set_timeout(matcher: Matcher, cid: str, timeout: float = 600):
    timer = timers.get(cid, None)
    if timer:
        timer.cancel()
    loop = asyncio.get_running_loop()
    timer = loop.call_later(
        timeout, lambda: asyncio.ensure_future(stop_game(matcher, cid))
    )
    timers[cid] = timer


async def handle_boardgame(
    bot: Union[V11Bot, V12Bot],
    matcher: Matcher,
    event: Union[V11MEvent, V12MEvent],
    argv: List[str],
):
    async def new_player(event: Union[V11MEvent, V12MEvent]) -> Player:
        user_id = event.get_user_id()
        user_name = ""
        if isinstance(event, V11MEvent):
            user_name = event.sender.card or event.sender.nickname or ""
        else:
            assert isinstance(bot, V12Bot)
            resp = await bot.get_user_info(user_id=user_id)
            user_name = resp["user_displayname"] or resp["user_name"]
        return Player(user_id, user_name)

    async def send(
        message: Optional[str] = None, image: Optional[bytes] = None
    ) -> NoReturn:
        if not (message or image):
            await matcher.finish()

        if isinstance(bot, V11Bot):
            msg = V11Msg()
            if message:
                msg.append(message)
            if image:
                msg.append(V11MsgSeg.image(image))
        else:
            msg = V12Msg()
            if message:
                msg.append(message)
            if image:
                resp = await bot.upload_file(type="data", name="boardgame", data=image)
                file_id = resp["file_id"]
                msg.append(V12MsgSeg.image(file_id))
        await matcher.finish(msg)

    try:
        args = parser.parse_args(argv)
    except ParserExit as e:
        if e.status == 0:
            await send(__plugin_meta__.usage)
        await send()

    options = Options(**vars(args))

    cid = get_cid(bot, event)
    if not games.get(cid, None):
        if options.stop or options.show or options.repent or options.skip:
            await send("没有正在进行的游戏")

        if not options.rule:
            await send("@我 + “五子棋”、“黑白棋”、“围棋”开始一局游戏。")

        rule = options.rule
        if rule in ["go", "围棋"]:
            Game = Go
        elif rule in ["gomoku", "五子棋"]:
            Game = Gomoku
        elif rule in ["othello", "黑白棋"]:
            Game = Othello
        else:
            await send("没有找到对应的规则，目前支持：围棋(go)、五子棋(gomoku)、黑白棋(othello)")

        if options.reload:
            game = await Game.load_record(cid)
            if not game:
                await matcher.finish("没有找到被中断的游戏")
            games[cid] = game
            await send(
                (
                    f"游戏发起时间：{game.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"黑方：{game.player_black}\n"
                    f"白方：{game.player_white}\n"
                    f"下一手轮到：{game.player_next}"
                ),
                await game.draw(),
            )

        game = Game()
        player = await new_player(event)
        if options.white:
            game.player_white = player
        else:
            game.player_black = player

        games[cid] = game
        set_timeout(matcher, cid)
        await game.save_record(cid)
        await send(
            f"{player} 发起了游戏 {game.name}！\n发送“落子 字母+数字”下棋，如“落子 A1”", await game.draw()
        )

    game = games[cid]
    set_timeout(matcher, cid)
    player = await new_player(event)

    if options.stop:
        if (not game.player_white or game.player_white != player) and (
            not game.player_black or game.player_black != player
        ):
            await send("只有游戏参与者才能结束游戏")
        game = games.pop(cid)
        await send(f"游戏已结束，可发送“重载{game.name}棋局”继续下棋")

    if options.show:
        await send(image=await game.draw())

    if options.rule:
        await send("当前有正在进行的游戏，可发送“停止下棋”结束游戏")

    if (
        game.player_black
        and game.player_white
        and game.player_black != player
        and game.player_white != player
    ):
        await send("游戏已经开始，无法加入")

    if options.skip:
        if not game.allow_skip:
            await send("当前游戏不允许跳过回合")
        if game.player_next and game.player_next != player:
            await send("当前不是你的回合")
        game.update(Pos.null())
        await game.save_record(cid)
        msg = f"{player} 选择跳过其回合"
        if game.player_next:
            msg += f"，下一手轮到 {game.player_next}"
        await send(msg)

    if options.repent:
        if len(game.history) <= 1:
            await matcher.finish("对局尚未开始")
        if game.player_last and game.player_last != player:
            await send("上一手棋不是你所下")
        game.pop()
        await game.save_record(cid)
        await send(f"{player} 进行了悔棋", await game.draw())

    if (game.player_next and game.player_next != player) or (
        game.player_last and game.player_last == player
    ):
        await send("当前不是你的回合")

    position = options.position
    if not position:
        await send("发送“落子 字母+数字”下棋，如“落子 A1”")

    try:
        pos = Pos.from_str(position)
    except ValueError:
        await send("请发送正确的坐标")

    if not game.in_range(pos):
        await send("落子超出边界")

    if game.get(pos):
        await send("此处已有落子")

    try:
        result = game.update(pos)
    except ValueError as e:
        await send(f"非法落子：{e}")

    if game.player_last:
        msg = f"{player} 落子于 {position.upper()}"
    else:
        if not game.player_black:
            game.player_black = player
        elif not game.player_white:
            game.player_white = player
        msg = f"{player} 加入了游戏并落子于 {position.upper()}"

    if result == MoveResult.ILLEGAL:
        await send("非法落子")
    elif result == MoveResult.SKIP:
        msg += f"，下一手依然轮到 {player}"
    elif result:
        games.pop(cid)
        game.is_game_over = True
        if result == MoveResult.BLACK_WIN:
            msg += f"，恭喜 {game.player_black} 获胜！"
        elif result == MoveResult.WHITE_WIN:
            msg += f"，恭喜 {game.player_white} 获胜！"
        elif result == MoveResult.DRAW:
            msg += f"，本局游戏平局"
    else:
        if game.player_next:
            msg += f"，下一手轮到 {game.player_next}"
    await game.save_record(cid)
    await send(msg, await game.draw())
