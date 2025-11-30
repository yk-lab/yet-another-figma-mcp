# Figma API トークン取得ガイド

## 概要

yet-another-figma-mcp で Figma ファイルをキャッシュするには、Figma API の Personal Access Token が必要です。

## 1. Figma 設定画面へのアクセス

> 📖 公式ガイド: [Manage personal access tokens - Figma Help Center](https://help.figma.com/hc/en-us/articles/8085703771159-Manage-personal-access-tokens)

1. [Figma](https://www.figma.com/) にログイン
1. 左上のアカウントメニュー（自分のアイコン）をクリック
1. **Settings** を選択
1. **Security** タブに移動

## 2. Personal Access Token の生成

1. **Personal access tokens** セクションまでスクロール
1. **Generate new token** をクリック
1. トークン名を入力（例: `yet-another-figma-mcp`）
1. 必要なスコープを選択（下記参照）
1. **Generate token** をクリック

> **重要**: トークンは生成直後のみ表示されます。ページを移動すると二度とコピーできなくなるため、必ずすぐにコピーしてください。

## 3. 必要なスコープ（権限）

> 📖 スコープ一覧: [API Scopes - Figma Developers](https://developers.figma.com/docs/rest-api/scopes/)

本ツールでは以下のスコープが必要です:

| スコープ            | 説明                         | 必須 |
| ------------------- | ---------------------------- | ---- |
| `file_content:read` | ファイルコンテンツの読み取り | ✓    |

### スコープの説明

- **file_content:read**: Figma ファイルのノード構造、コンポーネント、フレームなどのコンテンツを読み取るために必要

### 非推奨のスコープ

`file_read` スコープは非推奨です。より限定的な `file_content:read` を使用してください。

## 4. 環境変数への設定

### macOS / Linux

```bash
# 一時的な設定（現在のシェルセッションのみ）
export FIGMA_API_TOKEN="figd_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 永続的な設定（~/.bashrc または ~/.zshrc に追加）
echo 'export FIGMA_API_TOKEN="figd_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"' >> ~/.zshrc
source ~/.zshrc
```

### Windows (PowerShell)

```powershell
# 一時的な設定（現在のセッションのみ）
$env:FIGMA_API_TOKEN = "figd_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 永続的な設定（ユーザー環境変数）
[Environment]::SetEnvironmentVariable("FIGMA_API_TOKEN", "figd_xxxxxxxxxxxxxxxxxxxxxxxxxxxx", "User")
```

### Windows (コマンドプロンプト)

```cmd
REM 一時的な設定
set FIGMA_API_TOKEN=figd_xxxxxxxxxxxxxxxxxxxxxxxxxxxx

REM 永続的な設定
setx FIGMA_API_TOKEN "figd_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### .env ファイルを使用する場合

プロジェクトディレクトリに `.env` ファイルを作成:

```bash
FIGMA_API_TOKEN=figd_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> **注意**: `.env` ファイルは `.gitignore` に追加して、リポジトリにコミットしないでください。

## 5. 設定の確認

```bash
# 環境変数が設定されているか確認
echo $FIGMA_API_TOKEN

# API 接続テスト
yet-another-figma-mcp cache -f <your_file_id>
```

成功すれば、ファイルがキャッシュされます。

## トラブルシューティング

### 「認証エラー」が発生する

- トークンが正しくコピーされているか確認
- トークンが期限切れでないか確認
- 環境変数が正しく設定されているか確認:

```bash
echo $FIGMA_API_TOKEN
```

### 「ファイルが見つかりません」エラー

- ファイル ID が正しいか確認
- ファイルへのアクセス権があるか確認（共有設定）
- `file_content:read` スコープが付与されているか確認

### トークンを再生成したい

1. Figma Settings → Security → Personal access tokens
1. 既存のトークンを削除（ゴミ箱アイコン）
1. 新しいトークンを生成
1. 環境変数を更新

## セキュリティに関する注意

- トークンは秘密情報として扱ってください
- トークンをソースコードにハードコードしないでください
- 公開リポジトリにトークンをコミットしないでください
- 不要になったトークンは削除してください
- 定期的にトークンをローテーションすることを推奨します

## 参考リンク

- [Figma API Documentation](https://developers.figma.com/docs/rest-api/)
- [Personal Access Tokens](https://help.figma.com/hc/en-us/articles/8085703771159-Manage-personal-access-tokens)
- [API Scopes](https://developers.figma.com/docs/rest-api/scopes/)
