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
uv run pyright
```

### テスト

```bash
# 通常のテスト実行
uv run pytest

# 並列実行 (テスト数が多い場合に高速)
uv run pytest -n auto

# フレーキーテストの検出
uv run pytest --flake-finder --flake-runs=10
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
uv run pyright
uv run pytest
```

## プルリクエスト

1. フォークしてブランチを作成
1. 変更を実装
1. テストを追加・更新
1. リント・型チェック・テストがパスすることを確認
1. プルリクエストを作成

### コミットメッセージ（Conventional Commits）

本プロジェクトでは [Conventional Commits](https://www.conventionalcommits.org/) 形式を採用しています。
これにより、[Release Please](https://github.com/googleapis/release-please) による自動リリースが可能になります。

#### フォーマット

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### タイプ一覧

| タイプ     | 説明                                                 | リリースへの影響         |
| ---------- | ---------------------------------------------------- | ------------------------ |
| `feat`     | 新機能の追加                                         | マイナーバージョンアップ |
| `fix`      | バグ修正                                             | パッチバージョンアップ   |
| `docs`     | ドキュメントのみの変更                               | リリースなし             |
| `style`    | コードの意味に影響しない変更（空白、フォーマット等） | リリースなし             |
| `refactor` | バグ修正でも機能追加でもないコード変更               | リリースなし             |
| `perf`     | パフォーマンス改善                                   | パッチバージョンアップ   |
| `test`     | テストの追加・修正                                   | リリースなし             |
| `chore`    | ビルドプロセスやツールの変更                         | リリースなし             |
| `ci`       | CI 設定の変更                                        | リリースなし             |
| `security` | セキュリティ修正                                     | パッチバージョンアップ   |

#### 破壊的変更

破壊的変更がある場合は `!` を追加するか、フッターに `BREAKING CHANGE:` を記述します：

```text
feat!: API の互換性を破壊する変更

BREAKING CHANGE: get_cached_figma_file の戻り値の構造が変更されました
```

#### 例

```text
feat: ノード検索機能を追加
fix: キャッシュ読み込み時のエラーを修正
docs: README にセットアップ手順を追加
refactor: CacheStore クラスを整理
test: search_figma_nodes_by_name のテストを追加
ci: Release Please ワークフローを追加
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
