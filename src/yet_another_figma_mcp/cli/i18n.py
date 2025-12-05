"""CLI i18n (internationalization) support

Simple dict-based i18n for CLI messages.
Supports English (default) and Japanese.
"""

import locale
import os
from typing import Any

# Supported languages
SUPPORTED_LANGUAGES = ("en", "ja")
DEFAULT_LANGUAGE = "en"

# Current language (module-level state)
_current_language: str = DEFAULT_LANGUAGE


def get_system_language() -> str:
    """Detect system language from environment

    Checks in order:
    1. YAFM_LANG environment variable (app-specific)
    2. LANG environment variable
    3. System locale

    Returns:
        Language code ("ja" or "en")
    """
    # 1. App-specific environment variable
    app_lang = os.environ.get("YAFM_LANG", "").lower()
    if app_lang:
        if app_lang.startswith("ja"):
            return "ja"
        if app_lang.startswith("en"):
            return "en"

    # 2. LANG environment variable
    lang_env = os.environ.get("LANG", "").lower()
    if lang_env:
        if lang_env.startswith("ja"):
            return "ja"
        if lang_env.startswith("en"):
            return "en"

    # 3. System locale (use getlocale instead of deprecated getdefaultlocale)
    try:
        system_locale = locale.getlocale()[0] or ""
        system_locale_lower = system_locale.lower()
        if system_locale_lower.startswith("ja"):
            return "ja"
        if system_locale_lower.startswith("en"):
            return "en"
    except (ValueError, TypeError):
        pass

    return DEFAULT_LANGUAGE


def set_language(lang: str) -> None:
    """Set current language

    If an unsupported language is provided, the language is forcibly
    set to DEFAULT_LANGUAGE (not kept at the current value).

    Args:
        lang: Language code ("ja" or "en")
    """
    global _current_language
    if lang in SUPPORTED_LANGUAGES:
        _current_language = lang
    else:
        _current_language = DEFAULT_LANGUAGE


def get_language() -> str:
    """Get current language

    Returns:
        Current language code
    """
    return _current_language


def init_language() -> None:
    """Initialize language from system settings"""
    set_language(get_system_language())


