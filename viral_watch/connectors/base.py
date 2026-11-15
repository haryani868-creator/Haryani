from __future__ import annotations

import logging
from datetime import datetime, timezone

import requests

from ..models import Post

log = logging.getLogger("viral_watch")


class Connector:
    name = "base"
    timeout = 20

    def configured(self) -> bool:
        raise NotImplementedError

    def fetch(self, keywords: list[str]) -> list[Post]:
        raise NotImplementedError

    def _get(self, url: str, **kw) -> dict:
        r = requests.get(url, timeout=self.timeout, **kw)
        r.raise_for_status()
        return r.json()

    def _post(self, url: str, **kw) -> dict:
        r = requests.post(url, timeout=self.timeout, **kw)
        r.raise_for_status()
        return r.json()


def parse_time(value) -> datetime:
    """Terima ISO-8601 (dengan Z atau +0000) atau epoch saat."""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    s = str(value).replace("Z", "+00:00")
    if len(s) >= 5 and s[-5] in "+-" and s[-3] != ":":  # +0000 -> +00:00
        s = s[:-2] + ":" + s[-2:]
    dt = datetime.fromisoformat(s)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
