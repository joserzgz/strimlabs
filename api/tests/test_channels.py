import pytest
from tests.conftest import auth_headers


class TestGetMyChannels:
    @pytest.mark.asyncio
    async def test_returns_empty_list(self, client, test_user):
        resp = await client.get("/api/channels/me", headers=auth_headers(test_user.id))
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_returns_user_channels(self, client, test_user, test_channel):
        resp = await client.get("/api/channels/me", headers=auth_headers(test_user.id))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["channel_name"] == "test_channel"
        assert data[0]["platform"] == "twitch"
        assert data[0]["ai_enabled"] is True

    @pytest.mark.asyncio
    async def test_filter_by_platform(self, client, test_user, test_channel):
        resp = await client.get("/api/channels/me?platform=discord", headers=auth_headers(test_user.id))
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_does_not_return_other_users_channels(self, client, test_user, pro_user, test_channel):
        resp = await client.get("/api/channels/me", headers=auth_headers(pro_user.id))
        assert resp.status_code == 200
        assert resp.json() == []


class TestCreateChannel:
    @pytest.mark.asyncio
    async def test_create_twitch_channel(self, client, test_user):
        resp = await client.post(
            "/api/channels/me",
            headers=auth_headers(test_user.id),
            json={"platform": "twitch", "channel_name": "my_channel"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["platform"] == "twitch"
        assert data["channel_name"] == "my_channel"
        assert data["ai_enabled"] is True
        assert data["mod_action"] == "timeout"

    @pytest.mark.asyncio
    async def test_create_discord_channel(self, client, test_user):
        resp = await client.post(
            "/api/channels/me",
            headers=auth_headers(test_user.id),
            json={"platform": "discord", "discord_guild_id": "123456"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["platform"] == "discord"
        assert data["discord_guild_id"] == "123456"

    @pytest.mark.asyncio
    async def test_twitch_requires_channel_name(self, client, test_user):
        resp = await client.post(
            "/api/channels/me",
            headers=auth_headers(test_user.id),
            json={"platform": "twitch"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_discord_requires_guild_id(self, client, test_user):
        resp = await client.post(
            "/api/channels/me",
            headers=auth_headers(test_user.id),
            json={"platform": "discord"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_free_plan_max_channels(self, client, test_user, test_channel):
        # Free plan allows max 1 channel; test_channel already exists
        resp = await client.post(
            "/api/channels/me",
            headers=auth_headers(test_user.id),
            json={"platform": "twitch", "channel_name": "second_channel"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_pro_plan_allows_multiple(self, client, pro_user):
        for i in range(3):
            resp = await client.post(
                "/api/channels/me",
                headers=auth_headers(pro_user.id),
                json={"platform": "twitch", "channel_name": f"ch_{i}"},
            )
            assert resp.status_code == 200


class TestUpdateChannel:
    @pytest.mark.asyncio
    async def test_update_mod_action(self, client, test_user, test_channel):
        resp = await client.patch(
            f"/api/channels/me/{test_channel.id}",
            headers=auth_headers(test_user.id),
            json={"mod_action": "ban"},
        )
        assert resp.status_code == 200
        assert resp.json()["mod_action"] == "ban"

    @pytest.mark.asyncio
    async def test_update_ai_enabled(self, client, test_user, test_channel):
        resp = await client.patch(
            f"/api/channels/me/{test_channel.id}",
            headers=auth_headers(test_user.id),
            json={"ai_enabled": False},
        )
        assert resp.status_code == 200
        assert resp.json()["ai_enabled"] is False

    @pytest.mark.asyncio
    async def test_update_toxicity_threshold(self, client, test_user, test_channel):
        resp = await client.patch(
            f"/api/channels/me/{test_channel.id}",
            headers=auth_headers(test_user.id),
            json={"toxicity_threshold": 0.5},
        )
        assert resp.status_code == 200
        assert resp.json()["toxicity_threshold"] == 0.5

    @pytest.mark.asyncio
    async def test_update_timeout_seconds(self, client, test_user, test_channel):
        resp = await client.patch(
            f"/api/channels/me/{test_channel.id}",
            headers=auth_headers(test_user.id),
            json={"timeout_seconds": 300},
        )
        assert resp.status_code == 200
        assert resp.json()["timeout_seconds"] == 300

    @pytest.mark.asyncio
    async def test_toggle_active(self, client, test_user, test_channel):
        resp = await client.patch(
            f"/api/channels/me/{test_channel.id}",
            headers=auth_headers(test_user.id),
            json={"is_active": False},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    @pytest.mark.asyncio
    async def test_404_wrong_channel(self, client, test_user):
        resp = await client.patch(
            "/api/channels/me/99999",
            headers=auth_headers(test_user.id),
            json={"mod_action": "ban"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_404_other_users_channel(self, client, pro_user, test_channel):
        resp = await client.patch(
            f"/api/channels/me/{test_channel.id}",
            headers=auth_headers(pro_user.id),
            json={"mod_action": "ban"},
        )
        assert resp.status_code == 404


class TestDeleteChannel:
    @pytest.mark.asyncio
    async def test_delete_channel(self, client, test_user, test_channel):
        resp = await client.delete(
            f"/api/channels/me/{test_channel.id}",
            headers=auth_headers(test_user.id),
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

        # Verify it's gone
        resp2 = await client.get("/api/channels/me", headers=auth_headers(test_user.id))
        assert resp2.json() == []

    @pytest.mark.asyncio
    async def test_404_nonexistent(self, client, test_user):
        resp = await client.delete(
            "/api/channels/me/99999",
            headers=auth_headers(test_user.id),
        )
        assert resp.status_code == 404


class TestActiveChannels:
    @pytest.mark.asyncio
    async def test_returns_active_channels(self, client, test_channel):
        resp = await client.get("/api/channels/active?platform=twitch")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["channel_name"] == "test_channel"
        assert "plan" in data[0]

    @pytest.mark.asyncio
    async def test_excludes_inactive_channels(self, client, test_user, test_channel, db):
        test_channel.is_active = False
        db.add(test_channel)
        await db.commit()

        resp = await client.get("/api/channels/active?platform=twitch")
        assert resp.json() == []


class TestQuota:
    @pytest.mark.asyncio
    async def test_allowed_under_limit(self, client, test_channel):
        resp = await client.get(f"/api/channels/{test_channel.id}/quota")
        assert resp.status_code == 200
        data = resp.json()
        assert data["allowed"] is True

    @pytest.mark.asyncio
    async def test_denied_over_limit(self, client, test_user, test_channel, db):
        test_user.messages_this_month = 1000
        db.add(test_user)
        await db.commit()

        resp = await client.get(f"/api/channels/{test_channel.id}/quota")
        data = resp.json()
        assert data["allowed"] is False

    @pytest.mark.asyncio
    async def test_404_nonexistent_channel(self, client):
        resp = await client.get("/api/channels/99999/quota")
        assert resp.status_code == 404
