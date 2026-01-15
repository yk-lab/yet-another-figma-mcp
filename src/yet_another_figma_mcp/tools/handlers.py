"""MCP ツールハンドラ実装"""

from typing import Any, Literal

from yet_another_figma_mcp.cache import (
    CacheStore,
    InvalidFileIdError,
    normalize_node_id,
    validate_file_id,
)
from yet_another_figma_mcp.tools.simplify import simplify_node, truncate_children


def _handle_invalid_file_id(file_id: str) -> dict[str, Any]:
    """Generate error response for invalid file_id"""
    return {
        "error": "invalid_file_id",
        "message": (
            f"Invalid file ID: '{file_id}'. "
            "File ID should contain only letters, numbers, underscores, and hyphens."
        ),
        "file_id": file_id,
    }


def _search_by_index(
    index_dict: dict[str, list[str]],
    by_id: dict[str, dict[str, Any]],
    search_key: str,
    match_mode: Literal["exact", "partial"],
    ignore_case: bool,
) -> list[dict[str, Any]]:
    """Search index and return results / インデックスから検索して結果を返す共通ヘルパー

    Args:
        index_dict: Index to search (by_name or by_frame_title) / 検索対象のインデックス
        by_id: Node ID -> node info mapping / ノードID -> ノード情報のマッピング
        search_key: Search key / 検索キー
        match_mode: Match mode ("exact" or "partial") / マッチモード
        ignore_case: Ignore case (exact mode only) / 大文字小文字を無視するか (exact モードのみ)

    Returns:
        List of matched nodes / マッチしたノードのリスト
    """
    results: list[dict[str, Any]] = []

    if match_mode == "exact":
        if ignore_case:
            search_key_lower = search_key.lower()
            for key, node_ids in index_dict.items():
                if key.lower() == search_key_lower:
                    for node_id in node_ids:
                        node_info = by_id.get(node_id, {})
                        results.append({"id": node_id, **node_info})
        else:
            node_ids = index_dict.get(search_key, [])
            for node_id in node_ids:
                node_info = by_id.get(node_id, {})
                results.append({"id": node_id, **node_info})
    else:
        # partial match (always case-insensitive)
        search_key_lower = search_key.lower()
        for key, node_ids in index_dict.items():
            if search_key_lower in key.lower():
                for node_id in node_ids:
                    node_info = by_id.get(node_id, {})
                    results.append({"id": node_id, **node_info})

    return results


def get_cached_figma_file(store: CacheStore, file_id: str) -> dict[str, Any]:
    """Get Figma file metadata and frame list

    Args:
        store: Cache store
        file_id: Figma file ID

    Returns:
        File metadata and frame list. Contains 'error' field on error.
    """
    try:
        validate_file_id(file_id)
    except InvalidFileIdError:
        return _handle_invalid_file_id(file_id)

    index = store.get_index(file_id)
    if not index:
        return {
            "error": "file_not_found",
            "message": (
                f"File '{file_id}' not found in cache. "
                f"Run 'yet-another-figma-mcp cache -f {file_id}' to cache it first."
            ),
            "file_id": file_id,
        }

    file_data = store.get_file(file_id)
    if not file_data:
        return {
            "error": "file_data_missing",
            "message": f"File data for '{file_id}' is missing from cache.",
            "file_id": file_id,
        }

    # Return file metadata and main frame list
    frames: list[dict[str, Any]] = []
    for node_id, node_info in index.get("by_id", {}).items():
        if node_info.get("type") == "FRAME":
            # Include frames up to depth 3 (Document > Page > Frame or shallower)
            # This captures top-level frames and allows for edge cases
            if len(node_info.get("path", [])) <= 3:
                frames.append(
                    {
                        "id": node_id,
                        "name": node_info.get("name"),
                        "type": node_info.get("type"),
                        "path": node_info.get("path"),
                    }
                )

    return {
        "name": file_data.get("name"),
        "lastModified": file_data.get("lastModified"),
        "version": file_data.get("version"),
        "frames": frames,
    }


