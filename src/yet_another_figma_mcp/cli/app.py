"""CLI アプリケーション定義"""

from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint

from yet_another_figma_mcp import __version__

# サブコマンドモジュールをインポート (循環参照を避けるため関数内でインポート)

DEFAULT_CACHE_DIR = Path.home() / ".yet_another_figma_mcp"

app = typer.Typer(
    name="yet-another-figma-mcp",
    help="YetAnotherFigmaMCP - Figma ファイルキャッシュ MCP サーバー",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    """バージョン情報を表示"""
    if value:
        rprint(f"yet-another-figma-mcp {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="バージョン情報を表示",
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
