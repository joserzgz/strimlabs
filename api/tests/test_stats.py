import pytest
from tests.conftest import auth_headers


class TestGetStats:
    @pytest.mark.asyncio
    async def test_empty_stats(self, client, test_user, test_channel):
        resp = await client.get("/api/stats", headers=auth_headers(test_user.id))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_actions"] == 0
        assert data["breakdown"] == {}
        assert data["top_offenders"] == []

    @pytest.mark.asyncio
    async def test_stats_with_logs(self, client, test_user, test_channel, db):
        from services.modbot.models import ModActionLog
        logs = [
            ModActionLog(channel_id=test_channel.id, username="user1", message="m1", action="timeout"),
            ModActionLog(channel_id=test_channel.id, username="user1", message="m2", action="timeout"),
            ModActionLog(channel_id=test_channel.id, username="user2", message="m3", action="ban"),
        ]
        db.add_all(logs)
        await db.commit()

        resp = await client.get("/api/stats", headers=auth_headers(test_user.id))
        data = resp.json()
        assert data["total_actions"] == 3
        assert data["breakdown"]["timeout"] == 2
        assert data["breakdown"]["ban"] == 1
        assert len(data["top_offenders"]) == 2
        # user1 has 2 actions, should be first
        assert data["top_offenders"][0]["username"] == "user1"
        assert data["top_offenders"][0]["count"] == 2

    @pytest.mark.asyncio
    async def test_filter_by_channel(self, client, pro_user, db):
        from services.modbot.models import Channel, ModActionLog
        from core.db.models import Platform
        ch1 = Channel(user_id=pro_user.id, platform=Platform.twitch, channel_name="s1")
        ch2 = Channel(user_id=pro_user.id, platform=Platform.twitch, channel_name="s2")
        db.add_all([ch1, ch2])
        await db.commit()
        await db.refresh(ch1)
        await db.refresh(ch2)

        db.add(ModActionLog(channel_id=ch1.id, username="a", message="m", action="timeout"))
        db.add(ModActionLog(channel_id=ch2.id, username="b", message="m", action="ban"))
        db.add(ModActionLog(channel_id=ch2.id, username="c", message="m", action="ban"))
        await db.commit()

        resp = await client.get(
            f"/api/stats?channel_id={ch2.id}",
            headers=auth_headers(pro_user.id),
        )
        data = resp.json()
        assert data["total_actions"] == 2
        assert data["breakdown"].get("ban") == 2

    @pytest.mark.asyncio
    async def test_messages_this_month(self, client, test_user, test_channel, db):
        test_user.messages_this_month = 42
        db.add(test_user)
        await db.commit()

        resp = await client.get("/api/stats", headers=auth_headers(test_user.id))
        assert resp.json()["messages_this_month"] == 42
