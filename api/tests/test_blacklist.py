import pytest
from tests.conftest import auth_headers


class TestGetBlacklist:
    @pytest.mark.asyncio
    async def test_returns_entries(self, client, test_user, test_channel, db):
        from services.modbot.models import BlacklistEntry
        entry = BlacklistEntry(channel_id=test_channel.id, pattern="badword", added_by="test")
        db.add(entry)
        await db.commit()

        resp = await client.get(
            f"/api/blacklist?channel_id={test_channel.id}",
            headers=auth_headers(test_user.id),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["pattern"] == "badword"

    @pytest.mark.asyncio
    async def test_empty_list(self, client, test_user, test_channel):
        resp = await client.get(
            f"/api/blacklist?channel_id={test_channel.id}",
            headers=auth_headers(test_user.id),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_404_other_users_channel(self, client, pro_user, test_channel):
        resp = await client.get(
            f"/api/blacklist?channel_id={test_channel.id}",
            headers=auth_headers(pro_user.id),
        )
        assert resp.status_code == 404


class TestAddBlacklist:
    @pytest.mark.asyncio
    async def test_add_entry(self, client, test_user, test_channel):
        resp = await client.post(
            "/api/blacklist",
            headers=auth_headers(test_user.id),
            json={"channel_id": test_channel.id, "pattern": "spam.*link"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pattern"] == "spam.*link"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_404_wrong_channel(self, client, test_user):
        resp = await client.post(
            "/api/blacklist",
            headers=auth_headers(test_user.id),
            json={"channel_id": 99999, "pattern": "test"},
        )
        assert resp.status_code == 404


class TestDeleteBlacklist:
    @pytest.mark.asyncio
    async def test_delete_entry(self, client, test_user, test_channel, db):
        from services.modbot.models import BlacklistEntry
        entry = BlacklistEntry(channel_id=test_channel.id, pattern="removeme", added_by="test")
        db.add(entry)
        await db.commit()
        await db.refresh(entry)

        resp = await client.delete(
            f"/api/blacklist/{entry.id}",
            headers=auth_headers(test_user.id),
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    @pytest.mark.asyncio
    async def test_404_nonexistent(self, client, test_user):
        resp = await client.delete(
            "/api/blacklist/99999",
            headers=auth_headers(test_user.id),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_403_other_users_entry(self, client, pro_user, test_user, test_channel, db):
        from services.modbot.models import BlacklistEntry
        entry = BlacklistEntry(channel_id=test_channel.id, pattern="test", added_by="test")
        db.add(entry)
        await db.commit()
        await db.refresh(entry)

        resp = await client.delete(
            f"/api/blacklist/{entry.id}",
            headers=auth_headers(pro_user.id),
        )
        assert resp.status_code == 403
