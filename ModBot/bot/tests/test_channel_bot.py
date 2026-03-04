from twitch.channel_bot import TwitchChannelBot
from discord.guild_bot import DiscordGuildBot


class TestTwitchChannelBot:
    def test_defaults(self):
        bot = TwitchChannelBot(channel_id=1, channel_name="test")
        assert bot.plan == "free"
        assert bot.mod_action == "timeout"
        assert bot.timeout_seconds == 600
        assert bot.toxicity_threshold == 0.8
        assert bot.ai_enabled is True
        assert bot.blacklist_patterns == []
        assert bot.compiled_blacklist is None

    def test_update_config(self):
        bot = TwitchChannelBot(channel_id=1, channel_name="test")
        bot.update_config({
            "plan": "pro",
            "mod_action": "ban",
            "timeout_seconds": 300,
            "toxicity_threshold": 0.5,
            "ai_enabled": False,
        })
        assert bot.plan == "pro"
        assert bot.mod_action == "ban"
        assert bot.timeout_seconds == 300
        assert bot.toxicity_threshold == 0.5
        assert bot.ai_enabled is False

    def test_update_config_partial(self):
        bot = TwitchChannelBot(channel_id=1, channel_name="test")
        bot.update_config({"mod_action": "delete"})
        assert bot.mod_action == "delete"
        # Others should stay at defaults
        assert bot.plan == "free"
        assert bot.ai_enabled is True

    def test_update_config_preserves_missing_fields(self):
        bot = TwitchChannelBot(channel_id=1, channel_name="test", ai_enabled=False)
        bot.update_config({})
        assert bot.ai_enabled is False


class TestDiscordGuildBot:
    def test_defaults(self):
        bot = DiscordGuildBot(channel_id=1, guild_id="123", guild_name="TestGuild")
        assert bot.plan == "free"
        assert bot.mod_action == "timeout"
        assert bot.ai_enabled is True
        assert bot.monitored_channel_ids is None

    def test_should_moderate_all_when_none(self):
        bot = DiscordGuildBot(channel_id=1, guild_id="123", guild_name="Test")
        assert bot.should_moderate_channel("any_id") is True

    def test_should_moderate_specific_channels(self):
        bot = DiscordGuildBot(
            channel_id=1, guild_id="123", guild_name="Test",
            monitored_channel_ids={"ch1", "ch2"},
        )
        assert bot.should_moderate_channel("ch1") is True
        assert bot.should_moderate_channel("ch3") is False

    def test_update_config(self):
        bot = DiscordGuildBot(channel_id=1, guild_id="123", guild_name="Test")
        bot.update_config({
            "plan": "pro",
            "mod_action": "ban",
            "ai_enabled": False,
            "discord_channel_ids": ["ch1", "ch2"],
        })
        assert bot.plan == "pro"
        assert bot.mod_action == "ban"
        assert bot.ai_enabled is False
        assert bot.monitored_channel_ids == {"ch1", "ch2"}

    def test_update_config_clears_monitored_channels(self):
        bot = DiscordGuildBot(
            channel_id=1, guild_id="123", guild_name="Test",
            monitored_channel_ids={"ch1"},
        )
        bot.update_config({"discord_channel_ids": None})
        assert bot.monitored_channel_ids is None
