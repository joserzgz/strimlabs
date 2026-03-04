import re
from dataclasses import dataclass, field


@dataclass
class DiscordGuildBot:
    channel_id: int  # DB channel id
    guild_id: str
    guild_name: str
    plan: str = "free"
    mod_action: str = "timeout"
    timeout_seconds: int = 600
    toxicity_threshold: float = 0.8
    ai_enabled: bool = True
    monitored_channel_ids: set[str] | None = None  # None = all text channels
    blacklist_patterns: list[str] = field(default_factory=list)
    compiled_blacklist: re.Pattern | None = field(default=None, repr=False)

    def should_moderate_channel(self, discord_channel_id: str) -> bool:
        if self.monitored_channel_ids is None:
            return True
        return discord_channel_id in self.monitored_channel_ids

    def update_config(self, data: dict):
        self.plan = data.get("plan", self.plan)
        self.mod_action = data.get("mod_action", self.mod_action)
        self.timeout_seconds = data.get("timeout_seconds", self.timeout_seconds)
        self.toxicity_threshold = data.get("toxicity_threshold", self.toxicity_threshold)
        self.ai_enabled = data.get("ai_enabled", self.ai_enabled)
        ids = data.get("discord_channel_ids")
        self.monitored_channel_ids = set(ids) if ids else None
