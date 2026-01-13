"""キャッシュストア実装"""

import re
from pathlib import Path
from typing import Any


class InvalidFileIdError(ValueError):
    """無効な file_id が指定された場合のエラー"""

    pass


# Figma file ID の形式: 英数字とハイフン、アンダースコアのみ許可
# 例: "abc123", "AbC_123-xyz"
_VALID_FILE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def normalize_node_id(node_id: str) -> str:
    """node_id を正規化する (ハイフン形式をコロン形式に変換)

    Figma の URL では node-id=123-456 のようにハイフン形式が使われるが、
    API レスポンスでは 123:456 のようにコロン形式で保存されている。

    Args:
        node_id: 正規化する Figma ノード ID

    Returns:
        コロン形式に正規化されたノード ID
    """
    return node_id.replace("-", ":")


def validate_file_id(file_id: str) -> None:
    """file_id を検証し、パストラバーサル攻撃を防止する

    Args:
        file_id: 検証する Figma ファイル ID

    Raises:
        InvalidFileIdError: file_id が無効な形式の場合
    """
    if not file_id:
        raise InvalidFileIdError("file_id cannot be empty")

    if not _VALID_FILE_ID_PATTERN.match(file_id):
        raise InvalidFileIdError(
            f"Invalid file_id format: {file_id!r}. "
            "Only alphanumeric characters, hyphens, and underscores are allowed."
        )


class CacheStore:
    """Figma ファイルキャッシュのインメモリストア"""

    def __init__(self, cache_dir: Path | None = None) -> None:
        """キャッシュストアを初期化

        Args:
            cache_dir: キャッシュディレクトリ (デフォルト: ~/.yet_another_figma_mcp)
        """
        self.cache_dir = cache_dir or Path.home() / ".yet_another_figma_mcp"
        self.files: dict[str, dict[str, Any]] = {}  # file_id -> raw JSON
        self.indexes: dict[str, dict[str, Any]] = {}  # file_id -> nodes_index

    def get_file(self, file_id: str) -> dict[str, Any] | None:
        """ファイルの生 JSON を取得"""
        validate_file_id(file_id)
        if file_id not in self.files:
            self._load_file(file_id)
        return self.files.get(file_id)

    def get_index(self, file_id: str) -> dict[str, Any] | None:
        """ファイルのノードインデックスを取得"""
        validate_file_id(file_id)
        if file_id not in self.indexes:
            self._load_index(file_id)
        return self.indexes.get(file_id)

    def _load_file(self, file_id: str) -> None:
        """ディスクからファイル JSON をロード

        注意: file_id は呼び出し元で検証済みであることを前提とする
        """
        file_path = self.cache_dir / file_id / "file_raw.json"
        if file_path.exists():
            import json

            with open(file_path, encoding="utf-8") as f:
                self.files[file_id] = json.load(f)

    def _load_index(self, file_id: str) -> None:
        """ディスクからインデックスをロード

        注意: file_id は呼び出し元で検証済みであることを前提とする
        """
        index_path = self.cache_dir / file_id / "nodes_index.json"
        if index_path.exists():
            import json

            with open(index_path, encoding="utf-8") as f:
                self.indexes[file_id] = json.load(f)
