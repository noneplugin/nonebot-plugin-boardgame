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


@机器人 发送 “围棋” 或 “五子棋” 或 “黑白棋” 开始一个对应的棋局，一个群组内同时只能有一个棋局。

发送“落子 字母+数字”下棋，如“落子 A1”；

游戏发起者默认为先手，可使用 `--white` 选项选择后手；

发送“结束下棋”结束当前棋局；

发送“查看棋局”显示当前棋局；

发送“悔棋”可以进行悔棋；

发送“跳过回合”可跳过当前回合（仅黑白棋支持）；

手动结束游戏或超时结束游戏时，可发送“重载xx棋局”继续下棋，如 `重载围棋棋局`；


或者使用 `boardgame` 指令：

可用选项：
 - `-r RULE`, `--rule RULE`: 规则名
 - `-e`, `--stop`, `--end`: 停止下棋
 - `-v`, `--show`, `--view`: 显示棋盘
 - `--repent`: 悔棋
 - `--skip`: 跳过回合
 - `--reload`: 重新加载已停止的游戏
 - `--white`: 执白，即后手
 - `POSITION`: 落子位置


### 示例

<div align="left">
    <img src="https://s2.loli.net/2022/06/17/TbaCXSL1u4sd9rV.png" width="400" />
</div>
