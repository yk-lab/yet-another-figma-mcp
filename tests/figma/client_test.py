"""Figma API クライアントのテスト"""

# pyright: reportPrivateUsage=false
# ruff: noqa: S105, S106  # Test tokens are not real secrets

import platform
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import httpx
import pytest

from yet_another_figma_mcp import __version__
from yet_another_figma_mcp.cache import InvalidFileIdError
from yet_another_figma_mcp.figma import (
    FigmaAPIError,
    FigmaAuthenticationError,
    FigmaClient,
    FigmaFileNotFoundError,
    FigmaRateLimitError,
    FigmaServerError,
)
from yet_another_figma_mcp.figma.client import build_user_agent


class TestBuildUserAgent:
    """build_user_agent 関数のテスト"""

    def test_build_user_agent_format(self) -> None:
        """User-Agent の形式を確認"""
        user_agent = build_user_agent()

        # 期待される形式: yet-another-figma-mcp/{version} (Python/{py_version}; httpx/{httpx_version})
        assert user_agent.startswith("yet-another-figma-mcp/")
        assert __version__ in user_agent
        assert f"Python/{platform.python_version()}" in user_agent
        assert f"httpx/{httpx.__version__}" in user_agent

    def test_build_user_agent_contains_all_components(self) -> None:
        """User-Agent に必要なコンポーネントが含まれていることを確認"""
        user_agent = build_user_agent()

        # パッケージ名とバージョン
        assert "yet-another-figma-mcp" in user_agent
        # Python バージョン
        assert "Python/" in user_agent
        # httpx バージョン
        assert "httpx/" in user_agent


class TestFigmaClientInit:
    """FigmaClient 初期化のテスト"""

    def test_init_with_token(self) -> None:
        """トークン引数での初期化"""
        client = FigmaClient(token="test-token")
        assert client.token == "test-token"
        client.close()

    def test_init_with_env_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """環境変数からのトークン取得"""
        monkeypatch.setenv("FIGMA_API_TOKEN", "env-token")
        client = FigmaClient()
        assert client.token == "env-token"
        client.close()

    def test_init_without_token_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """トークン未設定時のエラー"""
        monkeypatch.delenv("FIGMA_API_TOKEN", raising=False)
        with pytest.raises(ValueError, match="Figma API token is required"):
            FigmaClient()

    def test_init_with_custom_settings(self) -> None:
        """カスタム設定での初期化"""
        client = FigmaClient(
            token="test-token",
            timeout=120.0,
            max_retries=5,
            retry_base_delay=2.0,
            retry_max_delay=60.0,
        )
        assert client.timeout == 120.0
        assert client.max_retries == 5
        assert client.retry_base_delay == 2.0
        assert client.retry_max_delay == 60.0
        client.close()

    def test_init_sets_user_agent_header(self) -> None:
        """初期化時に User-Agent ヘッダーが設定されることを確認"""
        client = FigmaClient(token="test-token")
        headers = client._client.headers

        assert "User-Agent" in headers
        assert "yet-another-figma-mcp" in headers["User-Agent"]
        assert "Python/" in headers["User-Agent"]
        assert "httpx/" in headers["User-Agent"]
        client.close()


class TestFigmaClientContextManager:
    """FigmaClient コンテキストマネージャのテスト"""

    def test_context_manager(self) -> None:
        """with 文での使用"""
        with FigmaClient(token="test-token") as client:
            assert client.token == "test-token"


class TestFigmaClientParseRetryAfterHeader:
    """Retry-After ヘッダーパースのテスト"""

    def test_parse_integer_seconds(self) -> None:
        """整数秒のパース"""
        response = MagicMock(spec=httpx.Response)
        response.headers = {"Retry-After": "60"}

        result = FigmaClient._parse_retry_after_header(response)
        assert result == 60

    def test_parse_missing_header(self) -> None:
        """ヘッダーがない場合"""
        response = MagicMock(spec=httpx.Response)
        response.headers = {}

        result = FigmaClient._parse_retry_after_header(response)
        assert result is None

    def test_parse_http_date_returns_none(self) -> None:
        """HTTP-date 形式は未サポートで None を返す"""
        response = MagicMock(spec=httpx.Response)
        response.headers = {"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"}

        result = FigmaClient._parse_retry_after_header(response)
        assert result is None

    def test_parse_invalid_value_returns_none(self) -> None:
        """無効な値は None を返す"""
        response = MagicMock(spec=httpx.Response)
        response.headers = {"Retry-After": "invalid"}

        result = FigmaClient._parse_retry_after_header(response)
        assert result is None


