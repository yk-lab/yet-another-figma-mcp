"""Figma API 関連の例外クラス"""


class FigmaAPIError(Exception):
    """Figma API エラーの基底クラス"""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """例外を初期化"""
        super().__init__(message)
        self.status_code = status_code


class FigmaAuthenticationError(FigmaAPIError):
    """認証エラー（401/403）"""

    def __init__(self, message: str = "Invalid or missing Figma API token") -> None:
        """認証エラーを初期化"""
        super().__init__(message, status_code=401)


class FigmaFileNotFoundError(FigmaAPIError):
    """ファイル未存在エラー（404）"""

    def __init__(self, file_id: str) -> None:
        """ファイル未存在エラーを初期化"""
        super().__init__(f"Figma file not found: {file_id}", status_code=404)
        self.file_id = file_id


class FigmaRateLimitError(FigmaAPIError):
    """レート制限エラー（429）"""

    def __init__(self, retry_after: int | None = None) -> None:
        """レート制限エラーを初期化"""
        message = "Rate limit exceeded"
        if retry_after:
            message += f", retry after {retry_after} seconds"
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class FigmaServerError(FigmaAPIError):
    """サーバーエラー（5xx）"""

    def __init__(self, status_code: int, message: str = "Figma API server error") -> None:
        """サーバーエラーを初期化"""
        super().__init__(message, status_code=status_code)
