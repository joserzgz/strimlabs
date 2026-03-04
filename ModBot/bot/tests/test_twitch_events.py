import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from twitch.channel_bot import TwitchChannelBot


def make_bot(**kwargs):
    defaults = {
        "channel_id": 1,
        "channel_name": "test_ch",
        "plan": "free",
        "mod_action": "timeout",
        "timeout_seconds": 600,
        "toxicity_threshold": 0.8,
        "ai_enabled": True,
    }
    defaults.update(kwargs)
    return TwitchChannelBot(**defaults)


def make_message(content="hello", author_name="viewer", channel_name="test_ch", echo=False):
    msg = MagicMock()
    msg.echo = echo
    msg.content = content
    msg.channel.name = channel_name
    msg.author.name = author_name
    msg.delete = AsyncMock()
    msg.channel.timeout = AsyncMock()
    msg.channel.ban = AsyncMock()
    return msg


class TestEventMessage:
    @pytest.mark.asyncio
    async def test_ignores_echo(self):
        from twitch.main import ModBot
        bot_instance = ModBot()
        msg = make_message(echo=True)
        # Should return early without error
        await bot_instance.event_message(msg)

    @pytest.mark.asyncio
    async def test_skips_if_no_bot(self):
        from twitch.main import ModBot, manager
        bot_instance = ModBot()
        msg = make_message(channel_name="unknown_channel")
        # No bot registered for this channel
        await bot_instance.event_message(msg)

    @pytest.mark.asyncio
    async def test_blacklist_triggers_action(self):
        from twitch.main import ModBot, manager
        bot_instance = ModBot()
        bot_instance._take_action = AsyncMock()

        channel_bot = make_bot()
        from moderation.shared import compile_blacklist
        channel_bot.compiled_blacklist = compile_blacklist([r"\bspam\b"])
        manager.channels["test_ch"] = channel_bot

        # Mock quota check
        mock_quota_resp = AsyncMock()
        mock_quota_resp.json = AsyncMock(return_value={"allowed": True})
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_quota_resp),
            __aexit__=AsyncMock(return_value=False),
        ))

        msg = make_message(content="this is spam")

        with patch("twitch.main.aiohttp.ClientSession", return_value=mock_session):
            await bot_instance.event_message(msg)

        bot_instance._take_action.assert_called_once()
        call_args = bot_instance._take_action.call_args
        assert call_args[0][2] == "blacklist"

        # Cleanup
        del manager.channels["test_ch"]

    @pytest.mark.asyncio
    async def test_ai_disabled_skips_perspective(self):
        from twitch.main import ModBot, manager
        bot_instance = ModBot()
        bot_instance._take_action = AsyncMock()

        channel_bot = make_bot(ai_enabled=False)
        from moderation.shared import compile_blacklist
        channel_bot.compiled_blacklist = compile_blacklist()
        manager.channels["test_ch"] = channel_bot

        # Mock quota
        mock_quota_resp = AsyncMock()
        mock_quota_resp.json = AsyncMock(return_value={"allowed": True})
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_quota_resp),
            __aexit__=AsyncMock(return_value=False),
        ))

        msg = make_message(content="hello world")

        with patch("twitch.main.aiohttp.ClientSession", return_value=mock_session):
            with patch("twitch.main.check_perspective_api") as mock_perspective:
                await bot_instance.event_message(msg)
                mock_perspective.assert_not_called()

        del manager.channels["test_ch"]

    @pytest.mark.asyncio
    async def test_ai_enabled_calls_perspective(self):
        from twitch.main import ModBot, manager
        bot_instance = ModBot()
        bot_instance._take_action = AsyncMock()

        channel_bot = make_bot(ai_enabled=True)
        from moderation.shared import compile_blacklist
        channel_bot.compiled_blacklist = compile_blacklist()
        manager.channels["test_ch"] = channel_bot

        # Mock quota
        mock_quota_resp = AsyncMock()
        mock_quota_resp.json = AsyncMock(return_value={"allowed": True})
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_quota_resp),
            __aexit__=AsyncMock(return_value=False),
        ))

        msg = make_message(content="hello world")

        with patch("twitch.main.aiohttp.ClientSession", return_value=mock_session):
            with patch("twitch.main.check_perspective_api", return_value=(False, 0.1)) as mock_perspective:
                await bot_instance.event_message(msg)
                mock_perspective.assert_called_once()

        del manager.channels["test_ch"]

    @pytest.mark.asyncio
    async def test_quota_denied_skips_moderation(self):
        from twitch.main import ModBot, manager
        bot_instance = ModBot()
        bot_instance._take_action = AsyncMock()

        channel_bot = make_bot()
        from moderation.shared import compile_blacklist
        channel_bot.compiled_blacklist = compile_blacklist([r"\bspam\b"])
        manager.channels["test_ch"] = channel_bot

        # Mock quota denied
        mock_quota_resp = AsyncMock()
        mock_quota_resp.json = AsyncMock(return_value={"allowed": False})
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_quota_resp),
            __aexit__=AsyncMock(return_value=False),
        ))

        msg = make_message(content="this is spam")

        with patch("twitch.main.aiohttp.ClientSession", return_value=mock_session):
            await bot_instance.event_message(msg)

        bot_instance._take_action.assert_not_called()

        del manager.channels["test_ch"]
