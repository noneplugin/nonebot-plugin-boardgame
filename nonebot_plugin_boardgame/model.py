from datetime import datetime

from nonebot_plugin_datastore import get_plugin_data
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

Model = get_plugin_data().Model


class GameRecord(Model):
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[str] = mapped_column(String(128))
    session_id: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(32))
    start_time: Mapped[datetime] = mapped_column(default=datetime.now())
    """ 游戏开始时间 """
    update_time: Mapped[datetime] = mapped_column(default=datetime.now())
    """ 游戏更新时间 """
    player_black_id: Mapped[str] = mapped_column(String(64), default="")
    """ 黑方id """
    player_black_name: Mapped[str] = mapped_column(Text, default="")
    """ 黑方名字 """
    player_white_id: Mapped[str] = mapped_column(String(64), default="")
    """ 白方id """
    player_white_name: Mapped[str] = mapped_column(Text, default="")
    """ 白方名字 """
    positions: Mapped[str] = mapped_column(Text, default="")
    """ 所有落子位置的字符串，以空格分隔 """
    is_game_over: Mapped[bool] = mapped_column(default=False)
    """ 游戏是否已结束 """
