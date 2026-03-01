import re
from dataclasses import dataclass, field


@dataclass
class TwitchChannelBot:
    channel_id: int
    channel_name: str
    plan: str = "free"
    mod_action: str = "timeout"
    timeout_seconds: int = 600
    toxicity_threshold: float = 0.8
    blacklist_patterns: list[str] = field(default_factory=list)
    compiled_blacklist: re.Pattern | None = field(default=None, repr=False)

    def update_config(self, data: dict):
        self.plan = data.get("plan", self.plan)
        self.mod_action = data.get("mod_action", self.mod_action)
        self.timeout_seconds = data.get("timeout_seconds", self.timeout_seconds)
        self.toxicity_threshold = data.get("toxicity_threshold", self.toxicity_threshold)
