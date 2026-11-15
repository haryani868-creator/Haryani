import os
import time
from datetime import datetime, timedelta, timezone

from .base import Connector, parse_time
from ..models import Post

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
QUERY_URL = "https://open.tiktokapis.com/v2/research/video/query/"
FIELDS = "id,username,video_description,create_time,like_count,comment_count,share_count,view_count"


class TikTokConnector(Connector):
    """TikTok Research API — perlu permohonan & kelulusan dari TikTok for Developers."""
    name = "tiktok"

    def __init__(self):
        self.key = os.getenv("TIKTOK_CLIENT_KEY", "")
        self.secret = os.getenv("TIKTOK_CLIENT_SECRET", "")
        self.region = os.getenv("TIKTOK_REGION", "MY")
        self._token = None
        self._token_exp = 0.0

    def configured(self) -> bool:
        return bool(self.key and self.secret)

    def _access_token(self) -> str:
        if self._token and time.time() < self._token_exp - 60:
            return self._token
        data = self._post(TOKEN_URL, data={
            "client_key": self.key, "client_secret": self.secret,
            "grant_type": "client_credentials",
        }, headers={"Content-Type": "application/x-www-form-urlencoded"})
        self._token = data["access_token"]
        self._token_exp = time.time() + int(data.get("expires_in", 7200))
        return self._token

    def fetch(self, keywords):
        today = datetime.now(timezone.utc).date()
        start = today - timedelta(days=2)
        body = {
            "query": {"and": [
                {"operation": "IN", "field_name": "region_code", "field_values": [self.region]},
                {"operation": "IN", "field_name": "keyword", "field_values": keywords},
            ]},
            "start_date": start.strftime("%Y%m%d"),
            "end_date": today.strftime("%Y%m%d"),
            "max_count": 100,
        }
        data = self._post(QUERY_URL, params={"fields": FIELDS}, json=body, headers={
            "Authorization": f"Bearer {self._access_token()}",
        })
        posts = []
        for v in data.get("data", {}).get("videos", []):
            desc = v.get("video_description", "")
            kw = next((k for k in keywords if k.lower() in desc.lower()), "")
            user = v.get("username", "")
            posts.append(Post(
                platform=self.name, post_id=str(v["id"]), author=f"@{user}",
                text=desc,
                url=f"https://www.tiktok.com/@{user}/video/{v['id']}",
                created_at=parse_time(v["create_time"]),
                likes=v.get("like_count", 0), comments=v.get("comment_count", 0),
                shares=v.get("share_count", 0), views=v.get("view_count", 0),
                keyword=kw,
            ))
        return posts