class TestFigmaClientRetryDelay:
    """リトライ待機時間計算のテスト"""

    def test_retry_after_respected(self) -> None:
        """Retry-After ヘッダーの尊重"""
        with FigmaClient(token="test-token") as client:
            delay = client._calculate_retry_delay(0, retry_after=10)
            assert delay == 10.0

    def test_exponential_backoff(self) -> None:
        """指数バックオフの計算"""
        with FigmaClient(token="test-token", retry_base_delay=1.0) as client:
            # attempt=0: 1 * 2^0 = 1 (±25% jitter)
            delay0 = client._calculate_retry_delay(0)
            assert 0.75 <= delay0 <= 1.25

            # attempt=1: 1 * 2^1 = 2 (±25% jitter)
            delay1 = client._calculate_retry_delay(1)
            assert 1.5 <= delay1 <= 2.5

            # attempt=2: 1 * 2^2 = 4 (±25% jitter)
            delay2 = client._calculate_retry_delay(2)
            assert 3.0 <= delay2 <= 5.0

    def test_max_delay_cap(self) -> None:
        """最大待機時間のクリップ"""
        with FigmaClient(token="test-token", retry_base_delay=10.0, retry_max_delay=15.0) as client:
            # attempt=5: 10 * 2^5 = 320 → capped to 15
            delay = client._calculate_retry_delay(5)
            assert delay == 15.0


class TestFigmaClientErrorHandling:
    """エラーハンドリングのテスト"""

    @pytest.fixture
    def client(self) -> Generator[FigmaClient]:
        """テスト用クライアント"""
        client = FigmaClient(token="test-token", max_retries=0)
        yield client
        client.close()

    def test_authentication_error_401(self, client: FigmaClient) -> None:
        """401 認証エラー"""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 401

        with pytest.raises(FigmaAuthenticationError):
            client._handle_response_error(response)

    def test_authentication_error_403(self, client: FigmaClient) -> None:
        """403 認証エラー"""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 403

        with pytest.raises(FigmaAuthenticationError):
            client._handle_response_error(response)

    def test_file_not_found_error(self, client: FigmaClient) -> None:
        """404 ファイル未存在エラー"""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 404

        with pytest.raises(FigmaFileNotFoundError) as exc_info:
            client._handle_response_error(response, file_id="abc123")

        assert exc_info.value.file_id == "abc123"
        assert "abc123" in str(exc_info.value)

    def test_rate_limit_error(self, client: FigmaClient) -> None:
        """429 レート制限エラー"""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 429
        response.headers = {"Retry-After": "60"}

        with pytest.raises(FigmaRateLimitError) as exc_info:
            client._handle_response_error(response)

        assert exc_info.value.retry_after == 60

    def test_server_error(self, client: FigmaClient) -> None:
        """5xx サーバーエラー"""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 503

        with pytest.raises(FigmaServerError) as exc_info:
            client._handle_response_error(response)

        assert exc_info.value.status_code == 503

    def test_generic_api_error(self, client: FigmaClient) -> None:
        """その他の API エラー"""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 400
        response.json.return_value = {"err": "Bad request"}

        with pytest.raises(FigmaAPIError) as exc_info:
            client._handle_response_error(response)

        assert exc_info.value.status_code == 400
        assert "Bad request" in str(exc_info.value)


class TestFigmaClientGetFile:
    """get_file メソッドのテスト"""

    def test_get_file_success(self) -> None:
        """正常取得"""
        with patch.object(FigmaClient, "_request_with_retry") as mock_request:
            mock_response = MagicMock(spec=httpx.Response)
            mock_response.json.return_value = {
                "name": "Test File",
                "document": {"id": "0:0", "name": "Document"},
            }
            mock_request.return_value = mock_response

            client = FigmaClient(token="test-token")
            result = client.get_file("file123")

            assert result["name"] == "Test File"
            mock_request.assert_called_once_with("GET", "/files/file123", file_id="file123")
            client.close()

    def test_get_file_validates_file_id(self) -> None:
        """file_id のバリデーション"""
        client = FigmaClient(token="test-token")

        with pytest.raises(InvalidFileIdError):
            client.get_file("")

        with pytest.raises(InvalidFileIdError):
            client.get_file("../etc/passwd")

        with pytest.raises(InvalidFileIdError):
            client.get_file("file/with/slash")

        client.close()


