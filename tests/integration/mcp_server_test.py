"""MCP サーバーの統合テスト"""

import json
from pathlib import Path
from typing import Any

import pytest

from yet_another_figma_mcp.cache.index import build_index, save_index
from yet_another_figma_mcp.server import create_server, get_store, set_cache_dir


@pytest.fixture
def server_with_cache(tmp_path: Path, sample_design_system: dict[str, Any]) -> tuple[Any, str]:
    """キャッシュ付きの MCP サーバーをセットアップ"""
    file_id = "test_design_system"
    file_dir = tmp_path / file_id
    file_dir.mkdir(parents=True)

    # ファイル保存
    with open(file_dir / "file_raw.json", "w", encoding="utf-8") as f:
        json.dump(sample_design_system, f, ensure_ascii=False)

    # インデックス生成・保存
    index = build_index(sample_design_system)
    save_index(index, tmp_path, file_id)

    # サーバーのキャッシュディレクトリを設定
    set_cache_dir(tmp_path)

    server = create_server()
    return server, file_id


class TestMCPServerSetup:
    """MCP サーバーのセットアップテスト"""

    def test_server_has_name(self, server_with_cache: tuple[Any, str]) -> None:
        """サーバーに名前が設定されている"""
        server, _ = server_with_cache
        assert server.name == "yet-another-figma-mcp"

    def test_server_is_created(self, server_with_cache: tuple[Any, str]) -> None:
        """サーバーが正常に作成される"""
        server, _ = server_with_cache
        assert server is not None


class TestMCPServerToolCallsDirect:
    """MCP サーバーのツール呼び出しテスト (直接呼び出し)"""

    def test_get_cached_figma_file_direct(self, server_with_cache: tuple[Any, str]) -> None:
        """get_cached_figma_file の直接呼び出し"""
        _, file_id = server_with_cache

        from yet_another_figma_mcp.tools import get_cached_figma_file

        store = get_store()
        result = get_cached_figma_file(store, file_id)

        assert "error" not in result
        assert result["name"] == "Design System"

    def test_get_cached_figma_node_direct(self, server_with_cache: tuple[Any, str]) -> None:
        """get_cached_figma_node の直接呼び出し"""
        _, file_id = server_with_cache

        from yet_another_figma_mcp.tools import get_cached_figma_node

        store = get_store()
        result = get_cached_figma_node(store, file_id, "1:2")

        assert "error" not in result
        assert result["name"] == "Primary Button"
        assert result["type"] == "COMPONENT"

    def test_search_figma_nodes_by_name_direct(self, server_with_cache: tuple[Any, str]) -> None:
        """search_figma_nodes_by_name の直接呼び出し"""
        _, file_id = server_with_cache

        from yet_another_figma_mcp.tools import search_figma_nodes_by_name

        store = get_store()
        results = search_figma_nodes_by_name(store, file_id, name="Button", match_mode="partial")

        assert len(results) >= 3

    def test_search_figma_nodes_with_ignore_case_direct(
        self, server_with_cache: tuple[Any, str]
    ) -> None:
        """ignore_case オプション付きの検索"""
        _, file_id = server_with_cache

        from yet_another_figma_mcp.tools import search_figma_nodes_by_name

        store = get_store()
        results = search_figma_nodes_by_name(
            store, file_id, name="button", match_mode="partial", ignore_case=True
        )

        assert len(results) >= 3

    def test_search_figma_frames_by_title_direct(self, server_with_cache: tuple[Any, str]) -> None:
        """search_figma_frames_by_title の直接呼び出し"""
        _, file_id = server_with_cache

        from yet_another_figma_mcp.tools import search_figma_frames_by_title

        store = get_store()
        results = search_figma_frames_by_title(store, file_id, title="Login", match_mode="partial")

        frame_names = [f["name"] for f in results]
        assert "Login Screen" in frame_names

    def test_list_figma_frames_direct(self, server_with_cache: tuple[Any, str]) -> None:
        """list_figma_frames の直接呼び出し"""
        _, file_id = server_with_cache

        from yet_another_figma_mcp.tools import list_figma_frames

        store = get_store()
        results = list_figma_frames(store, file_id)

        frame_names = [f["name"] for f in results]
        assert "Buttons" in frame_names
        assert "Login Screen" in frame_names


class TestMCPServerErrorHandlingDirect:
    """MCP サーバーのエラーハンドリングテスト (直接呼び出し)"""

    def test_nonexistent_file_returns_error(self, server_with_cache: tuple[Any, str]) -> None:
        """存在しないファイルへのアクセスはエラー"""
        from yet_another_figma_mcp.tools import get_cached_figma_file

        store = get_store()
        result = get_cached_figma_file(store, "nonexistent")

        assert result["error"] == "file_not_found"

    def test_nonexistent_node_returns_error(self, server_with_cache: tuple[Any, str]) -> None:
        """存在しないノードへのアクセスはエラー"""
        _, file_id = server_with_cache

        from yet_another_figma_mcp.tools import get_cached_figma_node

        store = get_store()
        result = get_cached_figma_node(store, file_id, "999:999")

        assert result["error"] == "node_not_found"

    def test_invalid_file_id_returns_error(self, server_with_cache: tuple[Any, str]) -> None:
        """無効なファイル ID はエラー"""
        from yet_another_figma_mcp.tools import get_cached_figma_file

        store = get_store()
        result = get_cached_figma_file(store, "../invalid")

        assert result["error"] == "invalid_file_id"


class TestCacheStoreSingleton:
    """キャッシュストアのシングルトン動作テスト"""

    def test_get_store_returns_same_instance(self, tmp_path: Path) -> None:
        """get_store は同じインスタンスを返す"""
        set_cache_dir(tmp_path)

        store1 = get_store()
        store2 = get_store()

        assert store1 is store2

    def test_set_cache_dir_resets_store(self, tmp_path: Path) -> None:
        """set_cache_dir でストアがリセットされる"""
        set_cache_dir(tmp_path)
        store1 = get_store()

        # 別のディレクトリを設定
        new_dir = tmp_path / "new_cache"
        new_dir.mkdir()
        set_cache_dir(new_dir)
        store2 = get_store()

        assert store1 is not store2
