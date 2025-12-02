"""MCP ツールハンドラ実装"""

from typing import Any, Literal

from yet_another_figma_mcp.cache import CacheStore, InvalidFileIdError, validate_file_id


def _handle_invalid_file_id(file_id: str) -> dict[str, Any]:
    """Generate error response for invalid file_id"""
    return {
        "error": "invalid_file_id",
        "message": f"Invalid file ID: '{file_id}'. File ID should be alphanumeric.",
        "file_id": file_id,
    }


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

    # Return root node and main frame list
    frames: list[dict[str, Any]] = []
    for node_id, node_info in index.get("by_id", {}).items():
        if node_info.get("type") == "FRAME":
            # Only shallow frames (direct children of pages)
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


def get_cached_figma_node(store: CacheStore, file_id: str, node_id: str) -> dict[str, Any]:
    """Get detailed information for a specific node

    Args:
        store: Cache store
        file_id: Figma file ID
        node_id: Node ID

    Returns:
        Node details. Contains 'error' field on error.
    """
    try:
        validate_file_id(file_id)
    except InvalidFileIdError:
        return _handle_invalid_file_id(file_id)

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

    results: list[dict[str, Any]] = []
    by_name = index.get("by_name", {})
    by_id = index.get("by_id", {})

    if match_mode == "exact":
        if ignore_case:
            # 大文字小文字を無視した完全一致
            name_lower = name.lower()
            for node_name, node_ids in by_name.items():
                if node_name.lower() == name_lower:
                    for node_id in node_ids:
                        node_info = by_id.get(node_id, {})
                        results.append({"id": node_id, **node_info})
        else:
            node_ids = by_name.get(name, [])
            for node_id in node_ids:
                node_info = by_id.get(node_id, {})
                results.append({"id": node_id, **node_info})
    else:
        # partial match (always case-insensitive)
        name_lower = name.lower()
        for node_name, node_ids in by_name.items():
            if name_lower in node_name.lower():
                for node_id in node_ids:
                    node_info = by_id.get(node_id, {})
                    results.append({"id": node_id, **node_info})

    if limit:
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

    results: list[dict[str, Any]] = []
    by_frame_title = index.get("by_frame_title", {})
    by_id = index.get("by_id", {})

    if match_mode == "exact":
        if ignore_case:
            # 大文字小文字を無視した完全一致
            title_lower = title.lower()
            for frame_title, node_ids in by_frame_title.items():
                if frame_title.lower() == title_lower:
                    for node_id in node_ids:
                        node_info = by_id.get(node_id, {})
                        results.append({"id": node_id, **node_info})
        else:
            node_ids = by_frame_title.get(title, [])
            for node_id in node_ids:
                node_info = by_id.get(node_id, {})
                results.append({"id": node_id, **node_info})
    else:
        # partial match (always case-insensitive)
        title_lower = title.lower()
        for frame_title, node_ids in by_frame_title.items():
            if title_lower in frame_title.lower():
                for node_id in node_ids:
                    node_info = by_id.get(node_id, {})
                    results.append({"id": node_id, **node_info})

    if limit:
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
