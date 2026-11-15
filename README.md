# Pemerhati Viral

Pantau kandungan yang sedang meletup di **X, TikTok, Instagram dan Facebook** — dengan skor viral dan papan pemuka web.

## Cara ia mengesan "viral"

Pos viral bukan sekadar banyak *like*. Ia mengumpul interaksi **jauh lebih laju** berbanding pos biasa di platform yang sama.

| Ukuran | Formula |
|---|---|
| Interaksi | suka + 2×komen + 3×kongsi + 1% tontonan |
| Kelajuan | interaksi ÷ jam sejak diterbitkan |
| Momentum | pertambahan interaksi sejam antara dua kutipan terakhir |
| **Skor viral** | max(kelajuan, momentum) ÷ median kelajuan platform |

Status: `naik` (≥ ½ ambang), `viral` (≥ ambang, lalai 5×), `meletup` (≥ 2× ambang). Pos dengan interaksi kurang daripada `VW_MIN_ENGAGEMENT` sentiasa `biasa`.
Garis dasar dikira **berasingan bagi setiap platform**, jadi TikTok (angka besar) tidak dibandingkan dengan Facebook.

## Mula pantas (mod demo, tanpa kunci API)

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env           # VW_DEMO=1 sudah aktif
.venv/bin/python -m viral_watch.app
# buka http://localhost:5000 dan tekan "Kumpul data sekarang"
```

Data demo adalah sintetik dan dilabel **DEMO**. Set `VW_DEMO=0` bila kunci sebenar sudah diisi.

## Kunci API setiap platform

| Platform | Pemboleh ubah `.env` | Keperluan |
|---|---|---|
| X | `X_BEARER_TOKEN` | X API v2, pelan **Basic** atau lebih tinggi (berbayar) untuk carian terkini |
| TikTok | `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_REGION` | **Research API** — perlu permohonan & kelulusan TikTok |
| Instagram | `IG_USER_ID`, `IG_ACCESS_TOKEN` | Graph API, akaun Business/Creator dipaut ke Page FB. Had 30 hashtag / 7 hari |
| Facebook | `FB_PAGE_IDS`, `FB_ACCESS_TOKEN` | Graph API. Page orang lain perlu kelulusan *Page Public Content Access* |

Platform tanpa kunci dilangkau secara automatik. Jika satu platform gagal, yang lain tetap berjalan.

## Kutipan berkala

Skor momentum perlukan sekurang-kurangnya dua kutipan. Pilih satu:

```bash
.venv/bin/python -m viral_watch.collector --loop 15   # CLI, setiap 15 minit
VW_AUTO_COLLECT_MIN=15 .venv/bin/python -m viral_watch.app   # dalam papan pemuka
```

## Struktur

```
viral_watch/
  scoring.py        logik skor viral
  db.py             SQLite: pos + snapshot interaksi dari masa ke masa
  collector.py      ambil data dari semua platform (CLI)
  app.py            papan pemuka Flask + API JSON (/api/posts, /api/history, /api/collect)
  connectors/       x, tiktok, instagram, facebook, demo
tests/              pytest
```

Ujian: `.venv/bin/python -m pytest`
