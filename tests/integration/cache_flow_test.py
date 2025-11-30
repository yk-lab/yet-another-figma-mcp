"""キャッシュ生成→読み込み→検索の統合テスト"""

import json
from pathlib import Path
from typing import Any

import pytest

from yet_another_figma_mcp.cache.index import build_index, save_index
from yet_another_figma_mcp.cache.store import CacheStore
from yet_another_figma_mcp.tools import (
    get_cached_figma_file,
    get_cached_figma_node,
    list_figma_frames,
    search_figma_frames_by_title,
    search_figma_nodes_by_name,
)


class TestCacheFlowIntegration:
    """キャッシュの生成から検索までの一連フローを検証"""

    @pytest.fixture
    def setup_cache(
        self, tmp_path: Path, sample_design_system: dict[str, Any]
    ) -> tuple[CacheStore, str]:
        """キャッシュをセットアップして store と file_id を返す"""
        file_id = "design_system_v1"
        file_dir = tmp_path / file_id
        file_dir.mkdir(parents=True)

        # ファイル保存
        with open(file_dir / "file_raw.json", "w", encoding="utf-8") as f:
            json.dump(sample_design_system, f, ensure_ascii=False)

        # インデックス生成・保存
        index = build_index(sample_design_system)
        save_index(index, tmp_path, file_id)

        store = CacheStore(tmp_path)
        return store, file_id

    def test_full_flow_get_file_metadata(self, setup_cache: tuple[CacheStore, str]) -> None:
        """ファイルメタデータ取得のフロー"""
        store, file_id = setup_cache

        result = get_cached_figma_file(store, file_id)

        assert "error" not in result
        assert result["name"] == "Design System"
        assert result["lastModified"] == "2024-06-15T10:30:00Z"
        assert "frames" in result
        # Components ページと Screens ページからフレームを取得
        frame_names = [f["name"] for f in result["frames"]]
        assert "Buttons" in frame_names
        assert "Input Fields" in frame_names
        assert "Login Screen" in frame_names
        assert "Dashboard" in frame_names

    def test_full_flow_get_node_by_id(self, setup_cache: tuple[CacheStore, str]) -> None:
        """ID によるノード取得のフロー"""
        store, file_id = setup_cache

        # Primary Button コンポーネントを取得
        result = get_cached_figma_node(store, file_id, "1:2")

        assert "error" not in result
        assert result["name"] == "Primary Button"
        assert result["type"] == "COMPONENT"
        # 子ノードが含まれている
        assert "children" in result

    def test_full_flow_search_by_name_exact(self, setup_cache: tuple[CacheStore, str]) -> None:
        """名前による完全一致検索のフロー"""
        store, file_id = setup_cache

        results = search_figma_nodes_by_name(
            store, file_id, name="Primary Button", match_mode="exact"
        )

        assert len(results) == 1
        assert results[0]["name"] == "Primary Button"

    def test_full_flow_search_by_name_partial(self, setup_cache: tuple[CacheStore, str]) -> None:
        """名前による部分一致検索のフロー"""
        store, file_id = setup_cache

        results = search_figma_nodes_by_name(store, file_id, name="Button", match_mode="partial")

        # Primary Button, Secondary Button, Icon Button, Submit Button, Menu Button, Profile Button
        assert len(results) >= 3
        for node in results:
            assert "Button" in node["name"]

    def test_full_flow_search_by_name_case_insensitive(
        self, setup_cache: tuple[CacheStore, str]
    ) -> None:
        """大文字小文字を区別しない検索のフロー"""
        store, file_id = setup_cache

        results = search_figma_nodes_by_name(
            store, file_id, name="button", match_mode="partial", ignore_case=True
        )

        assert len(results) >= 3

    def test_full_flow_search_by_name_multibyte(self, setup_cache: tuple[CacheStore, str]) -> None:
        """マルチバイト文字 (日本語) での検索フロー"""
        store, file_id = setup_cache

        # 日本語名の完全一致検索
        results = search_figma_nodes_by_name(
            store, file_id, name="プライマリボタン", match_mode="exact"
        )
        assert len(results) == 1
        assert results[0]["name"] == "プライマリボタン"

        # 日本語名の部分一致検索
        results = search_figma_nodes_by_name(store, file_id, name="ボタン", match_mode="partial")
        assert len(results) >= 2
        for node in results:
            assert "ボタン" in node["name"]

    def test_full_flow_search_frames_by_title_multibyte(
        self, setup_cache: tuple[CacheStore, str]
    ) -> None:
        """マルチバイト文字 (日本語) でのフレーム検索フロー"""
        store, file_id = setup_cache

        results = search_figma_frames_by_title(
            store, file_id, title="入力フィールド", match_mode="exact"
        )
        assert len(results) == 1
        assert results[0]["name"] == "入力フィールド"

    def test_full_flow_search_frames_by_title(self, setup_cache: tuple[CacheStore, str]) -> None:
        """フレームタイトルによる検索のフロー"""
        store, file_id = setup_cache

        results = search_figma_frames_by_title(store, file_id, title="Login", match_mode="partial")

        assert len(results) >= 1
        frame_names = [f["name"] for f in results]
        assert "Login Screen" in frame_names

    def test_full_flow_list_frames(self, setup_cache: tuple[CacheStore, str]) -> None:
        """フレーム一覧取得のフロー"""
        store, file_id = setup_cache

        results = list_figma_frames(store, file_id)

        frame_names = [f["name"] for f in results]
        # トップレベルフレームが含まれている
        assert "Buttons" in frame_names
        assert "Input Fields" in frame_names
        assert "Login Screen" in frame_names
        assert "Dashboard" in frame_names

    def test_full_flow_navigate_hierarchy(self, setup_cache: tuple[CacheStore, str]) -> None:
        """階層構造をたどるフロー"""
        store, file_id = setup_cache

        # まずフレーム一覧を取得
        frames = list_figma_frames(store, file_id)
        assert len(frames) > 0

        # Buttons フレームを見つける
        buttons_frame = None
        for frame in frames:
            if frame["name"] == "Buttons":
                buttons_frame = frame
                break
        assert buttons_frame is not None

        # Buttons フレームの詳細を取得
        node_result = get_cached_figma_node(store, file_id, buttons_frame["id"])
        assert "error" not in node_result
        assert node_result["type"] == "FRAME"
        assert "children" in node_result

        # 子コンポーネントを検証
        child_names = [c["name"] for c in node_result["children"]]
        assert "Primary Button" in child_names
        assert "Secondary Button" in child_names
        assert "Icon Button" in child_names


