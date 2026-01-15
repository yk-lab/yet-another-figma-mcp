"""Node simplification module / ノード簡略化モジュール

Convert Figma nodes to AI-optimized format.
Figma ノードをAI向けに最適化された形式に変換する。

Inspired by Figma-Context-MCP (https://github.com/GLips/Figma-Context-MCP).
"""

from typing import Any, TypedDict, cast


class SimplifiedNode(TypedDict, total=False):
    """AI-optimized node format / AI向けに最適化されたノード形式"""

    id: str
    name: str
    type: str
    # Text / テキスト
    text: str
    # Layout (CSS flexbox style) / レイアウト (CSS flexbox 風)
    layout: str
    # Size / サイズ
    width: int
    height: int
    # Style / スタイル
    fills: str
    strokes: str
    effects: str
    opacity: float
    borderRadius: str
    # Component / コンポーネント
    componentId: str
    # Children / 子要素
    children: list["SimplifiedNode"]


def _format_solid_color(color: dict[str, Any], opacity: float = 1.0) -> str:
    """Convert SOLID color to HEX or rgba format / SOLID 色を HEX または rgba 形式に変換する"""
    r = round(float(color.get("r", 0)) * 255)
    g = round(float(color.get("g", 0)) * 255)
    b = round(float(color.get("b", 0)) * 255)
    if opacity < 1:
        return f"rgba({r},{g},{b},{opacity:.2f})"
    return f"#{r:02x}{g:02x}{b:02x}"


def truncate_children(node: dict[str, Any], depth: int) -> dict[str, Any]:
    """Truncate node children at specified depth / ノードの子要素を指定した深さで切り詰める

    Args:
        node: Figma node / Figma ノード
        depth: Remaining depth (0 removes children) / 残り深さ (0 で子要素を削除)

    Returns:
        Node with depth limit applied / 深さ制限を適用したノード
    """
    if depth <= 0:
        # Remove children, keep only child count / 子要素を削除し、子要素数だけ残す
        result = {k: v for k, v in node.items() if k != "children"}
        children = node.get("children", [])
        if children:
            result["_childCount"] = len(children)
        return result

    # Process children recursively / 子要素を再帰的に処理
    result = dict(node)
    if "children" in node:
        result["children"] = [truncate_children(child, depth - 1) for child in node["children"]]
    return result


