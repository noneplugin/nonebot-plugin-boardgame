## nonebot-plugin-boardgame

适用于 [Nonebot2](https://github.com/nonebot/nonebot2) 的棋类游戏插件。

抄自隔壁 koishi（：[koishi-plugin-chess](https://github.com/koishijs/koishi-plugin-chess)


### 安装

- 使用 nb-cli

```
nb plugin install nonebot_plugin_boardgame
```

- 使用 pip

```
pip install nonebot_plugin_boardgame
```


### 使用

目前支持的规则有：

- 五子棋
- 围棋（禁全同，暂时不支持点目）
- 黑白棋

**以下命令需要加[命令前缀](https://v2.nonebot.dev/docs/api/config#Config-command_start) (默认为`/`)，可自行设置为空**

#### 开始和停止棋局

@机器人 发送 “围棋” 或 “五子棋” 或 “黑白棋” 开始一个对应的棋局，一个群组内同时只能有一个棋局。

或者使用 `boardgame` 指令：

```
boardgame --rule <rule> [--size <size>]
```

| 快捷名 | 规则名 | 默认大小 |
|:-:|:-:|:-:|
| 围棋 | go | 19 |
| 五子棋 | gomoku | 15 |
| 黑白棋 / 奥赛罗 | othello | 8 |

输入 `停止下棋` 或者 `boardgame --stop` 可以停止一个正在进行的棋局。

#### 落子，悔棋和跳过

输入 `落子 position` 如 `落子 A1` 或者 `boardgame position` 进行下棋。

当棋局开始时，第一个落子的人为先手，第二个落子的人为后手，此时棋局正式形成，其他人无法继续加入游戏。而参与游戏的两人可以依次使用“落子”指令进行游戏。

输入 `悔棋` 或者 `boardgame --repent` 进行悔棋，游戏会向前倒退一步。

输入 `跳过回合` 或者 `boardgame --skip` 可以跳过一个回合。

输入 `查看棋局` 或者 `boardgame --view` 可以查看当前棋局。
