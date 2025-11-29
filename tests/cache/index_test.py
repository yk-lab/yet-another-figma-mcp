"""cache/index モジュールのテスト"""

import json
from pathlib import Path
from typing import Any

import pytest

from yet_another_figma_mcp.cache.index import build_index, save_index
from yet_another_figma_mcp.cache.store import InvalidFileIdError


@pytest.fixture
def empty_index() -> dict[str, Any]:
    """空のインデックスデータ"""
    return {"by_id": {}, "by_name": {}, "by_frame_title": {}}


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
    """build_index 関数のテスト"""

    def test_build_index_creates_by_id(self, sample_figma_file: dict[str, Any]) -> None:
        """by_id にノード情報が登録される"""
        index = build_index(sample_figma_file)
        assert "by_id" in index
        assert "1:1" in index["by_id"]
        assert index["by_id"]["1:1"]["name"] == "Login Screen"

    def test_build_index_creates_by_name(self, sample_figma_file: dict[str, Any]) -> None:
        """by_name にノード名から ID へのマッピングが登録される"""
        index = build_index(sample_figma_file)
        assert "by_name" in index
        assert "Login Screen" in index["by_name"]
        assert "1:1" in index["by_name"]["Login Screen"]

    def test_build_index_creates_by_frame_title(self, sample_figma_file: dict[str, Any]) -> None:
        """by_frame_title に FRAME タイプのノードのみが登録される"""
        index = build_index(sample_figma_file)
        assert "by_frame_title" in index
        assert "Login Screen" in index["by_frame_title"]
        assert "Sign Up Screen" in index["by_frame_title"]
        # COMPONENT タイプは登録されない
        assert "Primary Button" not in index["by_frame_title"]

    def test_build_index_stores_node_type(self, sample_figma_file: dict[str, Any]) -> None:
        """by_id にノードタイプが保存される"""
        index = build_index(sample_figma_file)
        assert index["by_id"]["0:0"]["type"] == "DOCUMENT"
        assert index["by_id"]["0:1"]["type"] == "CANVAS"
        assert index["by_id"]["1:1"]["type"] == "FRAME"
        assert index["by_id"]["1:2"]["type"] == "COMPONENT"

    def test_build_index_stores_parent_id(self, sample_figma_file: dict[str, Any]) -> None:
        """by_id に親ノード ID が保存される"""
        index = build_index(sample_figma_file)
        # Document のルートは parent_id が None
        assert index["by_id"]["0:0"]["parent_id"] is None
        # Page の親は Document
        assert index["by_id"]["0:1"]["parent_id"] == "0:0"
        # Frame の親は Page
        assert index["by_id"]["1:1"]["parent_id"] == "0:1"
        # Component の親は Frame
        assert index["by_id"]["1:2"]["parent_id"] == "1:1"

    def test_build_index_generates_path(self, sample_figma_file: dict[str, Any]) -> None:
        """by_id に path 情報が生成される (Document > Page > Frame > ... 形式)"""
        index = build_index(sample_figma_file)
        # Document
        assert index["by_id"]["0:0"]["path"] == ["Document"]
        # Page
        assert index["by_id"]["0:1"]["path"] == ["Document", "Page 1"]
        # Frame
        assert index["by_id"]["1:1"]["path"] == ["Document", "Page 1", "Login Screen"]
        # Component
        assert index["by_id"]["1:2"]["path"] == [
            "Document",
            "Page 1",
            "Login Screen",
            "Primary Button",
        ]

    def test_build_index_handles_duplicate_names(self) -> None:
        """同じ名前のノードが複数ある場合、by_name に全て登録される"""
        file_data: dict[str, Any] = {
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
                            {"id": "1:1", "name": "Button", "type": "FRAME", "children": []},
                            {"id": "1:2", "name": "Button", "type": "FRAME", "children": []},
                            {"id": "1:3", "name": "Button", "type": "COMPONENT", "children": []},
                        ],
                    }
                ],
            }
        }
        index = build_index(file_data)
        # 3つの Button ノードが登録される
        assert len(index["by_name"]["Button"]) == 3
        assert "1:1" in index["by_name"]["Button"]
        assert "1:2" in index["by_name"]["Button"]
        assert "1:3" in index["by_name"]["Button"]
        # by_frame_title には FRAME タイプのみ
        assert len(index["by_frame_title"]["Button"]) == 2
        assert "1:1" in index["by_frame_title"]["Button"]
        assert "1:2" in index["by_frame_title"]["Button"]

    def test_build_index_handles_empty_document(self) -> None:
        """空のドキュメントを処理できる"""
        file_data: dict[str, Any] = {"document": {}}
        index = build_index(file_data)
        assert index["by_id"] == {"": {"name": "", "type": "", "parent_id": None, "path": [""]}}
        assert index["by_name"] == {}
        assert index["by_frame_title"] == {}

    def test_build_index_handles_missing_document(self) -> None:
        """document キーがない場合も処理できる"""
        file_data: dict[str, Any] = {"name": "Test"}
        index = build_index(file_data)
        assert index["by_id"] == {"": {"name": "", "type": "", "parent_id": None, "path": [""]}}
        assert index["by_name"] == {}
        assert index["by_frame_title"] == {}

    def test_build_index_handles_nodes_without_children(self) -> None:
        """children がないノードを処理できる"""
        file_data: dict[str, Any] = {
            "document": {
                "id": "0:0",
                "name": "Document",
                "type": "DOCUMENT",
                # children キーなし
            }
        }
        index = build_index(file_data)
        assert "0:0" in index["by_id"]
        assert index["by_id"]["0:0"]["name"] == "Document"

    def test_build_index_handles_empty_name(self) -> None:
        """名前が空のノードは by_name に登録されない"""
        file_data: dict[str, Any] = {
            "document": {
                "id": "0:0",
                "name": "",
                "type": "DOCUMENT",
                "children": [],
            }
        }
        index = build_index(file_data)
        assert "0:0" in index["by_id"]
        assert "" not in index["by_name"]

    def test_build_index_all_node_ids_in_by_id(self, sample_figma_file: dict[str, Any]) -> None:
        """全てのノードが by_id に登録される"""
        index = build_index(sample_figma_file)
        expected_ids = {"0:0", "0:1", "1:1", "1:2", "1:3"}
        assert set(index["by_id"].keys()) == expected_ids


