"""誕生日パーサーのテスト"""

from src.birthday_parser import parse_birthday_from_bio


def test_emoji_birthday():
    result = parse_birthday_from_bio("エンジニア 🎂 3/15 東京在住")
    assert result is not None
    assert result.month == 3
    assert result.day == 15


def test_japanese_birthday():
    result = parse_birthday_from_bio("3月20日生まれのデザイナー")
    assert result is not None
    assert result.month == 3
    assert result.day == 20


def test_birthday_keyword():
    result = parse_birthday_from_bio("誕生日: 12/25")
    assert result is not None
    assert result.month == 12
    assert result.day == 25


def test_no_birthday():
    result = parse_birthday_from_bio("普通のプロフィール文です")
    assert result is None


def test_invalid_date():
    result = parse_birthday_from_bio("🎂 13/40")
    assert result is None
