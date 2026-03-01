# PROMPT: Strimlabs ModBot — Implementación completa

Lee primero el archivo CLAUDE.md en la raíz para entender el contexto completo del proyecto.

## Tu tarea
Implementar TODOS los archivos del proyecto ModBot dentro de la carpeta ModBot/.
La estructura de archivos ya existe. Implementa cada archivo comenzando por DB → API → Bot.

## Archivos a implementar (en este orden)

### 1. ModBot/api/db/base.py
SQLAlchemy async engine con asyncpg. DATABASE_URL desde variables de entorno.
AsyncSession, SessionLocal, Base(DeclarativeBase), get_db() dependency.

### 2. ModBot/api/db/models.py
Todos los modelos con SQLAlchemy 2.x (Mapped[], mapped_column()).
Enums: Plan, SubscriptionStatus, ModAction.
Modelos: User, Channel, BlacklistEntry, ModActionLog con relaciones y cascades.
Ver esquema completo en CLAUDE.md.

### 3. ModBot/api/db/init_db.py
Crear tablas con Base.metadata.create_all.
Crear usuario admin si no existe (twitch_id="0", twitch_login="admin", is_admin=True, plan=pro).

### 4. ModBot/api/plan_limits.py
LIMITS dict con restricciones por plan.
Funciones: get_limits(), check_can_add_channel(), check_can_moderate(),
increment_message_count(), can_use_ai(), can_access_history().
Resetear contador messages_this_month si cambió el mes.

### 5. ModBot/api/routers/auth.py
Twitch OAuth completo (ver flujo en CLAUDE.md).
JWT helpers: create_jwt(), decode_jwt().
Dependencies: get_current_user(), require_active_subscription(), require_admin().
Endpoints: GET /twitch, GET /twitch/callback, GET /me, POST /admin/login.

### 6. ModBot/api/routers/channels.py
Todos los endpoints de canales (ver CLAUDE.md).
GET /active debe incluir blacklist compilada y flag use_ai según plan.
GET /:id/quota verifica límite mensual e incrementa contador.

### 7. ModBot/api/routers/blacklist.py
GET /?channel_id=, POST /, DELETE /:id.
Verificar que el canal pertenece al usuario autenticado.

### 8. ModBot/api/routers/history.py
GET / con paginación (page, limit). Bloquear con 403 si plan=free.
POST /internal sin autenticación (uso interno del bot).

### 9. ModBot/api/routers/stats.py
Total acciones, desglose por tipo (timeout/ban/delete),
top 5 ofensores, acciones por día (últimos 7 días).

### 10. ModBot/api/routers/settings.py
GET / y PATCH / para configuración global del usuario.

### 11. ModBot/api/routers/billing.py
Stripe: checkout, portal, webhook (4 eventos).
MercadoPago: checkout, webhook.
GET /status.
Al cancelar: downgrade a Free, NO eliminar cuenta.

### 12. ModBot/api/main.py
FastAPI con lifespan (init_db en startup).
CORS middleware.
Todos los routers incluidos con prefijos correctos.
GET /api/health → {"status": "ok"}.

### 13. ModBot/api/Dockerfile
Python 3.12-slim, libpq-dev, usuario no-root, uvicorn con 2 workers.

### 14. ModBot/bot/channel_bot.py
ChannelBot con blacklist compilada en regex.
BASE_PATTERNS mínimos incluidos.
Normalización: leet speak, espacios, símbolos.
Métodos: blacklist_match(), update_config(), propiedades.

### 15. ModBot/bot/manager.py
BotManager con dict interno channel_name → ChannelBot.
Métodos: join(), leave(), sync_from_db(), get_channel_bot(), active_channels().

### 16. ModBot/bot/main.py
ModBot(commands.Bot) con twitchio.
event_ready: sync inicial + _sync_loop task.
event_message: quota check → blacklist → IA (si Pro) → acción → log.
Perspective API con aiohttp, timeout 3s, si falla continuar.
_sync_loop: cada 60 segundos.

### 17. ModBot/bot/Dockerfile
Python 3.12-slim, usuario no-root, CMD python main.py.

## Al terminar
Mostrar:
1. Comando para arrancar: cd ModBot && docker compose up -d --build
2. Verificar: curl http://localhost:8000/api/health
3. Cualquier variable de entorno que necesite valor antes de arrancar
