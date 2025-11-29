"""cache コマンド実装"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from yet_another_figma_mcp.cache import InvalidFileIdError, validate_file_id
from yet_another_figma_mcp.cache.index import build_index, save_index
from yet_another_figma_mcp.cli.app import DEFAULT_CACHE_DIR
from yet_another_figma_mcp.figma import (
    FigmaAPIError,
    FigmaAuthenticationError,
    FigmaClient,
    FigmaFileNotFoundError,
    FigmaRateLimitError,
)

console = Console()


def _save_file_raw(file_data: dict[str, object], file_id: str, cache_dir: Path) -> Path:
    """ファイル JSON をディスクに保存"""
    validate_file_id(file_id)
    file_dir = cache_dir / file_id
    file_dir.mkdir(parents=True, exist_ok=True)
    file_path = file_dir / "file_raw.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(file_data, f, ensure_ascii=False, indent=2)
    return file_path


def _save_cache_metadata(file_id: str, cache_dir: Path) -> None:
    """キャッシュのメタデータ (タイムスタンプ等) を保存"""
    validate_file_id(file_id)
    file_dir = cache_dir / file_id
    file_dir.mkdir(parents=True, exist_ok=True)
    meta_path = file_dir / "cache_meta.json"

    now = datetime.now(timezone.utc)
    metadata: dict[str, object] = {
        "cached_at": now.isoformat(),
        "cached_at_unix": now.timestamp(),
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def _cache_single_file(
    client: FigmaClient,
    file_id: str,
    cache_dir: Path,
    refresh: bool,
) -> bool:
    """単一ファイルをキャッシュする

    Returns:
        True: 成功、False: 失敗
    """
    # file_id のバリデーション
    try:
        validate_file_id(file_id)
    except InvalidFileIdError as e:
        console.print(f"[red]✗[/red] {file_id}: 無効なファイル ID - {e}")
        return False

    # 既存キャッシュのチェック
    file_path = cache_dir / file_id / "file_raw.json"
    if file_path.exists() and not refresh:
        console.print(f"[yellow]⊘[/yellow] {file_id}: キャッシュ済み（--refresh で更新）")
        return True

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        # Figma API からファイル取得
        task = progress.add_task(f"{file_id}: Figma API から取得中...", total=None)
        try:
            file_data = client.get_file(file_id)
        except FigmaAuthenticationError:
            progress.remove_task(task)
            console.print(f"[red]✗[/red] {file_id}: 認証エラー - API トークンを確認してください")
            return False
        except FigmaFileNotFoundError:
            progress.remove_task(task)
            console.print(f"[red]✗[/red] {file_id}: ファイルが見つかりません")
            return False
        except FigmaRateLimitError as e:
            progress.remove_task(task)
            retry_msg = f"（{e.retry_after}秒後に再試行）" if e.retry_after else ""
            console.print(f"[red]✗[/red] {file_id}: レート制限{retry_msg}")
            return False
        except FigmaAPIError as e:
            progress.remove_task(task)
            console.print(f"[red]✗[/red] {file_id}: API エラー - {e}")
            return False

        # ファイル保存
        progress.update(task, description=f"{file_id}: ファイルを保存中...")
        _save_file_raw(file_data, file_id, cache_dir)

        # インデックス生成
        progress.update(task, description=f"{file_id}: インデックスを生成中...")
        index = build_index(file_data)
        save_index(index, cache_dir, file_id)

        # キャッシュメタデータ保存 (タイムスタンプ記録)
        _save_cache_metadata(file_id, cache_dir)

    file_name = file_data.get("name", "Unknown")
    console.print(f"[green]✓[/green] {file_id}: {file_name}")
    return True


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
    cache_dir: Annotated[
        Path | None,
        typer.Option("--cache-dir", "-d", help="キャッシュディレクトリ"),
    ] = None,
) -> None:
    """Figma ファイルのキャッシュを生成"""
    # ファイル ID の収集
    file_ids: list[str] = []

    if file_id:
        file_ids.extend(file_id)

    if file_id_list:
        try:
            with open(file_id_list, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # 空行とコメント行をスキップ
                    if line and not line.startswith("#"):
                        file_ids.append(line)
        except UnicodeDecodeError:
            console.print(
                "[red]エラー: ファイルリストの読み込みに失敗しました"
                "（UTF-8 でエンコードしてください）[/red]"
            )
            raise typer.Exit(1)

    if not file_ids:
        console.print("[red]エラー: ファイル ID を指定してください[/red]")
        console.print("使用例: yet-another-figma-mcp cache -f <file_id>")
        raise typer.Exit(1)

    # 重複除去
    file_ids = list(dict.fromkeys(file_ids))

    # キャッシュディレクトリ
    target_cache_dir = cache_dir or DEFAULT_CACHE_DIR

    console.print(f"[bold]キャッシュ先:[/bold] {target_cache_dir}")
    console.print(f"[bold]対象ファイル数:[/bold] {len(file_ids)}")
    console.print()

    # FigmaClient でファイル取得
    success_count = 0
    fail_count = 0
    total_count = len(file_ids)

    with FigmaClient() as client:
        for idx, fid in enumerate(file_ids, start=1):
            # 進捗表示
            console.print(f"[dim]({idx}/{total_count})[/dim] ", end="")
            if _cache_single_file(client, fid, target_cache_dir, refresh):
                success_count += 1
            else:
                fail_count += 1

    # 結果サマリー
    console.print()
    if fail_count == 0:
        console.print(f"[green]完了: {success_count} ファイルをキャッシュしました[/green]")
    else:
        console.print(f"[yellow]完了: {success_count} 成功, {fail_count} 失敗[/yellow]")
        raise typer.Exit(1)