class TestMultipleFilesIntegration:
    """複数ファイルのキャッシュ管理の統合テスト"""

    @pytest.fixture
    def setup_multiple_caches(
        self, tmp_path: Path, sample_design_system: dict[str, Any]
    ) -> tuple[CacheStore, list[str]]:
        """複数ファイルのキャッシュをセットアップ"""
        file_ids = ["file_a", "file_b", "file_c"]

        for i, file_id in enumerate(file_ids):
            file_dir = tmp_path / file_id
            file_dir.mkdir(parents=True)

            # ファイル名を変更してそれぞれ区別可能に
            file_data = {**sample_design_system, "name": f"Design System {i + 1}"}

            with open(file_dir / "file_raw.json", "w", encoding="utf-8") as f:
                json.dump(file_data, f, ensure_ascii=False)

            index = build_index(file_data)
            save_index(index, tmp_path, file_id)

        store = CacheStore(tmp_path)
        return store, file_ids

    def test_access_multiple_files(
        self, setup_multiple_caches: tuple[CacheStore, list[str]]
    ) -> None:
        """複数ファイルに個別にアクセス"""
        store, file_ids = setup_multiple_caches

        for i, file_id in enumerate(file_ids):
            result = get_cached_figma_file(store, file_id)
            assert "error" not in result
            assert result["name"] == f"Design System {i + 1}"

    def test_search_in_specific_file(
        self, setup_multiple_caches: tuple[CacheStore, list[str]]
    ) -> None:
        """特定ファイル内での検索"""
        store, file_ids = setup_multiple_caches

        # 各ファイルで同じクエリを実行
        for file_id in file_ids:
            results = search_figma_nodes_by_name(
                store, file_id, name="Button", match_mode="partial"
            )
            assert len(results) >= 3

    def test_nonexistent_file_returns_error(
        self, setup_multiple_caches: tuple[CacheStore, list[str]]
    ) -> None:
        """存在しないファイルへのアクセスはエラー"""
        store, _ = setup_multiple_caches

        result = get_cached_figma_file(store, "nonexistent_file")
        assert result["error"] == "file_not_found"


class TestIndexConsistency:
    """インデックスの一貫性テスト"""

    def test_all_nodes_searchable_by_id(
        self, tmp_path: Path, sample_design_system: dict[str, Any]
    ) -> None:
        """インデックス内の全ノードが ID で検索可能"""
        file_id = "test_file"
        file_dir = tmp_path / file_id
        file_dir.mkdir(parents=True)

        with open(file_dir / "file_raw.json", "w", encoding="utf-8") as f:
            json.dump(sample_design_system, f, ensure_ascii=False)

        index = build_index(sample_design_system)
        save_index(index, tmp_path, file_id)

        store = CacheStore(tmp_path)

        # インデックス内の全ノード ID を取得
        with open(file_dir / "nodes_index.json", encoding="utf-8") as f:
            index_data = json.load(f)

        node_ids = list(index_data["by_id"].keys())
        assert len(node_ids) > 0

        # 各ノードが取得可能か確認
        for node_id in node_ids:
            result = get_cached_figma_node(store, file_id, node_id)
            assert "error" not in result, f"Node {node_id} should be accessible"
            assert result["id"] == node_id

    def test_frame_search_returns_only_frames(
        self, tmp_path: Path, sample_design_system: dict[str, Any]
    ) -> None:
        """フレーム検索は FRAME タイプのみを返す"""
        file_id = "test_file"
        file_dir = tmp_path / file_id
        file_dir.mkdir(parents=True)

        with open(file_dir / "file_raw.json", "w", encoding="utf-8") as f:
            json.dump(sample_design_system, f, ensure_ascii=False)

        index = build_index(sample_design_system)
        save_index(index, tmp_path, file_id)

        store = CacheStore(tmp_path)

        results = list_figma_frames(store, file_id)

        # 全結果が FRAME であることを確認
        for frame in results:
            # list_figma_frames は type を含まないので、ノードを直接取得して確認
            node = get_cached_figma_node(store, file_id, frame["id"])
            assert node["type"] == "FRAME"
