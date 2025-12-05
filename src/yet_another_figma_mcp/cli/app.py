"""CLI アプリケーション定義"""

import os
from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint

from yet_another_figma_mcp import __version__
from yet_another_figma_mcp.cli.i18n import init_language, set_language, t

# サブコマンドモジュールをインポート (循環参照を避けるため関数内でインポート)

DEFAULT_CACHE_DIR = Path.home() / ".yet_another_figma_mcp"

# Initialize language from system settings
init_language()

app = typer.Typer(
    name="yet-another-figma-mcp",
    help=t("app.help"),
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    """バージョン情報を表示"""
    if value:
        rprint(f"yet-another-figma-mcp {__version__}")
        raise typer.Exit()


def lang_callback(value: str | None) -> None:
    """言語設定コールバック"""
    if value:
        set_language(value)
        # Also set environment variable for child processes
        os.environ["YAFM_LANG"] = value


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help=t("app.version_help"),
        ),
    ] = None,
    lang: Annotated[
        str | None,
        typer.Option(
            "--lang",
            "-L",
            callback=lang_callback,
            is_eager=True,
            help="Language (ja/en)",
        ),
    ] = None,
) -> None:
    """YetAnotherFigmaMCP - Figma ファイルキャッシュ MCP サーバー"""
    pass


# サブコマンドを登録
def _register_commands() -> None:
    """サブコマンドを登録"""
    from yet_another_figma_mcp.cli import cache, serve, status

    app.command()(cache.cache)
    app.command()(serve.serve)
    app.command()(status.status)


_register_commands()
