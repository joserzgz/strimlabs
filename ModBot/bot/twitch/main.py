import os
import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()

import aiohttp
from twitchio.ext import commands

from moderation.shared import blacklist_match, check_perspective_api
from .manager import TwitchBotManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("twitch.bot")

API_BASE = os.getenv("API_BASE", "http://sl-api-dev:8000")
BOT_TOKEN = os.getenv("TWITCH_BOT_TOKEN", "")
BOT_NICK = os.getenv("TWITCH_BOT_NICK", "strimlabs_bot")

manager = TwitchBotManager(API_BASE)


class ModBot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=BOT_TOKEN,
            nick=BOT_NICK,
            prefix="!",
            initial_channels=[],
        )

    async def event_ready(self):
        logger.info("Twitch bot connected as %s", self.nick)
        self.loop.create_task(self._sync_loop())

    async def _sync_loop(self):
        while True:
            try:
                result = await manager.sync_from_api()
                if result:
                    to_join, to_part = result
                    if to_join:
                        await self.join_channels(to_join)
                        logger.info("Joined: %s", to_join)
                    if to_part:
                        for ch in to_part:
                            await self.part_channels([ch])
                        logger.info("Parted: %s", to_part)
            except Exception as e:
                logger.error("Sync error: %s", e)
            await asyncio.sleep(60)

    async def event_message(self, message):
        if message.echo:
            return

        channel_name = message.channel.name
        bot = manager.get_bot(channel_name)
        if not bot:
            return

        # Quota check
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE}/api/channels/{bot.channel_id}/quota") as resp:
                    quota = await resp.json()
                    if not quota.get("allowed"):
                        return
        except Exception:
            return

        text = message.content
        author = message.author.name

        # Layer 1: Blacklist
        match = blacklist_match(text, bot.compiled_blacklist)
        if match:
            await self._take_action(message, bot, "blacklist", match)
            return

        # Layer 2: Perspective API (Pro only)
        if bot.plan == "pro":
            flagged, score = await check_perspective_api(text, bot.toxicity_threshold)
            if flagged:
                await self._take_action(message, bot, "toxicity", f"score={score:.2f}", score)
                return

    async def _take_action(self, message, bot, reason_type, reason_detail, score=None):
        author = message.author.name
        channel = message.channel

        try:
            if bot.mod_action == "delete":
                await message.delete()
            elif bot.mod_action == "ban":
                await channel.ban(author, reason=reason_detail)
            else:  # timeout
                await channel.timeout(author, duration=bot.timeout_seconds, reason=reason_detail)
        except Exception as e:
            logger.error("Action failed on %s: %s", bot.channel_name, e)

        # Log to API
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"{API_BASE}/api/history/internal",
                    json={
                        "channel_id": bot.channel_id,
                        "username": author,
                        "message": message.content,
                        "action": bot.mod_action,
                        "reason": f"{reason_type}: {reason_detail}",
                        "score": score,
                    },
                )
        except Exception as e:
            logger.error("Log failed: %s", e)


def main():
    bot = ModBot()
    bot.run()


if __name__ == "__main__":
    main()
