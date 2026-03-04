# Testing — Strimlabs ModBot

## Requisitos previos

- Python 3.12+
- Node.js 18+
- npm

---

## 1. API (`api/`)

### Instalar dependencias

```bash
cd api
pip install -r requirements.txt
```

### Ejecutar tests

```bash
# Todos los tests
pytest tests/ -v

# Con reporte de cobertura
pytest tests/ -v --cov=. --cov-report=term-missing

# Un archivo específico
pytest tests/test_channels.py -v

# Un test específico
pytest tests/test_channels.py::TestCreateChannel::test_create_twitch_channel -v
```

### Archivos de test

| Archivo | Qué cubre |
|---------|-----------|
| `test_plan_limits.py` | Límites de plan free/pro |
| `test_auth_deps.py` | JWT creación, validación, expiración |
| `test_auth.py` | `/auth/me`, admin login |
| `test_channels.py` | CRUD canales, quota, plan limits, active channels |
| `test_blacklist.py` | CRUD blacklist, autorización |
| `test_history.py` | Historial (plan gating), paginación, log interno |
| `test_stats.py` | Estadísticas, breakdown, top offenders |
| `test_billing.py` | Estado billing, upgrade/downgrade |

---

## 2. Bot (`ModBot/bot/`)

### Instalar dependencias

```bash
cd ModBot/bot
pip install -r requirements.txt
pip install pytest pytest-asyncio aioresponses
```

### Ejecutar tests

```bash
# Todos los tests
pytest tests/ -v

# Solo moderation shared
pytest tests/test_shared.py -v

# Solo dataclasses
pytest tests/test_channel_bot.py -v
```

### Archivos de test

| Archivo | Qué cubre |
|---------|-----------|
| `test_shared.py` | normalize_text, compile_blacklist, blacklist_match, check_perspective_api |
| `test_channel_bot.py` | TwitchChannelBot, DiscordGuildBot (defaults, update_config) |
| `test_managers.py` | TwitchBotManager, DiscordBotManager (sync, create, remove) |
| `test_twitch_events.py` | event_message (echo, blacklist, ai_enabled, quota) |
| `test_discord_events.py` | on_message (bot ignore, DMs, ai_enabled) |

---

## 3. Frontend (`ModBot/web/`)

### Instalar dependencias

```bash
cd ModBot/web
npm install
```

### Ejecutar tests

```bash
# Todos los tests
npm test

# Watch mode (re-ejecuta al guardar)
npm run test:watch

# Un archivo específico
npx vitest run src/__tests__/Channels.test.jsx
```

### Archivos de test

| Archivo | Qué cubre |
|---------|-----------|
| `client.test.js` | API client: tokens, fetch, headers, 401 redirect |
| `Login.test.jsx` | Botones de login, redirects a OAuth |
| `Channels.test.jsx` | Render canales, filtros, AI toggle, threshold slider |

---

## Ejecutar todo

Desde la raíz del proyecto:

```bash
# API
cd api && pytest tests/ -v && cd ..

# Bot
cd ModBot/bot && pytest tests/ -v && cd ..

# Frontend
cd ModBot/web && npm test && cd ..
```
