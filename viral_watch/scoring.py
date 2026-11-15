"""Logik skor viral.

Idea utama: pos viral bukan sekadar banyak 'like' — ia mengumpul interaksi
jauh LEBIH PANTAS berbanding pos biasa di platform yang sama.

- engagement  = like + 2*komen + 3*kongsi + 0.01*tontonan
  (kongsi paling berat kerana ia yang menyebarkan kandungan)
- velocity    = engagement sejam sejak diterbitkan
- momentum    = engagement sejam antara dua snapshot terakhir (pecutan semasa)
- viral_score = max(velocity, momentum) / median velocity platform
  -> "berapa kali ganda lebih laju daripada biasa"
"""
from __future__ import annotations

from datetime import datetime, timezone
from statistics import median

W_LIKE, W_COMMENT, W_SHARE, W_VIEW = 1.0, 2.0, 3.0, 0.01
MIN_AGE_HOURS = 0.5  # elak pembahagian dengan nombor terlalu kecil


def engagement(likes: int, comments: int, shares: int, views: int) -> float:
    return likes * W_LIKE + comments * W_COMMENT + shares * W_SHARE + views * W_VIEW


def age_hours(created_at: datetime, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    return max((now - created_at).total_seconds() / 3600, MIN_AGE_HOURS)


def velocity(eng: float, hours: float) -> float:
    return eng / max(hours, MIN_AGE_HOURS)


def momentum(prev_eng: float | None, prev_time: datetime | None,
             eng: float, now: datetime) -> float | None:
    if prev_eng is None or prev_time is None:
        return None
    hours = (now - prev_time).total_seconds() / 3600
    if hours <= 0:
        return None
    return max(eng - prev_eng, 0) / hours


def viral_score(vel: float, mom: float | None, baseline: float) -> float:
    if baseline <= 0:
        baseline = 1.0
    return max(vel, mom or 0.0) / baseline


def baseline_velocity(velocities: list[float]) -> float:
    vals = [v for v in velocities if v > 0]
    return median(vals) if vals else 1.0


def status(score: float, eng: float, multiplier: float, min_eng: int) -> str:
    if eng < min_eng:
        return "biasa"
    if score >= multiplier * 2:
        return "meletup"
    if score >= multiplier:
        return "viral"
    if score >= multiplier / 2:
        return "naik"
    return "biasa"
