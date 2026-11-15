import os

from .base import Connector, parse_time
from ..models import Post

API = "https://api.x.com/2/tweets/search/recent"


class XConnector(Connector):
    """X API v2 — carian 7 hari terkini. Perlu pelan Basic atau lebih tinggi."""
    name = "x"

    def __init__(self):
        self.token = os.getenv("X_BEARER_TOKEN", "")

    def configured(self) -> bool:
        return bool(self.token)

    def fetch(self, keywords):
        posts = []
        for kw in keywords:
            data = self._get(API, headers={"Authorization": f"Bearer {self.token}"}, params={
                "query": f"{kw} -is:retweet",
                "max_results": 100,
                "sort_order": "relevancy",
                "tweet.fields": "created_at,public_metrics,author_id",
                "expansions": "author_id",
                "user.fields": "username",
            })
            users = {u["id"]: u["username"] for u in data.get("includes", {}).get("users", [])}
            for t in data.get("data", []):
                m = t.get("public_metrics", {})
                user = users.get(t.get("author_id"), t.get("author_id", ""))
                posts.append(Post(
                    platform=self.name, post_id=t["id"], author=f"@{user}",
                    text=t.get("text", ""),
                    url=f"https://x.com/{user}/status/{t['id']}",
                    created_at=parse_time(t["created_at"]),
                    likes=m.get("like_count", 0),
                    comments=m.get("reply_count", 0),
                    shares=m.get("retweet_count", 0) + m.get("quote_count", 0),
                    views=m.get("impression_count", 0),
                    keyword=kw,
                ))
        return posts
