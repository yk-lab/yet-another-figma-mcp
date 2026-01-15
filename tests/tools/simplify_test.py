"""simplify モジュールのテスト"""

from typing import Any, cast

from yet_another_figma_mcp.tools.simplify import simplify_node, truncate_children


def _simplify(node: dict[str, Any], depth: int | None = None) -> dict[str, Any]:
    """simplify_node のラッパー (テスト用に dict[str, Any] を返す)"""
    return cast(dict[str, Any], simplify_node(node, depth))


class TestTruncateChildren:
    """truncate_children のテスト"""

    def test_depth_zero_removes_children(self) -> None:
        """depth=0 で子要素が削除される"""
        node = {
            "id": "1:1",
            "name": "Parent",
            "type": "FRAME",
            "children": [
                {"id": "1:2", "name": "Child1", "type": "TEXT"},
                {"id": "1:3", "name": "Child2", "type": "RECTANGLE"},
            ],
        }
        result = truncate_children(node, depth=0)
        assert "children" not in result
        assert result["_childCount"] == 2

    def test_depth_one_keeps_immediate_children(self) -> None:
        """depth=1 で直接の子要素のみ保持"""
        node = {
            "id": "1:1",
            "name": "Parent",
            "type": "FRAME",
            "children": [
                {
                    "id": "1:2",
                    "name": "Child",
                    "type": "FRAME",
                    "children": [
                        {"id": "1:3", "name": "Grandchild", "type": "TEXT"},
                    ],
                },
            ],
        }
        result = truncate_children(node, depth=1)
        assert len(result["children"]) == 1
        assert "children" not in result["children"][0]
        assert result["children"][0]["_childCount"] == 1

    def test_no_children_no_child_count(self) -> None:
        """子要素がない場合は _childCount なし"""
        node = {"id": "1:1", "name": "Leaf", "type": "TEXT"}
        result = truncate_children(node, depth=0)
        assert "_childCount" not in result


