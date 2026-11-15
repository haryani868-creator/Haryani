"""Niche: kurus & cantik — program kurus, produk kurus, diet, testimoni.

Setiap pos dikelaskan ke kategori berdasarkan kata dalam teks/hashtag.
Pos juga ditanda jika mengandungi tuntutan kesihatan berisiko (contohnya
'turun 10kg seminggu'), yang biasanya dikawal oleh KKM / Akta Ubat
(Iklan dan Penjualan) 1956. Berguna untuk elak meniru gaya iklan yang berisiko.
"""
from __future__ import annotations

import re

DEFAULT_KEYWORDS = [
    "kurus", "kuruscantik", "programkurus", "produkkurus", "turunberat",
    "dietsihat", "langsing", "slimming", "weightloss", "kempiskanperut",
]

# Kategori -> kata kunci (huruf kecil; dipadankan sebagai sebahagian perkataan)
CATEGORIES: dict[str, list[str]] = {
    "program": [
        "program kurus", "programkurus", "challenge", "cabaran", "bootcamp",
        "kelas", "coaching", "coach", "join group", "pakej program", "30 hari",
        "21 hari", "14 hari", "intermittent", "fasting", "keto",
    ],
    "produk": [
        "produk kurus", "produkkurus", "slimming", "kopi kurus", "teh kurus",
        "jus", "detox", "pil", "kapsul", "serbuk", "shake", "supplement",
        "suplemen", "collagen", "kolagen", "fiber", "fibre", "bengkung",
        "korset", "girdle", "order", "stokis", "agent", "ejen", "harga", "rm",
    ],
    "testimoni": [
        "testimoni", "testimonial", "before after", "beforeafter", "sebelum",
        "selepas", "dah turun", "berjaya turun", "turun berat", "transformasi",
        "transformation", "dari saiz", "kg dalam",
    ],
    "diet & senaman": [
        "diet", "resepi sihat", "makan sihat", "kalori", "calorie", "defisit",
        "senaman", "workout", "exercise", "gym", "zumba", "jalan kaki",
        "langkah", "protein", "meal prep",
    ],
    "kecantikan": [
        "cantik", "glowing", "kulit", "skincare", "awet muda", "langsing",
        "body goals", "bentuk badan", "pinggang", "perut kempis", "kempis",
    ],
}

# Tuntutan berisiko: penurunan pantas, jaminan, 'tanpa diet/senaman', ubat
RISKY_PATTERNS = [
    r"turun\s*\d+\s*kg\s*(dalam\s*)?(\d+\s*)?(hari|minggu|seminggu)",
    r"\d+\s*kg\s*(dalam\s*)?(\d+\s*)?(hari|minggu|seminggu)",
    r"tanpa\s*(diet|senaman|exercise|bersenam)",
    r"dijamin|jaminan\s*(turun|kurus)|100\s*%\s*(berkesan|kurus)",
    r"kurus\s*(segera|cepat|kilat|instant)",
    r"buang\s*lemak\s*(sekelip|serta)",
    r"lulus\s*kkm|kelulusan\s*kkm",  # perlu disemak — tuntutan selalu disalah guna
]
_RISKY = [re.compile(p, re.IGNORECASE) for p in RISKY_PATTERNS]


def _norm(text: str) -> str:
    # '#ProgramKurus' -> 'programkurus', 'before-after' -> 'before after'
    t = (text or "").lower().replace("#", " ")
    return re.sub(r"[-_/]", " ", t)


def classify(text: str) -> list[str]:
    t = _norm(text)
    squashed = t.replace(" ", "")
    found = []
    for cat, words in CATEGORIES.items():
        for w in words:
            if (re.search(rf"\b{re.escape(w)}\b", t)
                    or (" " in w and w.replace(" ", "") in squashed)):
                found.append(cat)
                break
    return found


def risky_claims(text: str) -> list[str]:
    t = _norm(text)
    hits = []
    for rx in _RISKY:
        m = rx.search(t)
        if m:
            hit = m.group(0).strip()
            if not any(hit in h for h in hits):  # buang padanan bertindih
                hits.append(hit)
    return hits
