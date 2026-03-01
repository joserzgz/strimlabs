import logging
import aiohttp
from .channel_bot import TwitchChannelBot
from moderation.shared import compile_blacklist

logger = logging.getLogger("twitch.manager")


class TwitchBotManager:
    def __init__(self, api_base: str):
        self.api_base = api_base
        self.channels: dict[str, TwitchChannelBot] = {}  # channel_name -> bot

    async def sync_from_api(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/api/channels/active?platform=twitch") as resp:
                    if resp.status != 200:
                        logger.error("Failed to fetch active channels: %s", resp.status)
                        return []
                    data = await resp.json()
        except Exception as e:
            logger.error("Error fetching channels: %s", e)
            return []

        active_names = set()
        channels_to_join = []
        channels_to_part = []

        for ch in data:
            name = ch["channel_name"]
            if not name:
                continue
            active_names.add(name)

            if name in self.channels:
                self.channels[name].update_config(ch)
            else:
                bot = TwitchChannelBot(
                    channel_id=ch["id"],
                    channel_name=name,
                    plan=ch.get("plan", "free"),
                    mod_action=ch.get("mod_action", "timeout"),
                    timeout_seconds=ch.get("timeout_seconds", 600),
                    toxicity_threshold=ch.get("toxicity_threshold", 0.8),
                )
                self.channels[name] = bot
                channels_to_join.append(name)

            # Fetch blacklist
            await self._load_blacklist(ch["id"], name)

        for name in list(self.channels.keys()):
            if name not in active_names:
                del self.channels[name]
                channels_to_part.append(name)

        return channels_to_join, channels_to_part

    async def _load_blacklist(self, channel_id: int, channel_name: str):
        try:
            async with aiohttp.ClientSession() as session:
                # Internal call — blacklist endpoint needs auth, so we use a simple
                # direct query approach. For simplicity, bot fetches from active endpoint
                # which includes patterns in a future iteration. For now, compile base only.
                pass
        except Exception:
            pass
        bot = self.channels.get(channel_name)
        if bot:
            bot.compiled_blacklist = compile_blacklist(bot.blacklist_patterns or None)

    def get_bot(self, channel_name: str) -> TwitchChannelBot | None:
        return self.channels.get(channel_name)
