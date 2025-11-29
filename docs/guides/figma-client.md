# Figma API クライアント利用ガイド

## 前提条件

- Python 3.13+
- uv がインストール済み
- Figma アカウントと API トークン

## 1. Figma API トークンの取得

1. [Figma](https://www.figma.com/) にログイン
1. 右上のアイコン → **Settings** → **Account**
1. **Personal access tokens** セクションで **Generate new token**
1. トークン名を入力して生成（トークンは一度しか表示されないのでコピー）

## 2. 環境変数の設定

```bash
export FIGMA_API_TOKEN="figd_xxxxxx..."
```

または `.env` ファイルを作成:

```bash
echo 'FIGMA_API_TOKEN=figd_xxxxxx...' > .env
```

## 3. Figma ファイル ID の確認

Figma ファイルの URL から ID を取得:

```text
https://www.figma.com/design/ABC123xyz/FileName
                           ^^^^^^^^^^^
                           これがファイル ID
```

## 4. Python REPL での動作確認

```bash
uv run python
```

```python
from yet_another_figma_mcp.figma import FigmaClient

# クライアント作成（環境変数から自動取得）
client = FigmaClient()

# または明示的にトークン指定
# client = FigmaClient(token="figd_xxxxxx...")

# ファイル取得
file_id = "ABC123xyz"  # 実際のファイル ID に置き換え
data = client.get_file(file_id)

# 基本情報の確認
print(f"ファイル名: {data['name']}")
print(f"最終更新: {data['lastModified']}")
print(f"バージョン: {data['version']}")

# ドキュメント構造の確認
doc = data['document']
print(f"ページ数: {len(doc.get('children', []))}")

for page in doc.get('children', []):
    print(f"  - {page['name']} ({page['type']})")

# クライアントを閉じる
client.close()
```

## 5. コンテキストマネージャでの使用

```python
from yet_another_figma_mcp.figma import FigmaClient

with FigmaClient() as client:
    data = client.get_file("ABC123xyz")
    print(data['name'])
# 自動的に close() が呼ばれる
```

## 6. エラーハンドリングの確認

```python
from yet_another_figma_mcp.figma import (
    FigmaClient,
    FigmaAuthenticationError,
    FigmaFileNotFoundError,
    FigmaRateLimitError,
)

with FigmaClient() as client:
    try:
        data = client.get_file("invalid-file-id")
    except FigmaAuthenticationError:
        print("認証エラー: トークンを確認してください")
    except FigmaFileNotFoundError as e:
        print(f"ファイルが見つかりません: {e.file_id}")
    except FigmaRateLimitError as e:
        print(f"レート制限: {e.retry_after}秒後に再試行")
```

## 7. カスタム設定での使用

```python
client = FigmaClient(
    token="figd_xxxxxx...",
    timeout=120.0,        # タイムアウト（秒）
    max_retries=5,        # 最大リトライ回数
    retry_base_delay=2.0, # リトライ基本待機時間
    retry_max_delay=60.0, # リトライ最大待機時間
)
```

## 8. ログの有効化

リトライ動作などを確認するためにログを有効化:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from yet_another_figma_mcp.figma import FigmaClient
# ...
```

## トラブルシューティング

### `ValueError: Figma API token is required`

環境変数 `FIGMA_API_TOKEN` が設定されていないか、空です。

```bash
echo $FIGMA_API_TOKEN  # 確認
export FIGMA_API_TOKEN="figd_..."  # 設定
```

### `FigmaAuthenticationError`

- トークンが無効または期限切れ
- Figma Settings で新しいトークンを生成

### `FigmaFileNotFoundError`

- ファイル ID が間違っている
- ファイルへのアクセス権限がない（共有設定を確認）

### タイムアウト

大きなファイルの場合、タイムアウトを増やす:

```python
client = FigmaClient(timeout=180.0)  # 3分
```