# Message catalog
# Format: MESSAGES[key][language] = message
MESSAGES: dict[str, dict[str, str]] = {
    # ============================================================
    # app.py - CLI application
    # ============================================================
    "app.help": {
        "ja": "YetAnotherFigmaMCP - Figma ファイルキャッシュ MCP サーバー",
        "en": "YetAnotherFigmaMCP - Figma file cache MCP server",
    },
    "app.version_help": {
        "ja": "バージョン情報を表示",
        "en": "Show version information",
    },
    # ============================================================
    # cache.py - cache command
    # ============================================================
    "cache.help": {
        "ja": "Figma ファイルのキャッシュを生成",
        "en": "Generate cache for Figma files",
    },
    "cache.file_id_help": {
        "ja": "Figma ファイル ID（複数指定可）",
        "en": "Figma file ID (can specify multiple)",
    },
    "cache.file_id_list_help": {
        "ja": "ファイル ID 一覧を記述したテキストファイル",
        "en": "Text file containing list of file IDs",
    },
    "cache.refresh_help": {
        "ja": "キャッシュを強制的に更新",
        "en": "Force refresh cache",
    },
    "cache.cache_dir_help": {
        "ja": "キャッシュディレクトリ",
        "en": "Cache directory",
    },
    "cache.invalid_file_id": {
        "ja": "{file_id}: 無効なファイル ID - {error}",
        "en": "{file_id}: Invalid file ID - {error}",
    },
    "cache.already_cached": {
        "ja": "{file_id}: キャッシュ済み（--refresh で更新）",
        "en": "{file_id}: Already cached (use --refresh to update)",
    },
    "cache.fetching": {
        "ja": "{file_id}: Figma API から取得中...",
        "en": "{file_id}: Fetching from Figma API...",
    },
    "cache.auth_error": {
        "ja": "{file_id}: 認証エラー - API トークンを確認してください",
        "en": "{file_id}: Authentication error - Please check your API token",
    },
    "cache.not_found": {
        "ja": "{file_id}: ファイルが見つかりません",
        "en": "{file_id}: File not found",
    },
    "cache.rate_limit": {
        "ja": "{file_id}: レート制限{retry_msg}",
        "en": "{file_id}: Rate limited{retry_msg}",
    },
    "cache.rate_limit_retry": {
        "ja": "（{seconds}秒後に再試行）",
        "en": " (retry after {seconds} seconds)",
    },
    "cache.api_error": {
        "ja": "{file_id}: API エラー - {error}",
        "en": "{file_id}: API error - {error}",
    },
    "cache.saving": {
        "ja": "{file_id}: ファイルを保存中...",
        "en": "{file_id}: Saving file...",
    },
    "cache.indexing": {
        "ja": "{file_id}: インデックスを生成中...",
        "en": "{file_id}: Generating index...",
    },
    "cache.file_list_read_error": {
        "ja": "エラー: ファイルリストの読み込みに失敗しました（UTF-8 でエンコードしてください）",
        "en": "Error: Failed to read file list (please encode in UTF-8)",
    },
    "cache.no_file_id": {
        "ja": "エラー: ファイル ID を指定してください",
        "en": "Error: Please specify a file ID",
    },
    "cache.usage_example": {
        "ja": "使用例: yet-another-figma-mcp cache -f <file_id>",
        "en": "Usage: yet-another-figma-mcp cache -f <file_id>",
    },
    "cache.cache_dir_label": {
        "ja": "キャッシュ先:",
        "en": "Cache directory:",
    },
    "cache.target_files_label": {
        "ja": "対象ファイル数:",
        "en": "Target files:",
    },
    "cache.complete_all_success": {
        "ja": "完了: {count} ファイルをキャッシュしました",
        "en": "Complete: Cached {count} file(s)",
    },
    "cache.complete_with_failures": {
        "ja": "完了: {success} 成功, {fail} 失敗",
        "en": "Complete: {success} succeeded, {fail} failed",
    },
    # ============================================================
    # serve.py - serve command
    # ============================================================
    "serve.help": {
        "ja": "MCP サーバーを起動 (stdio モード)",
        "en": "Start MCP server (stdio mode)",
    },
    "serve.verbose_help": {
        "ja": "詳細ログを出力（DEBUG レベル）",
        "en": "Enable verbose logging (DEBUG level)",
    },
    "serve.starting": {
        "ja": "MCP サーバーを起動中...",
        "en": "Starting MCP server...",
    },
    "serve.cache_dir": {
        "ja": "キャッシュディレクトリ: {path}",
        "en": "Cache directory: {path}",
    },
    "serve.sigterm_received": {
        "ja": "SIGTERM を受信しました",
        "en": "Received SIGTERM",
    },
    "serve.server_stopped": {
        "ja": "サーバーを終了しました",
        "en": "Server stopped",
    },
    # ============================================================
    # status.py - status command
    # ============================================================
    "status.help": {
        "ja": "キャッシュ済みファイルの一覧と状態を表示",
        "en": "Show list and status of cached files",
    },
    "status.json_help": {
        "ja": "JSON 形式で出力",
        "en": "Output in JSON format",
    },
    "status.no_cache_found": {
        "ja": "キャッシュが見つかりません: {path}",
        "en": "No cache found: {path}",
    },
    "status.table_title": {
        "ja": "キャッシュ済みファイル（{path}）",
        "en": "Cached files ({path})",
    },
    "status.total_files": {
        "ja": "合計: {count} ファイル",
        "en": "Total: {count} file(s)",
    },
}


def t(key: str, **kwargs: Any) -> str:
    """Translate message by key

    Falls back to DEFAULT_LANGUAGE if the current language has no translation,
    and returns the key itself if no translation exists at all.

    Args:
        key: Message key (e.g., "cache.fetching")
        **kwargs: Format arguments for the message

    Returns:
        Translated and formatted message, or the key string as fallback

    Example:
        >>> t("cache.fetching", file_id="abc123")
        "abc123: Figma API から取得中..."
    """
    lang = _current_language

    if key not in MESSAGES:
        # Fallback: return key itself if not found
        return key

    msg_dict = MESSAGES[key]
    if lang not in msg_dict:
        # Fallback to default language
        lang = DEFAULT_LANGUAGE

    if lang not in msg_dict:
        # Last resort: return key
        return key

    message = msg_dict[lang]

    if kwargs:
        try:
            return message.format(**kwargs)
        except KeyError:
            # If format fails, return unformatted message
            return message

    return message
