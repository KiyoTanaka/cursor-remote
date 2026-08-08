#!/usr/bin/env python3
"""X・Threads フォロワー誕生日通知 CLI"""

import argparse
import logging
import sys
from datetime import date

from src.db import get_all_followers_with_birthdays, get_stats, init_db, set_birthday
from src.notify import send_notifications
from src.sync import sync_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def cmd_sync(_args: argparse.Namespace) -> None:
    init_db()
    results = sync_all()
    print(f"同期完了: X={results['x']}人, Threads={results['threads']}人")
    if results["errors"]:
        for err in results["errors"]:
            print(f"  エラー: {err}", file=sys.stderr)


def cmd_notify(args: argparse.Namespace) -> None:
    init_db()
    today = date.fromisoformat(args.date) if args.date else date.today()
    sent = send_notifications(today)
    if sent:
        print(f"{today} の誕生日通知を送信しました")
    else:
        print(f"{today} — 通知対象なし、または通知チャネル未設定")


def cmd_list(_args: argparse.Namespace) -> None:
    init_db()
    followers = get_all_followers_with_birthdays()
    if not followers:
        print("誕生日が登録されているフォロワーはいません")
        return
    print(f"{'プラットフォーム':<10} {'名前':<20} {'ユーザー名':<20} {'誕生日':<8} {'情報源'}")
    print("-" * 80)
    for row in followers:
        platform = "X" if row["platform"] == "x" else "Threads"
        name = (row["display_name"] or "")[:18]
        bday = f"{row['birthday_month']:02d}/{row['birthday_day']:02d}"
        print(
            f"{platform:<10} {name:<20} @{row['username']:<19} {bday:<8} {row['birthday_source']}"
        )


def cmd_stats(_args: argparse.Namespace) -> None:
    init_db()
    stats = get_stats()
    print(f"フォロワー総数: {stats['total']}")
    print(f"  X: {stats['x']}")
    print(f"  Threads: {stats['threads']}")
    print(f"誕生日登録済み: {stats['with_birthday']}")


def cmd_set_birthday(args: argparse.Namespace) -> None:
    init_db()
    ok = set_birthday(args.platform, args.username, args.month, args.day)
    if ok:
        print(f"@{args.username} の誕生日を {args.month}/{args.day} に設定しました")
    else:
        print(f"@{args.username} が見つかりません。先に sync を実行してください。", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="X・Threads フォロワー誕生日通知")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("sync", help="フォロワーを同期する")

    notify_parser = sub.add_parser("notify", help="今日の誕生日通知を送信する")
    notify_parser.add_argument("--date", help="通知対象日 (YYYY-MM-DD)")

    sub.add_parser("list", help="誕生日登録済みフォロワー一覧")
    sub.add_parser("stats", help="統計情報を表示")

    set_parser = sub.add_parser("set-birthday", help="誕生日を手動設定")
    set_parser.add_argument("platform", choices=["x", "threads"])
    set_parser.add_argument("username")
    set_parser.add_argument("month", type=int)
    set_parser.add_argument("day", type=int)

    args = parser.parse_args()
    commands = {
        "sync": cmd_sync,
        "notify": cmd_notify,
        "list": cmd_list,
        "stats": cmd_stats,
        "set-birthday": cmd_set_birthday,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
