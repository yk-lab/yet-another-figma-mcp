"""MCP サーバーの統合テスト"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from mcp.types import CallToolRequest, CallToolRequestParams, ListToolsRequest

from yet_another_figma_mcp.cache.index import build_index, save_index
from yet_another_figma_mcp.server import create_server, get_store, set_cache_dir
from yet_another_figma_mcp.tools import (
    get_cached_figma_file,
    get_cached_figma_node,
    list_figma_frames,
    search_figma_frames_by_title,
    search_figma_nodes_by_name,
)


@pytest.fixture
def server_with_cache(tmp_path: Path, sample_design_system: dict[str, Any]) -> tuple[Any, str]:
    """キャッシュ付きの MCP サーバーをセットアップ"""
    file_id = "test_design_system"
    file_dir = tmp_path / file_id
    file_dir.mkdir(parents=True)

    # ファイル保存
    with open(file_dir / "file_raw.json", "w", encoding="utf-8") as f:
        json.dump(sample_design_system, f, ensure_ascii=False)

    # インデックス生成・保存
    index = build_index(sample_design_system)
    save_index(index, tmp_path, file_id)

    # サーバーのキャッシュディレクトリを設定
    set_cache_dir(tmp_path)

    server = create_server()
    return server, file_id


class TestMCPServerSetup:
    """MCP サーバーのセットアップテスト"""

    def test_server_has_name(self, server_with_cache: tuple[Any, str]) -> None:
        """サーバーに名前が設定されている"""
        server, _ = server_with_cache
        assert server.name == "yet-another-figma-mcp"

    def test_server_is_created(self, server_with_cache: tuple[Any, str]) -> None:
        """サーバーが正常に作成される"""
        server, _ = server_with_cache
        assert server is not None


class TestMCPServerListTools:
    """MCP サーバーの list_tools テスト"""

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_five_tools(
        self, server_with_cache: tuple[Any, str]
    ) -> None:
        """list_tools は 5 つのツールのみを返す"""
        server, _ = server_with_cache

        # request_handlers から ListToolsRequest ハンドラーを取得
        list_tools_handler = server.request_handlers[ListToolsRequest]
        server_result = await list_tools_handler(ListToolsRequest(method="tools/list"))
        tools_result = server_result.root

        tool_names = {tool.name for tool in tools_result.tools}
        expected_tools = {
            "get_cached_figma_file",
            "get_cached_figma_node",
            "search_figma_nodes_by_name",
            "search_figma_frames_by_title",
            "list_figma_frames",
        }

        assert tool_names == expected_tools
        assert len(tools_result.tools) == 5

    @pytest.mark.asyncio
    async def test_list_tools_have_required_schema(
        self, server_with_cache: tuple[Any, str]
    ) -> None:
        """各ツールに必須パラメータスキーマがある"""
        server, _ = server_with_cache

        list_tools_handler = server.request_handlers[ListToolsRequest]
        server_result = await list_tools_handler(ListToolsRequest(method="tools/list"))
        tools_result = server_result.root

        for tool in tools_result.tools:
            assert tool.inputSchema is not None
            assert "properties" in tool.inputSchema
            assert "required" in tool.inputSchema
            # 全ツールで file_id は必須
            assert "file_id" in tool.inputSchema["required"]


class TestMCPServerCallTool:
    """MCP サーバーの call_tool テスト"""

    @pytest.mark.asyncio
    async def test_call_tool_get_cached_figma_file(
        self, server_with_cache: tuple[Any, str]
    ) -> None:
        """call_tool 経由で get_cached_figma_file を呼び出し"""
        server, file_id = server_with_cache

        call_tool_handler = server.request_handlers[CallToolRequest]
        server_result = await call_tool_handler(
            CallToolRequest(
                method="tools/call",
                params=CallToolRequestParams(
                    name="get_cached_figma_file", arguments={"file_id": file_id}
                ),
            )
        )
        result = server_result.root

        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
        assert "error" not in data
        assert data["name"] == "Design System"

    @pytest.mark.asyncio
    async def test_call_tool_get_cached_figma_node(
        self, server_with_cache: tuple[Any, str]
    ) -> None:
        """call_tool 経由で get_cached_figma_node を呼び出し"""
        server, file_id = server_with_cache

        call_tool_handler = server.request_handlers[CallToolRequest]
        server_result = await call_tool_handler(
            CallToolRequest(
                method="tools/call",
                params=CallToolRequestParams(
                    name="get_cached_figma_node",
                    arguments={"file_id": file_id, "node_id": "1:2"},
                ),
            )
        )
        result = server_result.root

        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
        assert "error" not in data
        assert data["name"] == "Primary Button"
        assert data["type"] == "COMPONENT"

    @pytest.mark.asyncio
    async def test_call_tool_search_figma_nodes_by_name(
        self, server_with_cache: tuple[Any, str]
    ) -> None:
        """call_tool 経由で search_figma_nodes_by_name を呼び出し"""
        server, file_id = server_with_cache

        call_tool_handler = server.request_handlers[CallToolRequest]
        server_result = await call_tool_handler(
            CallToolRequest(
                method="tools/call",
                params=CallToolRequestParams(
                    name="search_figma_nodes_by_name",
                    arguments={"file_id": file_id, "name": "Button", "match_mode": "partial"},
                ),
            )
        )
        result = server_result.root

        assert len(result.content) == 1
        data: list[dict[str, Any]] = json.loads(result.content[0].text)
        assert isinstance(data, list)
        assert len(data) >= 3

    @pytest.mark.asyncio
    async def test_call_tool_search_figma_frames_by_title(
        self, server_with_cache: tuple[Any, str]
    ) -> None:
        """call_tool 経由で search_figma_frames_by_title を呼び出し"""
        server, file_id = server_with_cache

        call_tool_handler = server.request_handlers[CallToolRequest]
        server_result = await call_tool_handler(
            CallToolRequest(
                method="tools/call",
                params=CallToolRequestParams(
                    name="search_figma_frames_by_title",
                    arguments={"file_id": file_id, "title": "Login", "match_mode": "partial"},
                ),
            )
        )
        result = server_result.root

        assert len(result.content) == 1
        data: list[dict[str, Any]] = json.loads(result.content[0].text)
        assert isinstance(data, list)
        frame_names = [f["name"] for f in data]
        assert "Login Screen" in frame_names

    @pytest.mark.asyncio
    async def test_call_tool_list_figma_frames(self, server_with_cache: tuple[Any, str]) -> None:
        """call_tool 経由で list_figma_frames を呼び出し"""
        server, file_id = server_with_cache

        call_tool_handler = server.request_handlers[CallToolRequest]
        server_result = await call_tool_handler(
            CallToolRequest(
                method="tools/call",
                params=CallToolRequestParams(
                    name="list_figma_frames", arguments={"file_id": file_id}
                ),
            )
        )
        result = server_result.root

        assert len(result.content) == 1
        data: list[dict[str, Any]] = json.loads(result.content[0].text)
        assert isinstance(data, list)
        frame_names = [f["name"] for f in data]
        assert "Buttons" in frame_names
        assert "Login Screen" in frame_names

    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool_returns_error(
        self, server_with_cache: tuple[Any, str]
    ) -> None:
        """存在しないツールを呼び出すとエラー"""
        server, file_id = server_with_cache

        call_tool_handler = server.request_handlers[CallToolRequest]
        server_result = await call_tool_handler(
            CallToolRequest(
                method="tools/call",
                params=CallToolRequestParams(name="unknown_tool", arguments={"file_id": file_id}),
            )
        )
        result = server_result.root

        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
        assert data["error"] == "unknown_tool"
        assert "Unknown tool: unknown_tool" in data["message"]


class TestMCPServerToolCallsDirect:
    """MCP サーバーのツール呼び出しテスト (直接呼び出し)"""

    def test_get_cached_figma_file_direct(self, server_with_cache: tuple[Any, str]) -> None:
        """get_cached_figma_file の直接呼び出し"""
        _, file_id = server_with_cache

        store = get_store()
        result = get_cached_figma_file(store, file_id)

        assert "error" not in result
        assert result["name"] == "Design System"

    def test_get_cached_figma_node_direct(self, server_with_cache: tuple[Any, str]) -> None:
        """get_cached_figma_node の直接呼び出し"""
        _, file_id = server_with_cache

        store = get_store()
        result = get_cached_figma_node(store, file_id, "1:2")

        assert "error" not in result
        assert result["name"] == "Primary Button"
        assert result["type"] == "COMPONENT"

    def test_search_figma_nodes_by_name_direct(self, server_with_cache: tuple[Any, str]) -> None:
        """search_figma_nodes_by_name の直接呼び出し"""
        _, file_id = server_with_cache

        store = get_store()
        results = search_figma_nodes_by_name(store, file_id, name="Button", match_mode="partial")

        assert len(results) >= 3

    def test_search_figma_nodes_with_ignore_case_direct(
        self, server_with_cache: tuple[Any, str]
    ) -> None:
        """ignore_case オプション付きの検索"""
        _, file_id = server_with_cache

        store = get_store()
        results = search_figma_nodes_by_name(
            store, file_id, name="button", match_mode="partial", ignore_case=True
        )

        assert len(results) >= 3

    def test_search_figma_frames_by_title_direct(self, server_with_cache: tuple[Any, str]) -> None:
        """search_figma_frames_by_title の直接呼び出し"""
        _, file_id = server_with_cache

        store = get_store()
        results = search_figma_frames_by_title(store, file_id, title="Login", match_mode="partial")

        frame_names = [f["name"] for f in results]
        assert "Login Screen" in frame_names

    def test_list_figma_frames_direct(self, server_with_cache: tuple[Any, str]) -> None:
        """list_figma_frames の直接呼び出し"""
        _, file_id = server_with_cache

        store = get_store()
        results = list_figma_frames(store, file_id)

        frame_names = [f["name"] for f in results]
        assert "Buttons" in frame_names
        assert "Login Screen" in frame_names


class TestMCPServerErrorHandlingDirect:
    """MCP サーバーのエラーハンドリングテスト (直接呼び出し)"""

    def test_nonexistent_file_returns_error(self, server_with_cache: tuple[Any, str]) -> None:
        """存在しないファイルへのアクセスはエラー"""
        _ = server_with_cache  # fixture でキャッシュディレクトリを設定

        store = get_store()
        result = get_cached_figma_file(store, "nonexistent")

        assert result["error"] == "file_not_found"

    def test_nonexistent_node_returns_error(self, server_with_cache: tuple[Any, str]) -> None:
        """存在しないノードへのアクセスはエラー"""
        _, file_id = server_with_cache

        store = get_store()
        result = get_cached_figma_node(store, file_id, "999:999")

        assert result["error"] == "node_not_found"

    def test_invalid_file_id_returns_error(self, server_with_cache: tuple[Any, str]) -> None:
        """無効なファイル ID はエラー"""
        _ = server_with_cache  # fixture でキャッシュディレクトリを設定

        store = get_store()
        result = get_cached_figma_file(store, "../invalid")

        assert result["error"] == "invalid_file_id"


class TestMCPServerCallToolErrorHandling:
    """MCP サーバーの call_tool エラーハンドリングテスト

    注意: MCP SDK はツールのスキーマバリデーションを行うため、
    必須引数が不足している場合は call_tool ハンドラに到達する前にエラーが返される。
    SDK のバリデーションをバイパスするテストはアーキテクチャ的に不適切なため、
    ここでは SDK の動作を文書化するテストのみを行う。
    """

    @pytest.mark.asyncio
    async def test_call_tool_missing_required_argument_returns_error(
        self, server_with_cache: tuple[Any, str]
    ) -> None:
        """必須引数が不足している場合は MCP SDK がエラーを返す"""
        server, _ = server_with_cache

        call_tool_handler = server.request_handlers[CallToolRequest]
        server_result = await call_tool_handler(
            CallToolRequest(
                method="tools/call",
                params=CallToolRequestParams(
                    name="get_cached_figma_file",
                    arguments={},  # file_id が不足
                ),
            )
        )
        result = server_result.root

        # MCP SDK がエラーレスポンスを返す (isError フラグで判定)
        assert len(result.content) == 1
        assert result.isError is True

    @pytest.mark.asyncio
    async def test_call_tool_missing_node_id_returns_error(
        self, server_with_cache: tuple[Any, str]
    ) -> None:
        """get_cached_figma_node で node_id が不足している場合"""
        server, file_id = server_with_cache

        call_tool_handler = server.request_handlers[CallToolRequest]
        server_result = await call_tool_handler(
            CallToolRequest(
                method="tools/call",
                params=CallToolRequestParams(
                    name="get_cached_figma_node",
                    arguments={"file_id": file_id},  # node_id が不足
                ),
            )
        )
        result = server_result.root

        # MCP SDK がエラーレスポンスを返す (isError フラグで判定)
        assert len(result.content) == 1
        assert result.isError is True

    @pytest.mark.asyncio
    async def test_call_tool_unexpected_exception_returns_internal_error(
        self, server_with_cache: tuple[Any, str]
    ) -> None:
        """予期しない例外が発生した場合は internal_error を返す"""
        server, file_id = server_with_cache

        call_tool_handler = server.request_handlers[CallToolRequest]

        # get_cached_figma_file 内で例外を発生させる
        with patch(
            "yet_another_figma_mcp.server.get_cached_figma_file",
            side_effect=RuntimeError("Unexpected error"),
        ):
            server_result = await call_tool_handler(
                CallToolRequest(
                    method="tools/call",
                    params=CallToolRequestParams(
                        name="get_cached_figma_file",
                        arguments={"file_id": file_id},
                    ),
                )
            )
            result = server_result.root

        assert len(result.content) == 1
        data = json.loads(result.content[0].text)
        assert data["error"] == "internal_error"
        assert "RuntimeError" in data["message"]
        assert data["tool"] == "get_cached_figma_file"


class TestCacheStoreSingleton:
    """キャッシュストアのシングルトン動作テスト"""

    def test_get_store_returns_same_instance(self, tmp_path: Path) -> None:
        """get_store は同じインスタンスを返す"""
        set_cache_dir(tmp_path)

        store1 = get_store()
        store2 = get_store()

        assert store1 is store2

    def test_set_cache_dir_resets_store(self, tmp_path: Path) -> None:
        """set_cache_dir でストアがリセットされる"""
        set_cache_dir(tmp_path)
        store1 = get_store()

        # 別のディレクトリを設定
        new_dir = tmp_path / "new_cache"
        new_dir.mkdir()
        set_cache_dir(new_dir)
        store2 = get_store()

        assert store1 is not store2
