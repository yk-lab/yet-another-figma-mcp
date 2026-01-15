# YetAnotherFigmaMCP

[![CI](https://github.com/yk-lab/yet-another-figma-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/yk-lab/yet-another-figma-mcp/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/yk-lab/yet-another-figma-mcp/graph/badge.svg)](https://codecov.io/gh/yk-lab/yet-another-figma-mcp)
[![Maintainability](https://qlty.sh/gh/yk-lab/projects/yet-another-figma-mcp/maintainability.svg)](https://qlty.sh/gh/yk-lab/projects/yet-another-figma-mcp)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with pyright](https://img.shields.io/badge/pyright-checked-blue.svg)](https://github.com/microsoft/pyright)
![CodeRabbit Pull Request Reviews](https://img.shields.io/coderabbit/prs/github/yk-lab/yet-another-figma-mcp?utm_source=oss&utm_medium=github&utm_campaign=yk-lab%2Fyet-another-figma-mcp&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+Reviews)
[![DeepWiki](https://img.shields.io/badge/DeepWiki-yk--lab%2Fyet--another--figma--mcp-blue.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAyCAYAAAAnWDnqAAAAAXNSR0IArs4c6QAAA05JREFUaEPtmUtyEzEQhtWTQyQLHNak2AB7ZnyXZMEjXMGeK/AIi+QuHrMnbChYY7MIh8g01fJoopFb0uhhEqqcbWTp06/uv1saEDv4O3n3dV60RfP947Mm9/SQc0ICFQgzfc4CYZoTPAswgSJCCUJUnAAoRHOAUOcATwbmVLWdGoH//PB8mnKqScAhsD0kYP3j/Yt5LPQe2KvcXmGvRHcDnpxfL2zOYJ1mFwrryWTz0advv1Ut4CJgf5uhDuDj5eUcAUoahrdY/56ebRWeraTjMt/00Sh3UDtjgHtQNHwcRGOC98BJEAEymycmYcWwOprTgcB6VZ5JK5TAJ+fXGLBm3FDAmn6oPPjR4rKCAoJCal2eAiQp2x0vxTPB3ALO2CRkwmDy5WohzBDwSEFKRwPbknEggCPB/imwrycgxX2NzoMCHhPkDwqYMr9tRcP5qNrMZHkVnOjRMWwLCcr8ohBVb1OMjxLwGCvjTikrsBOiA6fNyCrm8V1rP93iVPpwaE+gO0SsWmPiXB+jikdf6SizrT5qKasx5j8ABbHpFTx+vFXp9EnYQmLx02h1QTTrl6eDqxLnGjporxl3NL3agEvXdT0WmEost648sQOYAeJS9Q7bfUVoMGnjo4AZdUMQku50McDcMWcBPvr0SzbTAFDfvJqwLzgxwATnCgnp4wDl6Aa+Ax283gghmj+vj7feE2KBBRMW3FzOpLOADl0Isb5587h/U4gGvkt5v60Z1VLG8BhYjbzRwyQZemwAd6cCR5/XFWLYZRIMpX39AR0tjaGGiGzLVyhse5C9RKC6ai42ppWPKiBagOvaYk8lO7DajerabOZP46Lby5wKjw1HCRx7p9sVMOWGzb/vA1hwiWc6jm3MvQDTogQkiqIhJV0nBQBTU+3okKCFDy9WwferkHjtxib7t3xIUQtHxnIwtx4mpg26/HfwVNVDb4oI9RHmx5WGelRVlrtiw43zboCLaxv46AZeB3IlTkwouebTr1y2NjSpHz68WNFjHvupy3q8TFn3Hos2IAk4Ju5dCo8B3wP7VPr/FGaKiG+T+v+TQqIrOqMTL1VdWV1DdmcbO8KXBz6esmYWYKPwDL5b5FA1a0hwapHiom0r/cKaoqr+27/XcrS5UwSMbQAAAABJRU5ErkJggg==)](https://deepwiki.com/yk-lab/yet-another-figma-mcp)

Figma ファイルをローカルキャッシュし、MCP (Model Context Protocol) サーバーとして提供する軽量ツール。

## 背景

Figma 無料プランでは API / MCP 呼び出し回数が月 6 回までに制限されています。本ツールは Figma のファイル・ノード JSON を事前取得しキャッシュすることで、この制限内で効率的にデザインデータを活用できるようにします。

## 特徴

- **事前キャッシュ方式**: Figma API を事前に叩いて JSON をローカル保存
- **検索用インデックス**: ノード名・フレーム名での高速検索
- **MCP サーバー**: AI エージェントからキャッシュデータを参照可能
- **API 呼び出し最小化**: キャッシュ生成時と明示的リフレッシュ時のみ API 使用

## インストール

```bash
pip install yet-another-figma-mcp
```

または uvx / pipx でも利用可能:

```bash
uvx yet-another-figma-mcp --help
pipx install yet-another-figma-mcp
```

## セットアップ

### Figma API トークンの設定

環境変数に Figma API トークンを設定:

```bash
export FIGMA_API_TOKEN="your-figma-api-token"
```

トークンは [Figma の設定画面](https://www.figma.com/developers/api#access-tokens) から取得できます。

## 使い方

### キャッシュの生成

```bash
# 単一ファイルのキャッシュ生成
yet-another-figma-mcp cache --file-id <FILE_ID>

# 複数ファイル
yet-another-figma-mcp cache --file-id <ID1> --file-id <ID2>

# ファイル ID リストから一括生成
yet-another-figma-mcp cache --file-id-list path/to/file_ids.txt

# 強制リフレッシュ（API を再度呼び出し）
yet-another-figma-mcp cache --file-id <FILE_ID> --refresh
```

### MCP サーバーの起動

```bash
# MCP サーバー起動
yet-another-figma-mcp serve

# 動作確認
yet-another-figma-mcp status
```

### Claude Desktop での設定

`claude_desktop_config.json` に以下を追加:

```json
{
  "mcpServers": {
    "figma-cache": {
      "command": "uvx",
      "args": ["yet-another-figma-mcp", "serve"]
    }
  }
}
```

## MCP ツール一覧

MCP サーバーは以下のツールを提供します:

### `get_cached_figma_file`

指定ファイルのノードツリーやメタデータを取得。

```
引数:
  - file_id: string (必須)

返り値:
  - ルートノードと主要フレーム一覧
  - ファイル全体のメタデータ
```

### `get_cached_figma_node`

単一ノードの詳細情報を取得。

```
引数:
  - file_id: string (必須)
  - node_id: string (必須)

返り値:
  - ノードのプロパティ（type, name, layout, style, children など）
```

### `search_figma_nodes_by_name`

ノード名でノードを検索。

```
引数:
  - file_id: string (必須)
  - name: string (必須)
  - match_mode: "exact" | "partial" (オプション、デフォルト: exact)
  - limit: number (オプション)

返り値:
  - マッチしたノードのリスト
```

### `search_figma_frames_by_title`

フレーム名からフレームノードを検索。

```
引数:
  - file_id: string (必須)
  - title: string (必須)
  - match_mode: "exact" | "partial" (オプション)
  - limit: number (オプション)

返り値:
  - 対象フレームノードの一覧
```

### `list_figma_frames`

ファイル直下の主要フレーム一覧を取得。

```
引数:
  - file_id: string (必須)

返り値:
  - フレーム名・node_id・パスのリスト
```

## キャッシュファイルの構造

```
~/.yet_another_figma_mcp/
  index.json                     # 全ファイル共通のメタ情報
  <file_id>/
    file_raw.json                # Figma API /files の生 JSON
    nodes_index.json             # ノード検索用インデックス
```

## ユースケース例

### 画面実装の参照

```
ユーザー: 「サインアップ画面を実装してください」
→ AI: search_figma_frames_by_title で「Sign Up」を検索
→ AI: get_cached_figma_node でフレーム構造を取得
→ AI: 取得したデザイン情報をもとにコード生成
```

### コンポーネントの特定

```
ユーザー: 「Primary Button のスタイルを教えて」
→ AI: search_figma_nodes_by_name で検索
→ AI: get_cached_figma_node で詳細取得
```

## 制限事項

本ツールは PoC（Proof of Concept）として以下の機能はスコープ外としています:

- スクリーンショット取得
- Code Connect（ノード⇔コンポーネント対応）
- 変数・デザイントークンの取得
- FigJam 対応

## 開発

### セットアップ

```bash
# 開発用依存関係をインストール
uv sync --group dev
```

### Task コマンド（推奨）

[Task](https://taskfile.dev/) がインストールされている場合、以下のコマンドが使えます:

```bash
# 利用可能なタスク一覧
task

# 依存関係インストール
task install

# リント
task lint

# リント（自動修正付き）
task lint:fix

# フォーマット
task format

# フォーマット確認（修正なし）
task format:check

# 型チェック
task typecheck

# テスト
task test

# テスト（詳細出力）
task test:verbose

# テスト（並列実行）
task test:parallel

# テスト（カバレッジ付き）
task test:cov

# 全チェック（lint + format:check + typecheck + test）
task check

# pre-commit フック実行
task pre-commit

# MCP サーバー起動
task serve

# MCP サーバー起動（詳細ログ付き）
task serve:verbose

# キャッシュ状態確認
task status

# Figma ファイルをキャッシュ
task cache -- -f <FILE_ID>

# 生成ファイルのクリーンアップ
task clean
```

### 手動実行

```bash
# リント
uv run ruff check .

# フォーマット
uv run ruff format .

# 型チェック
uv run pyright

# テスト
uv run pytest
```

## Acknowledgments

- [Figma-Context-MCP](https://github.com/GLips/Figma-Context-MCP) - AI 向けノード簡略化のアプローチを参考にさせていただきました

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照してください。
