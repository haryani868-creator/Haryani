"""Papan pemuka web.

    python -m viral_watch.app        # buka http://localhost:5000
"""
from __future__ import annotations

import logging
import os
import threading
import time

from flask import Flask, jsonify, render_template, request

from .collector import collect_once
from .config import Config
from .connectors import ALL, enabled
from .db import Store
from .niche import CATEGORIES


def create_app(cfg: Config | None = None, store: Store | None = None) -> Flask:
    cfg = cfg or Config.from_env()
    store = store or Store(cfg.db_path)
    app = Flask(__name__)
    lock = threading.Lock()

    def run_collect():
        with lock:
            return collect_once(cfg, store)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/status")
    def status():
        return jsonify({
            "keywords": cfg.keywords,
            "multiplier": cfg.viral_multiplier,
            "min_engagement": cfg.min_engagement,
            "demo": cfg.demo,
            "categories": list(CATEGORIES),
            "platforms": {c().name: c().configured() for c in ALL},
        })

    @app.get("/api/posts")
    def posts():
        platform = request.args.get("platform") or None
        hours = float(request.args.get("hours", 72))
        rows = store.ranked(platform=platform, within_hours=hours,
                            multiplier=cfg.viral_multiplier, min_eng=cfg.min_engagement,
                            category=request.args.get("category") or None)
        return jsonify(rows)

    @app.get("/api/history/<path:key>")
    def history(key):
        return jsonify(store.history(key))

    @app.post("/api/collect")
    def collect():
        return jsonify(run_collect())

    interval = float(os.getenv("VW_AUTO_COLLECT_MIN", "0"))
    if interval > 0:
        def loop():
            while True:
                run_collect()
                time.sleep(interval * 60)
        threading.Thread(target=loop, daemon=True).start()

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_app().run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
