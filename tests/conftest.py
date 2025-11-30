"""共通テストフィクスチャ"""

import json
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """fixtures ディレクトリのパスを返す"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_design_system(fixtures_dir: Path) -> dict[str, Any]:
    """Design System サンプルファイルを読み込む"""
    with open(fixtures_dir / "sample_design_system.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def simple_figma_file() -> dict[str, Any]:
    """シンプルな Figma ファイルデータ (テスト用最小構成)"""
    return {
        "name": "Simple Test File",
        "lastModified": "2024-01-01T00:00:00Z",
        "version": "1",
        "document": {
            "id": "0:0",
            "name": "Document",
            "type": "DOCUMENT",
            "children": [
                {
                    "id": "0:1",
                    "name": "Page 1",
                    "type": "CANVAS",
                    "children": [
                        {
                            "id": "1:1",
                            "name": "Login Screen",
                            "type": "FRAME",
                            "children": [
                                {
                                    "id": "1:2",
                                    "name": "Primary Button",
                                    "type": "COMPONENT",
                                    "children": [],
                                }
                            ],
                        },
                        {
                            "id": "1:3",
                            "name": "Sign Up Screen",
                            "type": "FRAME",
                            "children": [],
                        },
                    ],
                }
            ],
        },
    }