class TestSaveIndex:
    """save_index 関数のテスト"""

    def test_save_index_creates_file(self, tmp_path: Path) -> None:
        """インデックスファイルが作成される"""
        index = {
            "by_id": {
                "0:0": {"name": "Test", "type": "FRAME", "parent_id": None, "path": ["Test"]}
            },
            "by_name": {"Test": ["0:0"]},
            "by_frame_title": {"Test": ["0:0"]},
        }
        save_index(index, tmp_path, "abc123")
        index_path = tmp_path / "abc123" / "nodes_index.json"
        assert index_path.exists()

    def test_save_index_creates_directory(
        self, tmp_path: Path, empty_index: dict[str, Any]
    ) -> None:
        """ファイル ID 用のディレクトリが自動作成される"""
        save_index(empty_index, tmp_path, "new_file_id")
        assert (tmp_path / "new_file_id").is_dir()

    def test_save_index_content_is_valid_json(self, tmp_path: Path) -> None:
        """保存されたファイルは有効な JSON"""
        index = {
            "by_id": {
                "0:0": {"name": "Node", "type": "FRAME", "parent_id": None, "path": ["Node"]}
            },
            "by_name": {"Node": ["0:0"]},
            "by_frame_title": {"Node": ["0:0"]},
        }
        save_index(index, tmp_path, "test123")
        index_path = tmp_path / "test123" / "nodes_index.json"
        with open(index_path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == index

    def test_save_index_preserves_unicode(self, tmp_path: Path) -> None:
        """日本語などの Unicode 文字が正しく保存される"""
        index = {
            "by_id": {
                "0:0": {
                    "name": "ログイン画面",
                    "type": "FRAME",
                    "parent_id": None,
                    "path": ["ログイン画面"],
                }
            },
            "by_name": {"ログイン画面": ["0:0"]},
            "by_frame_title": {"ログイン画面": ["0:0"]},
        }
        save_index(index, tmp_path, "test123")
        index_path = tmp_path / "test123" / "nodes_index.json"

        # ファイル上に生の日本語テキストが残っていることを確認
        raw_text = index_path.read_text(encoding="utf-8")
        assert "ログイン画面" in raw_text

        # json.load でも正しく読み込める
        with open(index_path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["by_id"]["0:0"]["name"] == "ログイン画面"

    def test_save_index_rejects_invalid_file_id_path_traversal(
        self, tmp_path: Path, empty_index: dict[str, Any]
    ) -> None:
        """パストラバーサル攻撃を含む file_id は拒否"""
        with pytest.raises(InvalidFileIdError):
            save_index(empty_index, tmp_path, "../../../etc/passwd")

    def test_save_index_rejects_invalid_file_id_with_slash(
        self, tmp_path: Path, empty_index: dict[str, Any]
    ) -> None:
        """スラッシュを含む file_id は拒否"""
        with pytest.raises(InvalidFileIdError):
            save_index(empty_index, tmp_path, "abc/def")

    def test_save_index_rejects_empty_file_id(
        self, tmp_path: Path, empty_index: dict[str, Any]
    ) -> None:
        """空の file_id は拒否"""
        with pytest.raises(InvalidFileIdError):
            save_index(empty_index, tmp_path, "")

    def test_save_index_overwrites_existing(
        self, tmp_path: Path, empty_index: dict[str, Any]
    ) -> None:
        """既存のインデックスファイルを上書きする"""
        file_id = "test123"
        file_dir = tmp_path / file_id
        file_dir.mkdir(parents=True)
        (file_dir / "nodes_index.json").write_text('{"old": "data"}')

        save_index(empty_index, tmp_path, file_id)

        with open(file_dir / "nodes_index.json", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == empty_index
        assert "old" not in loaded
