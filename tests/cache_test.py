"""キャッシュモジュールのテスト"""

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest

from yet_another_figma_mcp.cache.index import build_index
from yet_another_figma_mcp.cache.store import CacheStore


@pytest.fixture
def sample_figma_file() -> dict[str, Any]:
    """サンプルの Figma ファイルデータ"""
    return {
        "name": "Test Design",
        "lastModified": "2024-01-01T00:00:00Z",
        "version": "1",
        "document": {
            "id": "0:0",
            "name": "Document",
            "type": "DOCUMENT",
            "children": [
                {
                    "id": "0:1",
                    "name": "Page 1",
                    "type": "CANVAS",
                    "children": [
                        {
                            "id": "1:1",
                            "name": "Login Screen",
                            "type": "FRAME",
                            "children": [
                                {
                                    "id": "1:2",
                                    "name": "Primary Button",
                                    "type": "COMPONENT",
                                    "children": [],
                                }
                            ],
                        },
                        {
                            "id": "1:3",
                            "name": "Sign Up Screen",
                            "type": "FRAME",
                            "children": [],
                        },
                    ],
                }
            ],
        },
    }


class TestBuildIndex:
    def test_build_index_creates_by_id(self, sample_figma_file: dict[str, Any]) -> None:
        index = build_index(sample_figma_file)
        assert "by_id" in index
        assert "1:1" in index["by_id"]
        assert index["by_id"]["1:1"]["name"] == "Login Screen"

    def test_build_index_creates_by_name(self, sample_figma_file: dict[str, Any]) -> None:
        index = build_index(sample_figma_file)
        assert "by_name" in index
        assert "Login Screen" in index["by_name"]
        assert "1:1" in index["by_name"]["Login Screen"]

    def test_build_index_creates_by_frame_title(self, sample_figma_file: dict[str, Any]) -> None:
        index = build_index(sample_figma_file)
        assert "by_frame_title" in index
        assert "Login Screen" in index["by_frame_title"]
        assert "Sign Up Screen" in index["by_frame_title"]


class TestCacheStore:
    def test_cache_store_loads_from_disk(self, sample_figma_file: dict[str, Any]) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            file_id = "test123"
            file_dir = cache_dir / file_id
            file_dir.mkdir(parents=True)

            # ファイルを保存
            with open(file_dir / "file_raw.json", "w") as f:
                json.dump(sample_figma_file, f)

            index = build_index(sample_figma_file)
            with open(file_dir / "nodes_index.json", "w") as f:
                json.dump(index, f)

            # ストアからロード
            store = CacheStore(cache_dir)
            loaded_file = store.get_file(file_id)
            assert loaded_file is not None
            assert loaded_file["name"] == "Test Design"

            loaded_index = store.get_index(file_id)
            assert loaded_index is not None
            assert "by_id" in loaded_index
