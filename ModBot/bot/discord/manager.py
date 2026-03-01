import logging
import aiohttp
from .guild_bot import DiscordGuildBot
from moderation.shared import compile_blacklist

logger = logging.getLogger("discord.manager")


class DiscordBotManager:
    def __init__(self, api_base: str):
        self.api_base = api_base
        self.guilds: dict[str, DiscordGuildBot] = {}  # guild_id -> bot

    async def sync_from_api(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/api/channels/active?platform=discord") as resp:
                    if resp.status != 200:
                        logger.error("Failed to fetch active channels: %s", resp.status)
                        return
                    data = await resp.json()
        except Exception as e:
            logger.error("Error fetching channels: %s", e)
            return

        active_guild_ids = set()

        for ch in data:
            guild_id = ch.get("discord_guild_id")
            if not guild_id:
                continue
            active_guild_ids.add(guild_id)

            ids = ch.get("discord_channel_ids")
            monitored = set(ids) if ids else None

            if guild_id in self.guilds:
                self.guilds[guild_id].update_config(ch)
            else:
                bot = DiscordGuildBot(
                    channel_id=ch["id"],
                    guild_id=guild_id,
                    guild_name=ch.get("channel_name", guild_id),
                    plan=ch.get("plan", "free"),
                    mod_action=ch.get("mod_action", "timeout"),
                    timeout_seconds=ch.get("timeout_seconds", 600),
                    toxicity_threshold=ch.get("toxicity_threshold", 0.8),
                    monitored_channel_ids=monitored,
                )
                self.guilds[guild_id] = bot

            bot = self.guilds[guild_id]
            bot.compiled_blacklist = compile_blacklist(bot.blacklist_patterns or None)

        for gid in list(self.guilds.keys()):
            if gid not in active_guild_ids:
                del self.guilds[gid]

    def get_bot(self, guild_id: str) -> DiscordGuildBot | None:
        return self.guilds.get(guild_id)
