# MCP Inspector での動作検証

MCP Inspector は MCP サーバーのデバッグとテストのためのツールです。

## 前提条件

- Node.js 18+ (npx を使用する場合)
- または Docker
- yet-another-figma-mcp がインストール済み
- キャッシュ済みの Figma ファイルが 1 つ以上

## 1. MCP Inspector の起動

### 方法 1: npx (推奨)

```bash
npx @modelcontextprotocol/inspector
```

ブラウザで `http://localhost:6274` が自動的に開きます。

### 方法 2: Docker

```bash
docker run --rm -p 6274:6274 -p 6277:6277 \
  ghcr.io/modelcontextprotocol/inspector:latest
```

## 2. MCP サーバーへの接続

Inspector の UI で以下を設定:

1. **Transport Type**: `STDIO` を選択
1. **Command**: 以下を入力

```text
uv run yet-another-figma-mcp serve
```

または、直接 Inspector からサーバーを起動:

```bash
npx @modelcontextprotocol/inspector uv run yet-another-figma-mcp serve
```

## 3. ツール一覧の確認

接続後、「Tools」タブでツール一覧を確認:

| ツール名                       | 説明                             |
| ------------------------------ | -------------------------------- |
| `get_cached_figma_file`        | ファイルメタデータとフレーム一覧 |
| `get_cached_figma_node`        | 単一ノードの詳細 (node_id 指定)  |
| `search_figma_nodes_by_name`   | ノード名で検索                   |
| `search_figma_frames_by_title` | フレームタイトルで検索           |
| `list_figma_frames`            | トップレベルフレーム一覧         |

## 4. ツール呼び出しのテスト

### get_cached_figma_file

```json
{
  "file_id": "your_file_id"
}
```

### get_cached_figma_node

```json
{
  "file_id": "your_file_id",
  "node_id": "1:2"
}
```

### search_figma_nodes_by_name

```json
{
  "file_id": "your_file_id",
  "name": "Button",
  "match_mode": "partial",
  "ignore_case": true
}
```

### search_figma_frames_by_title

```json
{
  "file_id": "your_file_id",
  "title": "Login",
  "match_mode": "partial"
}
```

### list_figma_frames

```json
{
  "file_id": "your_file_id"
}
```

## 5. CLI モードでのテスト

スクリプトやパイプラインでのテスト用に CLI モードも利用可能:

```bash
# ツール一覧
npx @modelcontextprotocol/inspector --cli \
  uv run yet-another-figma-mcp serve \
  --method tools/list

# ツール呼び出し
npx @modelcontextprotocol/inspector --cli \
  uv run yet-another-figma-mcp serve \
  --method tools/call \
  --tool-name get_cached_figma_file \
  --tool-arg file_id=your_file_id
```

## トラブルシューティング

### 「file_not_found」エラー

キャッシュが存在しません。先に `cache` コマンドでファイルをキャッシュ:

```bash
yet-another-figma-mcp cache -f <file_id>
```

### 「node_not_found」エラー

指定した `node_id` が存在しません。`list_figma_frames` で有効な ID を確認:

```json
{
  "file_id": "your_file_id"
}
```

### 「invalid_file_id」エラー

ファイル ID の形式が不正です。英数字、ハイフン、アンダースコアのみ使用可能:

- ✓ `ABC123xyz`
- ✓ `my-design-file`
- ✗ `../etc/passwd`
- ✗ `file id with spaces`

### Inspector が接続できない

1. サーバーが起動しているか確認
1. キャッシュディレクトリにアクセス権があるか確認
1. `--verbose` オプションでログを確認:

```bash
npx @modelcontextprotocol/inspector \
  uv run yet-another-figma-mcp serve --verbose
```

### ポート競合

デフォルトポート (6274, 6277) が使用中の場合:

```bash
CLIENT_PORT=8080 SERVER_PORT=9000 npx @modelcontextprotocol/inspector
```

## 参考リンク

- [MCP Inspector GitHub](https://github.com/modelcontextprotocol/inspector)
- [Model Context Protocol](https://modelcontextprotocol.io/)