class TestFigmaClientRetry:
    """リトライロジックのテスト"""

    def test_retry_on_server_error(self) -> None:
        """サーバーエラー時のリトライ"""
        with FigmaClient(token="test-token", max_retries=2, retry_base_delay=0.01) as client:
            with patch.object(client._client, "request") as mock_request:
                # 1回目: 503、2回目: 200
                error_response = MagicMock(spec=httpx.Response)
                error_response.status_code = 503
                error_response.is_success = False
                error_response.headers = {}

                success_response = MagicMock(spec=httpx.Response)
                success_response.status_code = 200
                success_response.is_success = True
                success_response.json.return_value = {"name": "Test"}

                mock_request.side_effect = [error_response, success_response]

                result = client._request_with_retry("GET", "/files/test")
                assert result.json()["name"] == "Test"
                assert mock_request.call_count == 2

    def test_retry_exhausted(self) -> None:
        """リトライ回数超過"""
        with FigmaClient(token="test-token", max_retries=1, retry_base_delay=0.01) as client:
            with patch.object(client._client, "request") as mock_request:
                error_response = MagicMock(spec=httpx.Response)
                error_response.status_code = 503
                error_response.is_success = False
                error_response.headers = {}

                mock_request.return_value = error_response

                with pytest.raises(FigmaServerError):
                    client._request_with_retry("GET", "/files/test")

                assert mock_request.call_count == 2  # 初回 + 1回リトライ

    def test_no_retry_on_client_error(self) -> None:
        """クライアントエラー（4xx）はリトライしない"""
        with FigmaClient(token="test-token", max_retries=3, retry_base_delay=0.01) as client:
            with patch.object(client._client, "request") as mock_request:
                error_response = MagicMock(spec=httpx.Response)
                error_response.status_code = 400
                error_response.is_success = False
                error_response.json.return_value = {"err": "Bad request"}

                mock_request.return_value = error_response

                with pytest.raises(FigmaAPIError):
                    client._request_with_retry("GET", "/files/test")

                assert mock_request.call_count == 1  # リトライなし

    def test_retry_on_timeout(self) -> None:
        """タイムアウト時のリトライ"""
        with FigmaClient(token="test-token", max_retries=2, retry_base_delay=0.01) as client:
            with patch.object(client._client, "request") as mock_request:
                success_response = MagicMock(spec=httpx.Response)
                success_response.status_code = 200
                success_response.is_success = True
                success_response.json.return_value = {"name": "Test"}

                mock_request.side_effect = [
                    httpx.TimeoutException("Timeout"),
                    success_response,
                ]

                result = client._request_with_retry("GET", "/files/test")
                assert result.json()["name"] == "Test"
                assert mock_request.call_count == 2


class TestFigmaExceptions:
    """例外クラスのテスト"""

    def test_figma_api_error(self) -> None:
        """FigmaAPIError 基本テスト"""
        error = FigmaAPIError("Test error", status_code=400)
        assert str(error) == "Test error"
        assert error.status_code == 400

    def test_figma_authentication_error(self) -> None:
        """FigmaAuthenticationError テスト"""
        error = FigmaAuthenticationError()
        assert "token" in str(error).lower()
        assert error.status_code == 401

    def test_figma_file_not_found_error(self) -> None:
        """FigmaFileNotFoundError テスト"""
        error = FigmaFileNotFoundError("abc123")
        assert error.file_id == "abc123"
        assert "abc123" in str(error)
        assert error.status_code == 404

    def test_figma_rate_limit_error(self) -> None:
        """FigmaRateLimitError テスト"""
        error = FigmaRateLimitError(retry_after=30)
        assert error.retry_after == 30
        assert "30" in str(error)
        assert error.status_code == 429

    def test_figma_server_error(self) -> None:
        """FigmaServerError テスト"""
        error = FigmaServerError(503)
        assert error.status_code == 503
