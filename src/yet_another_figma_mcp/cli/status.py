"""status コマンド実装"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from yet_another_figma_mcp.cache import InvalidFileIdError, validate_file_id
from yet_another_figma_mcp.cli.app import DEFAULT_CACHE_DIR
from yet_another_figma_mcp.cli.i18n import t

console = Console()


def _get_cached_files_info(cache_dir: Path) -> list[dict[str, object]]:
    """キャッシュディレクトリ内のファイル情報を取得

    Returns:
        ファイル情報のリスト
    """
    files_info: list[dict[str, object]] = []

    if not cache_dir.exists():
        return files_info

    for file_dir in cache_dir.iterdir():
        if not file_dir.is_dir():
            continue

        file_id = file_dir.name

        # file_id のバリデーション (不正なディレクトリ名をスキップ)
        try:
            validate_file_id(file_id)
        except InvalidFileIdError:
            continue

        file_raw_path = file_dir / "file_raw.json"
        index_path = file_dir / "nodes_index.json"
        meta_path = file_dir / "cache_meta.json"

        if not file_raw_path.exists():
            continue

        # ファイル情報を読み込み
        try:
            with open(file_raw_path, encoding="utf-8") as f:
                file_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        file_name = file_data.get("name", "Unknown")

        # ノード数をインデックスから取得
        node_count = 0
        if index_path.exists():
            try:
                with open(index_path, encoding="utf-8") as f:
                    index_data = json.load(f)
                    node_count = len(index_data.get("by_id", {}))
            except (json.JSONDecodeError, OSError):
                pass

        # キャッシュ日時をメタデータから取得
        cached_at: str | None = None
        if meta_path.exists():
            try:
                with open(meta_path, encoding="utf-8") as f:
                    meta_data = json.load(f)
                    cached_at = meta_data.get("cached_at")
            except (json.JSONDecodeError, OSError):
                pass

        # フォールバック: file_raw.json の mtime を使用
        if not cached_at:
            mtime = file_raw_path.stat().st_mtime
            cached_at = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()

        files_info.append(
            {
                "file_id": file_id,
                "name": file_name,
                "cached_at": cached_at,
                "node_count": node_count,
            }
        )

    # キャッシュ日時で降順ソート (新しい順)
    files_info.sort(key=lambda x: str(x.get("cached_at", "")), reverse=True)

    return files_info


def _format_datetime(iso_string: str) -> str:
    """ISO 形式の日時文字列を読みやすい形式に変換"""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        # ローカルタイムゾーンに変換
        local_dt = dt.astimezone()
        return local_dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return iso_string


def status(
    cache_dir: Annotated[
        Path | None,
        typer.Option("--cache-dir", "-d", help=t("cache.cache_dir_help")),
    ] = None,
    output_json: Annotated[
        bool,
        typer.Option("--json", "-j", help=t("status.json_help")),
    ] = False,
) -> None:
    """キャッシュ済みファイルの一覧と状態を表示"""
    target_cache_dir = cache_dir or DEFAULT_CACHE_DIR

    files_info = _get_cached_files_info(target_cache_dir)

    if output_json:
        # JSON 出力
        rprint(json.dumps(files_info, ensure_ascii=False, indent=2))
        return

    # テーブル出力
    if not files_info:
        console.print(f"[yellow]{t('status.no_cache_found', path=target_cache_dir)}[/yellow]")
        return

    table = Table(title=t("status.table_title", path=target_cache_dir))
    table.add_column("File ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Cached At", style="yellow")
    table.add_column("Nodes", justify="right", style="magenta")

    for info in files_info:
        cached_at_str = _format_datetime(str(info.get("cached_at", "")))
        table.add_row(
            str(info.get("file_id", "")),
            str(info.get("name", "")),
            cached_at_str,
            str(info.get("node_count", 0)),
        )

    console.print(table)
    console.print(f"\n[dim]{t('status.total_files', count=len(files_info))}[/dim]")
