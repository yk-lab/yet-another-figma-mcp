"""MCP ツールハンドラ実装"""

from typing import Any, Literal

from yet_another_figma_mcp.cache import CacheStore, InvalidFileIdError, validate_file_id


def _handle_invalid_file_id(file_id: str) -> dict[str, Any]:
    """無効な file_id のエラーレスポンスを生成"""
    return {
        "error": "invalid_file_id",
        "message": f"無効なファイル ID: '{file_id}'",
        "file_id": file_id,
    }


def get_cached_figma_file(store: CacheStore, file_id: str) -> dict[str, Any]:
    """指定ファイルのノードツリーやメタデータを取得

    Args:
        store: キャッシュストア
        file_id: Figma ファイル ID

    Returns:
        ファイルメタデータとフレーム一覧。エラー時は error フィールドを含む
    """
    try:
        validate_file_id(file_id)
    except InvalidFileIdError:
        return _handle_invalid_file_id(file_id)

    index = store.get_index(file_id)
    if not index:
        return {
            "error": "file_not_found",
            "message": f"ファイル '{file_id}' がキャッシュに見つかりません",
            "file_id": file_id,
        }

    file_data = store.get_file(file_id)
    if not file_data:
        return {
            "error": "file_data_missing",
            "message": f"ファイル '{file_id}' のデータが見つかりません",
            "file_id": file_id,
        }

    # ルートノードと主要フレーム一覧を返す
    frames: list[dict[str, Any]] = []
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


def get_cached_figma_node(store: CacheStore, file_id: str, node_id: str) -> dict[str, Any]:
    """単一ノードの詳細情報を取得

    Args:
        store: キャッシュストア
        file_id: Figma ファイル ID
        node_id: ノード ID

    Returns:
        ノードの詳細情報。エラー時は error フィールドを含む
    """
    try:
        validate_file_id(file_id)
    except InvalidFileIdError:
        return _handle_invalid_file_id(file_id)

    file_data = store.get_file(file_id)
    if not file_data:
        return {
            "error": "file_not_found",
            "message": f"ファイル '{file_id}' がキャッシュに見つかりません",
            "file_id": file_id,
        }

    def find_node(node: dict[str, Any], target_id: str) -> dict[str, Any] | None:
        """ノードツリーから指定 ID のノードを再帰的に検索"""
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
            "message": f"ノード '{node_id}' が見つかりません",
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
    """ノード名でノードを検索

    Args:
        store: キャッシュストア
        file_id: Figma ファイル ID
        name: 検索するノード名
        match_mode: マッチモード ("exact" or "partial")
        limit: 最大取得件数
        ignore_case: exact モード時に大文字小文字を区別しない (デフォルト: False)。
            partial モードは常に大文字小文字を無視

    Returns:
        マッチしたノードのリスト
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
        # partial match (常に大文字小文字を無視)
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
    """フレーム名からフレームノードを検索

    Args:
        store: キャッシュストア
        file_id: Figma ファイル ID
        title: 検索するフレーム名
        match_mode: マッチモード ("exact" or "partial")
        limit: 最大取得件数
        ignore_case: exact モード時に大文字小文字を区別しない (デフォルト: False)。
            partial モードは常に大文字小文字を無視

    Returns:
        マッチしたフレームノードのリスト
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
        # partial match (常に大文字小文字を無視)
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
