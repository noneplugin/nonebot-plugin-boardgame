import re
import shlex
from dataclasses import dataclass
from typing import Dict, List, Optional, NoReturn, Type

from nonebot.matcher import Matcher
from nonebot.exception import ParserExit
from nonebot.rule import to_me, ArgumentParser
from nonebot import on_command, on_shell_command
from nonebot.params import ShellCommandArgv, CommandArg
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment

from .go import Go
from .gomoku import Gomoku
from .othello import Othello
from .game import Rule, Game, MoveResult, Player

__help__plugin_name__ = "chess"
__des__ = "棋类游戏"
__cmd__ = """
@我 + “五子棋”、“黑白棋”、“围棋”开始一局游戏;
再发送“落子 字母+数字”下棋，如“落子 A1”;
发送“结束下棋”结束当前棋局
""".strip()
__short_cmd__ = "五子棋、黑白棋、围棋"
__example__ = """
@小Q 五子棋
落子 G8
结束下棋
""".strip()
__usage__ = f"{__des__}\nUsage:\n{__cmd__}\nExample:\n{__example__}"


parser = ArgumentParser("chess", description="棋类游戏")
group = parser.add_mutually_exclusive_group()
group.add_argument("-r", "--rule", help="棋局规则，目前支持：围棋(go)、五子棋(gomoku)、黑白棋/奥赛罗(othello)")
group.add_argument("-e", "--stop", "--end", action="store_true", help="停止下棋")
group.add_argument("-v", "--show", "--view", action="store_true", help="显示棋盘")
group.add_argument("--skip", action="store_true", help="跳过回合")
group.add_argument("--repent", action="store_true", help="悔棋")
parser.add_argument("-s", "--size", type=int, help="棋盘大小")
parser.add_argument("position", nargs="?", help="落子位置")


chess = on_shell_command("chess", parser=parser, block=True, priority=13)


@chess.handle()
async def _(
    matcher: Matcher, event: GroupMessageEvent, argv: List[str] = ShellCommandArgv()
):
    await handle_chess(matcher, event, argv)


def shortcut(cmd: str, argv: List[str] = [], **kwargs):
    command = on_command(cmd, **kwargs, block=True, priority=13)

    @command.handle()
    async def _(
        matcher: Matcher, event: GroupMessageEvent, msg: Message = CommandArg()
    ):
        try:
            args = shlex.split(msg.extract_plain_text().strip())
        except:
            args = []
        await handle_chess(matcher, event, argv + args)


shortcut("下棋", rule=to_me())
shortcut("五子棋", ["--rule", "gomoku", "--size", "15"], rule=to_me())
shortcut("黑白棋", ["--rule", "othello", "--size", "8"], aliases={"奥赛罗"}, rule=to_me())
shortcut("围棋", ["--rule", "go", "--size", "19"], rule=to_me())
shortcut("停止下棋", ["--stop"], aliases={"结束下棋", "停止游戏", "结束游戏"})
shortcut("查看棋盘", ["--show"], aliases={"查看棋局", "显示棋盘", "显示棋局"})
shortcut("跳过回合", ["--skip"])
shortcut("悔棋", ["--repent"])
shortcut("落子")


def new_player(event: GroupMessageEvent) -> Player:
    return Player(event.user_id, event.sender.card or event.sender.nickname or "")


@dataclass
class Options:
    rule: str = ""
    size: int = 0
    stop: bool = False
    show: bool = False
    skip: bool = False
    repent: bool = False
    position: str = ""


rules: Dict[str, Type[Rule]] = {
    "go": Go,
    "gomoku": Gomoku,
    "othello": Othello,
}


games: Dict[str, Game] = {}