class TestSimplifyNode:
    """simplify_node のテスト"""

    def test_basic_properties(self) -> None:
        """基本プロパティが抽出される"""
        node = {
            "id": "1:1",
            "name": "Button",
            "type": "FRAME",
        }
        result = _simplify(node)
        assert result["id"] == "1:1"
        assert result["name"] == "Button"
        assert result["type"] == "FRAME"

    def test_text_node_extracts_characters(self) -> None:
        """TEXT ノードで characters が抽出される"""
        node = {
            "id": "1:1",
            "name": "Label",
            "type": "TEXT",
            "characters": "Click me",
        }
        result = _simplify(node)
        assert result["text"] == "Click me"

    def test_size_from_bounding_box(self) -> None:
        """absoluteBoundingBox からサイズが抽出される"""
        node = {
            "id": "1:1",
            "name": "Box",
            "type": "RECTANGLE",
            "absoluteBoundingBox": {"x": 0, "y": 0, "width": 100.7, "height": 50.2},
        }
        result = _simplify(node)
        assert result["width"] == 101  # rounded from 100.7
        assert result["height"] == 50  # rounded from 50.2

    def test_auto_layout_horizontal(self) -> None:
        """横方向の Auto Layout が変換される"""
        node = {
            "id": "1:1",
            "name": "Row",
            "type": "FRAME",
            "layoutMode": "HORIZONTAL",
            "itemSpacing": 8,
            "paddingTop": 16,
            "paddingRight": 16,
            "paddingBottom": 16,
            "paddingLeft": 16,
        }
        result = _simplify(node)
        assert "flex-row" in result["layout"]
        assert "gap-8" in result["layout"]
        assert "p-16" in result["layout"]

    def test_auto_layout_vertical(self) -> None:
        """縦方向の Auto Layout が変換される"""
        node = {
            "id": "1:1",
            "name": "Column",
            "type": "FRAME",
            "layoutMode": "VERTICAL",
            "itemSpacing": 12,
        }
        result = _simplify(node)
        assert "flex-col" in result["layout"]
        assert "gap-12" in result["layout"]

    def test_asymmetric_padding(self) -> None:
        """非対称パディングが変換される"""
        node = {
            "id": "1:1",
            "name": "Box",
            "type": "FRAME",
            "layoutMode": "VERTICAL",
            "paddingTop": 8,
            "paddingRight": 16,
            "paddingBottom": 8,
            "paddingLeft": 16,
        }
        result = _simplify(node)
        assert "py-8" in result["layout"]
        assert "px-16" in result["layout"]

    def test_complex_padding_all_different(self) -> None:
        """4 values all different padding / 4 値すべて異なるパディング"""
        node = {
            "id": "1:1",
            "name": "Box",
            "type": "FRAME",
            "layoutMode": "VERTICAL",
            "paddingTop": 4,
            "paddingRight": 8,
            "paddingBottom": 12,
            "paddingLeft": 16,
        }
        result = _simplify(node)
        assert "p-[4,8,12,16]" in result["layout"]

    def test_alignment_justify_and_items(self) -> None:
        """Alignment properties / アラインメントプロパティ"""
        node = {
            "id": "1:1",
            "name": "Box",
            "type": "FRAME",
            "layoutMode": "HORIZONTAL",
            "primaryAxisAlignItems": "CENTER",
            "counterAxisAlignItems": "MAX",
        }
        result = _simplify(node)
        assert "justify-center" in result["layout"]
        assert "items-max" in result["layout"]

    def test_fills_solid_color(self) -> None:
        """SOLID 塗りつぶしが HEX に変換される"""
        node = {
            "id": "1:1",
            "name": "Box",
            "type": "RECTANGLE",
            "fills": [
                {
                    "type": "SOLID",
                    "visible": True,
                    "color": {"r": 1, "g": 0, "b": 0},
                }
            ],
        }
        result = _simplify(node)
        assert result["fills"] == "#ff0000"

    def test_fills_with_opacity(self) -> None:
        """透明度付き塗りつぶしが rgba に変換される"""
        node = {
            "id": "1:1",
            "name": "Box",
            "type": "RECTANGLE",
            "fills": [
                {
                    "type": "SOLID",
                    "visible": True,
                    "color": {"r": 0, "g": 0, "b": 1},
                    "opacity": 0.5,
                }
            ],
        }
        result = _simplify(node)
        assert "rgba(0,0,255,0.50)" in result["fills"]

    def test_strokes(self) -> None:
        """ストロークが変換される"""
        node = {
            "id": "1:1",
            "name": "Box",
            "type": "RECTANGLE",
            "strokes": [
                {
                    "type": "SOLID",
                    "visible": True,
                    "color": {"r": 0, "g": 0, "b": 0},
                }
            ],
            "strokeWeight": 2,
        }
        result = _simplify(node)
        assert result["strokes"] == "2px #000000"

    def test_strokes_with_opacity(self) -> None:
        """ストロークの透明度が反映される"""
        node = {
            "id": "1:1",
            "name": "Box",
            "type": "RECTANGLE",
            "strokes": [
                {
                    "type": "SOLID",
                    "visible": True,
                    "color": {"r": 1, "g": 0, "b": 0},
                    "opacity": 0.5,
                }
            ],
            "strokeWeight": 1,
        }
        result = _simplify(node)
        assert result["strokes"] == "1px rgba(255,0,0,0.50)"

    def test_corner_radius(self) -> None:
        """角丸が変換される"""
        node = {
            "id": "1:1",
            "name": "Box",
            "type": "RECTANGLE",
            "cornerRadius": 8,
        }
        result = _simplify(node)
        assert result["borderRadius"] == "8px"

    def test_individual_corner_radius(self) -> None:
        """個別の角丸が変換される"""
        node = {
            "id": "1:1",
            "name": "Box",
            "type": "RECTANGLE",
            "topLeftRadius": 4,
            "topRightRadius": 8,
            "bottomRightRadius": 12,
            "bottomLeftRadius": 16,
        }
        result = _simplify(node)
        assert result["borderRadius"] == "4px 8px 12px 16px"

    def test_drop_shadow(self) -> None:
        """ドロップシャドウが変換される"""
        node = {
            "id": "1:1",
            "name": "Box",
            "type": "RECTANGLE",
            "effects": [
                {
                    "type": "DROP_SHADOW",
                    "visible": True,
                    "offset": {"x": 0, "y": 4},
                    "radius": 8,
                }
            ],
        }
        result = _simplify(node)
        assert "shadow(0px 4px 8px)" in result["effects"]

    def test_blur_effect(self) -> None:
        """ブラーエフェクトが変換される"""
        node = {
            "id": "1:1",
            "name": "Box",
            "type": "RECTANGLE",
            "effects": [
                {
                    "type": "LAYER_BLUR",
                    "visible": True,
                    "radius": 10,
                }
            ],
        }
        result = _simplify(node)
        assert "blur(10px)" in result["effects"]

    def test_invisible_effect_skipped(self) -> None:
        """Invisible effects are skipped / 非表示エフェクトはスキップされる"""
        node = {
            "id": "1:1",
            "name": "Box",
            "type": "RECTANGLE",
            "effects": [
                {
                    "type": "DROP_SHADOW",
                    "visible": False,
                    "offset": {"x": 0, "y": 4},
                    "radius": 8,
                },
                {
                    "type": "LAYER_BLUR",
                    "visible": True,
                    "radius": 5,
                },
            ],
        }
        result = _simplify(node)
        assert result["effects"] == "blur(5px)"
        assert "shadow" not in result["effects"]

    def test_opacity(self) -> None:
        """透明度が抽出される"""
        node = {
            "id": "1:1",
            "name": "Box",
            "type": "RECTANGLE",
            "opacity": 0.75,
        }
        result = _simplify(node)
        assert result["opacity"] == 0.75

    def test_component_id(self) -> None:
        """コンポーネントIDが抽出される"""
        node = {
            "id": "1:1",
            "name": "Instance",
            "type": "INSTANCE",
            "componentId": "2:1",
        }
        result = _simplify(node)
        assert result["componentId"] == "2:1"

    def test_children_with_depth(self) -> None:
        """子要素が depth で制限される"""
        node = {
            "id": "1:1",
            "name": "Parent",
            "type": "FRAME",
            "children": [
                {
                    "id": "1:2",
                    "name": "Child",
                    "type": "FRAME",
                    "children": [
                        {"id": "1:3", "name": "Grandchild", "type": "TEXT"},
                    ],
                },
            ],
        }
        result = _simplify(node, depth=1)
        assert len(result["children"]) == 1
        assert result["children"][0]["name"] == "Child"
        # depth=1 なので孫要素は切り詰められる
        assert result["children"][0].get("children") == []
        assert result["children"][0].get("_childCount") == 1

    def test_children_unlimited_depth(self) -> None:
        """depth=None で全ての子要素が含まれる"""
        node = {
            "id": "1:1",
            "name": "Parent",
            "type": "FRAME",
            "children": [
                {
                    "id": "1:2",
                    "name": "Child",
                    "type": "FRAME",
                    "children": [
                        {"id": "1:3", "name": "Grandchild", "type": "TEXT"},
                    ],
                },
            ],
        }
        result = _simplify(node, depth=None)
        assert len(result["children"]) == 1
        assert len(result["children"][0]["children"]) == 1
        assert result["children"][0]["children"][0]["name"] == "Grandchild"
