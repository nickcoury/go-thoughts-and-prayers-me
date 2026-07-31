"""GoThoughtsAndPrayersMe — Backend API

Flask + SQLite + rate limiting. Serves at localhost:8643.
Proxied by Caddy at nickcoury.duckdns.org:8443/thoughts/
"""

import sqlite3
import re
import time
import os
import html
from datetime import datetime, timezone
from collections import defaultdict
from threading import Lock

from flask import Flask, request, jsonify, g

app = Flask(__name__)

# ── CORS ───────────────────────────────────────────────────────────
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Max-Age"] = "86400"
    return response

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "thoughts.db")

# ── Rate limiting ──────────────────────────────────────────────────
# Per-IP sliding window. Tiny traffic, in-memory is fine.
_rate_lock = Lock()
_rate_buckets: dict[str, list[float]] = defaultdict(list)

RATE_DONATE_PER_MIN = 10       # max donations per IP per minute
RATE_CREATE_PER_HOUR = 3       # max campaign creations per IP per hour
RATE_WINDOW_CREATE = 3600      # 1 hour in seconds


def _check_rate(ip: str, limit: int, window: float) -> bool:
    """Return True if under the rate limit, False if exceeded."""
    now = time.monotonic()
    with _rate_lock:
        bucket = _rate_buckets[ip]
        # prune old entries
        cutoff = now - window
        while bucket and bucket[0] < cutoff:
            bucket.pop(0)
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True


# ── Database ────────────────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            slug        TEXT NOT NULL UNIQUE,
            title       TEXT NOT NULL,
            description TEXT NOT NULL,
            goal_thoughts INTEGER NOT NULL DEFAULT 0,
            goal_prayers  INTEGER NOT NULL DEFAULT 0,
            current_thoughts INTEGER NOT NULL DEFAULT 0,
            current_prayers  INTEGER NOT NULL DEFAULT 0,
            organizer_name TEXT NOT NULL DEFAULT 'Anonymous',
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS donations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL REFERENCES campaigns(id),
            donor_name  TEXT NOT NULL DEFAULT 'Anonymous',
            message     TEXT NOT NULL DEFAULT '',
            thoughts    INTEGER NOT NULL DEFAULT 0,
            prayers     INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_donations_campaign
            ON donations(campaign_id, created_at DESC);
    """)
    db.commit()
    db.close()


# ── Helpers ─────────────────────────────────────────────────────────

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

MAX_TITLE_LEN = 140
MAX_DESC_LEN = 5000
MAX_MSG_LEN = 1000
MAX_NAME_LEN = 80
MIN_THOUGHTS = 1
MAX_THOUGHTS = 1_000_000
MIN_PRAYERS = 1
MAX_PRAYERS = 1_000_000
MIN_GOAL = 1
MAX_GOAL = 99_999_999


def _clean(s: str, max_len: int) -> str:
    """Strip, truncate, escape HTML entities."""
    s = s.strip()[:max_len]
    return html.escape(s, quote=False)


def _validate_positive_int(val, default=1, minimum=1, maximum=1_000_000) -> int:
    try:
        n = int(val)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(n, maximum))


# ── Routes ──────────────────────────────────────────────────────────

@app.route("/api/campaigns", methods=["GET"])
def list_campaigns():
    db = get_db()
    rows = db.execute(
        """SELECT slug, title, description, goal_thoughts, goal_prayers,
                  current_thoughts, current_prayers, organizer_name, created_at
           FROM campaigns
           ORDER BY created_at DESC
           LIMIT 50"""
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/campaigns/<slug>", methods=["GET"])
def get_campaign(slug: str):
    db = get_db()
    camp = db.execute(
        "SELECT * FROM campaigns WHERE slug = ?", (slug,)
    ).fetchone()
    if camp is None:
        return jsonify({"error": "Campaign not found"}), 404

    donations = db.execute(
        """SELECT donor_name, message, thoughts, prayers, created_at
           FROM donations
           WHERE campaign_id = ?
           ORDER BY created_at DESC
           LIMIT 100""",
        (camp["id"],),
    ).fetchall()

    result = dict(camp)
    result["donations"] = [dict(d) for d in donations]
    return jsonify(result)


@app.route("/api/campaigns", methods=["POST"])
def create_campaign():
    ip = request.remote_addr or "127.0.0.1"
    if not _check_rate(ip, RATE_CREATE_PER_HOUR, RATE_WINDOW_CREATE):
        return jsonify({"error": "Too many campaigns created. Please wait."}), 429

    data = request.get_json(silent=True) or {}

    # Honeypot — bots fill hidden fields
    if data.get("website") or data.get("url"):
        return jsonify({"error": "Invalid submission"}), 400

    title = _clean(data.get("title", ""), MAX_TITLE_LEN)
    description = _clean(data.get("description", ""), MAX_DESC_LEN)
    organizer = _clean(data.get("organizer_name", "Anonymous"), MAX_NAME_LEN)
    goal_thoughts = _validate_positive_int(
        data.get("goal_thoughts", 0), default=0, minimum=MIN_GOAL, maximum=MAX_GOAL
    )
    goal_prayers = _validate_positive_int(
        data.get("goal_prayers", 0), default=0, minimum=MIN_GOAL, maximum=MAX_GOAL
    )

    if not title:
        return jsonify({"error": "Title is required"}), 400
    if not description:
        return jsonify({"error": "Description is required"}), 400
    if goal_thoughts == 0 and goal_prayers == 0:
        return jsonify({"error": "Set at least one goal (thoughts or prayers)"}), 400

    # Generate slug from title
    slug_base = re.sub(r"[^a-z0-9]+", "-", title.lower().strip()).strip("-")[:60]
    if not slug_base:
        slug_base = "campaign"

    db = get_db()
    slug = slug_base
    counter = 1
    while db.execute("SELECT 1 FROM campaigns WHERE slug = ?", (slug,)).fetchone():
        suffix = f"-{counter}"
        slug = slug_base[: 60 - len(suffix)] + suffix
        counter += 1

    db.execute(
        """INSERT INTO campaigns (slug, title, description, goal_thoughts, goal_prayers, organizer_name)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (slug, title, description, goal_thoughts, goal_prayers, organizer),
    )
    db.commit()

    camp = db.execute("SELECT * FROM campaigns WHERE slug = ?", (slug,)).fetchone()
    return jsonify(dict(camp)), 201