async def handle_chess(matcher: Matcher, event: GroupMessageEvent, argv: List[str]):
    async def send(
        message: Optional[str] = None, image: Optional[bytes] = None
    ) -> NoReturn:
        if not (message or image):
            await matcher.finish()
        msg = Message()
        if message:
            msg.append(message)
        if image:
            msg.append(MessageSegment.image(image))
        await matcher.finish(msg)

    try:
        args = parser.parse_args(argv)
    except ParserExit as e:
        if e.status == 0:
            await send(e.message)
        await send()

    options = Options(**vars(args))

    cid = str(event.group_id)
    if not games.get(cid, None):
        if (
            options.position
            or options.stop
            or options.show
            or options.skip
            or options.repent
        ):
            await send("没有正在进行的游戏")

        if options.size and (options.size < 2 or options.size > 20):
            await send("棋盘大小应该为不小于 2，不大于 20 的整数")

        if not options.rule:
            await send("@我 + “五子棋”、“黑白棋”、“围棋”开始一局游戏。")

        if options.rule not in rules:
            await send("没有找到对应的规则")

        rule = rules[options.rule]()
        game = Game(rule, options.size)
        game.p1 = new_player(event)

        result = rule.create(game)
        if result:
            await send(result)

        games[cid] = game
        await send(
            f"{game.p1} 发起了游戏 {game.name}！\n发送“落子 字母+数字”下棋，如“落子 A1”", await game.draw()
        )

    if options.stop:
        games.pop(cid)
        await send("游戏已停止")

    game = games[cid]

    if options.show:
        await send(image=await game.draw())

    if options.rule or options.size:
        await send("当前有正在进行的游戏，可发送“停止下棋”结束游戏")

    player = new_player(event)
    if game.p2 and game.p1 != player and game.p2 != player:
        await send("游戏已经开始，无法加入")

    if not game.next and (options.skip or options.repent):
        await send("对局尚未开始")

    if options.skip:
        if game.next != player:
            await send("当前不是你的回合")
        if not game.allow_skip:
            await send("当前规则不允许跳过回合")
        game.next = game.p2 if game.p1 == player else game.p1
        await send(f"{player} 选择跳过其回合，下一手轮到 {game.next}")

    if options.repent:
        last = game.p2 if game.p1 == game.next else game.p1
        if last != player:
            await send("上一手棋不是你所下")
        game.history.pop()
        game.refresh()
        game.next = last
        await send(f"{player} 进行了悔棋", await game.draw())

    if game.p2 and player != game.next:
        await send("当前不是你的回合")

    if not game.p2 and game.p1 and player == game.p1 and len(game.history) >= 1:
        await send("当前不是你的回合，请等待新的玩家加入")

    position = options.position
    if not position:
        await send("发送“落子 字母+数字”下棋，如“落子 A1”")

    match_obj = re.match(r"^([a-z])(\d+)$", position, re.IGNORECASE)
    if not match_obj:
        await send("请发送正确的坐标")

    x = (ord(match_obj.group(1).lower()) - ord("a")) % 32
    y = int(match_obj.group(2)) - 1

    if x < 0 or x >= game.size or y < 0 or y >= game.size:
        await send("落子超出边界")

    if game.get(x, y):
        await send("此处已有落子")

    message = ""
    if game.p2:
        message = f"{player} 落子于 {position.upper()}"
    else:
        message = f"{player} 加入了游戏并落子于 {position.upper()}"
        if len(game.history) < 1:
            if player != game.p1:
                game.p2 = game.p1
                game.p1 = player
            else:
                message = f"{player} 落子于 {position.upper()}"
        else:
            game.p2 = player

    value = 1 if player == game.p1 else -1
    result = game.update(x, y, value)

    if result == MoveResult.ILLEGAL:
        game.next = player
        await send("非法落子")
    elif result == MoveResult.SKIP:
        message += f"，下一手依然轮到 {player}"
    elif result == MoveResult.P1WIN:
        games.pop(cid)
        message += f"，恭喜 {game.p1} 获胜！"
    elif result == MoveResult.P2WIN:
        games.pop(cid)
        message += f"，恭喜 {game.p2} 获胜！"
    elif result == MoveResult.DRAW:
        games.pop(cid)
        message += f"，本局游戏平局"
    elif isinstance(result, str):
        game.next = player
        await send(f"非法落子（{result}）")
    else:
        if game.p1 and game.p2:
            game.next = game.p2 if player == game.p1 else game.p1
            if game.next:
                message += f"，下一手轮到 {game.next}"
    game.save()
    await send(message, await game.draw(x, y))
