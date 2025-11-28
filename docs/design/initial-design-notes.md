# Figma MCP キャッシュツール設計まとめ（要約）

## 1. 背景

- Figma 無料プランにおける API / MCP 呼び出し回数が **月 6 回まで**に制限された。
- そのため **Figma のファイル・ノード JSON を事前取得しキャッシュして利用する MCP サーバー**を作る方針に決定。
- Figma は **ID プロバイダー（OAuth Provider）としては利用できない**ため、認証は **API トークン前提**で行う。

______________________________________________________________________

## 2. 実装方針（PoC）

### 2-1. 実行環境

- **Python 実行環境あり**を前提（pip / uvx / pipx で配布）。
- 配布形態は PyPI 上のパッケージ（例: `figma-mcp-cache`）。

### 2-2. キャッシュ方式

- **事前キャッシュ生成方式** を基本とする。
  - CLI から Figma API `/files/{file_id}` を叩いて JSON を取得。
  - 取得した JSON をローカルディスクに保存し、その上に **検索用インデックス** を生成。
  - MCP サーバーからは **Figma API を直接叩かず、常にキャッシュのみを参照**。
- API 呼び出しは
  - 初回キャッシュ生成
  - 明示的な `--refresh` 要求時 だけに限定し、月 6 回制限の中で運用可能にする。

### 2-3. トークン管理

- \*\*環境変数 \*\***FIGMA_API_TOKEN** を基本とし、必要に応じて `--token` オプションで上書き可能とする。

### 2-4. 複数ファイル対応

- `--file-id <FIGMA_FILE_ID>` を複数指定可能。
- または、ファイル ID 一覧を記述したテキストファイルを `--file-id-list <path>` で指定し、一括キャッシュ生成を行う。

______________________________________________________________________

## 3. CLI コマンド設計（キャッシュ／サーバー側）

### 3-1. キャッシュ関連コマンド

```bash
# 単一ファイルのキャッシュ生成
figma-mcp-cache cache --file-id <FILE_ID>

# 複数ファイル
figma-mcp-cache cache --file-id <ID1> --file-id <ID2>

# ファイル ID リストから一括生成
figma-mcp-cache cache --file-id-list path/to/file_ids.txt

# 強制リフレッシュ
figma-mcp-cache cache --file-id <FILE_ID> --refresh
```

### 3-2. MCP サーバー起動・管理コマンド

```bash
# MCP サーバー起動
figma-mcp-cache serve

# 動作確認（任意・簡易ヘルスチェック）
figma-mcp-cache status

# サーバー停止（必要であれば）
figma-mcp-cache stop
```

> PoC 段階では設定ファイルは持たず、`reload-config` などのコマンドは持たない前提。

______________________________________________________________________

## 4. MCP サーバーが提供するツール一覧（AI エージェント／MCP クライアント向け）

### 4-1. 位置づけ

- **公式 Figma MCP**:
  - Code Connect / 変数 / スクリーンショット / FigJam など高機能。
- **Figma-Context-MCP（Framelink）**:
  - Figma からレイアウト＋スタイル情報を JSON で取得・画像 DL に特化。
- **今回のキャッシュ MCP**:
  - Figma API は事前キャッシュのみ。
  - MCP からは **JSON 検索・取得専用の軽量ツール群**を提供。

### 4-2. 提供ツール案（今回の MCP）

**命名方針**：

- AI エージェントから見て意味が一意で誤解が少ないこと
- 「キャッシュ前提」であることが名前から分かること
- 他の Figma 関連 MCP ツールと衝突しにくいこと

そのため、最終的なツール名の推奨セットは以下とする：

#### 1. `get_cached_figma_file`

- **目的**: 指定ファイルのノードツリーやメタデータを取得する。
- **引数**:
  - `file_id: string`
- **返り値**（イメージ）:
  - ルートノードと、その直下の主要フレーム一覧（id / name / type / path など）。
  - 必要に応じてファイル全体のメタデータ（ページ構成など）。
