import pytest
from tests.conftest import auth_headers


class TestBillingStatus:
    @pytest.mark.asyncio
    async def test_free_user_status(self, client, test_user):
        resp = await client.get("/api/billing/status", headers=auth_headers(test_user.id))
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"] == "free"
        assert data["subscription_status"] == "active"
        assert data["payment_provider"] is None

    @pytest.mark.asyncio
    async def test_pro_user_status(self, client, pro_user, db):
        pro_user.payment_provider = "stripe"
        pro_user.subscription_id = "sub_123"
        db.add(pro_user)
        await db.commit()

        resp = await client.get("/api/billing/status", headers=auth_headers(pro_user.id))
        data = resp.json()
        assert data["plan"] == "pro"
        assert data["payment_provider"] == "stripe"


class TestUpgradeDowngrade:
    @pytest.mark.asyncio
    async def test_upgrade_user(self, db, test_user):
        from core.billing.router import _upgrade_user
        await _upgrade_user(test_user.id, "sub_abc", "stripe")

        await db.refresh(test_user)
        assert test_user.plan == "pro"
        assert test_user.subscription_status == "active"
        assert test_user.subscription_id == "sub_abc"
        assert test_user.payment_provider == "stripe"
        assert test_user.plan_start is not None

    @pytest.mark.asyncio
    async def test_downgrade_user(self, db, pro_user):
        from core.billing.router import _downgrade_user
        await _downgrade_user(pro_user.id)

        await db.refresh(pro_user)
        assert pro_user.plan == "free"
        assert pro_user.subscription_status == "canceled"
        assert pro_user.plan_end is not None

    @pytest.mark.asyncio
    async def test_upgrade_nonexistent_user(self, db):
        from core.billing.router import _upgrade_user
        # Should not raise
        await _upgrade_user(99999, "sub_x", "stripe")