@app.route("/api/campaigns/<slug>/donate", methods=["POST"])
def donate(slug: str):
    ip = request.remote_addr or "127.0.0.1"
    if not _check_rate(ip, RATE_DONATE_PER_MIN, 60):
        return jsonify({"error": "Too many donations. Please wait a moment."}), 429

    db = get_db()
    camp = db.execute(
        "SELECT * FROM campaigns WHERE slug = ?", (slug,)
    ).fetchone()
    if camp is None:
        return jsonify({"error": "Campaign not found"}), 404

    data = request.get_json(silent=True) or {}

    # Honeypot
    if data.get("website") or data.get("url"):
        return jsonify({"error": "Invalid submission"}), 400

    donor = _clean(data.get("donor_name", "Anonymous"), MAX_NAME_LEN)
    message = _clean(data.get("message", ""), MAX_MSG_LEN)
    thoughts = _validate_positive_int(
        data.get("thoughts", 0), default=0, minimum=0, maximum=MAX_THOUGHTS
    )
    prayers = _validate_positive_int(
        data.get("prayers", 0), default=0, minimum=0, maximum=MAX_PRAYERS
    )

    if thoughts == 0 and prayers == 0:
        return jsonify({"error": "Please send at least one thought or prayer"}), 400

    # Block obvious spam patterns
    spam_patterns = ["http://", "https://", "www.", ".com", ".ru", ".cn"]
    msg_lower = message.lower()
    if any(p in msg_lower for p in spam_patterns):
        return jsonify({"error": "Messages cannot contain links"}), 400

    db.execute(
        """INSERT INTO donations (campaign_id, donor_name, message, thoughts, prayers)
           VALUES (?, ?, ?, ?, ?)""",
        (camp["id"], donor, message, thoughts, prayers),
    )
    db.execute(
        """UPDATE campaigns
           SET current_thoughts = current_thoughts + ?,
               current_prayers  = current_prayers + ?
           WHERE id = ?""",
        (thoughts, prayers, camp["id"]),
    )
    db.commit()

    # Return updated campaign
    camp = db.execute(
        "SELECT * FROM campaigns WHERE slug = ?", (slug,)
    ).fetchone()
    return jsonify(dict(camp)), 201


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# ── Startup ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    init_db()

    # Handle --seed flag
    if "--seed" in sys.argv:
        from seed import seed_campaigns

        seed_campaigns()
        print("Database seeded.")
        sys.exit(0)

    from waitress import serve

    port = int(os.environ.get("PORT", 8643))
    print(f"Starting GoThoughtsAndPrayersMe on :{port}")
    serve(app, host="127.0.0.1", port=port)
