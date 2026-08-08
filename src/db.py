import sqlite3
from contextlib import contextmanager
from datetime import date
from typing import Iterator

from src.config import DB_PATH, DATA_DIR


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS followers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                display_name TEXT,
                bio TEXT,
                birthday_month INTEGER,
                birthday_day INTEGER,
                birthday_source TEXT,
                profile_url TEXT,
                synced_at TEXT NOT NULL,
                UNIQUE(platform, user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_followers_birthday
                ON followers(birthday_month, birthday_day);
            """
        )
        conn.commit()
    finally:
        conn.close()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def upsert_follower(
    platform: str,
    user_id: str,
    username: str,
    display_name: str | None,
    bio: str | None,
    birthday_month: int | None,
    birthday_day: int | None,
    birthday_source: str | None,
    profile_url: str | None,
    synced_at: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO followers (
                platform, user_id, username, display_name, bio,
                birthday_month, birthday_day, birthday_source,
                profile_url, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(platform, user_id) DO UPDATE SET
                username = excluded.username,
                display_name = excluded.display_name,
                bio = excluded.bio,
                birthday_month = COALESCE(excluded.birthday_month, followers.birthday_month),
                birthday_day = COALESCE(excluded.birthday_day, followers.birthday_day),
                birthday_source = COALESCE(excluded.birthday_source, followers.birthday_source),
                profile_url = excluded.profile_url,
                synced_at = excluded.synced_at
            """,
            (
                platform,
                user_id,
                username,
                display_name,
                bio,
                birthday_month,
                birthday_day,
                birthday_source,
                profile_url,
                synced_at,
            ),
        )


def set_birthday(
    platform: str,
    username: str,
    month: int,
    day: int,
) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE followers
            SET birthday_month = ?, birthday_day = ?, birthday_source = 'manual'
            WHERE platform = ? AND username = ?
            """,
            (month, day, platform, username),
        )
        return cursor.rowcount > 0


def get_birthdays_today(today: date) -> list[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT platform, username, display_name, birthday_month, birthday_day,
                   birthday_source, profile_url
            FROM followers
            WHERE birthday_month = ? AND birthday_day = ?
            ORDER BY platform, display_name
            """,
            (today.month, today.day),
        ).fetchall()
    return list(rows)


def get_all_followers_with_birthdays() -> list[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT platform, username, display_name, birthday_month, birthday_day,
                   birthday_source, profile_url
            FROM followers
            WHERE birthday_month IS NOT NULL AND birthday_day IS NOT NULL
            ORDER BY birthday_month, birthday_day, platform
            """
        ).fetchall()
    return list(rows)


def get_stats() -> dict:
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM followers").fetchone()[0]
        with_birthday = conn.execute(
            "SELECT COUNT(*) FROM followers WHERE birthday_month IS NOT NULL"
        ).fetchone()[0]
        x_count = conn.execute(
            "SELECT COUNT(*) FROM followers WHERE platform = 'x'"
        ).fetchone()[0]
        threads_count = conn.execute(
            "SELECT COUNT(*) FROM followers WHERE platform = 'threads'"
        ).fetchone()[0]
    return {
        "total": total,
        "with_birthday": with_birthday,
        "x": x_count,
        "threads": threads_count,
    }
