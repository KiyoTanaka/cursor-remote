import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "followers.db"


@dataclass
class Settings:
    x_bearer_token: str = os.getenv("X_BEARER_TOKEN", "")
    x_api_key: str = os.getenv("X_API_KEY", "")
    x_api_secret: str = os.getenv("X_API_SECRET", "")
    x_access_token: str = os.getenv("X_ACCESS_TOKEN", "")
    x_access_token_secret: str = os.getenv("X_ACCESS_TOKEN_SECRET", "")
    x_user_id: str = os.getenv("X_USER_ID", "")

    threads_access_token: str = os.getenv("THREADS_ACCESS_TOKEN", "")
    threads_user_id: str = os.getenv("THREADS_USER_ID", "")

    discord_webhook_url: str = os.getenv("DISCORD_WEBHOOK_URL", "")
    slack_webhook_url: str = os.getenv("SLACK_WEBHOOK_URL", "")
    ntfy_topic: str = os.getenv("NTFY_TOPIC", "birthday-notify")

    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from: str = os.getenv("SMTP_FROM", "")
    smtp_to: str = os.getenv("SMTP_TO", "")

    timezone: str = os.getenv("TZ", "Asia/Tokyo")

    def has_x_credentials(self) -> bool:
        return bool(
            self.x_api_key
            and self.x_api_secret
            and self.x_access_token
            and self.x_access_token_secret
        )

    def has_threads_credentials(self) -> bool:
        return bool(self.threads_access_token)

    def has_notification_channel(self) -> bool:
        return bool(
            self.discord_webhook_url
            or self.slack_webhook_url
            or self.ntfy_topic
            or (self.smtp_host and self.smtp_to)
        )


settings = Settings()
