# YetAnotherFigmaMCP

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

```bash
# 開発用依存関係をインストール
uv sync --group dev

# リント
uv run ruff check .

# フォーマット
uv run ruff format .

# 型チェック
uv run mypy src/yet_another_figma_mcp

# テスト
uv run pytest
```

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照してください。