def get_cached_figma_node(
    store: CacheStore,
    file_id: str,
    node_id: str,
    depth: int | None = None,
    simplified: bool = False,
) -> dict[str, Any]:
    """Get detailed information for a specific node

    Args:
        store: Cache store
        file_id: Figma file ID
        node_id: Node ID (supports both URL format "1-2" and API format "1:2")
        depth: Maximum depth of children to include (None for unlimited).
               Use 0 to exclude children, 1 for immediate children only, etc.
        simplified: If True, return AI-optimized format with CSS-like properties.
                   Reduces response size significantly.

    Returns:
        Node details. Contains 'error' field on error.
    """
    try:
        validate_file_id(file_id)
    except InvalidFileIdError:
        return _handle_invalid_file_id(file_id)

    # URL のハイフン形式 (7749-4609) を API のコロン形式 (7749:4609) に正規化
    node_id = normalize_node_id(node_id)

    file_data = store.get_file(file_id)
    if not file_data:
        return {
            "error": "file_not_found",
            "message": (
                f"File '{file_id}' not found in cache. "
                f"Run 'yet-another-figma-mcp cache -f {file_id}' to cache it first."
            ),
            "file_id": file_id,
        }

    def find_node(node: dict[str, Any], target_id: str) -> dict[str, Any] | None:
        """Recursively search for a node by ID in the node tree"""
        if node.get("id") == target_id:
            return node
        for child in node.get("children", []):
            result = find_node(child, target_id)
            if result:
                return result
        return None

    document = file_data.get("document", {})
    result = find_node(document, node_id)

    if not result:
        return {
            "error": "node_not_found",
            "message": f"Node '{node_id}' not found in file '{file_id}'.",
            "file_id": file_id,
            "node_id": node_id,
        }

    # Simplified mode / 簡略化モード
    if simplified:
        return simplify_node(result, depth)  # type: ignore[return-value]

    # Apply depth limit only / 深さ制限のみ適用
    if depth is not None:
        return truncate_children(result, depth)

    return result


def search_figma_nodes_by_name(
    store: CacheStore,
    file_id: str,
    name: str,
    match_mode: Literal["exact", "partial"] = "exact",
    limit: int | None = None,
    ignore_case: bool = False,
) -> list[dict[str, Any]]:
    """Search nodes by name

    Args:
        store: Cache store
        file_id: Figma file ID
        name: Node name to search for
        match_mode: Match mode ("exact" or "partial")
        limit: Maximum number of results
        ignore_case: Case-insensitive matching for exact mode (default: False).
            Partial mode is always case-insensitive.

    Returns:
        List of matching nodes
    """
    try:
        validate_file_id(file_id)
    except InvalidFileIdError:
        return []

    index = store.get_index(file_id)
    if not index:
        return []

    by_name = index.get("by_name", {})
    by_id = index.get("by_id", {})
    results = _search_by_index(by_name, by_id, name, match_mode, ignore_case)

    if limit is not None:
        results = results[:limit]

    return results


def search_figma_frames_by_title(
    store: CacheStore,
    file_id: str,
    title: str,
    match_mode: Literal["exact", "partial"] = "exact",
    limit: int | None = None,
    ignore_case: bool = False,
) -> list[dict[str, Any]]:
    """Search frame nodes by title

    Args:
        store: Cache store
        file_id: Figma file ID
        title: Frame title to search for
        match_mode: Match mode ("exact" or "partial")
        limit: Maximum number of results
        ignore_case: Case-insensitive matching for exact mode (default: False).
            Partial mode is always case-insensitive.

    Returns:
        List of matching frame nodes
    """
    try:
        validate_file_id(file_id)
    except InvalidFileIdError:
        return []

    index = store.get_index(file_id)
    if not index:
        return []

    by_frame_title = index.get("by_frame_title", {})
    by_id = index.get("by_id", {})
    results = _search_by_index(by_frame_title, by_id, title, match_mode, ignore_case)

    if limit is not None:
        results = results[:limit]

    return results


def list_figma_frames(store: CacheStore, file_id: str) -> list[dict[str, Any]]:
    """List top-level frames in the file"""
    try:
        validate_file_id(file_id)
    except InvalidFileIdError:
        return []

    index = store.get_index(file_id)
    if not index:
        return []

    results: list[dict[str, Any]] = []
    by_id = index.get("by_id", {})

    for node_id, node_info in by_id.items():
        if node_info.get("type") == "FRAME":
            # Only page-level frames (short path)
            path = node_info.get("path", [])
            if len(path) == 3:  # Document > Page > Frame
                results.append(
                    {
                        "id": node_id,
                        "name": node_info.get("name"),
                        "path": path,
                    }
                )

    return results
