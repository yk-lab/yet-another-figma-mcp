"""CLI エントリーポイント"""

from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint

from yet_another_figma_mcp import __version__

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


@app.command()
def cache(
    file_id: Annotated[
        list[str] | None,
        typer.Option("--file-id", "-f", help="Figma ファイル ID（複数指定可）"),
    ] = None,
    file_id_list: Annotated[
        Path | None,
        typer.Option(
            "--file-id-list",
            "-l",
            exists=True,
            help="ファイル ID 一覧を記述したテキストファイル",
        ),
    ] = None,
    refresh: Annotated[
        bool,
        typer.Option("--refresh", "-r", help="キャッシュを強制的に更新"),
    ] = False,
) -> None:
    """Figma ファイルのキャッシュを生成"""
    rprint("[yellow]Cache command - not yet implemented[/yellow]")
    if file_id:
        rprint(f"File IDs: {file_id}")
    if file_id_list:
        rprint(f"File ID list: {file_id_list}")
    if refresh:
        rprint("[blue]Refresh mode enabled[/blue]")


@app.command()
def serve() -> None:
    """MCP サーバーを起動"""
    rprint("[yellow]Serve command - not yet implemented[/yellow]")


@app.command()
def status() -> None:
    """サーバーの動作状況を確認"""
    rprint("[yellow]Status command - not yet implemented[/yellow]")


if __name__ == "__main__":
    app()
