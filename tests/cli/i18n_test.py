"""Tests for CLI i18n module"""

import os
from unittest.mock import patch

import pytest


class TestI18nBasics:
    """Basic i18n functionality tests"""

    def test_t_returns_japanese_by_default(self) -> None:
        """Test that t() returns Japanese message by default"""
        # Fresh import to reset state
        from yet_another_figma_mcp.cli import i18n

        i18n.set_language("ja")
        result = i18n.t("cache.fetching", file_id="abc123")
        assert "Figma API から取得中" in result
        assert "abc123" in result

    def test_t_returns_english_when_set(self) -> None:
        """Test that t() returns English message when language is set to en"""
        from yet_another_figma_mcp.cli import i18n

        i18n.set_language("en")
        result = i18n.t("cache.fetching", file_id="abc123")
        assert "Fetching from Figma API" in result
        assert "abc123" in result
        # Reset to default
        i18n.set_language("ja")

    def test_t_with_format_args(self) -> None:
        """Test that t() formats messages with arguments"""
        from yet_another_figma_mcp.cli import i18n

        i18n.set_language("ja")
        result = i18n.t("cache.complete_with_failures", success=5, fail=2)
        assert "5" in result
        assert "2" in result

    def test_t_returns_key_for_unknown_key(self) -> None:
        """Test that t() returns the key itself for unknown keys"""
        from yet_another_figma_mcp.cli import i18n

        result = i18n.t("unknown.key.here")
        assert result == "unknown.key.here"

    def test_set_language_ignores_unsupported(self) -> None:
        """Test that set_language ignores unsupported languages"""
        from yet_another_figma_mcp.cli import i18n

        i18n.set_language("ja")
        i18n.set_language("fr")  # Unsupported
        assert i18n.get_language() == "ja"  # Should fall back to default


class TestLanguageDetection:
    """Tests for language detection from environment"""

    def test_get_system_language_from_yafm_lang_ja(self) -> None:
        """Test YAFM_LANG=ja detection"""
        from yet_another_figma_mcp.cli import i18n

        with patch.dict(os.environ, {"YAFM_LANG": "ja_JP.UTF-8"}, clear=False):
            result = i18n.get_system_language()
            assert result == "ja"

    def test_get_system_language_from_yafm_lang_en(self) -> None:
        """Test YAFM_LANG=en detection"""
        from yet_another_figma_mcp.cli import i18n

        with patch.dict(os.environ, {"YAFM_LANG": "en_US.UTF-8"}, clear=False):
            result = i18n.get_system_language()
            assert result == "en"

    def test_get_system_language_from_lang_env(self) -> None:
        """Test LANG environment variable detection"""
        from yet_another_figma_mcp.cli import i18n

        with patch.dict(os.environ, {"LANG": "en_US.UTF-8", "YAFM_LANG": ""}, clear=False):
            result = i18n.get_system_language()
            assert result == "en"

    def test_yafm_lang_takes_priority_over_lang(self) -> None:
        """Test that YAFM_LANG takes priority over LANG"""
        from yet_another_figma_mcp.cli import i18n

        with patch.dict(os.environ, {"YAFM_LANG": "en", "LANG": "ja_JP.UTF-8"}, clear=False):
            result = i18n.get_system_language()
            assert result == "en"


class TestMessageCatalog:
    """Tests for message catalog completeness"""

    def test_all_messages_have_both_languages(self) -> None:
        """Test that all messages have both ja and en translations"""
        from yet_another_figma_mcp.cli.i18n import MESSAGES

        for key, translations in MESSAGES.items():
            assert "ja" in translations, f"Missing Japanese translation for {key}"
            assert "en" in translations, f"Missing English translation for {key}"

    def test_all_messages_are_non_empty(self) -> None:
        """Test that all messages are non-empty strings"""
        from yet_another_figma_mcp.cli.i18n import MESSAGES

        for key, translations in MESSAGES.items():
            for lang, message in translations.items():
                assert isinstance(message, str), f"{key}[{lang}] is not a string"
                assert len(message) > 0, f"{key}[{lang}] is empty"

    @pytest.mark.parametrize(
        "key",
        [
            "app.help",
            "app.version_help",
            "cache.help",
            "cache.file_id_help",
            "cache.fetching",
            "cache.auth_error",
            "cache.complete_all_success",
            "serve.starting",
            "serve.server_stopped",
            "status.no_cache_found",
            "status.total_files",
        ],
    )
    def test_key_messages_exist(self, key: str) -> None:
        """Test that key messages exist in the catalog"""
        from yet_another_figma_mcp.cli.i18n import MESSAGES

        assert key in MESSAGES, f"Missing message key: {key}"


class TestFormatArgs:
    """Tests for message format argument handling"""

    def test_missing_format_arg_returns_unformatted(self) -> None:
        """Test that missing format args don't raise errors"""
        from yet_another_figma_mcp.cli import i18n

        i18n.set_language("ja")
        # cache.fetching expects {file_id}
        result = i18n.t("cache.fetching")  # No file_id provided
        # Should return the unformatted message without raising
        assert "{file_id}" in result

    def test_extra_format_args_ignored(self) -> None:
        """Test that extra format args are ignored"""
        from yet_another_figma_mcp.cli import i18n

        i18n.set_language("ja")
        result = i18n.t("cache.fetching", file_id="abc", extra_arg="ignored")
        assert "abc" in result
