"""Application tracker -- SQLite-backed log of job applications.

DB lives at ~/.local/share/resume-engine/tracker.db (XDG data dir).
"""

from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_XDG_DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
DATA_DIR = _XDG_DATA_HOME / "resume-engine"
DB_FILE = DATA_DIR / "tracker.db"

# ---------------------------------------------------------------------------
# Valid statuses
# ---------------------------------------------------------------------------

VALID_STATUSES = ["applied", "screening", "interview", "offer", "rejected", "withdrawn"]

STATUS_STYLES = {
    "applied":   "cyan",
    "screening": "blue",
    "interview": "yellow",
    "offer":     "bold green",
    "rejected":  "red",
    "withdrawn": "dim",
}

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DB_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            company    TEXT NOT NULL,
            role       TEXT NOT NULL,
            date       TEXT NOT NULL,
            status     TEXT NOT NULL DEFAULT 'applied',
            url        TEXT,
            notes      TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def add_application(
    company: str,
    role: str,
    applied_date: str | None = None,
    status: str = "applied",
    url: str | None = None,
    notes: str | None = None,
    db_path: Path | None = None,
) -> int:
    """Insert a new application. Returns new row id."""
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Choose: {', '.join(VALID_STATUSES)}")
    today = date.today().isoformat()
    row_date = applied_date or today
    now = _now_iso()

    conn = _connect(db_path)
    cur = conn.execute(
        "INSERT INTO applications (company, role, date, status, url, notes, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (company, role, row_date, status, url, notes, now, now),
    )
    conn.commit()
    conn.close()
    return cur.lastrowid  # type: ignore[return-value]


def list_applications(
    status: str | None = None,
    company: str | None = None,
    limit: int | None = None,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Return applications, newest first, with optional filters."""
    conn = _connect(db_path)
    query = "SELECT * FROM applications WHERE 1=1"
    params: list[Any] = []

    if status:
        query += " AND LOWER(status) = LOWER(?)"
        params.append(status)
    if company:
        query += " AND LOWER(company) LIKE LOWER(?)"
        params.append(f"%{company}%")

    query += " ORDER BY date DESC, id DESC"
    if limit:
        query += f" LIMIT {int(limit)}"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_application(app_id: int, db_path: Path | None = None) -> dict[str, Any] | None:
    """Return a single application by id, or None."""
    conn = _connect(db_path)
    row = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_application(
    app_id: int,
    status: str | None = None,
    notes: str | None = None,
    url: str | None = None,
    db_path: Path | None = None,
) -> bool:
    """Update status/notes/url for an application. Returns False if not found."""
    if status and status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Choose: {', '.join(VALID_STATUSES)}")

    conn = _connect(db_path)
    row = conn.execute("SELECT id FROM applications WHERE id = ?", (app_id,)).fetchone()
    if not row:
        conn.close()
        return False

    now = _now_iso()
    if status is not None:
        conn.execute("UPDATE applications SET status = ?, updated_at = ? WHERE id = ?", (status, now, app_id))
    if notes is not None:
        conn.execute("UPDATE applications SET notes = ?, updated_at = ? WHERE id = ?", (notes, now, app_id))
    if url is not None:
        conn.execute("UPDATE applications SET url = ?, updated_at = ? WHERE id = ?", (url, now, app_id))

    conn.commit()
    conn.close()
    return True


def delete_application(app_id: int, db_path: Path | None = None) -> bool:
    """Delete an application. Returns False if not found."""
    conn = _connect(db_path)
    cur = conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def get_stats(db_path: Path | None = None) -> dict[str, Any]:
    """Return summary stats across all applications."""
    conn = _connect(db_path)
    total = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    by_status = {
        row[0]: row[1]
        for row in conn.execute(
            "SELECT status, COUNT(*) FROM applications GROUP BY status"
        ).fetchall()
    }
    conn.close()
    return {"total": total, "by_status": by_status}
