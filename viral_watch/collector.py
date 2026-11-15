"""Pengumpul: ambil data dari setiap platform dan simpan snapshot.

Guna:
    python -m viral_watch.collector            # sekali jalan
    python -m viral_watch.collector --loop 15  # setiap 15 minit
"""
from __future__ import annotations

import argparse
import logging
import time

from .config import Config
from .connectors import enabled
from .db import Store

log = logging.getLogger("viral_watch")


def collect_once(cfg: Config, store: Store) -> dict[str, int]:
    results: dict[str, int] = {}
    conns = enabled(cfg.demo)
    if not conns:
        log.warning("Tiada platform dikonfigurasi. Isi kunci dalam .env atau set VW_DEMO=1.")
    for c in conns:
        try:
            posts = c.fetch(cfg.keywords)
            results[c.name] = store.save(posts)
            log.info("%s: %d pos disimpan", c.name, results[c.name])
        except Exception as e:  # satu platform gagal tidak patut hentikan yang lain
            log.error("%s gagal: %s", c.name, e)
            results[c.name] = -1
    return results


def print_top(cfg: Config, store: Store, n: int = 10) -> None:
    rows = store.ranked(multiplier=cfg.viral_multiplier, min_eng=cfg.min_engagement, limit=n)
    print(f"\n{'Skor':>6}  {'Status':<8} {'Platform':<10} {'Interaksi':>10}  {'Kategori':<22} Teks")
    for r in rows:
        text = (r["text"] or "").replace("\n", " ")[:50]
        cats = ",".join(r["categories"])[:22]
        flag = " ⚠" if r["risky"] else ""
        print(f"{r['score']:>6.1f}x {r['status']:<8} {r['platform']:<10} {int(r['engagement']):>10}  {cats:<22} {text}{flag}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Pengumpul Pemerhati Viral")
    ap.add_argument("--loop", type=float, metavar="MINIT", help="ulang setiap N minit")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = Config.from_env()
    store = Store(cfg.db_path)
    while True:
        collect_once(cfg, store)
        print_top(cfg, store)
        if not args.loop:
            break
        time.sleep(args.loop * 60)


if __name__ == "__main__":
    main()
