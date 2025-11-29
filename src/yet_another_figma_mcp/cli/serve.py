"""serve コマンド実装"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Annotated

import typer

from yet_another_figma_mcp.cli.app import DEFAULT_CACHE_DIR


def serve(
    cache_dir: Annotated[
        Path | None,
        typer.Option("--cache-dir", "-d", help="キャッシュディレクトリ"),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-V", help="詳細ログを出力（DEBUG レベル）"),
    ] = False,
) -> None:
    """MCP サーバーを起動 (stdio モード)"""
    from yet_another_figma_mcp.server import run_server, set_cache_dir

    # キャッシュディレクトリの設定
    target_cache_dir = cache_dir or DEFAULT_CACHE_DIR
    set_cache_dir(target_cache_dir)

    # stderr にログ出力を設定 (MCP は stdout を使用するため)
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )
    logger = logging.getLogger("yet-another-figma-mcp")

    logger.info("MCP サーバーを起動中...")
    logger.info("キャッシュディレクトリ: %s", target_cache_dir)

    # SIGTERM ハンドラを設定 (SIGINT は KeyboardInterrupt で処理)
    def sigterm_handler(signum: int, frame: object) -> None:
        """SIGTERM シグナルを受信したときの処理"""
        logger.info("SIGTERM を受信しました")
        sys.exit(0)

    signal.signal(signal.SIGTERM, sigterm_handler)

    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("サーバーを終了しました")
