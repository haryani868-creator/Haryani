from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from .models import Post
from . import scoring

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    key TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    post_id TEXT NOT NULL,
    author TEXT,
    text TEXT,
    url TEXT,
    keyword TEXT,
    created_at TEXT NOT NULL,
    first_seen TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS snapshots (
    key TEXT NOT NULL REFERENCES posts(key),
    ts TEXT NOT NULL,
    likes INTEGER, comments INTEGER, shares INTEGER, views INTEGER,
    engagement REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_snap_key_ts ON snapshots(key, ts);
"""


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


class Store:
    def __init__(self, path: str):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        # Satu sambungan dikongsi antara thread Flask; kunci supaya akses bersiri
        self.lock = threading.RLock()

    def save(self, posts: list[Post], now: datetime | None = None) -> int:
        now = now or datetime.now(timezone.utc)
        with self.lock, self.conn:
            for p in posts:
                self.conn.execute(
                    "INSERT OR IGNORE INTO posts VALUES (?,?,?,?,?,?,?,?,?)",
                    (p.key, p.platform, p.post_id, p.author, p.text, p.url,
                     p.keyword, _iso(p.created_at), _iso(now)),
                )
                eng = scoring.engagement(p.likes, p.comments, p.shares, p.views)
                self.conn.execute(
                    "INSERT INTO snapshots VALUES (?,?,?,?,?,?,?)",
                    (p.key, _iso(now), p.likes, p.comments, p.shares, p.views, eng),
                )
        return len(posts)

    def history(self, key: str) -> list[dict]:
        with self.lock:
            return self._history(key)

    def _history(self, key: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT ts, engagement FROM snapshots WHERE key=? ORDER BY ts", (key,)
        ).fetchall()
        return [dict(r) for r in rows]

    def ranked(self, platform: str | None = None, within_hours: float = 72,
               multiplier: float = 5.0, min_eng: int = 500,
               now: datetime | None = None, limit: int = 100) -> list[dict]:
        """Kira skor viral untuk semua pos terkini dan susun dari tertinggi."""
        with self.lock:
            return self._ranked(platform, within_hours, multiplier, min_eng, now, limit)

    def _ranked(self, platform, within_hours, multiplier, min_eng, now, limit):
        now = now or datetime.now(timezone.utc)
        q = "SELECT * FROM posts"
        args: list = []
        if platform:
            q += " WHERE platform=?"
            args.append(platform)
        posts = [dict(r) for r in self.conn.execute(q, args)]

        items = []
        for p in posts:
            created = _dt(p["created_at"])
            age = scoring.age_hours(created, now)
            if age > within_hours:
                continue
            snaps = self.conn.execute(
                "SELECT * FROM snapshots WHERE key=? ORDER BY ts DESC LIMIT 2",
                (p["key"],),
            ).fetchall()
            if not snaps:
                continue
            last = snaps[0]
            prev = snaps[1] if len(snaps) > 1 else None
            last_ts = _dt(last["ts"])
            vel = scoring.velocity(last["engagement"], scoring.age_hours(created, last_ts))
            mom = scoring.momentum(
                prev["engagement"] if prev else None,
                _dt(prev["ts"]) if prev else None,
                last["engagement"], last_ts,
            )
            items.append({
                **p,
                "likes": last["likes"], "comments": last["comments"],
                "shares": last["shares"], "views": last["views"],
                "engagement": last["engagement"],
                "age_hours": round(age, 1),
                "velocity": vel, "momentum": mom,
            })

        # Garis dasar dikira per platform supaya TikTok tidak dibanding dengan Facebook
        by_platform: dict[str, list[float]] = {}
        for it in items:
            by_platform.setdefault(it["platform"], []).append(it["velocity"])
        baselines = {k: scoring.baseline_velocity(v) for k, v in by_platform.items()}

        for it in items:
            s = scoring.viral_score(it["velocity"], it["momentum"], baselines[it["platform"]])
            it["score"] = round(s, 2)
            it["status"] = scoring.status(s, it["engagement"], multiplier, min_eng)
            it["velocity"] = round(it["velocity"], 1)
            it["momentum"] = None if it["momentum"] is None else round(it["momentum"], 1)

        items.sort(key=lambda x: x["score"], reverse=True)
        return items[:limit]
