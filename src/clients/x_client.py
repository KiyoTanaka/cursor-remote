import logging
from datetime import datetime, timezone

import tweepy

from src.birthday_parser import parse_birthday_from_bio
from src.config import settings
from src.db import upsert_follower

logger = logging.getLogger(__name__)


def sync_x_followers() -> int:
    """X API からフォロワー一覧を取得し、プロフィール文から誕生日を推定する。"""
    if not settings.has_x_credentials():
        raise ValueError(
            "X API の認証情報が未設定です。"
            "X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET を設定してください。"
        )

    client = tweepy.Client(
        consumer_key=settings.x_api_key,
        consumer_secret=settings.x_api_secret,
        access_token=settings.x_access_token,
        access_token_secret=settings.x_access_token_secret,
        wait_on_rate_limit=True,
    )

    user_id = settings.x_user_id
    if not user_id:
        me = client.get_me()
        if not me.data:
            raise ValueError("X ユーザー ID を取得できませんでした。")
        user_id = me.data.id

    synced_at = datetime.now(timezone.utc).isoformat()
    count = 0

    paginator = tweepy.Paginator(
        client.get_users_followers,
        id=user_id,
        user_fields=["description", "name", "username"],
        max_results=1000,
    )

    for response in paginator:
        if not response.data:
            continue
        for user in response.data:
            bio = user.description or ""
            parsed = parse_birthday_from_bio(bio)
            upsert_follower(
                platform="x",
                user_id=str(user.id),
                username=user.username,
                display_name=user.name,
                bio=bio,
                birthday_month=parsed.month if parsed else None,
                birthday_day=parsed.day if parsed else None,
                birthday_source=parsed.source if parsed else None,
                profile_url=f"https://x.com/{user.username}",
                synced_at=synced_at,
            )
            count += 1

    logger.info("X フォロワー %d 人を同期しました", count)
    return count
