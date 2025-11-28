"""ツールハンドラのテスト"""

import json
from pathlib import Path
from typing import Any

import pytest

from yet_another_figma_mcp.cache.index import build_index
from yet_another_figma_mcp.cache.store import CacheStore
from yet_another_figma_mcp.tools import (
    get_cached_figma_file,
    get_cached_figma_node,
    list_figma_frames,
    search_figma_frames_by_title,
    search_figma_nodes_by_name,
)


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


@pytest.fixture
def store_with_data(tmp_path: Path, sample_figma_file: dict[str, Any]) -> CacheStore:
    """データが入ったキャッシュストア"""
    file_id = "test123"
    file_dir = tmp_path / file_id
    file_dir.mkdir(parents=True)

    with open(file_dir / "file_raw.json", "w") as f:
        json.dump(sample_figma_file, f)

    index = build_index(sample_figma_file)
    with open(file_dir / "nodes_index.json", "w") as f:
        json.dump(index, f)

    return CacheStore(tmp_path)


class TestGetCachedFigmaFile:
    def test_returns_file_metadata(self, store_with_data: CacheStore) -> None:
        result = get_cached_figma_file(store_with_data, "test123")
        assert result is not None
        assert result["name"] == "Test Design"
        assert "frames" in result

    def test_returns_none_for_missing_file(self, store_with_data: CacheStore) -> None:
        result = get_cached_figma_file(store_with_data, "nonexistent")
        assert result is None


class TestGetCachedFigmaNode:
    def test_returns_node_details(self, store_with_data: CacheStore) -> None:
        result = get_cached_figma_node(store_with_data, "test123", "1:1")
        assert result is not None
        assert result["name"] == "Login Screen"
        assert result["type"] == "FRAME"

    def test_returns_none_for_missing_node(self, store_with_data: CacheStore) -> None:
        result = get_cached_figma_node(store_with_data, "test123", "999:999")
        assert result is None


class TestSearchFigmaNodesByName:
    def test_exact_match(self, store_with_data: CacheStore) -> None:
        results = search_figma_nodes_by_name(store_with_data, "test123", "Primary Button", "exact")
        assert len(results) == 1
        assert results[0]["name"] == "Primary Button"

    def test_partial_match(self, store_with_data: CacheStore) -> None:
        results = search_figma_nodes_by_name(store_with_data, "test123", "Button", "partial")
        assert len(results) >= 1

    def test_limit(self, store_with_data: CacheStore) -> None:
        results = search_figma_nodes_by_name(
            store_with_data, "test123", "Screen", "partial", limit=1
        )
        assert len(results) == 1


class TestSearchFigmaFramesByTitle:
    def test_exact_match(self, store_with_data: CacheStore) -> None:
        results = search_figma_frames_by_title(store_with_data, "test123", "Login Screen", "exact")
        assert len(results) == 1
        assert results[0]["name"] == "Login Screen"

    def test_partial_match(self, store_with_data: CacheStore) -> None:
        results = search_figma_frames_by_title(store_with_data, "test123", "Screen", "partial")
        assert len(results) == 2  # Login Screen, Sign Up Screen


class TestListFigmaFrames:
    def test_lists_top_frames(self, store_with_data: CacheStore) -> None:
        results = list_figma_frames(store_with_data, "test123")
        assert len(results) == 2
        names = [r["name"] for r in results]
        assert "Login Screen" in names
        assert "Sign Up Screen" in names
