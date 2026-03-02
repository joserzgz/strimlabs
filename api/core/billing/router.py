import os
from datetime import datetime, timezone

import stripe
import mercadopago
from fastapi import APIRouter, Depends, HTTPException, Request

from core.db import async_session, User
from core.auth.deps import get_current_user

router = APIRouter()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5174")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "")
MP_WEBHOOK_SECRET = os.getenv("MP_WEBHOOK_SECRET", "")


# ── Stripe ───────────────────────────────────────────────────

@router.post("/stripe/checkout")
async def stripe_checkout(user: User = Depends(get_current_user)):
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
        success_url=f"{FRONTEND_URL}/settings?billing=success",
        cancel_url=f"{FRONTEND_URL}/settings?billing=cancel",
        metadata={"user_id": str(user.id)},
    )
    return {"url": session.url}


@router.get("/stripe/portal")
async def stripe_portal(user: User = Depends(get_current_user)):
    if not user.subscription_id or user.payment_provider != "stripe":
        raise HTTPException(400, "No active Stripe subscription")
    session = stripe.billing_portal.Session.create(
        customer=user.subscription_id,
        return_url=f"{FRONTEND_URL}/settings",
    )
    return {"url": session.url}


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except Exception:
        raise HTTPException(400, "Invalid webhook")

    if event["type"] == "checkout.session.completed":
        data = event["data"]["object"]
        user_id = int(data["metadata"]["user_id"])
        await _upgrade_user(user_id, data.get("subscription"), "stripe")
    elif event["type"] in ("customer.subscription.deleted", "customer.subscription.updated"):
        sub = event["data"]["object"]
        if sub.get("status") in ("canceled", "unpaid"):
            user_id = int(sub.get("metadata", {}).get("user_id", 0))
            if user_id:
                await _downgrade_user(user_id)

    return {"ok": True}


# ── MercadoPago ──────────────────────────────────────────────

@router.post("/mp/checkout")
async def mp_checkout(user: User = Depends(get_current_user)):
    sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
    preference = {
        "items": [{
            "title": "ModBot Pro",
            "quantity": 1,
            "currency_id": "MXN",
            "unit_price": 199.0,
        }],
        "back_urls": {
            "success": f"{FRONTEND_URL}/settings?billing=success",
            "failure": f"{FRONTEND_URL}/settings?billing=cancel",
        },
        "auto_return": "approved",
        "external_reference": str(user.id),
    }
    result = sdk.preference().create(preference)
    if result["status"] != 201:
        raise HTTPException(500, "MercadoPago error")
    return {"url": result["response"]["init_point"]}


@router.post("/mp/webhook")
async def mp_webhook(request: Request):
    body = await request.json()
    if body.get("type") == "payment":
        sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
        payment = sdk.payment().get(body["data"]["id"])
        if payment["status"] == 200:
            info = payment["response"]
            if info.get("status") == "approved":
                user_id = int(info.get("external_reference", 0))
                if user_id:
                    await _upgrade_user(user_id, str(info["id"]), "mercadopago")
    return {"ok": True}


# ── Billing status ───────────────────────────────────────────

@router.get("/status")
async def billing_status(user: User = Depends(get_current_user)):
    return {
        "plan": user.plan,
        "subscription_status": user.subscription_status,
        "payment_provider": user.payment_provider,
        "plan_start": user.plan_start.isoformat() if user.plan_start else None,
        "plan_end": user.plan_end.isoformat() if user.plan_end else None,
    }


# ── Helpers ──────────────────────────────────────────────────

async def _upgrade_user(user_id: int, subscription_id: str | None, provider: str):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user:
            user.plan = "pro"
            user.subscription_status = "active"
            user.subscription_id = subscription_id
            user.payment_provider = provider
            user.plan_start = datetime.now(timezone.utc)
            await session.commit()


async def _downgrade_user(user_id: int):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user:
            user.plan = "free"
            user.subscription_status = "canceled"
            user.plan_end = datetime.now(timezone.utc)
            await session.commit()
