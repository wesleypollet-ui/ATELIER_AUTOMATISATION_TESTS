import sqlite3
import json
import os

DB_PATH = os.environ.get("DB_PATH", "runs.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Crée la table runs si elle n'existe pas encore."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                api       TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                summary   TEXT NOT NULL,
                tests     TEXT NOT NULL
            )
        """)
        conn.commit()


def save_run(run: dict) -> None:
    """Sauvegarde un run complet en base."""
    required_keys = {"api", "timestamp", "summary", "tests"}
    missing = required_keys - run.keys()
    if missing:
        raise ValueError(f"Clés manquantes dans run: {missing}")

    init_db()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO runs (api, timestamp, summary, tests) VALUES (?, ?, ?, ?)",
            (
                run["api"],
                run["timestamp"],
                json.dumps(run["summary"], ensure_ascii=False),
                json.dumps(run["tests"], ensure_ascii=False),
            ),
        )
        conn.commit()


def list_runs(limit: int = 20) -> list[dict]:
    """Retourne les `limit` derniers runs, du plus récent au plus ancien."""
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()

    return [
        {
            "id": row["id"],
            "api": row["api"],
            "timestamp": row["timestamp"],
            "summary": json.loads(row["summary"]),
            "tests": json.loads(row["tests"]),
        }
        for row in rows
    ]


def get_last_run() -> dict | None:
    """Retourne le dernier run ou None si aucun run en base."""
    runs = list_runs(limit=1)
    return runs[0] if runs else None
