"""CLI アプリケーションのテスト"""

from typer.testing import CliRunner

from yet_another_figma_mcp import __version__
from yet_another_figma_mcp.cli import app

runner = CliRunner()


class TestVersionOption:
    """--version オプションのテスト"""

    def test_version_option_shows_version(self) -> None:
        """--version でバージョン情報を表示"""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert __version__ in result.output
        assert "yet-another-figma-mcp" in result.output

    def test_version_short_option_shows_version(self) -> None:
        """-v でバージョン情報を表示"""
        result = runner.invoke(app, ["-v"])

        assert result.exit_code == 0
        assert __version__ in result.output


class TestAppHelp:
    """ヘルプ表示のテスト"""

    def test_help_shows_available_commands(self) -> None:
        """--help で利用可能なコマンドを表示"""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "cache" in result.output
        assert "serve" in result.output
        assert "status" in result.output

    def test_no_args_shows_help(self) -> None:
        """引数なしでヘルプを表示 (no_args_is_help=True)"""
        result = runner.invoke(app, [])

        # no_args_is_help=True の場合は exit_code=0 でヘルプ表示
        # (typer の仕様による)
        assert "cache" in result.output
        assert "serve" in result.output
        assert "status" in result.output
