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
        """Return a list of available MCP tools"""
        return [
            Tool(
                name="get_cached_figma_file",
                description=(
                    "Get cached Figma file metadata and top-level frames. "
                    "Returns file name, version, last modified date, and a list of main frames. "
                    "Use this tool first to understand the structure of a Figma file."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_id": {
                            "type": "string",
                            "description": (
                                "The Figma file ID. "
                                "Found in URLs like figma.com/file/<file_id>/... "
                                "or figma.com/design/<file_id>/..."
                            ),
                        },
                    },
                    "required": ["file_id"],
                },
            ),
            Tool(
                name="get_cached_figma_node",
                description=(
                    "Get detailed information for a specific node including all properties "
                    "(type, name, layout, style, children, etc.). "
                    "Use this after finding a node ID via search or list_figma_frames. "
                    "Use 'depth' to limit children depth, 'simplified' for AI-optimized output."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_id": {
                            "type": "string",
                            "description": (
                                "The Figma file ID. "
                                "Found in URLs like figma.com/file/<file_id>/... "
                                "or figma.com/design/<file_id>/..."
                            ),
                        },
                        "node_id": {
                            "type": "string",
                            "description": (
                                "The node ID in format '1:234', '1234:5678', or '1-234' (URL format). "
                                "Found in Figma URL as ?node-id=1-234 or from search results."
                            ),
                        },
                        "depth": {
                            "type": "integer",
                            "description": (
                                "Maximum depth of children to include. "
                                "0 = no children, 1 = immediate children only, etc. "
                                "Omit for unlimited depth. Use this to reduce response size."
                            ),
                        },
                        "simplified": {
                            "type": "boolean",
                            "description": (
                                "If true, return AI-optimized format with CSS-like properties "
                                "(e.g., 'flex-row gap-8 p-16' for layout). "
                                "Significantly reduces response size. Recommended for large nodes."
                            ),
                            "default": False,
                        },
                    },
                    "required": ["file_id", "node_id"],
                },
            ),
            Tool(
                name="search_figma_nodes_by_name",
                description=(
                    "Search nodes by name. Supports exact and partial matching. "
                    "Returns matching nodes with their IDs, types, and paths. "
                    "Useful for finding specific components, buttons, icons, etc."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_id": {
                            "type": "string",
                            "description": (
                                "The Figma file ID. "
                                "Found in URLs like figma.com/file/<file_id>/... "
                                "or figma.com/design/<file_id>/..."
                            ),
                        },
                        "name": {
                            "type": "string",
                            "description": "The node name to search for (e.g., 'Button', 'Header', 'Icon')",
                        },
                        "match_mode": {
                            "type": "string",
                            "enum": ["exact", "partial"],
                            "default": "exact",
                            "description": (
                                "Match mode: 'exact' for exact name match, "
                                "'partial' for substring match (always case-insensitive)"
                            ),
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                        },
                        "ignore_case": {
                            "type": "boolean",
                            "default": False,
                            "description": "If true, perform case-insensitive matching (only for exact mode)",
                        },
                    },
                    "required": ["file_id", "name"],
                },
            ),
            Tool(
                name="search_figma_frames_by_title",
                description=(
                    "Search frame nodes by title. Useful for finding specific screens, "
                    "pages, or components. Returns matching frames with their IDs and paths."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_id": {
                            "type": "string",
                            "description": (
                                "The Figma file ID. "
                                "Found in URLs like figma.com/file/<file_id>/... "
                                "or figma.com/design/<file_id>/..."
                            ),
                        },
                        "title": {
                            "type": "string",
                            "description": (
                                "The frame title to search for "
                                "(e.g., 'Login Screen', 'Dashboard', 'Settings')"
                            ),
                        },
                        "match_mode": {
                            "type": "string",
                            "enum": ["exact", "partial"],
                            "default": "exact",
                            "description": (
                                "Match mode: 'exact' for exact title match, "
                                "'partial' for substring match (always case-insensitive)"
                            ),
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                        },
                        "ignore_case": {
                            "type": "boolean",
                            "default": False,
                            "description": "If true, perform case-insensitive matching (only for exact mode)",
                        },
                    },
                    "required": ["file_id", "title"],
                },
            ),
            Tool(
                name="list_figma_frames",
                description=(
                    "List all top-level frames in the file (direct children of pages). "
                    "Useful for getting an overview of the design structure. "
                    "Returns frame names, IDs, and their paths in the document hierarchy."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_id": {
                            "type": "string",
                            "description": (
                                "The Figma file ID. "
                                "Found in URLs like figma.com/file/<file_id>/... "
                                "or figma.com/design/<file_id>/..."
                            ),
                        },
                    },
                    "required": ["file_id"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Call an MCP tool

        Note: The MCP SDK performs schema validation, so missing required arguments
        are handled by the SDK before reaching this handler.
        """
        try:
            store = get_store()
            result: dict[str, Any] | list[dict[str, Any]]

            if name == "get_cached_figma_file":
                result = get_cached_figma_file(store, arguments["file_id"])
            elif name == "get_cached_figma_node":
                result = get_cached_figma_node(
                    store,
                    arguments["file_id"],
                    arguments["node_id"],
                    depth=arguments.get("depth"),
                    simplified=arguments.get("simplified", False),
                )
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
                result = {"error": "unknown_tool", "message": f"Unknown tool: {name}"}

            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        except Exception as e:
            # Catch unexpected errors to prevent server crash
            logger.exception("Unexpected error in tool %s", name)
            result = {
                "error": "internal_error",
                "message": f"Unexpected error while executing tool ({type(e).__name__})",
                "tool": name,
            }
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    return server


async def run_server() -> None:
    """MCP サーバーを起動"""
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())
