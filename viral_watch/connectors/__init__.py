from .base import Connector
from .x import XConnector
from .tiktok import TikTokConnector
from .instagram import InstagramConnector
from .facebook import FacebookConnector
from .demo import DemoConnector

ALL = [XConnector, TikTokConnector, InstagramConnector, FacebookConnector]


def enabled(demo: bool = False) -> list[Connector]:
    conns: list[Connector] = [c() for c in ALL]
    conns = [c for c in conns if c.configured()]
    if demo:
        conns.append(DemoConnector())
    return conns
