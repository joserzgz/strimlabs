import pytest
from datetime import datetime, timedelta, timezone
import jwt as pyjwt
from core.auth.deps import create_jwt, JWT_SECRET


class TestCreateJwt:
    def test_creates_valid_token(self):
        token = create_jwt(42)
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        assert payload["sub"] == 42
        assert "exp" in payload

    def test_token_has_correct_subject(self):
        token = create_jwt(1)
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        assert payload["sub"] == 1

    def test_token_is_not_expired(self):
        token = create_jwt(1)
        # Should not raise
        pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])

    def test_token_with_wrong_secret_fails(self):
        token = create_jwt(1)
        with pytest.raises(pyjwt.InvalidSignatureError):
            pyjwt.decode(token, "wrong-secret", algorithms=["HS256"])


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self, client, test_user):
        from tests.conftest import auth_headers
        resp = await client.get("/api/auth/me", headers=auth_headers(test_user.id))
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == test_user.id
        assert data["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_missing_token_returns_401(self, client):
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, client):
        resp = await client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_token_returns_401(self, client, test_user):
        payload = {
            "sub": test_user.id,
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")
        resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_nonexistent_user_returns_401(self, client):
        token = create_jwt(99999)
        resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401
