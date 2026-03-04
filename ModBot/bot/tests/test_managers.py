import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from twitch.manager import TwitchBotManager
from discord.manager import DiscordBotManager


class TestTwitchBotManager:
    def test_get_bot_not_found(self):
        manager = TwitchBotManager("http://fake:8000")
        assert manager.get_bot("nonexistent") is None

    @pytest.mark.asyncio
    async def test_sync_creates_bots(self):
        manager = TwitchBotManager("http://fake:8000")
        api_data = [
            {
                "id": 1,
                "channel_name": "streamer1",
                "plan": "pro",
                "mod_action": "timeout",
                "timeout_seconds": 600,
                "toxicity_threshold": 0.8,
                "ai_enabled": True,
            }
        ]

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=api_data)

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_resp),
            __aexit__=AsyncMock(return_value=False),
        ))

        with patch("twitch.manager.aiohttp.ClientSession", return_value=mock_session):
            result = await manager.sync_from_api()

        to_join, to_part = result
        assert "streamer1" in to_join
        assert manager.get_bot("streamer1") is not None
        assert manager.get_bot("streamer1").ai_enabled is True

    @pytest.mark.asyncio
    async def test_sync_removes_inactive(self):
        manager = TwitchBotManager("http://fake:8000")
        # Manually add a bot
        from twitch.channel_bot import TwitchChannelBot
        manager.channels["old_channel"] = TwitchChannelBot(channel_id=99, channel_name="old_channel")

        # API returns empty = no active channels
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=[])

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_resp),
            __aexit__=AsyncMock(return_value=False),
        ))

        with patch("twitch.manager.aiohttp.ClientSession", return_value=mock_session):
            result = await manager.sync_from_api()

        _, to_part = result
        assert "old_channel" in to_part
        assert manager.get_bot("old_channel") is None

    @pytest.mark.asyncio
    async def test_sync_api_error(self):
        manager = TwitchBotManager("http://fake:8000")

        mock_resp = AsyncMock()
        mock_resp.status = 500

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_resp),
            __aexit__=AsyncMock(return_value=False),
        ))

        with patch("twitch.manager.aiohttp.ClientSession", return_value=mock_session):
            result = await manager.sync_from_api()
        assert result == []


class TestDiscordBotManager:
    def test_get_bot_not_found(self):
        manager = DiscordBotManager("http://fake:8000")
        assert manager.get_bot("nonexistent") is None

    @pytest.mark.asyncio
    async def test_sync_creates_guild_bots(self):
        manager = DiscordBotManager("http://fake:8000")
        api_data = [
            {
                "id": 1,
                "discord_guild_id": "guild_123",
                "channel_name": "MyServer",
                "plan": "free",
                "mod_action": "delete",
                "timeout_seconds": 300,
                "toxicity_threshold": 0.5,
                "ai_enabled": False,
                "discord_channel_ids": ["ch1", "ch2"],
            }
        ]

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=api_data)

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_resp),
            __aexit__=AsyncMock(return_value=False),
        ))

        with patch("discord.manager.aiohttp.ClientSession", return_value=mock_session):
            await manager.sync_from_api()

        bot = manager.get_bot("guild_123")
        assert bot is not None
        assert bot.ai_enabled is False
        assert bot.mod_action == "delete"
        assert bot.monitored_channel_ids == {"ch1", "ch2"}

    @pytest.mark.asyncio
    async def test_sync_removes_inactive_guilds(self):
        manager = DiscordBotManager("http://fake:8000")
        from discord.guild_bot import DiscordGuildBot
        manager.guilds["old_guild"] = DiscordGuildBot(
            channel_id=99, guild_id="old_guild", guild_name="Old"
        )

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=[])

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_resp),
            __aexit__=AsyncMock(return_value=False),
        ))

        with patch("discord.manager.aiohttp.ClientSession", return_value=mock_session):
            await manager.sync_from_api()

        assert manager.get_bot("old_guild") is None
