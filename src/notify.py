import logging
import smtplib
from datetime import date
from email.mime.text import MIMEText

import requests

from src.config import settings
from src.db import get_birthdays_today

logger = logging.getLogger(__name__)


def format_birthday_message(today: date, birthdays: list) -> str:
    if not birthdays:
        return f"🎂 {today.month}月{today.day}日 — 今日誕生日のフォロワーはいません。"

    lines = [f"🎂 {today.month}月{today.day}日 — 今日誕生日のフォロワー ({len(birthdays)}人)"]
    lines.append("")

    for row in birthdays:
        platform_label = "X" if row["platform"] == "x" else "Threads"
        name = row["display_name"] or row["username"]
        source = row["birthday_source"] or "不明"
        url = row["profile_url"] or ""
        lines.append(f"• [{platform_label}] {name} (@{row['username']})")
        if url:
            lines.append(f"  {url}")
        lines.append(f"  情報源: {source}")
        lines.append("")

    return "\n".join(lines)


def send_notifications(today: date | None = None) -> bool:
    """今日誕生日のフォロワーがいれば通知を送信する。"""
    if today is None:
        today = date.today()

    birthdays = get_birthdays_today(today)
    message = format_birthday_message(today, birthdays)

    if not birthdays:
        logger.info("今日誕生日のフォロワーはいません")
        return False

    if not settings.has_notification_channel():
        logger.warning("通知チャネルが未設定です。メッセージ:\n%s", message)
        print(message)
        return False

    sent = False
    if settings.discord_webhook_url:
        sent |= _send_discord(message)
    if settings.slack_webhook_url:
        sent |= _send_slack(message)
    if settings.ntfy_topic:
        sent |= _send_ntfy(message, len(birthdays))
    if settings.smtp_host and settings.smtp_to:
        sent |= _send_email(message, today)

    return sent


def _send_discord(message: str) -> bool:
    try:
        response = requests.post(
            settings.discord_webhook_url,
            json={"content": message},
            timeout=30,
        )
        response.raise_for_status()
        logger.info("Discord に通知を送信しました")
        return True
    except requests.RequestException as e:
        logger.error("Discord 通知に失敗: %s", e)
        return False


def _send_slack(message: str) -> bool:
    try:
        response = requests.post(
            settings.slack_webhook_url,
            json={"text": message},
            timeout=30,
        )
        response.raise_for_status()
        logger.info("Slack に通知を送信しました")
        return True
    except requests.RequestException as e:
        logger.error("Slack 通知に失敗: %s", e)
        return False


def _send_ntfy(message: str, count: int) -> bool:
    try:
        response = requests.post(
            f"https://ntfy.sh/{settings.ntfy_topic}",
            data=message.encode("utf-8"),
            headers={
                "Title": f"🎂 今日は{count}人が誕生日！",
                "Priority": "default",
                "Tags": "birthday,cake",
            },
            timeout=30,
        )
        response.raise_for_status()
        logger.info("ntfy.sh に通知を送信しました")
        return True
    except requests.RequestException as e:
        logger.error("ntfy 通知に失敗: %s", e)
        return False


def _send_email(message: str, today: date) -> bool:
    try:
        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = f"🎂 {today.month}月{today.day}日 フォロワー誕生日通知"
        msg["From"] = settings.smtp_from or settings.smtp_user
        msg["To"] = settings.smtp_to

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)

        logger.info("メールを送信しました")
        return True
    except smtplib.SMTPException as e:
        logger.error("メール送信に失敗: %s", e)
        return False
