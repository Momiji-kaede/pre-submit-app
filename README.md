# 📝 課題提出アプリ

課題提出用Webアプリケーション

## 技術スタック

- **フロントエンド**: HTML, CSS
- **バックエンド**: Python (Flask)
- **データベース**: SQLite (SQL)

## セットアップ手順

### 1. 必要なライブラリをインストール

```bash
pip install -r requirements.txt
```

### 2. アプリケーションを起動

```bash
python app.py
```

### 3. ブラウザでアクセス

```
http://localhost:5000
```

## ファイル構成

```
project/
├── app.py                 # Flask アプリケーションメイン
├── database.py           # データベース設定
├── requirements.txt      # 依存ライブラリ
├── templates/
│   ├── login.html       # ログイン画面
│   ├── register.html    # 新規登録画面
│   └── dashboard.html   # ダッシュボード
└── static/
    └── style.css        # スタイルシート
```

## 機能

### 現在実装済み
- ✅ ログイン画面（モダンなデザイン）
- ✅ 新規登録画面
- ✅ パスワード暗号化
- ✅ セッション管理
- ✅ ダッシュボード表示

### 今後実装予定
- 📝 課題一覧表示
- 📤 課題提出機能
- ✅ 提出済み課題確認
- ⚙️ プロフィール設定

## 使用方法

1. **新規登録**: 「新規登録はこちら」から新しいアカウントを作成
2. **ログイン**: ユーザー名とパスワードでログイン
3. **ダッシュボード**: ログイン後、各機能にアクセス

## セキュリティについて

- パスワードはWerkzeugで安全にハッシュ化されています
- Flaskのセッション機能を使用しています
- `app.py`の`secret_key`は本番環境で必ず変更してください

```python
app.secret_key = 'your-secret-key-change-this'  # ここを変更
```

## ライセンス

MITライセンス