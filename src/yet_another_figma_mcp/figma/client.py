"""Figma API クライアント"""

import os
from typing import Any

import httpx


class FigmaClient:
    """Figma REST API クライアント"""

    BASE_URL = "https://api.figma.com/v1"

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.environ.get("FIGMA_API_TOKEN", "")
        if not self.token:
            raise ValueError(
                "Figma API token is required. "
                "Set FIGMA_API_TOKEN environment variable or pass token parameter."
            )
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            headers={"X-Figma-Token": self.token},
            timeout=30.0,
        )

    def get_file(self, file_id: str) -> dict[str, Any]:
        """Figma ファイルを取得"""
        response = self._client.get(f"/files/{file_id}")
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    def close(self) -> None:
        """クライアントを閉じる"""
        self._client.close()

    def __enter__(self) -> "FigmaClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
