import os

from .base import Connector, parse_time
from ..models import Post


class InstagramConnector(Connector):
    """Instagram Graph API — carian hashtag (top_media + recent_media).

    Perlu akaun Instagram Business/Creator yang dipaut ke Page Facebook.
    Had Meta: maksimum 30 hashtag unik setiap 7 hari.
    Nota: Meta tidak memberi kiraan 'share' atau 'view' untuk hashtag media.
    """
    name = "instagram"

    def __init__(self):
        self.user_id = os.getenv("IG_USER_ID", "")
        self.token = os.getenv("IG_ACCESS_TOKEN", "")
        self.base = f"https://graph.facebook.com/{os.getenv('GRAPH_API_VERSION', 'v21.0')}"
        self._hashtag_ids: dict[str, str] = {}

    def configured(self) -> bool:
        return bool(self.user_id and self.token)

    def _hashtag_id(self, tag: str) -> str | None:
        if tag not in self._hashtag_ids:
            data = self._get(f"{self.base}/ig_hashtag_search", params={
                "user_id": self.user_id, "q": tag.lstrip("#"), "access_token": self.token,
            })
            ids = data.get("data", [])
            if not ids:
                return None
            self._hashtag_ids[tag] = ids[0]["id"]
        return self._hashtag_ids[tag]

    def fetch(self, keywords):
        posts, seen = [], set()
        fields = "id,caption,like_count,comments_count,timestamp,permalink"
        for kw in keywords:
            hid = self._hashtag_id(kw)
            if not hid:
                continue
            for edge in ("top_media", "recent_media"):
                data = self._get(f"{self.base}/{hid}/{edge}", params={
                    "user_id": self.user_id, "fields": fields,
                    "limit": 50, "access_token": self.token,
                })
                for m in data.get("data", []):
                    if m["id"] in seen or "timestamp" not in m:
                        continue
                    seen.add(m["id"])
                    posts.append(Post(
                        platform=self.name, post_id=m["id"], author="",
                        text=m.get("caption", ""), url=m.get("permalink", ""),
                        created_at=parse_time(m["timestamp"]),
                        likes=m.get("like_count", 0),
                        comments=m.get("comments_count", 0),
                        keyword=kw,
                    ))
        return posts
