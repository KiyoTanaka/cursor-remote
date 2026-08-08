import logging
from datetime import datetime, timezone

import requests

from src.birthday_parser import parse_birthday_from_bio
from src.config import settings
from src.db import upsert_follower

logger = logging.getLogger(__name__)

THREADS_API_BASE = "https://graph.threads.net/v1.0"


def lookup_threads_profile(username: str) -> dict | None:
    """Threads ユーザーの公開プロフィールを取得する。"""
    if not settings.has_threads_credentials():
        raise ValueError(
            "Threads API の認証情報が未設定です。THREADS_ACCESS_TOKEN を設定してください。"
        )

    response = requests.get(
        f"{THREADS_API_BASE}/profile_lookup",
        params={
            "username": username,
            "access_token": settings.threads_access_token,
        },
        timeout=30,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def sync_threads_follower(username: str) -> bool:
    """指定した Threads ユーザーのプロフィールを同期する。"""
    profile = lookup_threads_profile(username)
    if not profile:
        logger.warning("Threads ユーザー @%s が見つかりません", username)
        return False

    bio = profile.get("biography", "")
    parsed = parse_birthday_from_bio(bio)
    synced_at = datetime.now(timezone.utc).isoformat()

    upsert_follower(
        platform="threads",
        user_id=profile.get("username", username),
        username=profile.get("username", username),
        display_name=profile.get("name"),
        bio=bio,
        birthday_month=parsed.month if parsed else None,
        birthday_day=parsed.day if parsed else None,
        birthday_source=parsed.source if parsed else None,
        profile_url=f"https://www.threads.net/@{username}",
        synced_at=synced_at,
    )
    return True


def sync_threads_followers_from_list(usernames: list[str]) -> int:
    """
    Threads フォロワーを同期する。

    公式 Threads API にはフォロワー一覧取得エンドポイントがないため、
    ユーザー名リストから個別にプロフィールを取得する。
    data/threads_followers.txt に1行1ユーザー名で登録可能。
    """
    count = 0
    for username in usernames:
        username = username.strip().lstrip("@")
        if not username:
            continue
        try:
            if sync_threads_follower(username):
                count += 1
        except requests.HTTPError as e:
            logger.error("Threads @%s の取得に失敗: %s", username, e)
    logger.info("Threads フォロワー %d 人を同期しました", count)
    return count
