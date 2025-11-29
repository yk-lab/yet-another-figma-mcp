"""インデックス生成・管理"""

import json
from pathlib import Path
from typing import Any

from yet_another_figma_mcp.cache.store import validate_file_id


def build_index(file_data: dict[str, Any]) -> dict[str, Any]:
    """Figma ファイル JSON からノードインデックスを生成"""
    by_id: dict[str, dict[str, Any]] = {}
    by_name: dict[str, list[str]] = {}
    by_frame_title: dict[str, list[str]] = {}

    def traverse(node: dict[str, Any], name_path: list[str], parent_id: str | None) -> None:
        """ノードツリーを再帰的に走査してインデックスを構築"""
        node_id = node.get("id", "")
        node_name = node.get("name", "")
        node_type = node.get("type", "")

        current_name_path = [*name_path, node_name]

        # by_id に登録
        by_id[node_id] = {
            "name": node_name,
            "type": node_type,
            "parent_id": parent_id,
            "path": current_name_path,
        }

        # by_name に登録
        if node_name:
            if node_name not in by_name:
                by_name[node_name] = []
            by_name[node_name].append(node_id)

        # FRAME タイプは by_frame_title にも登録
        if node_type == "FRAME" and node_name:
            if node_name not in by_frame_title:
                by_frame_title[node_name] = []
            by_frame_title[node_name].append(node_id)

        # 子ノードを再帰処理（現在のノード ID を親 ID として渡す）
        children = node.get("children", [])
        for child in children:
            traverse(child, current_name_path, node_id)

    # ドキュメントルートから走査
    document = file_data.get("document", {})
    traverse(document, [], None)

    return {
        "by_id": by_id,
        "by_name": by_name,
        "by_frame_title": by_frame_title,
    }


def save_index(index: dict[str, Any], cache_dir: Path, file_id: str) -> None:
    """インデックスをディスクに保存

    Args:
        index: 保存するインデックスデータ
        cache_dir: キャッシュディレクトリのパス
        file_id: Figma ファイル ID

    Raises:
        InvalidFileIdError: file_id が無効な形式の場合
    """
    validate_file_id(file_id)
    file_dir = cache_dir / file_id
    file_dir.mkdir(parents=True, exist_ok=True)

    index_path = file_dir / "nodes_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
