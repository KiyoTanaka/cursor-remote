import logging
from pathlib import Path

from src.clients.threads_client import sync_threads_followers_from_list
from src.clients.x_client import sync_x_followers
from src.config import PROJECT_ROOT, settings

logger = logging.getLogger(__name__)

THREADS_FOLLOWERS_FILE = PROJECT_ROOT / "data" / "threads_followers.txt"


def load_threads_usernames() -> list[str]:
    if not THREADS_FOLLOWERS_FILE.exists():
        return []
    content = THREADS_FOLLOWERS_FILE.read_text(encoding="utf-8")
    return [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]


def sync_all() -> dict:
    """X と Threads のフォロワーを同期する。"""
    results = {"x": 0, "threads": 0, "errors": []}

    if settings.has_x_credentials():
        try:
            results["x"] = sync_x_followers()
        except Exception as e:
            logger.error("X 同期エラー: %s", e)
            results["errors"].append(f"X: {e}")
    else:
        logger.warning("X API 認証情報が未設定のためスキップ")

    if settings.has_threads_credentials():
        usernames = load_threads_usernames()
        if usernames:
            try:
                results["threads"] = sync_threads_followers_from_list(usernames)
            except Exception as e:
                logger.error("Threads 同期エラー: %s", e)
                results["errors"].append(f"Threads: {e}")
        else:
            logger.warning(
                "Threads フォロワーリストが空です。"
                f"{THREADS_FOLLOWERS_FILE} にユーザー名を追加してください。"
            )
    else:
        logger.warning("Threads API 認証情報が未設定のためスキップ")

    return results
