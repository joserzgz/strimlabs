# Strimlabs — Contexto para Claude Code

## Qué es
Plataforma SaaS de herramientas para streamers. Monorepo con dos proyectos activos:
- **landing/** — Landing page corporativa de strimlabs.com
- **ModBot/** — Bot de moderación SaaS multi-tenant para Twitch

## Dominio
strimlabs.com

## Identidad visual (SIEMPRE respetar)
```css
--purple:  #8B2BE2;
--cyan:    #00E5FF;
--bg:      #0D0F14;
--bg2:     #12151C;
--surface: #181C26;
--surface2:#1E2230;
--border:  rgba(0,229,255,0.12);
--border2: rgba(0,229,255,0.25);
--text:    #E8EAF0;
--muted:   #4A5270;
--gradient: linear-gradient(90deg, #8B2BE2, #00E5FF);
```
Tipografía: Space Mono (headings/mono) + DM Sans (body)
Logo: SVG círculo + play triangle + ondas, gradiente purple→cyan

## Stack por proyecto

### landing/
- React 18 + Vite
- CSS puro con variables (sin Tailwind)
- Animaciones CSS nativas

### ModBot/api/
- Python 3.12 + FastAPI + SQLAlchemy 2.x async + asyncpg
- PostgreSQL 16
- JWT (PyJWT) + bcrypt
- Stripe SDK + mercadopago SDK

### ModBot/bot/
- Python 3.12 + twitchio 2.x + aiohttp
- BotManager multi-tenant (join/leave dinámico)
- Perspective API de Google para detección de toxicidad

### ModBot/web/
- React 18 + Vite
- Dashboard con auth, stats, blacklist, historial, settings

## Modelos de DB

```python
User: id, twitch_id, twitch_login, twitch_display_name, email, avatar_url,
      plan (free|pro), subscription_status (trialing|active|past_due|canceled),
      subscription_id, payment_provider, plan_start, plan_end,
      is_admin, hashed_password, messages_this_month, messages_reset_at, created_at

Channel: id, user_id→User, channel_name, is_active, mod_action (timeout|ban|delete),
         timeout_seconds, toxicity_threshold, created_at

BlacklistEntry: id, channel_id→Channel, pattern, added_by, created_at

ModActionLog: id, channel_id→Channel, username, message, action, reason, score, created_at
```

## Planes
```
Free: 1 canal | blacklist+regex | dashboard | 1,000 msg/mes | sin IA | sin historial
Pro:  ilimitado | todo incluido | $9.99 USD (Stripe) | $199 MXN (MercadoPago)
```

## Flujo OAuth Twitch
```
GET /api/auth/twitch
  → redirect id.twitch.tv/oauth2/authorize (scopes: user:read:email channel:moderate)
  → callback con ?code=xxx
  → intercambiar code → access_token
  → GET api.twitch.tv/helix/users
  → upsert User en DB (nuevo: plan=free, subscription_status=active)
  → JWT propio → redirect FRONTEND_URL/dashboard?token=xxx
```

## Flujo de pagos
```
Stripe:      /billing/stripe/checkout → Checkout Session → webhook → plan=pro
MercadoPago: /billing/mp/checkout → Preference → webhook → plan=pro
Al cancelar: downgrade a Free (NO se elimina la cuenta)
```

## Lógica del bot (event_message)
```
1. Ignorar echo
2. Obtener channel_bot del manager
3. GET /api/channels/{id}/quota (verifica límite mensual)
4. Capa 1: blacklist_match() — sin latencia, en memoria
5. Capa 2 (solo Pro): Perspective API — timeout 3s, si falla → continuar
6. Si flagged → _take_action() + POST /api/history/internal
7. Sync loop cada 60s: GET /api/channels/active → manager.sync_from_db()
```

## Variables de entorno requeridas
```
POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_REDIRECT_URI
TWITCH_BOT_TOKEN, TWITCH_BOT_NICK
JWT_SECRET, JWT_EXPIRE_HOURS, ADMIN_PASSWORD
STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_ID
MP_ACCESS_TOKEN, MP_WEBHOOK_SECRET
PERSPECTIVE_API_KEY
FRONTEND_URL, API_URL, API_BASE
```

## Rutas API principales
```
GET  /api/auth/twitch                → OAuth redirect
GET  /api/auth/twitch/callback       → OAuth callback
GET  /api/auth/me                    → usuario actual
POST /api/auth/admin/login           → login admin interno

GET|POST        /api/channels/me     → canales del usuario
PATCH|DELETE    /api/channels/me/:id → actualizar/eliminar canal
GET             /api/channels/active → endpoint interno para el bot
GET             /api/channels/:id/quota → verifica y cuenta mensajes

GET|POST|DELETE /api/blacklist       → gestión de blacklist

GET  /api/history                    → historial (Pro only)
POST /api/history/internal           → el bot loguea acciones

GET  /api/stats                      → estadísticas del usuario

POST /api/billing/stripe/checkout    → iniciar pago Stripe
GET  /api/billing/stripe/portal      → portal gestión Stripe
POST /api/billing/stripe/webhook     → webhook Stripe
POST /api/billing/mp/checkout        → iniciar pago MercadoPago
POST /api/billing/mp/webhook         → webhook MercadoPago
GET  /api/billing/status             → estado suscripción actual
```

## Shared (assets compartidos)
- shared/components/StrimlabsLogo.jsx  → componente SVG del logo
- shared/components/Nav.jsx            → nav corporativo compartido
- shared/theme.css                     → variables CSS globales
- shared/logo/strimlabs.png            → logo oficial
