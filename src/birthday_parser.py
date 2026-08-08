import re
from dataclasses import dataclass


@dataclass
class ParsedBirthday:
    month: int
    day: int
    source: str


# プロフィール文から誕生日を推定するパターン
BIRTHDAY_PATTERNS: list[tuple[re.Pattern, str]] = [
    # 🎂 3/15, 🎂03/15, birthday: 3/15
    (re.compile(r"(?:🎂|birthday|bday|誕生日|バースデー)[:\s]*(\d{1,2})[/月\.](\d{1,2})日?", re.I), "bio_emoji"),
    # 3月15日生まれ, 3月15日
    (re.compile(r"(\d{1,2})月(\d{1,2})日(?:生まれ|誕生|birth)?", re.I), "bio_jp"),
    # 03/15, 3/15 (単独、前後に誕生日関連キーワードがある場合)
    (re.compile(r"(?:born|生まれ|birth)[:\s]*(\d{1,2})[/\.](\d{1,2})", re.I), "bio_born"),
    # MM/DD format near birthday keywords
    (re.compile(r"(?:🎂|🎁|🎉|誕生日).{0,20}?(\d{1,2})[/\.](\d{1,2})", re.I), "bio_near_emoji"),
    # ♓ 3/15 (星座 + 日付)
    (re.compile(r"(?:♈|♉|♊|♋|♌|♍|♎|♏|♐|♑|♒|♓).{0,10}?(\d{1,2})[/\.](\d{1,2})", re.I), "bio_zodiac"),
]


def parse_birthday_from_bio(bio: str | None) -> ParsedBirthday | None:
    """プロフィール文から誕生日を推定する。"""
    if not bio:
        return None

    for pattern, source in BIRTHDAY_PATTERNS:
        match = pattern.search(bio)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            if _is_valid_date(month, day):
                return ParsedBirthday(month=month, day=day, source=source)

    return None


def _is_valid_date(month: int, day: int) -> bool:
    if not (1 <= month <= 12):
        return False
    days_in_month = [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= day <= days_in_month[month]
