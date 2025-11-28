"""キャッシュストア実装"""

from pathlib import Path
from typing import Any


class CacheStore:
    """Figma ファイルキャッシュのインメモリストア"""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or Path.home() / ".yet_another_figma_mcp"
        self.files: dict[str, dict[str, Any]] = {}  # file_id -> raw JSON
        self.indexes: dict[str, dict[str, Any]] = {}  # file_id -> nodes_index

    def get_file(self, file_id: str) -> dict[str, Any] | None:
        """ファイルの生 JSON を取得"""
        if file_id not in self.files:
            self._load_file(file_id)
        return self.files.get(file_id)

    def get_index(self, file_id: str) -> dict[str, Any] | None:
        """ファイルのノードインデックスを取得"""
        if file_id not in self.indexes:
            self._load_index(file_id)
        return self.indexes.get(file_id)

    def _load_file(self, file_id: str) -> None:
        """ディスクからファイル JSON をロード"""
        file_path = self.cache_dir / file_id / "file_raw.json"
        if file_path.exists():
            import json

            with open(file_path, encoding="utf-8") as f:
                self.files[file_id] = json.load(f)

    def _load_index(self, file_id: str) -> None:
        """ディスクからインデックスをロード"""
        index_path = self.cache_dir / file_id / "nodes_index.json"
        if index_path.exists():
            import json

            with open(index_path, encoding="utf-8") as f:
                self.indexes[file_id] = json.load(f)
