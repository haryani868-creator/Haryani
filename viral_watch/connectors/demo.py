"""Data demo sintetik supaya papan pemuka boleh dicuba tanpa kunci API.

Setiap pos demo mempunyai ID bermula 'demo-' dan dipaparkan dengan label DEMO.
Beberapa pos sengaja dibuat 'meletup' (pertumbuhan eksponen) untuk menunjukkan
bagaimana skor viral berfungsi.
"""
import random
from datetime import datetime, timedelta, timezone

from .base import Connector
from ..models import Post

PLATFORMS = ["x", "tiktok", "instagram", "facebook"]
TOPICS = [
    "Resepi nasi lemak 5 minit", "Kucing comel tidur atas laptop", "Tips jimat duit gaji",
    "Prank kawan sekelas", "Cabaran tarian baharu", "Review kedai mamak tersembunyi",
    "Banjir kilat di jalan utama", "Lawak bahasa Melayu vs Inggeris", "Tutorial tudung mudah",
    "Cerita seram asrama", "Harga barang naik lagi", "Kereta lama dibaik pulih",
    "Rumah kampung estetik", "Pelajar dapat 11A", "Konsert artis tempatan",
]


class DemoConnector(Connector):
    name = "demo"

    def configured(self) -> bool:
        return True

    def fetch(self, keywords, now: datetime | None = None):
        now = now or datetime.now(timezone.utc)
        # 'Kumpulan' pos bertukar setiap 24 jam supaya pos lama tidak kekal selamanya
        epoch = now.replace(minute=0, second=0, microsecond=0)
        epoch -= timedelta(hours=epoch.hour % 24)
        rng = random.Random(int(epoch.timestamp()))
        kws = keywords or ["viral"]
        posts = []
        for i in range(40):
            platform = PLATFORMS[i % len(PLATFORMS)]
            created = epoch - timedelta(hours=rng.uniform(1, 30))
            hours = max((now - created).total_seconds() / 3600, 0.1)
            rate = rng.lognormvariate(3, 0.8)          # interaksi sejam biasa
            explosive = i % 9 == 0                      # ~5 pos meletup
            growth = (1 + 0.15 * hours) ** 2 if explosive else 1.0
            likes = int(rate * hours * growth * (8 if explosive else 1))
            jitter = random.Random(f"{i}-{int(now.timestamp() // 300)}").uniform(0.97, 1.03)
            likes = int(likes * jitter)
            kw = kws[i % len(kws)]
            posts.append(Post(
                platform=platform,
                post_id=f"demo-{int(epoch.timestamp())}-{i}",
                author=f"@demo_user{i}",
                text=f"[DEMO] {TOPICS[i % len(TOPICS)]} #{kw}",
                url="",
                created_at=created,
                likes=likes,
                comments=int(likes * rng.uniform(0.02, 0.1)),
                shares=int(likes * rng.uniform(0.01, 0.3 if explosive else 0.05)),
                views=int(likes * rng.uniform(10, 40)) if platform in ("tiktok", "x") else 0,
                keyword=kw,
            ))
        return posts
