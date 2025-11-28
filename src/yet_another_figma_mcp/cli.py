"""CLI エントリーポイント"""

import click

from yet_another_figma_mcp import __version__


@click.group()
@click.version_option(version=__version__, prog_name="yet-another-figma-mcp")
def main() -> None:
    """YetAnotherFigmaMCP - Figma ファイルキャッシュ MCP サーバー"""
    pass


@main.command()
@click.option(
    "--file-id",
    multiple=True,
    help="Figma ファイル ID（複数指定可）",
)
@click.option(
    "--file-id-list",
    type=click.Path(exists=True),
    help="ファイル ID 一覧を記述したテキストファイル",
)
@click.option(
    "--refresh",
    is_flag=True,
    default=False,
    help="キャッシュを強制的に更新",
)
def cache(file_id: tuple[str, ...], file_id_list: str | None, refresh: bool) -> None:
    """Figma ファイルのキャッシュを生成"""
    click.echo("Cache command - not yet implemented")
    if file_id:
        click.echo(f"File IDs: {file_id}")
    if file_id_list:
        click.echo(f"File ID list: {file_id_list}")
    if refresh:
        click.echo("Refresh mode enabled")


@main.command()
def serve() -> None:
    """MCP サーバーを起動"""
    click.echo("Serve command - not yet implemented")


@main.command()
def status() -> None:
    """サーバーの動作状況を確認"""
    click.echo("Status command - not yet implemented")


if __name__ == "__main__":
    main()
