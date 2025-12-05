"""status コマンドのテスト"""

import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from yet_another_figma_mcp.cache.index import build_index
from yet_another_figma_mcp.cli import app
from yet_another_figma_mcp.cli import i18n

runner = CliRunner()


@pytest.fixture(autouse=True)
def reset_language_to_english() -> None:
    """Reset language to English for all tests in this module"""
    i18n.set_language("en")


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
                    ],
                }
            ],
        },
    }


@pytest.fixture
def cache_with_files(tmp_path: Path, sample_figma_file: dict[str, Any]) -> Path:
    """キャッシュディレクトリとファイルを作成"""
    # ファイル 1
    file1_dir = tmp_path / "abc123"
    file1_dir.mkdir(parents=True)

    with open(file1_dir / "file_raw.json", "w") as f:
        json.dump(sample_figma_file, f)

    index1 = build_index(sample_figma_file)
    with open(file1_dir / "nodes_index.json", "w") as f:
        json.dump(index1, f)

    with open(file1_dir / "cache_meta.json", "w") as f:
        json.dump({"cached_at": "2024-01-15T10:00:00+00:00"}, f)

    # ファイル 2
    file2_data = {**sample_figma_file, "name": "Another Design"}
    file2_dir = tmp_path / "xyz789"
    file2_dir.mkdir(parents=True)

    with open(file2_dir / "file_raw.json", "w") as f:
        json.dump(file2_data, f)

    index2 = build_index(file2_data)
    with open(file2_dir / "nodes_index.json", "w") as f:
        json.dump(index2, f)

    with open(file2_dir / "cache_meta.json", "w") as f:
        json.dump({"cached_at": "2024-01-20T15:30:00+00:00"}, f)

    return tmp_path


