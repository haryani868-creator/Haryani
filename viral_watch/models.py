from dataclasses import dataclass
from datetime import datetime


@dataclass
class Post:
    platform: str          # x, tiktok, instagram, facebook, demo
    post_id: str
    author: str
    text: str
    url: str
    created_at: datetime   # UTC, timezone-aware
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0
    keyword: str = ""

    @property
    def key(self) -> str:
        return f"{self.platform}:{self.post_id}"
