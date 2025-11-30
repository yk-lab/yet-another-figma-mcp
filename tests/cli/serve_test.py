"""serve コマンドのテスト"""

import signal
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from yet_another_figma_mcp.cli import app

runner = CliRunner()


class TestServeCommand:
    """serve コマンドのテスト"""

    def test_serve_calls_run_server(self, tmp_path: Path) -> None:
        """serve コマンドが run_server を呼び出す"""
        with (
            patch("yet_another_figma_mcp.cli.serve.asyncio.run") as mock_asyncio_run,
            patch("yet_another_figma_mcp.server.set_cache_dir") as mock_set_cache_dir,
        ):
            mock_asyncio_run.return_value = None

            result = runner.invoke(app, ["serve", "-d", str(tmp_path)])

        # asyncio.run が呼び出されることを確認
        mock_asyncio_run.assert_called_once()
        # set_cache_dir が呼び出されることを確認
        mock_set_cache_dir.assert_called_once_with(tmp_path)
        assert result.exit_code == 0

    def test_serve_uses_default_cache_dir(self) -> None:
        """serve コマンドがデフォルトのキャッシュディレクトリを使用"""
        with (
            patch("yet_another_figma_mcp.cli.serve.asyncio.run") as mock_asyncio_run,
            patch("yet_another_figma_mcp.server.set_cache_dir") as mock_set_cache_dir,
        ):
            mock_asyncio_run.return_value = None

            result = runner.invoke(app, ["serve"])

        mock_set_cache_dir.assert_called_once()
        # デフォルトは ~/.yet_another_figma_mcp
        called_path = mock_set_cache_dir.call_args[0][0]
        assert called_path == Path.home() / ".yet_another_figma_mcp"
        assert result.exit_code == 0

    def test_serve_help_shows_description(self) -> None:
        """serve --help がコマンド説明を表示"""
        result = runner.invoke(app, ["serve", "--help"])

        assert result.exit_code == 0
        assert "MCP サーバーを起動" in result.stdout

    def test_serve_accepts_cache_dir_option(self) -> None:
        """serve コマンドが --cache-dir オプションを受け付ける"""
        result = runner.invoke(app, ["serve", "--help"])

        assert result.exit_code == 0
        assert "--cache-dir" in result.stdout or "-d" in result.stdout

    def test_serve_accepts_verbose_option(self) -> None:
        """serve コマンドが --verbose オプションを受け付ける"""
        result = runner.invoke(app, ["serve", "--help"])

        assert result.exit_code == 0
        assert "--verbose" in result.stdout or "-V" in result.stdout

    def test_serve_verbose_sets_debug_level(self, tmp_path: Path) -> None:
        """--verbose オプションで DEBUG レベルのログが有効になる"""
        import logging

        with (
            patch("yet_another_figma_mcp.cli.serve.asyncio.run") as mock_asyncio_run,
            patch("yet_another_figma_mcp.server.set_cache_dir"),
            patch("yet_another_figma_mcp.cli.serve.logging.basicConfig") as mock_basic_config,
        ):
            mock_asyncio_run.return_value = None

            result = runner.invoke(app, ["serve", "-d", str(tmp_path), "--verbose"])

        assert result.exit_code == 0
        # basicConfig が DEBUG レベルで呼ばれることを確認
        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == logging.DEBUG


class TestServeCommandSignalHandling:
    """serve コマンドのシグナルハンドリングテスト"""

    def test_serve_handles_keyboard_interrupt(self, tmp_path: Path) -> None:
        """KeyboardInterrupt が適切にハンドリングされる"""
        with (
            patch("yet_another_figma_mcp.cli.serve.asyncio.run") as mock_asyncio_run,
            patch("yet_another_figma_mcp.server.set_cache_dir"),
        ):
            mock_asyncio_run.side_effect = KeyboardInterrupt()

            result = runner.invoke(app, ["serve", "-d", str(tmp_path)])

        # KeyboardInterrupt で正常終了
        assert result.exit_code == 0

    def test_serve_registers_sigterm_handler(self, tmp_path: Path) -> None:
        """SIGTERM ハンドラが登録される"""
        registered_handler = None

        def capture_signal(signum: int, handler: object) -> None:
            nonlocal registered_handler
            if signum == signal.SIGTERM:
                registered_handler = handler

        with (
            patch("yet_another_figma_mcp.cli.serve.asyncio.run") as mock_asyncio_run,
            patch("yet_another_figma_mcp.server.set_cache_dir"),
            patch("yet_another_figma_mcp.cli.serve.signal.signal", side_effect=capture_signal),
        ):
            mock_asyncio_run.return_value = None

            result = runner.invoke(app, ["serve", "-d", str(tmp_path)])

        assert result.exit_code == 0
        assert registered_handler is not None

    def test_sigterm_handler_calls_sys_exit(self, tmp_path: Path) -> None:
        """SIGTERM ハンドラが sys.exit(0) を呼び出す"""
        registered_handler = None

        original_signal = signal.signal

        def capture_signal(signum: int, handler: object) -> object:
            nonlocal registered_handler
            if signum == signal.SIGTERM:
                registered_handler = handler
            return original_signal(signum, handler)  # type: ignore[arg-type]

        with (
            patch("yet_another_figma_mcp.cli.serve.asyncio.run") as mock_asyncio_run,
            patch("yet_another_figma_mcp.server.set_cache_dir"),
            patch("yet_another_figma_mcp.cli.serve.signal.signal", side_effect=capture_signal),
        ):
            mock_asyncio_run.return_value = None

            result = runner.invoke(app, ["serve", "-d", str(tmp_path)])

        assert result.exit_code == 0
        assert registered_handler is not None

        # ハンドラを呼び出して sys.exit(0) が呼ばれることを確認
        with patch("yet_another_figma_mcp.cli.serve.sys.exit") as mock_exit:
            registered_handler(signal.SIGTERM, None)  # type: ignore[operator]
            mock_exit.assert_called_once_with(0)
