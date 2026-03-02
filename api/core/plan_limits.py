PLAN_LIMITS = {
    "free": {
        "max_channels": 1,
        "messages_per_month": 1000,
        "has_ai": False,
        "has_history": False,
    },
    "pro": {
        "max_channels": 999,
        "messages_per_month": 999_999_999,
        "has_ai": True,
        "has_history": True,
    },
}


def get_limits(plan: str) -> dict:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