def simplify_node(node: dict[str, Any], depth: int | None = None) -> SimplifiedNode:
    """Simplify node for AI consumption / ノードをAI向けに簡略化する

    Args:
        node: Figma node (raw data) / Figma ノード (生データ)
        depth: Children depth limit (None for unlimited) / 子要素の深さ制限 (None で無制限)

    Returns:
        Simplified node / 簡略化されたノード
    """
    result: SimplifiedNode = {
        "id": node.get("id", ""),
        "name": node.get("name", ""),
        "type": node.get("type", ""),
    }

    # Text node / テキストノードの場合
    if node.get("type") == "TEXT":
        characters = node.get("characters", "")
        if characters:
            result["text"] = characters

    # Size info / サイズ情報
    bbox = node.get("absoluteBoundingBox") or node.get("size")
    if bbox:
        if "width" in bbox:
            result["width"] = round(bbox["width"])
        if "height" in bbox:
            result["height"] = round(bbox["height"])

    # Layout info (Auto Layout) / レイアウト情報 (Auto Layout)
    layout_parts: list[str] = []
    layout_mode = node.get("layoutMode")
    if layout_mode:
        if layout_mode == "HORIZONTAL":
            layout_parts.append("flex-row")
        elif layout_mode == "VERTICAL":
            layout_parts.append("flex-col")

        # gap
        item_spacing = node.get("itemSpacing")
        if item_spacing:
            layout_parts.append(f"gap-{round(item_spacing)}")

        # padding
        padding_values = [
            node.get("paddingTop", 0),
            node.get("paddingRight", 0),
            node.get("paddingBottom", 0),
            node.get("paddingLeft", 0),
        ]
        if any(p > 0 for p in padding_values):
            # Simplify: p-N if all same, py-N px-N if different / 簡略化: 全部同じならp-N、違えばpy-N px-N形式
            if len(set(padding_values)) == 1:
                layout_parts.append(f"p-{round(padding_values[0])}")
            else:
                py = padding_values[0] if padding_values[0] == padding_values[2] else None
                px = padding_values[1] if padding_values[1] == padding_values[3] else None
                if py is not None and px is not None:
                    if py > 0:
                        layout_parts.append(f"py-{round(py)}")
                    if px > 0:
                        layout_parts.append(f"px-{round(px)}")
                else:
                    layout_parts.append(
                        f"p-[{round(padding_values[0])},{round(padding_values[1])},"
                        f"{round(padding_values[2])},{round(padding_values[3])}]"
                    )

        # alignment
        primary_align = node.get("primaryAxisAlignItems")
        counter_align = node.get("counterAxisAlignItems")
        if primary_align and primary_align != "MIN":
            layout_parts.append(f"justify-{primary_align.lower()}")
        if counter_align and counter_align != "MIN":
            layout_parts.append(f"items-{counter_align.lower()}")

    if layout_parts:
        result["layout"] = " ".join(layout_parts)

    # Fills / 塗りつぶし
    fills = node.get("fills", [])
    if fills and isinstance(fills, list):
        fill_strs: list[str] = []
        for fill in cast(list[dict[str, Any]], fills):
            if fill.get("visible", True) and fill.get("type") == "SOLID":
                color = fill.get("color", {})
                opacity = float(fill.get("opacity", 1))
                fill_strs.append(_format_solid_color(color, opacity))
        if fill_strs:
            result["fills"] = " ".join(fill_strs)

    # Strokes / ストローク
    strokes = node.get("strokes", [])
    if strokes and isinstance(strokes, list):
        stroke_strs: list[str] = []
        for stroke in cast(list[dict[str, Any]], strokes):
            if stroke.get("visible", True) and stroke.get("type") == "SOLID":
                color = stroke.get("color", {})
                opacity = float(stroke.get("opacity", 1))
                stroke_strs.append(_format_solid_color(color, opacity))
        stroke_weight = node.get("strokeWeight")
        if stroke_strs and stroke_weight:
            result["strokes"] = f"{stroke_weight}px {' '.join(stroke_strs)}"

    # Effects / エフェクト
    effects = node.get("effects", [])
    if effects and isinstance(effects, list):
        effect_strs: list[str] = []
        for effect in cast(list[dict[str, Any]], effects):
            if not effect.get("visible", True):
                continue
            effect_type = effect.get("type")
            if effect_type == "DROP_SHADOW":
                offset = effect.get("offset", {})
                x = round(float(offset.get("x", 0)))
                y = round(float(offset.get("y", 0)))
                radius = round(float(effect.get("radius", 0)))
                effect_strs.append(f"shadow({x}px {y}px {radius}px)")
            elif effect_type == "LAYER_BLUR":
                radius = round(float(effect.get("radius", 0)))
                effect_strs.append(f"blur({radius}px)")
        if effect_strs:
            result["effects"] = " ".join(effect_strs)

    # Opacity / 透明度
    opacity = node.get("opacity")
    if opacity is not None and opacity < 1:
        result["opacity"] = round(opacity, 2)

    # Border radius / 角丸
    corner_radius = node.get("cornerRadius")
    if corner_radius:
        result["borderRadius"] = f"{round(corner_radius)}px"
    else:
        # Individual corner radius / 個別の角丸
        corners = [
            node.get("topLeftRadius", 0),
            node.get("topRightRadius", 0),
            node.get("bottomRightRadius", 0),
            node.get("bottomLeftRadius", 0),
        ]
        if any(c > 0 for c in corners):
            result["borderRadius"] = " ".join(f"{round(c)}px" for c in corners)

    # Component ID / コンポーネントID
    component_id = node.get("componentId")
    if component_id:
        result["componentId"] = component_id

    # Children / 子要素
    children = node.get("children", [])
    if children:
        if depth is not None and depth <= 0:
            # Depth limit reached, return only child count / 深さ制限に達した場合は子要素数だけ返す
            result["children"] = []  # type: ignore
            # _childCount is not in SimplifiedNode but added for info / _childCount は SimplifiedNode に含まれないが、情報として追加
            result["_childCount"] = len(children)  # type: ignore
        else:
            next_depth = None if depth is None else depth - 1
            result["children"] = [simplify_node(child, next_depth) for child in children]

    return result
