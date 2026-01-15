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
        assert "error" not in result
        assert result["name"] == "Test Design"
        assert "frames" in result

    def test_returns_error_for_missing_file(self, store_with_data: CacheStore) -> None:
        result = get_cached_figma_file(store_with_data, "nonexistent")
        assert result["error"] == "file_not_found"
        assert "message" in result
        assert result["file_id"] == "nonexistent"

    def test_returns_error_for_invalid_file_id(self, store_with_data: CacheStore) -> None:
        """無効な file_id はエラーを返す"""
        result = get_cached_figma_file(store_with_data, "../invalid")
        assert result["error"] == "invalid_file_id"
        assert result["file_id"] == "../invalid"

    def test_returns_error_when_file_data_missing(
        self, tmp_path: Path, sample_figma_file: dict[str, Any]
    ) -> None:
        """インデックスはあるがファイルデータがない場合はエラーを返す"""
        file_id = "indexonly"
        file_dir = tmp_path / file_id
        file_dir.mkdir(parents=True)

        # インデックスのみ作成 (file_raw.json は作成しない)
        index = build_index(sample_figma_file)
        with open(file_dir / "nodes_index.json", "w") as f:
            json.dump(index, f)

        store = CacheStore(tmp_path)
        result = get_cached_figma_file(store, file_id)
        assert result["error"] == "file_data_missing"
        assert result["file_id"] == file_id


class TestGetCachedFigmaNode:
    def test_returns_error_for_invalid_file_id(self, store_with_data: CacheStore) -> None:
        """無効な file_id はエラーを返す"""
        result = get_cached_figma_node(store_with_data, "../invalid", "1:1")
        assert result["error"] == "invalid_file_id"
        assert result["file_id"] == "../invalid"

    def test_returns_node_details(self, store_with_data: CacheStore) -> None:
        result = get_cached_figma_node(store_with_data, "test123", "1:1")
        assert "error" not in result
        assert result["name"] == "Login Screen"
        assert result["type"] == "FRAME"

    def test_returns_error_for_missing_node(self, store_with_data: CacheStore) -> None:
        result = get_cached_figma_node(store_with_data, "test123", "999:999")
        assert result["error"] == "node_not_found"
        assert "message" in result
        assert result["node_id"] == "999:999"

    def test_returns_error_for_missing_file(self, store_with_data: CacheStore) -> None:
        result = get_cached_figma_node(store_with_data, "nonexistent", "1:1")
        assert result["error"] == "file_not_found"
        assert result["file_id"] == "nonexistent"

    def test_accepts_hyphen_format_node_id(self, store_with_data: CacheStore) -> None:
        """URL形式のハイフン区切りnode_idでもノードを取得できる"""
        # "1-1" は URL の node-id パラメータ形式、内部的には "1:1"
        result = get_cached_figma_node(store_with_data, "test123", "1-1")
        assert "error" not in result
        assert result["name"] == "Login Screen"
        assert result["type"] == "FRAME"

    def test_accepts_nested_node_with_hyphen_format(self, store_with_data: CacheStore) -> None:
        """ネストされたノードもハイフン形式で取得できる"""
        result = get_cached_figma_node(store_with_data, "test123", "1-2")
        assert "error" not in result
        assert result["name"] == "Primary Button"
        assert result["type"] == "COMPONENT"

    def test_depth_zero_excludes_children(self, store_with_data: CacheStore) -> None:
        """depth=0 で子要素が除外される"""
        result = get_cached_figma_node(store_with_data, "test123", "1:1", depth=0)
        assert "error" not in result
        assert result["name"] == "Login Screen"
        assert "children" not in result
        assert result["_childCount"] == 1  # Primary Button

    def test_depth_one_includes_immediate_children(self, store_with_data: CacheStore) -> None:
        """depth=1 で直接の子要素のみ含まれる"""
        result = get_cached_figma_node(store_with_data, "test123", "1:1", depth=1)
        assert "error" not in result
        assert "children" in result
        assert len(result["children"]) == 1
        # 子要素の子要素は含まれない
        child = result["children"][0]
        assert child["name"] == "Primary Button"
        assert "children" not in child or child.get("_childCount") == 0

    def test_simplified_mode_returns_css_like_format(self, store_with_data: CacheStore) -> None:
        """simplified=True でCSS風の簡略化形式で返る"""
        result = get_cached_figma_node(store_with_data, "test123", "1:1", simplified=True)
        assert "error" not in result
        assert result["name"] == "Login Screen"
        assert result["type"] == "FRAME"
        # 簡略化モードでは余計なプロパティが除外される
        assert "absoluteBoundingBox" not in result

    def test_simplified_with_depth(self, store_with_data: CacheStore) -> None:
        """simplified=True と depth の組み合わせ"""
        result = get_cached_figma_node(store_with_data, "test123", "1:1", depth=0, simplified=True)
        assert "error" not in result
        assert result["name"] == "Login Screen"
        # 子要素が除外されている
        assert result.get("children") == []
        assert result.get("_childCount") == 1


