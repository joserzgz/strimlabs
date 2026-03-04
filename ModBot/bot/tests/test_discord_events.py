import pytest
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock
from discord.guild_bot import DiscordGuildBot


def make_guild_bot(**kwargs):
    defaults = {
        "channel_id": 1,
        "guild_id": "guild_123",
        "guild_name": "TestGuild",
        "plan": "free",
        "mod_action": "timeout",
        "timeout_seconds": 600,
        "toxicity_threshold": 0.8,
        "ai_enabled": True,
    }
    defaults.update(kwargs)
    return DiscordGuildBot(**defaults)


def make_discord_message(content="hello", is_bot=False, guild_id="guild_123", channel_id="ch_1"):
    msg = MagicMock()
    msg.content = content
    msg.author.bot = is_bot
    msg.author.__str__ = lambda self: "testuser#1234"
    msg.guild = MagicMock()
    msg.guild.id = int(guild_id) if guild_id.isdigit() else 123
    msg.guild.__str__ = lambda self: guild_id
    type(msg.guild).id = PropertyMock(return_value=int(guild_id) if guild_id.isdigit() else 123)
    msg.channel.id = int(channel_id.replace("ch_", "")) if channel_id.startswith("ch_") else 1
    msg.delete = AsyncMock()
    msg.guild.ban = AsyncMock()
    msg.author.timeout = AsyncMock()
    return msg


class TestOnMessage:
    @pytest.mark.asyncio
    async def test_ignores_bot_messages(self):
        from discord.main import on_message
        msg = make_discord_message(is_bot=True)
        # Should return early without error
        await on_message(msg)

    @pytest.mark.asyncio
    async def test_ignores_dms(self):
        from discord.main import on_message
        msg = make_discord_message()
        msg.guild = None
        await on_message(msg)

    @pytest.mark.asyncio
    async def test_ai_disabled_skips_perspective(self):
        from discord.main import on_message, manager

        guild_bot = make_guild_bot(ai_enabled=False)
        from moderation.shared import compile_blacklist
        guild_bot.compiled_blacklist = compile_blacklist()
        manager.guilds["123"] = guild_bot

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

        msg = make_discord_message(content="hello world", guild_id="123")

        with patch("discord.main.aiohttp.ClientSession", return_value=mock_session):
            with patch("discord.main.check_perspective_api") as mock_perspective:
                await on_message(msg)
                mock_perspective.assert_not_called()

        del manager.guilds["123"]

    @pytest.mark.asyncio
    async def test_ai_enabled_calls_perspective(self):
        from discord.main import on_message, manager

        guild_bot = make_guild_bot(ai_enabled=True)
        from moderation.shared import compile_blacklist
        guild_bot.compiled_blacklist = compile_blacklist()
        manager.guilds["123"] = guild_bot

        mock_quota_resp = AsyncMock()
        mock_quota_resp.json = AsyncMock(return_value={"allowed": True})
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_quota_resp),
            __aexit__=AsyncMock(return_value=False),
        ))

        msg = make_discord_message(content="hello world", guild_id="123")

        with patch("discord.main.aiohttp.ClientSession", return_value=mock_session):
            with patch("discord.main.check_perspective_api", return_value=(False, 0.1)) as mock_perspective:
                await on_message(msg)
                mock_perspective.assert_called_once()

        del manager.guilds["123"]
