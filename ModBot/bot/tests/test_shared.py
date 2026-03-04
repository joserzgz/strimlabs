import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from moderation.shared import normalize_text, compile_blacklist, blacklist_match, check_perspective_api


class TestNormalizeText:
    def test_lowercase(self):
        assert normalize_text("HELLO") == "hello"

    def test_leet_speak_numbers(self):
        result = normalize_text("h3ll0 w0rld")
        assert result == "hello world"

    def test_leet_speak_symbols(self):
        result = normalize_text("@$$h0l3")
        assert result == "asshole"

    def test_removes_separators(self):
        result = normalize_text("b.a.d.w.o.r.d")
        assert result == "badword"

    def test_removes_dashes_underscores(self):
        result = normalize_text("f-u-c-k")
        assert result == "fuck"

    def test_collapses_spaces(self):
        result = normalize_text("hello    world")
        assert result == "hello world"

    def test_strips_whitespace(self):
        result = normalize_text("  hello  ")
        assert result == "hello"

    def test_empty_string(self):
        assert normalize_text("") == ""

    def test_pipe_to_l(self):
        result = normalize_text("|ove")
        assert result == "love"


class TestCompileBlacklist:
    def test_returns_pattern_with_base(self):
        result = compile_blacklist()
        assert result is not None

    def test_includes_user_patterns(self):
        result = compile_blacklist(["custom_word"])
        assert result is not None
        assert result.search("custom_word") is not None

    def test_case_insensitive(self):
        result = compile_blacklist(["testpattern"])
        assert result.search("TESTPATTERN") is not None

    def test_empty_user_patterns_still_has_base(self):
        result = compile_blacklist([])
        assert result is not None


class TestBlacklistMatch:
    def test_match_base_pattern(self):
        compiled = compile_blacklist()
        result = blacklist_match("kys right now", compiled)
        assert result is not None

    def test_no_match_clean_text(self):
        compiled = compile_blacklist()
        result = blacklist_match("hello world how are you", compiled)
        assert result is None

    def test_match_with_leet_speak(self):
        compiled = compile_blacklist()
        result = blacklist_match("k1ll your self", compiled)
        assert result is not None

    def test_match_user_pattern(self):
        compiled = compile_blacklist([r"\bspam\b"])
        result = blacklist_match("this is spam", compiled)
        assert result is not None

    def test_none_pattern_returns_none(self):
        assert blacklist_match("anything", None) is None

    def test_raw_text_fallback(self):
        compiled = compile_blacklist([r"\bKYS\b"])
        result = blacklist_match("KYS", compiled)
        assert result is not None


class TestCheckPerspectiveApi:
    @pytest.mark.asyncio
    async def test_no_api_key_returns_false(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PERSPECTIVE_API_KEY", None)
            flagged, score = await check_perspective_api("test", 0.8)
            assert flagged is False
            assert score == 0.0

    @pytest.mark.asyncio
    async def test_high_score_flagged(self):
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={
            "attributeScores": {
                "TOXICITY": {
                    "summaryScore": {"value": 0.95}
                }
            }
        })

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_resp),
            __aexit__=AsyncMock(return_value=False),
        ))

        with patch.dict(os.environ, {"PERSPECTIVE_API_KEY": "test-key"}):
            with patch("moderation.shared.aiohttp.ClientSession", return_value=mock_session):
                flagged, score = await check_perspective_api("toxic text", 0.8)
                assert flagged is True
                assert score == 0.95

    @pytest.mark.asyncio
    async def test_low_score_not_flagged(self):
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={
            "attributeScores": {
                "TOXICITY": {
                    "summaryScore": {"value": 0.2}
                }
            }
        })

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_resp),
            __aexit__=AsyncMock(return_value=False),
        ))

        with patch.dict(os.environ, {"PERSPECTIVE_API_KEY": "test-key"}):
            with patch("moderation.shared.aiohttp.ClientSession", return_value=mock_session):
                flagged, score = await check_perspective_api("nice text", 0.8)
                assert flagged is False
                assert score == 0.2

    @pytest.mark.asyncio
    async def test_api_error_returns_false(self):
        mock_resp = AsyncMock()
        mock_resp.status = 500

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.post = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_resp),
            __aexit__=AsyncMock(return_value=False),
        ))

        with patch.dict(os.environ, {"PERSPECTIVE_API_KEY": "test-key"}):
            with patch("moderation.shared.aiohttp.ClientSession", return_value=mock_session):
                flagged, score = await check_perspective_api("text", 0.8)
                assert flagged is False
                assert score == 0.0

    @pytest.mark.asyncio
    async def test_network_exception_returns_false(self):
        with patch.dict(os.environ, {"PERSPECTIVE_API_KEY": "test-key"}):
            with patch("moderation.shared.aiohttp.ClientSession", side_effect=Exception("network error")):
                flagged, score = await check_perspective_api("text", 0.8)
                assert flagged is False
                assert score == 0.0
