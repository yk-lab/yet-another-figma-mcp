"""Figma API クライアント"""

import logging
import os
import platform
import random
import time
from types import TracebackType
from typing import Any

import httpx

from yet_another_figma_mcp import __version__
from yet_another_figma_mcp.cache import validate_file_id
from yet_another_figma_mcp.figma.exceptions import (
    FigmaAPIError,
    FigmaAuthenticationError,
    FigmaFileNotFoundError,
    FigmaRateLimitError,
    FigmaServerError,
)

logger = logging.getLogger(__name__)

# デフォルト設定
DEFAULT_TIMEOUT = 60.0  # Figma の大きなファイルは時間がかかる
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BASE_DELAY = 1.0  # 秒
DEFAULT_RETRY_MAX_DELAY = 30.0  # 秒


def build_user_agent() -> str:
    """Build User-Agent string for API requests

    Format: yet-another-figma-mcp/{version} (Python/{py_version}; httpx/{httpx_version})

    Returns:
        User-Agent string
    """
    py_version = platform.python_version()
    httpx_version = httpx.__version__
    return f"yet-another-figma-mcp/{__version__} (Python/{py_version}; httpx/{httpx_version})"


class FigmaClient:
    """Figma REST API クライアント

    Attributes:
        token: Figma API トークン
        timeout: リクエストタイムアウト (秒)
        max_retries: 最大リトライ回数
        retry_base_delay: リトライ基本待機時間 (秒)
        retry_max_delay: リトライ最大待機時間 (秒)
    """

    BASE_URL = "https://api.figma.com/v1"

    def __init__(
        self,
        token: str | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_base_delay: float = DEFAULT_RETRY_BASE_DELAY,
        retry_max_delay: float = DEFAULT_RETRY_MAX_DELAY,
    ) -> None:
        """FigmaClient を初期化

        Args:
            token: Figma API トークン。未指定時は環境変数 FIGMA_API_TOKEN から取得
            timeout: リクエストタイムアウト (秒)
            max_retries: 最大リトライ回数 (レート制限・サーバーエラー時)
            retry_base_delay: リトライ基本待機時間 (秒)
            retry_max_delay: リトライ最大待機時間 (秒)

        Raises:
            ValueError: API トークンが未設定の場合
        """
        self.token = token or os.environ.get("FIGMA_API_TOKEN", "")
        if not self.token:
            raise ValueError(
                "Figma API token is required. "
                "Set FIGMA_API_TOKEN environment variable or pass token parameter."
            )
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self.retry_max_delay = retry_max_delay

        self._client = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "X-Figma-Token": self.token,
                "User-Agent": build_user_agent(),
            },
            timeout=self.timeout,
        )

    @staticmethod
    def _parse_retry_after_header(response: httpx.Response) -> int | None:
        """Retry-After ヘッダーをパースして秒数を取得

        Args:
            response: httpx レスポンス

        Returns:
            待機秒数 (ヘッダーがない、または解析不能な場合は None)
        """
        retry_after = response.headers.get("Retry-After")
        if not retry_after:
            return None
        try:
            return int(retry_after)
        except ValueError:
            # HTTP-date format (RFC 7231) は現時点では未サポート
            return None

    def _calculate_retry_delay(self, attempt: int, retry_after: int | None = None) -> float:
        """リトライ待機時間を計算 (指数バックオフ + ジッター)

        Args:
            attempt: 現在の試行回数 (0から開始)
            retry_after: サーバー指定の待機時間 (秒)

        Returns:
            待機時間 (秒)
        """
        if retry_after:
            return float(retry_after)

        # 指数バックオフ: base_delay * 2^attempt
        delay = self.retry_base_delay * (2**attempt)
        # ジッター: ±25% のランダム変動
        jitter = delay * 0.25 * (2 * random.random() - 1)  # noqa: S311 # nosec B311
        delay = delay + jitter
        # 最大待機時間でクリップ
        return min(delay, self.retry_max_delay)

    def _handle_response_error(self, response: httpx.Response, file_id: str | None = None) -> None:
        """レスポンスエラーを処理してカスタム例外を送出

        Args:
            response: httpx レスポンス
            file_id: ファイル ID（404 エラー時に使用）

        Raises:
            FigmaAuthenticationError: 認証エラー（401/403）
            FigmaFileNotFoundError: ファイル未存在（404）
            FigmaRateLimitError: レート制限（429）
            FigmaServerError: サーバーエラー（5xx）
            FigmaAPIError: その他の API エラー
        """
        status_code = response.status_code

        if status_code in (401, 403):
            raise FigmaAuthenticationError()

        if status_code == 404:
            if file_id:
                raise FigmaFileNotFoundError(file_id)
            raise FigmaAPIError("Resource not found", status_code=404)

        if status_code == 429:
            retry_after_int = self._parse_retry_after_header(response)
            raise FigmaRateLimitError(retry_after=retry_after_int)

        if status_code >= 500:
            raise FigmaServerError(status_code)

        # その他のエラー
        try:
            error_detail = response.json()
            message = error_detail.get("err", str(error_detail))
        except (ValueError, KeyError):
            message = response.text or f"HTTP {status_code}"

        raise FigmaAPIError(message, status_code=status_code)

    def _request_with_retry(
        self,
        method: str,
        path: str,
        *,
        file_id: str | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """リトライ付きでリクエストを実行

        Args:
            method: HTTP メソッド
            path: API パス
            file_id: ファイル ID（エラーメッセージ用）
            **kwargs: httpx.Client.request に渡す追加引数

        Returns:
            成功レスポンス

        Raises:
            FigmaAPIError: API エラー（リトライ後も失敗した場合を含む）
        """
        last_exception: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.request(method, path, **kwargs)

                if response.is_success:
                    return response

                # リトライ対象のエラー
                if response.status_code in (429, 500, 502, 503, 504):
                    retry_after_int = self._parse_retry_after_header(response)

                    if attempt < self.max_retries:
                        delay = self._calculate_retry_delay(attempt, retry_after_int)
                        logger.warning(
                            "Request failed with status %d, retrying in %.1f seconds "
                            "(attempt %d/%d)",
                            response.status_code,
                            delay,
                            attempt + 1,
                            self.max_retries,
                        )
                        time.sleep(delay)
                        continue

                # リトライ対象外またはリトライ回数超過
                self._handle_response_error(response, file_id)

            except httpx.TimeoutException as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(
                        "Request timed out, retrying in %.1f seconds (attempt %d/%d)",
                        delay,
                        attempt + 1,
                        self.max_retries,
                    )
                    time.sleep(delay)
                    continue
                raise FigmaAPIError(
                    f"Request timed out after {self.max_retries + 1} attempts"
                ) from e

            except httpx.RequestError as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(
                        "Request failed: %s, retrying in %.1f seconds (attempt %d/%d)",
                        str(e),
                        delay,
                        attempt + 1,
                        self.max_retries,
                    )
                    time.sleep(delay)
                    continue
                raise FigmaAPIError(f"Request failed: {e}") from e

        # ここには到達しないはずだが、念のため
        raise FigmaAPIError("Max retries exceeded") from last_exception

    def get_file(self, file_id: str) -> dict[str, Any]:
        """Figma ファイルを取得

        Args:
            file_id: Figma ファイル ID

        Returns:
            ファイルデータ（ドキュメント構造含む）

        Raises:
            InvalidFileIdError: file_id が無効な形式の場合
            FigmaAuthenticationError: 認証エラー
            FigmaFileNotFoundError: ファイルが存在しない
            FigmaRateLimitError: レート制限
            FigmaServerError: サーバーエラー
            FigmaAPIError: その他の API エラー
        """
        validate_file_id(file_id)
        response = self._request_with_retry("GET", f"/files/{file_id}", file_id=file_id)
        result: dict[str, Any] = response.json()
        return result

    def close(self) -> None:
        """クライアントを閉じる"""
        self._client.close()

    def __enter__(self) -> "FigmaClient":
        """コンテキストマネージャの開始"""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """コンテキストマネージャの終了"""
        self.close()