class TestSearchFigmaNodesByName:
    def test_returns_empty_for_invalid_file_id(self, store_with_data: CacheStore) -> None:
        """無効な file_id は空リストを返す"""
        results = search_figma_nodes_by_name(store_with_data, "../invalid", "Button", "exact")
        assert results == []

    def test_returns_empty_for_missing_index(self, store_with_data: CacheStore) -> None:
        """インデックスがない場合は空リストを返す"""
        results = search_figma_nodes_by_name(store_with_data, "nonexistent", "Button", "exact")
        assert results == []

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

    def test_exact_match_case_sensitive_by_default(self, store_with_data: CacheStore) -> None:
        """exact モードはデフォルトで大文字小文字を区別する"""
        results = search_figma_nodes_by_name(store_with_data, "test123", "primary button", "exact")
        assert len(results) == 0

    def test_exact_match_ignore_case(self, store_with_data: CacheStore) -> None:
        """ignore_case=True で大文字小文字を無視した完全一致"""
        results = search_figma_nodes_by_name(
            store_with_data, "test123", "primary button", "exact", ignore_case=True
        )
        assert len(results) == 1
        assert results[0]["name"] == "Primary Button"

    def test_partial_match_always_case_insensitive(self, store_with_data: CacheStore) -> None:
        """partial モードは常に大文字小文字を無視する"""
        results = search_figma_nodes_by_name(store_with_data, "test123", "button", "partial")
        assert len(results) >= 1
        assert any(r["name"] == "Primary Button" for r in results)


class TestSearchFigmaFramesByTitle:
    def test_returns_empty_for_invalid_file_id(self, store_with_data: CacheStore) -> None:
        """無効な file_id は空リストを返す"""
        results = search_figma_frames_by_title(store_with_data, "../invalid", "Screen", "exact")
        assert results == []

    def test_returns_empty_for_missing_index(self, store_with_data: CacheStore) -> None:
        """インデックスがない場合は空リストを返す"""
        results = search_figma_frames_by_title(store_with_data, "nonexistent", "Screen", "exact")
        assert results == []

    def test_limit(self, store_with_data: CacheStore) -> None:
        """limit パラメータで取得件数を制限できる"""
        results = search_figma_frames_by_title(
            store_with_data, "test123", "Screen", "partial", limit=1
        )
        assert len(results) == 1

    def test_exact_match(self, store_with_data: CacheStore) -> None:
        results = search_figma_frames_by_title(store_with_data, "test123", "Login Screen", "exact")
        assert len(results) == 1
        assert results[0]["name"] == "Login Screen"

    def test_partial_match(self, store_with_data: CacheStore) -> None:
        results = search_figma_frames_by_title(store_with_data, "test123", "Screen", "partial")
        assert len(results) == 2  # Login Screen, Sign Up Screen

    def test_exact_match_case_sensitive_by_default(self, store_with_data: CacheStore) -> None:
        """exact モードはデフォルトで大文字小文字を区別する"""
        results = search_figma_frames_by_title(store_with_data, "test123", "login screen", "exact")
        assert len(results) == 0

    def test_exact_match_ignore_case(self, store_with_data: CacheStore) -> None:
        """ignore_case=True で大文字小文字を無視した完全一致"""
        results = search_figma_frames_by_title(
            store_with_data, "test123", "login screen", "exact", ignore_case=True
        )
        assert len(results) == 1
        assert results[0]["name"] == "Login Screen"

    def test_partial_match_always_case_insensitive(self, store_with_data: CacheStore) -> None:
        """partial モードは常に大文字小文字を無視する"""
        results = search_figma_frames_by_title(store_with_data, "test123", "screen", "partial")
        assert len(results) == 2
        names = [r["name"] for r in results]
        assert "Login Screen" in names
        assert "Sign Up Screen" in names


class TestListFigmaFrames:
    def test_returns_empty_for_invalid_file_id(self, store_with_data: CacheStore) -> None:
        """無効な file_id は空リストを返す"""
        results = list_figma_frames(store_with_data, "../invalid")
        assert results == []

    def test_returns_empty_for_missing_index(self, store_with_data: CacheStore) -> None:
        """インデックスがない場合は空リストを返す"""
        results = list_figma_frames(store_with_data, "nonexistent")
        assert results == []

    def test_lists_top_frames(self, store_with_data: CacheStore) -> None:
        results = list_figma_frames(store_with_data, "test123")
        assert len(results) == 2
        names = [r["name"] for r in results]
        assert "Login Screen" in names
        assert "Sign Up Screen" in names
