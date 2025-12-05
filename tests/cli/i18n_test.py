"""Tests for CLI i18n module"""

import pytest
from pytest_mock import MockerFixture


class TestI18nBasics:
    """Basic i18n functionality tests"""

    def test_t_returns_japanese_by_default(self) -> None:
        """Test that t() returns Japanese message by default"""
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

    def test_get_system_language_from_yafm_lang_ja(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test YAFM_LANG=ja detection"""
        from yet_another_figma_mcp.cli import i18n

        monkeypatch.setenv("YAFM_LANG", "ja_JP.UTF-8")
        result = i18n.get_system_language()
        assert result == "ja"

    def test_get_system_language_from_yafm_lang_en(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test YAFM_LANG=en detection"""
        from yet_another_figma_mcp.cli import i18n

        monkeypatch.setenv("YAFM_LANG", "en_US.UTF-8")
        result = i18n.get_system_language()
        assert result == "en"

    def test_get_system_language_from_lang_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test LANG environment variable detection"""
        from yet_another_figma_mcp.cli import i18n

        monkeypatch.setenv("YAFM_LANG", "")
        monkeypatch.setenv("LANG", "en_US.UTF-8")
        result = i18n.get_system_language()
        assert result == "en"

    def test_yafm_lang_takes_priority_over_lang(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that YAFM_LANG takes priority over LANG"""
        from yet_another_figma_mcp.cli import i18n

        monkeypatch.setenv("YAFM_LANG", "en")
        monkeypatch.setenv("LANG", "ja_JP.UTF-8")
        result = i18n.get_system_language()
        assert result == "en"

    def test_get_system_language_from_locale_ja(
        self, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
    ) -> None:
        """Test system locale detection for Japanese"""
        from yet_another_figma_mcp.cli import i18n

        monkeypatch.setenv("YAFM_LANG", "")
        monkeypatch.setenv("LANG", "")
        mocker.patch(
            "yet_another_figma_mcp.cli.i18n.locale.getdefaultlocale",
            return_value=("ja_JP", "UTF-8"),
        )
        result = i18n.get_system_language()
        assert result == "ja"

    def test_get_system_language_from_locale_en(
        self, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
    ) -> None:
        """Test system locale detection for English"""
        from yet_another_figma_mcp.cli import i18n

        monkeypatch.setenv("YAFM_LANG", "")
        monkeypatch.setenv("LANG", "")
        mocker.patch(
            "yet_another_figma_mcp.cli.i18n.locale.getdefaultlocale",
            return_value=("en_US", "UTF-8"),
        )
        result = i18n.get_system_language()
        assert result == "en"

    def test_get_system_language_locale_returns_none(
        self, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
    ) -> None:
        """Test fallback when locale returns None"""
        from yet_another_figma_mcp.cli import i18n

        monkeypatch.setenv("YAFM_LANG", "")
        monkeypatch.setenv("LANG", "")
        mocker.patch(
            "yet_another_figma_mcp.cli.i18n.locale.getdefaultlocale",
            return_value=(None, None),
        )
        result = i18n.get_system_language()
        assert result == "ja"  # Default

    def test_get_system_language_locale_raises_error(
        self, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
    ) -> None:
        """Test fallback when locale raises ValueError"""
        from yet_another_figma_mcp.cli import i18n

        monkeypatch.setenv("YAFM_LANG", "")
        monkeypatch.setenv("LANG", "")
        mocker.patch(
            "yet_another_figma_mcp.cli.i18n.locale.getdefaultlocale",
            side_effect=ValueError("Invalid locale"),
        )
        result = i18n.get_system_language()
        assert result == "ja"  # Default

    def test_get_system_language_unsupported_locale(
        self, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
    ) -> None:
        """Test fallback for unsupported locale (e.g., French)"""
        from yet_another_figma_mcp.cli import i18n

        monkeypatch.setenv("YAFM_LANG", "")
        monkeypatch.setenv("LANG", "")
        mocker.patch(
            "yet_another_figma_mcp.cli.i18n.locale.getdefaultlocale",
            return_value=("fr_FR", "UTF-8"),
        )
        result = i18n.get_system_language()
        assert result == "ja"  # Default

    def test_get_system_language_lang_env_ja(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test LANG=ja detection"""
        from yet_another_figma_mcp.cli import i18n

        monkeypatch.setenv("YAFM_LANG", "")
        monkeypatch.setenv("LANG", "ja_JP.UTF-8")
        result = i18n.get_system_language()
        assert result == "ja"

    def test_get_system_language_unsupported_lang_env(
        self, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
    ) -> None:
        """Test fallback for unsupported LANG (falls through to locale)"""
        from yet_another_figma_mcp.cli import i18n

        monkeypatch.setenv("YAFM_LANG", "")
        monkeypatch.setenv("LANG", "fr_FR.UTF-8")
        mocker.patch(
            "yet_another_figma_mcp.cli.i18n.locale.getdefaultlocale",
            return_value=("fr_FR", "UTF-8"),
        )
        result = i18n.get_system_language()
        assert result == "ja"  # Default

    def test_get_system_language_unsupported_yafm_lang(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test fallback for unsupported YAFM_LANG (falls through to LANG)"""
        from yet_another_figma_mcp.cli import i18n

        monkeypatch.setenv("YAFM_LANG", "fr")
        monkeypatch.setenv("LANG", "en_US.UTF-8")
        result = i18n.get_system_language()
        assert result == "en"  # Falls through to LANG


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


class TestTFunctionFallback:
    """Tests for t() function fallback behavior"""

    def test_t_fallback_to_default_language(self, mocker: MockerFixture) -> None:
        """Test fallback to default language when current language missing"""
        from yet_another_figma_mcp.cli import i18n

        # Temporarily add a message with only Japanese
        mocker.patch.dict(i18n.MESSAGES, {"test.only_ja": {"ja": "日本語のみ"}})

        i18n.set_language("en")
        result = i18n.t("test.only_ja")
        # Should fall back to Japanese
        assert result == "日本語のみ"
        i18n.set_language("ja")

    def test_t_returns_key_when_no_translation(self, mocker: MockerFixture) -> None:
        """Test that t() returns key when no translation exists"""
        from yet_another_figma_mcp.cli import i18n

        # Temporarily add a message with no translations
        mocker.patch.dict(i18n.MESSAGES, {"test.empty": {}})

        result = i18n.t("test.empty")
        # Should return the key itself
        assert result == "test.empty"

    def test_t_handles_format_key_error(self, mocker: MockerFixture) -> None:
        """Test that t() handles KeyError during format gracefully"""
        from yet_another_figma_mcp.cli import i18n

        # Temporarily add a message with a format placeholder
        mocker.patch.dict(i18n.MESSAGES, {"test.format": {"ja": "Hello {name}, your ID is {id}"}})

        i18n.set_language("ja")
        # Only provide 'name', missing 'id' should cause KeyError
        result = i18n.t("test.format", name="World")
        # Should return unformatted message due to KeyError
        assert result == "Hello {name}, your ID is {id}"
