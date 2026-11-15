from datetime import datetime, timedelta, timezone

from viral_watch import scoring
from viral_watch.connectors.base import parse_time
from viral_watch.connectors.demo import DemoConnector
from viral_watch.db import Store
from viral_watch.models import Post

NOW = datetime(2026, 11, 15, 12, tzinfo=timezone.utc)


def post(pid, platform="x", likes=100, age_h=2.0):
    return Post(platform=platform, post_id=pid, author="a", text="t", url="",
                created_at=NOW - timedelta(hours=age_h), likes=likes)


def test_engagement_weights_shares_most():
    assert scoring.engagement(0, 0, 10, 0) > scoring.engagement(0, 10, 0, 0) > scoring.engagement(10, 0, 0, 0)


def test_status_thresholds():
    assert scoring.status(11, 1000, 5, 500) == "meletup"
    assert scoring.status(6, 1000, 5, 500) == "viral"
    assert scoring.status(3, 1000, 5, 500) == "naik"
    assert scoring.status(50, 100, 5, 500) == "biasa"  # terlalu sedikit interaksi


def test_outlier_ranks_first_and_is_viral():
    s = Store(":memory:")
    posts = [post(f"n{i}", likes=100) for i in range(10)] + [post("hot", likes=5000)]
    s.save(posts, now=NOW)
    rows = s.ranked(now=NOW)
    assert rows[0]["post_id"] == "hot"
    assert rows[0]["status"] == "meletup"
    assert rows[-1]["status"] == "biasa"


def test_baseline_is_per_platform():
    s = Store(":memory:")
    # TikTok secara semula jadi jauh lebih tinggi; ia tidak patut 'viral' hanya kerana itu
    s.save([post(f"x{i}", "x", likes=100) for i in range(5)]
           + [post(f"t{i}", "tiktok", likes=10000) for i in range(5)], now=NOW)
    assert all(r["score"] == 1.0 for r in s.ranked(now=NOW))


def test_momentum_detects_sudden_acceleration():
    s = Store(":memory:")
    old = [post(f"n{i}", likes=1000, age_h=10) for i in range(5)]
    s.save(old + [post("late", likes=1000, age_h=10)], now=NOW)
    later = NOW + timedelta(hours=1)
    s.save(old + [post("late", likes=20000, age_h=10)], now=later)
    rows = s.ranked(now=later)
    assert rows[0]["post_id"] == "late"
    assert rows[0]["momentum"] == 19000.0


def test_parse_time_formats():
    assert parse_time("2026-11-15T10:00:00Z") == parse_time("2026-11-15T10:00:00+0000")
    assert parse_time(0).year == 1970


def test_demo_produces_explosive_posts():
    s = Store(":memory:")
    d = DemoConnector()
    s.save(d.fetch(["viral"], now=NOW), now=NOW)
    later = NOW + timedelta(minutes=30)
    s.save(d.fetch(["viral"], now=later), now=later)
    rows = s.ranked(now=later)
    assert len(rows) == 40
    assert any(r["status"] in ("viral", "meletup") for r in rows)


from viral_watch import niche
from viral_watch.connectors.x import XConnector


def test_classify_niche_categories():
    assert "produk" in niche.classify("Kopi kurus RM49, order dengan stokis")
    assert "program" in niche.classify("Join #ProgramKurus 30 hari")
    assert "testimoni" in niche.classify("Before-after: dah turun 6kg")
    assert "diet & senaman" in niche.classify("Workout pagi + makan sihat")
    assert niche.classify("Cuaca panas hari ini") == []


def test_risky_claims_detected():
    assert niche.risky_claims("Turun 5kg seminggu tanpa diet!")
    assert niche.risky_claims("Kurus segera, dijamin!")
    assert niche.risky_claims("Resepi salad ayam sihat") == []


def test_category_filter_keeps_platform_baseline():
    s = Store(":memory:")
    posts = [post(f"n{i}", likes=100) for i in range(9)]
    hot = post("hot", likes=5000)
    hot.text = "Testimoni turun berat"
    s.save(posts + [hot], now=NOW)
    rows = s.ranked(now=NOW, category="testimoni")
    assert [r["post_id"] for r in rows] == ["hot"]
    assert rows[0]["status"] == "meletup"


def test_x_queries_combine_keywords_under_limit():
    groups = XConnector._queries([f"kata{i}" for i in range(100)])
    assert len(groups) > 1
    assert all(len("(" + " OR ".join(g) + ") -is:retweet") <= 500 for g in groups)
    assert sum(len(g) for g in groups) == 100


def test_momentum_ignores_snapshots_too_close_together():
    s = Store(":memory:")
    s.save([post("a", likes=100)], now=NOW)
    s.save([post("a", likes=110)], now=NOW + timedelta(seconds=20))
    assert s.ranked(now=NOW + timedelta(seconds=20))[0]["momentum"] is None
