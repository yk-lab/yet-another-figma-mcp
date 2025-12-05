"""cache コマンドのテスト"""

# pyright: reportPrivateUsage=false

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from yet_another_figma_mcp.cli import app
from yet_another_figma_mcp.cli import i18n
from yet_another_figma_mcp.figma import (
    FigmaAuthenticationError,
    FigmaFileNotFoundError,
    FigmaRateLimitError,
)

runner = CliRunner()


@pytest.fixture(autouse=True)
def reset_language_to_english() -> None:
    """Reset language to English for all tests in this module"""
    i18n.set_language("en")


@pytest.fixture
def mock_figma_response() -> dict[str, Any]:
    """Figma API レスポンスのモック"""
    return {
        "name": "Test Design",
        "lastModified": "2024-01-01T00:00:00Z",
        "document": {
            "id": "0:0",
            "name": "Document",
            "type": "DOCUMENT",
            "children": [
                {
                    "id": "1:1",
                    "name": "Page 1",
                    "type": "CANVAS",
                    "children": [
                        {
                            "id": "2:1",
                            "name": "Frame 1",
                            "type": "FRAME",
                            "children": [],
                        }
                    ],
                }
            ],
        },
    }


class TestCacheCommandValidation:
    """cache コマンドのバリデーションテスト"""

    def test_no_file_id_shows_error(self) -> None:
        """ファイル ID 未指定でエラー"""
        result = runner.invoke(app, ["cache"])
        assert result.exit_code == 1
        assert "Please specify a file ID" in result.stdout

    def test_invalid_file_id_shows_error(self, tmp_path: Path) -> None:
        """無効なファイル ID でエラー"""
        with patch("yet_another_figma_mcp.cli.cache.FigmaClient"):
            result = runner.invoke(app, ["cache", "-f", "../invalid", "-d", str(tmp_path)])
        assert result.exit_code == 1
        assert "Invalid file ID" in result.stdout

    def test_non_utf8_file_list_shows_error(self, tmp_path: Path) -> None:
        """UTF-8 以外のエンコーディングでエラー"""
        file_list = tmp_path / "files.txt"
        # Shift_JIS でエンコードされたファイル（日本語を含む）
        file_list.write_bytes("ファイルID\n".encode("shift_jis"))

        result = runner.invoke(app, ["cache", "-l", str(file_list), "-d", str(tmp_path)])
        assert result.exit_code == 1
        assert "UTF-8" in result.stdout


