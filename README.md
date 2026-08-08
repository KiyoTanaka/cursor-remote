# X・Threads フォロワー誕生日通知

X（旧Twitter）と Threads のフォロワーの誕生日を管理し、毎日午前0時（日本時間）に通知するシステムです。

## 重要な制限事項

**X API および Threads API では、フォロワーの誕生日を直接取得することはできません。** これはプライバシー保護のためのプラットフォーム制限です。

本システムでは以下の方法で誕生日を把握します：

1. **プロフィール文の自動解析** — 「🎂 3/15」「3月20日生まれ」などのパターンを検出
2. **手動登録** — CLI で誕生日を個別に設定
3. **Threads フォロワーリスト** — 公式 API にフォロワー一覧がないため、`data/threads_followers.txt` に手動登録

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

```bash
cp .env.example .env
# .env を編集して API キーと通知先を設定
```

#### X API 認証情報

[X Developer Portal](https://developer.x.com/) でアプリを作成し、以下を取得：

| 変数名 | 説明 |
|--------|------|
| `X_API_KEY` | API Key (Consumer Key) |
| `X_API_SECRET` | API Secret (Consumer Secret) |
| `X_ACCESS_TOKEN` | Access Token |
| `X_ACCESS_TOKEN_SECRET` | Access Token Secret |
| `X_USER_ID` | 自分のユーザー ID（省略可、自動取得） |

#### Threads API 認証情報

[Meta for Developers](https://developers.facebook.com/docs/threads) でアプリを作成：

| 変数名 | 説明 |
|--------|------|
| `THREADS_ACCESS_TOKEN` | Threads Graph API アクセストークン |

#### 通知チャネル（いずれか1つ以上）

| 変数名 | 説明 |
|--------|------|
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL |
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL |
| `NTFY_TOPIC` | [ntfy.sh](https://ntfy.sh) のトピック名（スマホ通知に便利） |
| `SMTP_*` | メール通知用 SMTP 設定 |

### 3. Threads フォロワーの登録

`data/threads_followers.txt` にフォロワーのユーザー名を1行1件で記載：

```
follower1
follower2
```

### 4. 初回同期

```bash
python -m src.main sync
```

## 使い方

```bash
# フォロワーを同期（X API + Threads）
python -m src.main sync

# 今日の誕生日通知を送信
python -m src.main notify

# 特定の日付で通知テスト
python -m src.main notify --date 2026-03-15

# 誕生日登録済みフォロワー一覧
python -m src.main list

# 統計情報
python -m src.main stats

# 誕生日を手動設定
python -m src.main set-birthday x username 3 15
python -m src.main set-birthday threads username 12 25
```

## 自動実行（GitHub Actions）

リポジトリの **Settings → Secrets and variables → Actions** に環境変数を登録すると、以下が自動実行されます：

| ワークフロー | スケジュール | 内容 |
|-------------|-------------|------|
| `birthday-notify.yml` | 毎日 0:00 JST | 今日誕生日のフォロワーを通知（無料） |
| `sync-followers.yml` | 毎月1日 9:00 JST | フォロワー情報を同期（X API 利用・約540円/3600人） |

### コスト目安（X API・Owned Read）

| フォロワー数 | 月1回同期の目安 |
|-------------|----------------|
| 1,000人 | 約150円/月 |
| 3,600人 | 約540円/月 |

同期は月1回のみ。毎日0時の通知はデータベースを参照するだけなので API 費用はかかりません。

### 初回セットアップ

Secrets 登録後、**Actions から「フォロワー同期」を手動実行**して初回データを取得してください。その後は毎月1日に自動同期、毎日0時に自動通知されます。

## ntfy.sh でスマホ通知を受け取る

1. スマホに [ntfy アプリ](https://ntfy.sh) をインストール
2. `.env` に `NTFY_TOPIC=あなたのトピック名` を設定（ユニークな名前を推奨）
3. アプリで同じトピックを購読

## プロジェクト構成

```
├── src/
│   ├── main.py              # CLI エントリーポイント
│   ├── config.py            # 設定管理
│   ├── db.py                # SQLite データベース
│   ├── birthday_parser.py   # プロフィール文から誕生日を推定
│   ├── sync.py              # フォロワー同期
│   ├── notify.py            # 通知送信
│   └── clients/
│       ├── x_client.py      # X API クライアント
│       └── threads_client.py # Threads API クライアント
├── data/
│   ├── threads_followers.txt # Threads フォロワーリスト
│   └── followers.db          # フォロワーデータ（自動生成）
├── .github/workflows/        # 自動実行スケジュール
└── tests/                    # テスト
```
