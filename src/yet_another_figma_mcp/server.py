"""MCP サーバー実装"""

import json
from logging import getLogger
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from yet_another_figma_mcp.cache import CacheStore
from yet_another_figma_mcp.tools import (
    get_cached_figma_file,
    get_cached_figma_node,
    list_figma_frames,
    search_figma_frames_by_title,
    search_figma_nodes_by_name,
)

logger = getLogger(__name__)

# グローバルなキャッシュストアとキャッシュディレクトリ
_store: CacheStore | None = None
_cache_dir: Path | None = None


def set_cache_dir(cache_dir: Path) -> None:
    """キャッシュディレクトリを設定"""
    global _cache_dir, _store
    _cache_dir = cache_dir
    # キャッシュディレクトリが変更されたらストアをリセット
    _store = None


def get_store() -> CacheStore:
    """キャッシュストアを取得（シングルトン）"""
    global _store
    if _store is None:
        _store = CacheStore(_cache_dir)
    return _store


def create_server() -> Server:
    """MCP サーバーを作成"""
    server = Server("yet-another-figma-mcp")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """利用可能な MCP ツール一覧を返す"""
        return [
            Tool(
                name="get_cached_figma_file",
                description="指定ファイルのノードツリーやメタデータを取得",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_id": {
                            "type": "string",
                            "description": "Figma ファイル ID",
                        },
                    },
                    "required": ["file_id"],
                },
            ),
            Tool(
                name="get_cached_figma_node",
                description="単一ノードの詳細情報を取得",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_id": {
                            "type": "string",
                            "description": "Figma ファイル ID",
                        },
                        "node_id": {
                            "type": "string",
                            "description": "ノード ID",
                        },
                    },
                    "required": ["file_id", "node_id"],
                },
            ),
            Tool(
                name="search_figma_nodes_by_name",
                description="ノード名でノードを検索",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_id": {
                            "type": "string",
                            "description": "Figma ファイル ID",
                        },
                        "name": {
                            "type": "string",
                            "description": "検索するノード名",
                        },
                        "match_mode": {
                            "type": "string",
                            "enum": ["exact", "partial"],
                            "default": "exact",
                            "description": "マッチモード",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "最大取得件数",
                        },
                        "ignore_case": {
                            "type": "boolean",
                            "default": False,
                            "description": "大文字小文字を区別しない検索",
                        },
                    },
                    "required": ["file_id", "name"],
                },
            ),
            Tool(
                name="search_figma_frames_by_title",
                description="フレーム名からフレームノードを検索",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_id": {
                            "type": "string",
                            "description": "Figma ファイル ID",
                        },
                        "title": {
                            "type": "string",
                            "description": "検索するフレーム名",
                        },
                        "match_mode": {
                            "type": "string",
                            "enum": ["exact", "partial"],
                            "default": "exact",
                            "description": "マッチモード",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "最大取得件数",
                        },
                        "ignore_case": {
                            "type": "boolean",
                            "default": False,
                            "description": "大文字小文字を区別しない検索",
                        },
                    },
                    "required": ["file_id", "title"],
                },
            ),
            Tool(
                name="list_figma_frames",
                description="ファイル直下の主要フレーム一覧を取得",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_id": {
                            "type": "string",
                            "description": "Figma ファイル ID",
                        },
                    },
                    "required": ["file_id"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """MCP ツールを呼び出す

        Note: MCP SDK がスキーマバリデーションを行うため、必須引数の不足は
        このハンドラに到達する前に SDK によって処理される。
        """
        try:
            store = get_store()
            result: dict[str, Any] | list[dict[str, Any]]

            if name == "get_cached_figma_file":
                result = get_cached_figma_file(store, arguments["file_id"])
            elif name == "get_cached_figma_node":
                result = get_cached_figma_node(store, arguments["file_id"], arguments["node_id"])
            elif name == "search_figma_nodes_by_name":
                result = search_figma_nodes_by_name(
                    store,
                    arguments["file_id"],
                    arguments["name"],
                    arguments.get("match_mode", "exact"),
                    arguments.get("limit"),
                    arguments.get("ignore_case", False),
                )
            elif name == "search_figma_frames_by_title":
                result = search_figma_frames_by_title(
                    store,
                    arguments["file_id"],
                    arguments["title"],
                    arguments.get("match_mode", "exact"),
                    arguments.get("limit"),
                    arguments.get("ignore_case", False),
                )
            elif name == "list_figma_frames":
                result = list_figma_frames(store, arguments["file_id"])
            else:
                result = {"error": "unknown_tool", "message": f"不明なツールです（{name}）"}

            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        except Exception as e:
            # 予期しないエラーをキャッチしてサーバークラッシュを防止
            logger.exception("Unexpected error in tool %s", name)
            result = {
                "error": "internal_error",
                "message": f"ツール実行中に予期しないエラーが発生しました（{type(e).__name__}）",
                "tool": name,
            }
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    return server


async def run_server() -> None:
    """MCP サーバーを起動"""
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())
