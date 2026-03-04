import pytest
from tests.conftest import auth_headers


class TestAuthMe:
    @pytest.mark.asyncio
    async def test_returns_user_profile(self, client, test_user):
        resp = await client.get("/api/auth/me", headers=auth_headers(test_user.id))
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == test_user.id
        assert data["email"] == "test@example.com"
        assert data["plan"] == "free"
        assert data["is_admin"] is False
        assert isinstance(data["linked_accounts"], list)

    @pytest.mark.asyncio
    async def test_returns_linked_accounts(self, client, db, test_user):
        from core.db.models import LinkedAccount, Platform
        la = LinkedAccount(
            user_id=test_user.id,
            platform=Platform.twitch,
            platform_user_id="tw123",
            platform_username="testuser",
            platform_display_name="TestUser",
        )
        db.add(la)
        await db.commit()

        resp = await client.get("/api/auth/me", headers=auth_headers(test_user.id))
        data = resp.json()
        assert len(data["linked_accounts"]) == 1
        assert data["linked_accounts"][0]["platform"] == "twitch"
        assert data["linked_accounts"][0]["username"] == "testuser"


class TestAdminLogin:
    @pytest.mark.asyncio
    async def test_valid_password_returns_token(self, client, admin_user):
        resp = await client.post("/api/auth/admin/login", json={"password": "testpass"})
        assert resp.status_code == 200
        assert "token" in resp.json()

    @pytest.mark.asyncio
    async def test_wrong_password_returns_401(self, client, admin_user):
        resp = await client.post("/api/auth/admin/login", json={"password": "wrong"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_no_admin_returns_401(self, client):
        resp = await client.post("/api/auth/admin/login", json={"password": "testpass"})
        assert resp.status_code == 401
