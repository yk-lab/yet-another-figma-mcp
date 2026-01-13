"""cache/store モジュールのテスト"""

import json
from pathlib import Path
from typing import Any

import pytest

from yet_another_figma_mcp.cache.index import build_index
from yet_another_figma_mcp.cache.store import (
    CacheStore,
    InvalidFileIdError,
    normalize_node_id,
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


class TestCacheStore:
    def test_cache_store_loads_from_disk(
        self, tmp_path: Path, sample_figma_file: dict[str, Any]
    ) -> None:
        """ディスクからキャッシュを読み込めることを確認"""
        file_id = "test123"
        file_dir = tmp_path / file_id
        file_dir.mkdir(parents=True)

        # ファイルを保存
        with open(file_dir / "file_raw.json", "w") as f:
            json.dump(sample_figma_file, f)

        index = build_index(sample_figma_file)
        with open(file_dir / "nodes_index.json", "w") as f:
            json.dump(index, f)

        # ストアからロード
        store = CacheStore(tmp_path)
        loaded_file = store.get_file(file_id)
        assert loaded_file is not None
        assert loaded_file["name"] == "Test Design"

        loaded_index = store.get_index(file_id)
        assert loaded_index is not None
        assert "by_id" in loaded_index


class TestFileIdValidation:
    """file_id のバリデーションテスト (パストラバーサル攻撃対策)"""

    def test_valid_file_id_alphanumeric(self) -> None:
        """英数字のみの file_id は有効"""
        store = CacheStore()
        # 存在しないファイルなので None が返るが、エラーにはならない
        result = store.get_file("abc123")
        assert result is None

    def test_valid_file_id_with_hyphen(self) -> None:
        """ハイフンを含む file_id は有効"""
        store = CacheStore()
        result = store.get_file("abc-123-xyz")
        assert result is None

    def test_valid_file_id_with_underscore(self) -> None:
        """アンダースコアを含む file_id は有効"""
        store = CacheStore()
        result = store.get_file("abc_123_xyz")
        assert result is None

    def test_invalid_file_id_path_traversal(self) -> None:
        """パストラバーサル攻撃を含む file_id は拒否"""
        store = CacheStore()
        with pytest.raises(InvalidFileIdError):
            store.get_file("../../../etc/passwd")

    def test_invalid_file_id_with_slash(self) -> None:
        """スラッシュを含む file_id は拒否"""
        store = CacheStore()
        with pytest.raises(InvalidFileIdError):
            store.get_file("abc/def")

    def test_invalid_file_id_with_backslash(self) -> None:
        """バックスラッシュを含む file_id は拒否"""
        store = CacheStore()
        with pytest.raises(InvalidFileIdError):
            store.get_file("abc\\def")

    def test_invalid_file_id_with_dot_dot(self) -> None:
        """.. を含む file_id は拒否"""
        store = CacheStore()
        with pytest.raises(InvalidFileIdError):
            store.get_file("..")

    def test_invalid_file_id_empty(self) -> None:
        """空の file_id は拒否"""
        store = CacheStore()
        with pytest.raises(InvalidFileIdError):
            store.get_file("")

    def test_invalid_file_id_with_space(self) -> None:
        """スペースを含む file_id は拒否"""
        store = CacheStore()
        with pytest.raises(InvalidFileIdError):
            store.get_file("abc def")

    def test_get_index_also_validates(self) -> None:
        """get_index も同様にバリデーションを行う"""
        store = CacheStore()
        with pytest.raises(InvalidFileIdError):
            store.get_index("../../../etc/passwd")


class TestNormalizeNodeId:
    """node_id の正規化テスト (URL形式 → API形式)"""

    def test_hyphen_to_colon(self) -> None:
        """ハイフン形式をコロン形式に変換"""
        assert normalize_node_id("7749-4609") == "7749:4609"

    def test_multiple_hyphens(self) -> None:
        """複数のハイフンがある場合も全て変換"""
        assert normalize_node_id("1-2-3") == "1:2:3"

    def test_already_colon_format(self) -> None:
        """既にコロン形式の場合はそのまま"""
        assert normalize_node_id("7749:4609") == "7749:4609"

    def test_no_separator(self) -> None:
        """セパレータがない場合はそのまま"""
        assert normalize_node_id("12345") == "12345"

    def test_empty_string(self) -> None:
        """空文字列はそのまま"""
        assert normalize_node_id("") == ""

    def test_complex_id(self) -> None:
        """複雑なノードIDの変換"""
        assert normalize_node_id("123-456-789") == "123:456:789"