class TestCacheCommandSuccess:
    """cache コマンドの正常系テスト"""

    def test_cache_single_file(self, tmp_path: Path, mock_figma_response: dict[str, Any]) -> None:
        """単一ファイルのキャッシュ"""
        with patch("yet_another_figma_mcp.cli.cache.FigmaClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_file.return_value = mock_figma_response
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = runner.invoke(app, ["cache", "-f", "abc123", "-d", str(tmp_path)])

        assert result.exit_code == 0
        assert "abc123" in result.stdout
        assert "Test Design" in result.stdout
        assert "Complete" in result.stdout

        # ファイルが保存されていることを確認
        file_path = tmp_path / "abc123" / "file_raw.json"
        assert file_path.exists()
        with open(file_path) as f:
            saved_data = json.load(f)
        assert saved_data["name"] == "Test Design"

        # インデックスが生成されていることを確認
        index_path = tmp_path / "abc123" / "nodes_index.json"
        assert index_path.exists()
        with open(index_path) as f:
            index_data = json.load(f)
        assert "by_id" in index_data
        assert "by_name" in index_data
        assert "by_frame_title" in index_data

    def test_cache_multiple_files(
        self, tmp_path: Path, mock_figma_response: dict[str, Any]
    ) -> None:
        """複数ファイルのキャッシュ"""
        with patch("yet_another_figma_mcp.cli.cache.FigmaClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_file.return_value = mock_figma_response
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = runner.invoke(
                app,
                ["cache", "-f", "file1", "-f", "file2", "-d", str(tmp_path)],
            )

        assert result.exit_code == 0
        assert (tmp_path / "file1" / "file_raw.json").exists()
        assert (tmp_path / "file2" / "file_raw.json").exists()

    def test_cache_shows_progress(
        self, tmp_path: Path, mock_figma_response: dict[str, Any]
    ) -> None:
        """複数ファイルキャッシュ時に進捗表示される"""
        with patch("yet_another_figma_mcp.cli.cache.FigmaClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_file.return_value = mock_figma_response
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = runner.invoke(
                app,
                ["cache", "-f", "file1", "-f", "file2", "-f", "file3", "-d", str(tmp_path)],
            )

        assert result.exit_code == 0
        # 進捗表示 (n/m) が出力される
        assert "(1/3)" in result.stdout
        assert "(2/3)" in result.stdout
        assert "(3/3)" in result.stdout

    def test_cache_saves_metadata_with_timestamp(
        self, tmp_path: Path, mock_figma_response: dict[str, Any]
    ) -> None:
        """キャッシュ時にタイムスタンプを含むメタデータが保存される"""
        with patch("yet_another_figma_mcp.cli.cache.FigmaClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_file.return_value = mock_figma_response
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = runner.invoke(app, ["cache", "-f", "abc123", "-d", str(tmp_path)])

        assert result.exit_code == 0

        # メタデータファイルが保存されていることを確認
        meta_path = tmp_path / "abc123" / "cache_meta.json"
        assert meta_path.exists()

        with open(meta_path) as f:
            meta = json.load(f)

        # タイムスタンプが記録されていることを確認
        assert "cached_at" in meta
        assert "cached_at_unix" in meta
        # ISO 形式のタイムスタンプ
        assert "T" in meta["cached_at"]
        # Unix タイムスタンプ
        assert isinstance(meta["cached_at_unix"], float)

    def test_cache_from_file_list(
        self, tmp_path: Path, mock_figma_response: dict[str, Any]
    ) -> None:
        """ファイルリストからのキャッシュ"""
        # ファイルリスト作成
        file_list = tmp_path / "files.txt"
        file_list.write_text("file1\n# comment\nfile2\n\nfile3\n")

        with patch("yet_another_figma_mcp.cli.cache.FigmaClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_file.return_value = mock_figma_response
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = runner.invoke(app, ["cache", "-l", str(file_list), "-d", str(tmp_path)])

        assert result.exit_code == 0
        assert (tmp_path / "file1" / "file_raw.json").exists()
        assert (tmp_path / "file2" / "file_raw.json").exists()
        assert (tmp_path / "file3" / "file_raw.json").exists()

    def test_skip_cached_file_without_refresh(self, tmp_path: Path) -> None:
        """refresh なしでキャッシュ済みファイルをスキップ"""
        # 既存キャッシュを作成
        cache_dir = tmp_path / "abc123"
        cache_dir.mkdir()
        (cache_dir / "file_raw.json").write_text("{}")

        with patch("yet_another_figma_mcp.cli.cache.FigmaClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = runner.invoke(app, ["cache", "-f", "abc123", "-d", str(tmp_path)])

        assert result.exit_code == 0
        assert "Already cached" in result.stdout
        # API は呼ばれない
        mock_client.get_file.assert_not_called()

    def test_refresh_overwrites_cache(
        self, tmp_path: Path, mock_figma_response: dict[str, Any]
    ) -> None:
        """refresh でキャッシュを上書き"""
        # 既存キャッシュを作成
        cache_dir = tmp_path / "abc123"
        cache_dir.mkdir()
        (cache_dir / "file_raw.json").write_text('{"name": "Old"}')

        with patch("yet_another_figma_mcp.cli.cache.FigmaClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_file.return_value = mock_figma_response
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = runner.invoke(app, ["cache", "-f", "abc123", "-r", "-d", str(tmp_path)])

        assert result.exit_code == 0
        # API が呼ばれる
        mock_client.get_file.assert_called_once()
        # 新しいデータで上書き
        with open(cache_dir / "file_raw.json") as f:
            data = json.load(f)
        assert data["name"] == "Test Design"


class TestCacheCommandErrors:
    """cache コマンドのエラー系テスト"""

    def test_authentication_error(self, tmp_path: Path) -> None:
        """認証エラー"""
        with patch("yet_another_figma_mcp.cli.cache.FigmaClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_file.side_effect = FigmaAuthenticationError()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = runner.invoke(app, ["cache", "-f", "abc123", "-d", str(tmp_path)])

        assert result.exit_code == 1
        assert "Authentication error" in result.stdout

    def test_file_not_found_error(self, tmp_path: Path) -> None:
        """ファイル未存在エラー"""
        with patch("yet_another_figma_mcp.cli.cache.FigmaClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_file.side_effect = FigmaFileNotFoundError("abc123")
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = runner.invoke(app, ["cache", "-f", "abc123", "-d", str(tmp_path)])

        assert result.exit_code == 1
        assert "File not found" in result.stdout

    def test_rate_limit_error(self, tmp_path: Path) -> None:
        """レート制限エラー"""
        with patch("yet_another_figma_mcp.cli.cache.FigmaClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_file.side_effect = FigmaRateLimitError(retry_after=60)
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = runner.invoke(app, ["cache", "-f", "abc123", "-d", str(tmp_path)])

        assert result.exit_code == 1
        assert "Rate limited" in result.stdout
        assert "60 seconds" in result.stdout

    def test_partial_failure(self, tmp_path: Path, mock_figma_response: dict[str, Any]) -> None:
        """一部失敗時のサマリー"""
        with patch("yet_another_figma_mcp.cli.cache.FigmaClient") as mock_client_class:
            mock_client = MagicMock()
            # 1つ目は成功、2つ目は失敗
            mock_client.get_file.side_effect = [
                mock_figma_response,
                FigmaFileNotFoundError("file2"),
            ]
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client_class.return_value = mock_client

            result = runner.invoke(
                app,
                ["cache", "-f", "file1", "-f", "file2", "-d", str(tmp_path)],
            )

        assert result.exit_code == 1
        assert "1 succeeded" in result.stdout
        assert "1 failed" in result.stdout
