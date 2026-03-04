import os
import asyncio
import logging
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

import aiohttp
import discord

from moderation.shared import blacklist_match, check_perspective_api
from .manager import DiscordBotManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("discord.bot")

API_BASE = os.getenv("API_BASE", "http://sl-api-dev:8000")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

client = discord.Client(intents=intents)
manager = DiscordBotManager(API_BASE)


@client.event
async def on_ready():
    logger.info("Discord bot connected as %s", client.user)
    client.loop.create_task(sync_loop())


async def sync_loop():
    while True:
        try:
            await manager.sync_from_api()
        except Exception as e:
            logger.error("Sync error: %s", e)
        await asyncio.sleep(60)


@client.event
async def on_message(message: discord.Message):
    # Ignore bots and DMs
    if message.author.bot:
        return
    if not message.guild:
        return

    guild_id = str(message.guild.id)
    bot = manager.get_bot(guild_id)
    if not bot:
        return

    # Check if this text channel should be moderated
    if not bot.should_moderate_channel(str(message.channel.id)):
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
    author_name = str(message.author)

    # Layer 1: Blacklist
    match = blacklist_match(text, bot.compiled_blacklist)
    if match:
        await take_action(message, bot, "blacklist", match)
        return

    # Layer 2: Perspective API
    flagged, score = await check_perspective_api(text, bot.toxicity_threshold)
    if flagged:
        await take_action(message, bot, "toxicity", f"score={score:.2f}", score)
        return


async def take_action(message: discord.Message, bot, reason_type: str, reason_detail: str, score=None):
    author = message.author
    author_name = str(author)

    try:
        if bot.mod_action == "delete":
            await message.delete()
        elif bot.mod_action == "ban":
            await message.guild.ban(author, reason=reason_detail, delete_message_seconds=0)
        else:  # timeout
            await author.timeout(timedelta(seconds=bot.timeout_seconds), reason=reason_detail)
            try:
                await message.delete()
            except Exception:
                pass
    except discord.Forbidden:
        logger.warning("Missing permissions in guild %s", bot.guild_id)
    except Exception as e:
        logger.error("Action failed in guild %s: %s", bot.guild_id, e)

    # Log to API
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"{API_BASE}/api/history/internal",
                json={
                    "channel_id": bot.channel_id,
                    "username": author_name,
                    "message": message.content,
                    "action": bot.mod_action,
                    "reason": f"{reason_type}: {reason_detail}",
                    "score": score,
                },
            )
    except Exception as e:
        logger.error("Log failed: %s", e)


def main():
    client.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
