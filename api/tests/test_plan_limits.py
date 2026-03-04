from core.plan_limits import get_limits, PLAN_LIMITS


class TestGetLimits:
    def test_free_plan(self):
        limits = get_limits("free")
        assert limits["max_channels"] == 1
        assert limits["messages_per_month"] == 1000
        assert limits["has_ai"] is True
        assert limits["has_history"] is False

    def test_pro_plan(self):
        limits = get_limits("pro")
        assert limits["max_channels"] == 999
        assert limits["messages_per_month"] == 999_999_999
        assert limits["has_ai"] is True
        assert limits["has_history"] is True

    def test_unknown_plan_defaults_to_free(self):
        limits = get_limits("enterprise")
        assert limits == PLAN_LIMITS["free"]

    def test_empty_plan_defaults_to_free(self):
        limits = get_limits("")
        assert limits == PLAN_LIMITS["free"]
