import pytest
from tests.conftest import auth_headers


class TestGetHistory:
    @pytest.mark.asyncio
    async def test_free_plan_denied(self, client, test_user):
        resp = await client.get("/api/history", headers=auth_headers(test_user.id))
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_pro_plan_returns_logs(self, client, pro_user, db):
        from services.modbot.models import Channel, ModActionLog
        from core.db.models import Platform
        ch = Channel(user_id=pro_user.id, platform=Platform.twitch, channel_name="pro_ch")
        db.add(ch)
        await db.commit()
        await db.refresh(ch)

        log = ModActionLog(
            channel_id=ch.id,
            username="baduser",
            message="toxic msg",
            action="timeout",
            reason="toxicity",
            score=0.95,
        )
        db.add(log)
        await db.commit()

        resp = await client.get("/api/history", headers=auth_headers(pro_user.id))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["username"] == "baduser"
        assert data[0]["action"] == "timeout"

    @pytest.mark.asyncio
    async def test_filter_by_channel(self, client, pro_user, db):
        from services.modbot.models import Channel, ModActionLog
        from core.db.models import Platform
        ch1 = Channel(user_id=pro_user.id, platform=Platform.twitch, channel_name="ch1")
        ch2 = Channel(user_id=pro_user.id, platform=Platform.twitch, channel_name="ch2")
        db.add_all([ch1, ch2])
        await db.commit()
        await db.refresh(ch1)
        await db.refresh(ch2)

        db.add(ModActionLog(channel_id=ch1.id, username="u1", message="m1", action="ban"))
        db.add(ModActionLog(channel_id=ch2.id, username="u2", message="m2", action="timeout"))
        await db.commit()

        resp = await client.get(
            f"/api/history?channel_id={ch1.id}",
            headers=auth_headers(pro_user.id),
        )
        data = resp.json()
        assert len(data) == 1
        assert data[0]["username"] == "u1"

    @pytest.mark.asyncio
    async def test_pagination(self, client, pro_user, db):
        from services.modbot.models import Channel, ModActionLog
        from core.db.models import Platform
        ch = Channel(user_id=pro_user.id, platform=Platform.twitch, channel_name="pag_ch")
        db.add(ch)
        await db.commit()
        await db.refresh(ch)

        for i in range(5):
            db.add(ModActionLog(channel_id=ch.id, username=f"u{i}", message=f"m{i}", action="timeout"))
        await db.commit()

        resp = await client.get("/api/history?limit=2&page=1", headers=auth_headers(pro_user.id))
        assert len(resp.json()) == 2

        resp2 = await client.get("/api/history?limit=2&page=3", headers=auth_headers(pro_user.id))
        assert len(resp2.json()) == 1


class TestInternalLog:
    @pytest.mark.asyncio
    async def test_log_action(self, client, test_channel):
        resp = await client.post(
            "/api/history/internal",
            json={
                "channel_id": test_channel.id,
                "username": "spammer",
                "message": "buy followers",
                "action": "timeout",
                "reason": "blacklist: spam",
                "score": 0.0,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    @pytest.mark.asyncio
    async def test_log_without_score(self, client, test_channel):
        resp = await client.post(
            "/api/history/internal",
            json={
                "channel_id": test_channel.id,
                "username": "user1",
                "message": "bad word",
                "action": "delete",
            },
        )
        assert resp.status_code == 200
