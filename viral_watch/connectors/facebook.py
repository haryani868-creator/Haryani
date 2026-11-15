import os

from .base import Connector, parse_time
from ..models import Post


class FacebookConnector(Connector):
    """Facebook Graph API — pos dari senarai Page.

    Untuk Page milik anda, token Page biasa mencukupi. Untuk Page awam orang lain,
    aplikasi anda perlu kelulusan 'Page Public Content Access' daripada Meta.
    Kata kunci digunakan sebagai penapis pada teks pos.
    """
    name = "facebook"

    def __init__(self):
        self.page_ids = [p.strip() for p in os.getenv("FB_PAGE_IDS", "").split(",") if p.strip()]
        self.token = os.getenv("FB_ACCESS_TOKEN", "")
        self.base = f"https://graph.facebook.com/{os.getenv('GRAPH_API_VERSION', 'v21.0')}"

    def configured(self) -> bool:
        return bool(self.page_ids and self.token)

    def fetch(self, keywords):
        fields = ("id,message,created_time,permalink_url,from,shares,"
                  "reactions.summary(total_count).limit(0),comments.summary(total_count).limit(0)")
        posts = []
        lowered = [k.lower() for k in keywords]
        for page in self.page_ids:
            data = self._get(f"{self.base}/{page}/posts", params={
                "fields": fields, "limit": 50, "access_token": self.token,
            })
            for p in data.get("data", []):
                msg = p.get("message", "")
                kw = next((k for k in lowered if k in msg.lower()), "")
                if lowered and not kw:
                    continue
                posts.append(Post(
                    platform=self.name, post_id=p["id"],
                    author=p.get("from", {}).get("name", page),
                    text=msg, url=p.get("permalink_url", ""),
                    created_at=parse_time(p["created_time"]),
                    likes=p.get("reactions", {}).get("summary", {}).get("total_count", 0),
                    comments=p.get("comments", {}).get("summary", {}).get("total_count", 0),
                    shares=p.get("shares", {}).get("count", 0),
                    keyword=kw,
                ))
        return posts
