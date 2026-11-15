import os
from dataclasses import dataclass, field
from pathlib import Path

from .niche import DEFAULT_KEYWORDS


def _load_dotenv(path: str = ".env") -> None:
    """Muat .env ringkas tanpa kebergantungan tambahan."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


@dataclass
class Config:
    keywords: list[str] = field(default_factory=list)
    viral_multiplier: float = 5.0
    min_engagement: int = 500
    db_path: str = "data/viral_watch.db"
    demo: bool = False

    @classmethod
    def from_env(cls) -> "Config":
        _load_dotenv()
        kw = os.getenv("VW_KEYWORDS") or ",".join(DEFAULT_KEYWORDS)
        return cls(
            keywords=[k.strip() for k in kw.split(",") if k.strip()],
            viral_multiplier=float(os.getenv("VW_VIRAL_MULTIPLIER", "5")),
            min_engagement=int(os.getenv("VW_MIN_ENGAGEMENT", "500")),
            db_path=os.getenv("VW_DB_PATH", "data/viral_watch.db"),
            demo=os.getenv("VW_DEMO", "0").lower() in ("1", "true", "yes"),
        )