- **元の案との対応**: 旧 `get_file_tree` 相当。

#### 2. `get_cached_figma_node`

- **目的**: 単一ノードの詳細情報を取得。
- **引数**:
  - `file_id: string`
  - `node_id: string`
- **返り値**:
  - 対象ノードのプロパティ（type, name, layout, style, children の ID など）。
- **元の案との対応**: 旧 `get_node_by_id` 相当。

#### 3. `search_figma_nodes_by_name`

- **目的**: ノード名（タイトル）でノードを検索。
- **引数**:
  - `file_id: string`
  - `name: string`
  - `match_mode: "exact" | "partial"`（オプション、デフォルト exact）
  - `limit: number`（オプション）
- **返り値**:
  - マッチしたノードのリスト（node_id / name / type / path などのメタ情報）。
- **元の案との対応**: 旧 `find_nodes_by_name` 相当。

#### 4. `search_figma_frames_by_title`

- **目的**: 「画面名（フレーム名）」からフレームノードを取得。
- **引数**:
  - `file_id: string`
  - `title: string`
  - `match_mode: "exact" | "partial"`
  - `limit: number`
- **返り値**:
  - 対象フレームノードの一覧（id / name / path）。
  - 必要に応じて、その直下ノードの概要を含める。
- **元の案との対応**: 旧 `find_frames_by_title` 相当。

#### 5. `list_figma_frames`

- **目的**: ファイル直下の主要フレーム一覧を取得（画面カタログ用途）。
- **引数**:
  - `file_id: string`
- **返り値**:
  - フレーム名・node_id・簡易パスなどのリスト。
- **元の案との対応**: 旧 `list_top_frames` 相当。

> 公式 Figma MCP の `get_*` / `find_*` 系にある程度寄せつつ、`cached` / `figma` を含めることで、他ツールとの衝突を避けながら意味を明確にしている。

______________________________________________________________________

## 5. 公式 MCP・Framelink・今回 MCP の比較

### 5-1. 主なツール比較（機能観点）

| 観点 / 機能                       | 公式 Figma MCP 例                               | Framelink Figma-Context-MCP          | 今回のキャッシュ MCP 案                             |
| --------------------------------- | ----------------------------------------------- | ------------------------------------ | --------------------------------------------------- |
| レイアウト＋スタイルの取得        | `get_design_context` / `get_metadata`           | `get_figma_data`                     | `get_file_tree` / `get_node_by_id`                  |
| 変数・トークン（カラー等）の取得  | `get_variable_defs`                             | 生 JSON から自前解析                 | **当面スコープ外**                                  |
| Code Connect（ノード⇔コンポ対応） | `get_code_connect_map` / `add_code_connect_map` | なし                                 | **やらない前提**                                    |
| スクリーンショット取得            | `get_screenshot`                                | `download_figma_images`              | **スコープ外**                                      |
| FigJam 対応                       | `get_figjam`                                    | 主に Design ファイル対象             | **当面スコープ外**                                  |
| 軽量メタデータ取得                | `get_metadata`                                  | シンプルな JSON                      | `nodes_index.json` による自前インデックス           |
| ユーザー情報 / whoami             | `whoami`                                        | なし                                 | なし                                                |
| ノード名・フレーム名で検索        | （専用ツールなし）                              | 実装内で解決（推測）                 | `find_nodes_by_name`, `find_frames_by_title` を提供 |
| キャッシュ前提か                  | 都度 Figma API                                  | 都度 API（ローカルキャッシュは任意） | **完全に事前キャッシュ前提**                        |

______________________________________________________________________

## 6. キャッシュファイルの構造設計

### 6-1. ディレクトリ構成（例）

```text
~/.figma_mcp_cache/
  index.json                     # 全ファイル共通のメタ情報
  <file_id>/
    file_raw.json                # Figma API /files の生 JSON
    nodes_index.json             # ノード検索用インデックス
```