class TestStatusCommand:
    """status コマンドのテスト"""

    def test_status_shows_cached_files(self, cache_with_files: Path) -> None:
        """キャッシュ済みファイルの一覧を表示"""
        result = runner.invoke(app, ["status", "--cache-dir", str(cache_with_files)])

        assert result.exit_code == 0
        assert "abc123" in result.output
        assert "xyz789" in result.output
        assert "Test Design" in result.output
        assert "Another Design" in result.output

    def test_status_shows_no_cache_message(self, tmp_path: Path) -> None:
        """キャッシュがない場合のメッセージを表示"""
        result = runner.invoke(app, ["status", "--cache-dir", str(tmp_path)])

        assert result.exit_code == 0
        assert "No cache found" in result.output

    def test_status_shows_no_cache_for_nonexistent_dir(self, tmp_path: Path) -> None:
        """存在しないディレクトリの場合もメッセージを表示"""
        nonexistent = tmp_path / "nonexistent"
        result = runner.invoke(app, ["status", "--cache-dir", str(nonexistent)])

        assert result.exit_code == 0
        assert "No cache found" in result.output

    def test_status_json_output(self, cache_with_files: Path) -> None:
        """JSON 形式で出力"""
        result = runner.invoke(app, ["status", "--cache-dir", str(cache_with_files), "--json"])

        assert result.exit_code == 0

        # JSON としてパースできることを確認
        data: list[dict[str, object]] = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 2

        # ファイル情報が含まれていることを確認
        file_ids = [item["file_id"] for item in data]
        assert "abc123" in file_ids
        assert "xyz789" in file_ids

    def test_status_json_output_empty(self, tmp_path: Path) -> None:
        """キャッシュがない場合の JSON 出力"""
        result = runner.invoke(app, ["status", "--cache-dir", str(tmp_path), "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data == []

    def test_status_shows_node_count(self, cache_with_files: Path) -> None:
        """ノード数が表示される"""
        result = runner.invoke(app, ["status", "--cache-dir", str(cache_with_files), "--json"])

        data = json.loads(result.output)
        for item in data:
            assert "node_count" in item
            assert item["node_count"] > 0

    def test_status_sorted_by_cached_at(self, cache_with_files: Path) -> None:
        """キャッシュ日時で降順ソートされる"""
        result = runner.invoke(app, ["status", "--cache-dir", str(cache_with_files), "--json"])

        data = json.loads(result.output)
        # xyz789 (2024-01-20) が abc123 (2024-01-15) より先に来る
        assert data[0]["file_id"] == "xyz789"
        assert data[1]["file_id"] == "abc123"

    def test_status_handles_missing_index(
        self, tmp_path: Path, sample_figma_file: dict[str, Any]
    ) -> None:
        """インデックスがなくてもファイルが表示される"""
        file_dir = tmp_path / "noindex"
        file_dir.mkdir(parents=True)

        with open(file_dir / "file_raw.json", "w") as f:
            json.dump(sample_figma_file, f)

        result = runner.invoke(app, ["status", "--cache-dir", str(tmp_path), "--json"])

        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["file_id"] == "noindex"
        assert data[0]["node_count"] == 0

    def test_status_handles_missing_meta(
        self, tmp_path: Path, sample_figma_file: dict[str, Any]
    ) -> None:
        """メタデータがなくてもファイルが表示される (mtime を使用)"""
        file_dir = tmp_path / "nometa"
        file_dir.mkdir(parents=True)

        with open(file_dir / "file_raw.json", "w") as f:
            json.dump(sample_figma_file, f)

        result = runner.invoke(app, ["status", "--cache-dir", str(tmp_path), "--json"])

        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["file_id"] == "nometa"
        # cached_at が設定されている (mtime からのフォールバック)
        assert data[0]["cached_at"] is not None

    def test_status_help(self) -> None:
        """ヘルプメッセージを表示"""
        result = runner.invoke(app, ["status", "--help"])

        assert result.exit_code == 0
        # Docstrings are evaluated at import time, so they stay in Japanese
        assert "キャッシュ済みファイルの一覧と状態を表示" in result.output

    def test_status_skips_invalid_file_id_directory(
        self, tmp_path: Path, sample_figma_file: dict[str, Any]
    ) -> None:
        """不正なファイル ID のディレクトリはスキップされる"""
        # 有効なキャッシュ
        valid_dir = tmp_path / "valid123"
        valid_dir.mkdir(parents=True)
        with open(valid_dir / "file_raw.json", "w") as f:
            json.dump(sample_figma_file, f)

        # 不正なディレクトリ名 (パストラバーサル)
        invalid_dir = tmp_path / "..invalid"
        invalid_dir.mkdir(parents=True)
        with open(invalid_dir / "file_raw.json", "w") as f:
            json.dump(sample_figma_file, f)

        result = runner.invoke(app, ["status", "--cache-dir", str(tmp_path), "--json"])

        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["file_id"] == "valid123"

    def test_status_skips_non_directory(
        self, tmp_path: Path, sample_figma_file: dict[str, Any]
    ) -> None:
        """ディレクトリ以外のファイルはスキップされる"""
        # 有効なキャッシュ
        valid_dir = tmp_path / "valid123"
        valid_dir.mkdir(parents=True)
        with open(valid_dir / "file_raw.json", "w") as f:
            json.dump(sample_figma_file, f)

        # 通常のファイル (ディレクトリではない)
        (tmp_path / "somefile.txt").write_text("not a directory")

        result = runner.invoke(app, ["status", "--cache-dir", str(tmp_path), "--json"])

        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["file_id"] == "valid123"

    def test_status_skips_corrupted_json(self, tmp_path: Path) -> None:
        """破損した JSON ファイルはスキップされる"""
        # 有効なキャッシュ
        valid_dir = tmp_path / "valid123"
        valid_dir.mkdir(parents=True)
        with open(valid_dir / "file_raw.json", "w") as f:
            json.dump({"name": "Valid File"}, f)

        # 破損した JSON
        corrupted_dir = tmp_path / "corrupted"
        corrupted_dir.mkdir(parents=True)
        (corrupted_dir / "file_raw.json").write_text("{invalid json")

        result = runner.invoke(app, ["status", "--cache-dir", str(tmp_path), "--json"])

        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["file_id"] == "valid123"

    def test_status_handles_corrupted_index_json(
        self, tmp_path: Path, sample_figma_file: dict[str, Any]
    ) -> None:
        """破損したインデックス JSON でもファイルは表示される"""
        file_dir = tmp_path / "abc123"
        file_dir.mkdir(parents=True)

        with open(file_dir / "file_raw.json", "w") as f:
            json.dump(sample_figma_file, f)

        # 破損したインデックス
        (file_dir / "nodes_index.json").write_text("{invalid json")

        result = runner.invoke(app, ["status", "--cache-dir", str(tmp_path), "--json"])

        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["file_id"] == "abc123"
        assert data[0]["node_count"] == 0

    def test_status_handles_corrupted_meta_json(
        self, tmp_path: Path, sample_figma_file: dict[str, Any]
    ) -> None:
        """破損したメタデータ JSON でもファイルは表示される (mtime 使用)"""
        file_dir = tmp_path / "abc123"
        file_dir.mkdir(parents=True)

        with open(file_dir / "file_raw.json", "w") as f:
            json.dump(sample_figma_file, f)

        # 破損したメタデータ
        (file_dir / "cache_meta.json").write_text("{invalid json")

        result = runner.invoke(app, ["status", "--cache-dir", str(tmp_path), "--json"])

        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["file_id"] == "abc123"
        # mtime からのフォールバックで cached_at が設定される
        assert data[0]["cached_at"] is not None

    def test_status_skips_directory_without_file_raw(self, tmp_path: Path) -> None:
        """file_raw.json がないディレクトリはスキップされる"""
        # 有効なキャッシュ
        valid_dir = tmp_path / "valid123"
        valid_dir.mkdir(parents=True)
        with open(valid_dir / "file_raw.json", "w") as f:
            json.dump({"name": "Valid File"}, f)

        # file_raw.json がないディレクトリ
        empty_dir = tmp_path / "emptydir"
        empty_dir.mkdir(parents=True)
        # インデックスだけある状態
        (empty_dir / "nodes_index.json").write_text("{}")

        result = runner.invoke(app, ["status", "--cache-dir", str(tmp_path), "--json"])

        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["file_id"] == "valid123"

    def test_status_handles_invalid_datetime_format(
        self, tmp_path: Path, sample_figma_file: dict[str, Any]
    ) -> None:
        """不正な日時形式でもファイルは表示される (テーブル出力で確認)"""
        file_dir = tmp_path / "abc123"
        file_dir.mkdir(parents=True)

        with open(file_dir / "file_raw.json", "w") as f:
            json.dump(sample_figma_file, f)

        # 不正な日時形式のメタデータ
        with open(file_dir / "cache_meta.json", "w") as f:
            json.dump({"cached_at": "not-a-valid-date"}, f)

        # テーブル出力で実行 (_format_datetime が呼ばれる)
        result = runner.invoke(app, ["status", "--cache-dir", str(tmp_path)])

        assert result.exit_code == 0
        assert "abc123" in result.output
        # 不正な日時はそのまま表示される
        assert "not-a-valid-date" in result.output
