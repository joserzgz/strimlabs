import os
import sys

# Add bot root to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("API_BASE", "http://fake-api:8000")
os.environ.setdefault("TWITCH_BOT_TOKEN", "fake_token")
os.environ.setdefault("TWITCH_BOT_NICK", "test_bot")
os.environ.setdefault("DISCORD_BOT_TOKEN", "fake_discord_token")
