# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Build and Development Commands

```bash
# Install dependencies (uses PEP 735 dependency groups)
uv sync --group dev

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/cache_test.py

# Run a specific test function
uv run pytest tests/cache_test.py::TestCacheStore::test_cache_store_loads_from_disk

# Type checking
uv run pyright

# Lint and format
uv run ruff check --fix .
uv run ruff format .

# Run all pre-commit hooks
uv run pre-commit run --all-files
```

## Architecture

Figma MCP サーバーで、Figma 無料プランの API 制限 (月 6 回) を回避するためにファイルを事前キャッシュする。

### Core Flow

1. **CLI** (`cli.py`) → ユーザーが `cache` コマンドで Figma API からファイル取得
1. **FigmaClient** (`figma/client.py`) → API 呼び出しと JSON 保存
1. **Index Builder** (`cache/index.py`) → `by_id`, `by_name`, `by_frame_title` の 3 種類のインデックス生成
1. **CacheStore** (`cache/store.py`) → ディスクからキャッシュをロード、インメモリで保持
1. **MCP Server** (`server.py`) → 5 つのツールを MCP プロトコルで公開

### Key Modules

- `cache/store.py`: `CacheStore` クラス。`_validate_file_id()` でパストラバーサル攻撃を防止
- `cache/index.py`: `build_index()` で Figma ノードツリーを走査し検索用インデックス生成
- `tools/handlers.py`: MCP ツール実装。`CacheStore` を使ってクエリ処理
- `server.py`: `mcp` SDK を使った stdio サーバー。グローバルシングルトン `_store` でキャッシュ共有

### Index Structure

```python
{
    "by_id": {"1:1": {"name": "Frame", "type": "FRAME", "parent_id": "0:1", "path": [...]}},
    "by_name": {"Button": ["1:2", "1:5"]},
    "by_frame_title": {"Login Screen": ["1:1"]}
}
```

## Project-Specific Patterns

- **Test naming**: `*_test.py` 形式 (`test_*.py` ではない)
- **Type checker**: pyright (MCP SDK と同じ) を使用。type ignore 不要
- **file_id validation**: 全ての `file_id` は `_validate_file_id()` を通す (正規表現 `^[a-zA-Z0-9_-]+$`)
- **tmp_path fixture**: テストで一時ファイルを使う場合は `tmp_path` を使用 (自動クリーンアップ)
- **Parentheses style**: docstring・コメント (開発者向け) は半角括弧 `()`、ユーザー向けメッセージは全角括弧 `（）` を使用

## MCP Tools

サーバーが公開する 5 つのツール：

1. `get_cached_figma_file` - ファイルメタデータとフレーム一覧
1. `get_cached_figma_node` - 単一ノードの詳細 (node_id 指定)
1. `search_figma_nodes_by_name` - ノード名で検索 (exact/partial)
1. `search_figma_frames_by_title` - フレーム名で検索 (exact/partial)
1. `list_figma_frames` - トップレベルフレーム一覧

## Commit Message Format

Conventional Commits 形式：

```
feat: 新機能の追加
fix: バグ修正
docs: ドキュメント更新
refactor: リファクタリング
test: テスト追加・修正
security: セキュリティ修正
```

## Dependencies

- **httpx**: HTTP クライアント (Figma API 呼び出し)
- **mcp[cli,rich]**: MCP サーバー SDK + Typer/Rich CLI
- **pydantic**: データバリデーション
- **hatch-vcs**: Git タグベースのバージョニング (ビルド時)
