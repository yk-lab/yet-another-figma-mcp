"""MCP ツールハンドラ実装"""

from typing import Any, Literal

from yet_another_figma_mcp.cache import CacheStore


def get_cached_figma_file(store: CacheStore, file_id: str) -> dict[str, Any] | None:
    """指定ファイルのノードツリーやメタデータを取得"""
    index = store.get_index(file_id)
    if not index:
        return None

    file_data = store.get_file(file_id)
    if not file_data:
        return None

    # ルートノードと主要フレーム一覧を返す
    frames = []
    for node_id, node_info in index.get("by_id", {}).items():
        if node_info.get("type") == "FRAME":
            # 浅い階層のフレームのみ（ページ直下など）
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


def get_cached_figma_node(store: CacheStore, file_id: str, node_id: str) -> dict[str, Any] | None:
    """単一ノードの詳細情報を取得"""
    file_data = store.get_file(file_id)
    if not file_data:
        return None

    def find_node(node: dict[str, Any], target_id: str) -> dict[str, Any] | None:
        if node.get("id") == target_id:
            return node
        for child in node.get("children", []):
            result = find_node(child, target_id)
            if result:
                return result
        return None

    document = file_data.get("document", {})
    return find_node(document, node_id)


def search_figma_nodes_by_name(
    store: CacheStore,
    file_id: str,
    name: str,
    match_mode: Literal["exact", "partial"] = "exact",
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """ノード名でノードを検索"""
    index = store.get_index(file_id)
    if not index:
        return []

    results: list[dict[str, Any]] = []
    by_name = index.get("by_name", {})
    by_id = index.get("by_id", {})

    if match_mode == "exact":
        node_ids = by_name.get(name, [])
        for node_id in node_ids:
            node_info = by_id.get(node_id, {})
            results.append({"id": node_id, **node_info})
    else:
        # partial match
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
) -> list[dict[str, Any]]:
    """フレーム名からフレームノードを検索"""
    index = store.get_index(file_id)
    if not index:
        return []

    results: list[dict[str, Any]] = []
    by_frame_title = index.get("by_frame_title", {})
    by_id = index.get("by_id", {})

    if match_mode == "exact":
        node_ids = by_frame_title.get(title, [])
        for node_id in node_ids:
            node_info = by_id.get(node_id, {})
            results.append({"id": node_id, **node_info})
    else:
        # partial match
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
    """ファイル直下の主要フレーム一覧を取得"""
    index = store.get_index(file_id)
    if not index:
        return []

    results: list[dict[str, Any]] = []
    by_id = index.get("by_id", {})

    for node_id, node_info in by_id.items():
        if node_info.get("type") == "FRAME":
            # ページ直下のフレームのみ（path が短いもの）
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
