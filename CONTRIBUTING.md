# Contributing to YetAnotherFigmaMCP

YetAnotherFigmaMCP への貢献に興味を持っていただきありがとうございます。

## 開発環境のセットアップ

### 前提条件

- Python 3.13 以上
- [uv](https://docs.astral.sh/uv/) (推奨)
- Git

### セットアップ手順

1. リポジトリをクローン:

```bash
git clone https://github.com/yk-lab/yet-another-figma-mcp.git
cd yet-another-figma-mcp
```

2. 開発用依存関係をインストール:

```bash
uv sync --group dev
```

3. pre-commit フックをセットアップ:

```bash
uv run pre-commit install
```

## 開発ワークフロー

### コードスタイル

本プロジェクトでは [Ruff](https://docs.astral.sh/ruff/) を使用してコードの品質を維持しています。

```bash
# リントチェック
uv run ruff check .

# 自動修正
uv run ruff check --fix .

# フォーマット
uv run ruff format .
```

### 型チェック

```bash
uv run mypy src/yet_another_figma_mcp
```

### テスト

```bash
uv run pytest
```

### コミット前のチェック

pre-commit が設定されていれば、コミット時に自動でチェックが実行されます。

手動で実行する場合:

```bash
uv run pre-commit run --all-files
```

または個別に:

```bash
uv run ruff check .
uv run ruff format .
uv run mypy src/yet_another_figma_mcp
uv run pytest
```

## プルリクエスト

1. フォークしてブランチを作成
1. 変更を実装
1. テストを追加・更新
1. リント・型チェック・テストがパスすることを確認
1. プルリクエストを作成

### コミットメッセージ

意味のある簡潔なコミットメッセージを書いてください:

```
feat: ノード検索機能を追加
fix: キャッシュ読み込み時のエラーを修正
docs: README にセットアップ手順を追加
refactor: CacheStore クラスを整理
test: search_figma_nodes_by_name のテストを追加
```

## ディレクトリ構造

```
yet-another-figma-mcp/
├── src/
│   └── yet_another_figma_mcp/
│       ├── __init__.py
│       ├── cli.py              # CLI エントリーポイント
│       ├── server.py           # MCP サーバー実装
│       ├── cache/
│       │   ├── __init__.py
│       │   ├── store.py        # キャッシュストア
│       │   └── index.py        # インデックス管理
│       ├── figma/
│       │   ├── __init__.py
│       │   └── client.py       # Figma API クライアント
│       └── tools/
│           ├── __init__.py
│           └── handlers.py     # MCP ツールハンドラ
├── tests/
├── pyproject.toml
├── README.md
└── CONTRIBUTING.md
```

## 質問・相談

Issue を作成して質問や相談をしてください。