### 6-2. `index.json` の例

```json
{
  "files": {
    "abc123": {
      "name": "App Design v2",
      "last_fetched_at": "2025-11-28T09:00:00Z",
      "node_count": 1834,
      "hash": "sha256:...."
    },
    "xyz789": {
      "name": "Marketing LP",
      "last_fetched_at": "2025-11-20T11:00:00Z",
      "node_count": 420,
      "hash": "sha256:...."
    }
  }
}
```

### 6-3. `nodes_index.json` の例（1 ファイル単位）

```json
{
  "by_id": {
    "0:1": {
      "name": "Sign Up Screen",
      "type": "FRAME",
      "parent_id": "0:0",
      "path": ["Document", "Auth", "Sign Up Screen"]
    },
    "12:34": {
      "name": "Primary Button",
      "type": "COMPONENT",
      "parent_id": "0:1",
      "path": ["Document", "Auth", "Sign Up Screen", "Buttons", "Primary Button"]
    }
  },
  "by_name": {
    "Sign Up Screen": ["0:1"],
    "Primary Button": ["12:34"]
  },
  "by_frame_title": {
    "Sign Up Screen": ["0:1"],
    "Login Screen": ["0:2"]
  }
}
```

- `by_id`: `node_id -> 軽量なノードメタ情報`。
- `by_name`: `name -> node_id[]`（同名ノード対策）。
- `by_frame_title`: `フレーム名 -> frame_node_id[]`。
- 実際の詳細プロパティ（layout, style, constraints など）は `file_raw.json` を参照し、インデックス側は軽量に保つ。

______________________________________________________________________

## 7. インメモリ KV の使い方

PoC 段階では **外部 KV（Redis など）は使わず、Python の dict で十分**とする。

```python
class CacheStore:
    def __init__(self):
        self.files: dict[str, dict] = {}    # file_id -> raw JSON (必要に応じて)
        self.indexes: dict[str, dict] = {}  # file_id -> nodes_index
```

- 初回アクセス時に `nodes_index.json` を読み込み `indexes[file_id]` に展開。
- 必要に応じて `file_raw.json` も `files[file_id]` に読み込む。
- MCP ツール実行時は：
  - `get_node_by_id` → `indexes[file_id]["by_id"][node_id]`
  - `find_nodes_by_name` → `indexes[file_id]["by_name"].get(name)`
  - `find_frames_by_title` → `indexes[file_id]["by_frame_title"].get(title)`

プロセスが落ちてもキャッシュはディスク上に残っているため、再起動時に必要なファイルだけオンデマンドでロードすればよい。

______________________________________________________________________

## 8. 想定ユースケース（AI エージェント視点）

- 「◯◯という画面を実装してください」
  - → MCP クライアントが `find_frames_by_title` を呼び、該当フレームの node_id を取得。
  - → さらに `get_node_by_id` でフレーム配下の構造をたどりつつコード生成。
- 「このコンポーネントはどのノード？」
  - → `find_nodes_by_name` で名前ベース検索。
- 「ノード ID の詳細を見せて」
  - → `get_node_by_id` を呼び、layout / style / children を取得。

この範囲で、**デザイン → コード生成ワークフローの基盤**としては十分機能する想定。

______________________________________________________________________

## 9. 総括

- PoC としては **キャッシュ型の軽量 Figma MCP サーバー**を提供する方針で確定。
- Figma API はキャッシュ生成 CLI からのみ使用し、MCP ツール側は常にローカルキャッシュを参照する。
- ツールは「ファイルツリー取得」「ノード ID 指定取得」「名前・画面タイトルでの検索」に絞り、スクリーンショットや Code Connect など重めの機能はスコープ外とする。
- インメモリ KV は Python の dict で実装し、永続キャッシュは JSON ファイルベースでシンプルに管理する。
