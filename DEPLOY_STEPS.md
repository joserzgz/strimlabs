1. Preparar el servidor

# Conectar por SSH
ssh root@TU_IP

# Actualizar sistema
apt update && apt upgrade -y

# Instalar dependencias base
apt install -y curl git ufw

# Instalar Docker (oficial)
curl -fsSL https://get.docker.com | sh
systemctl enable docker

# Instalar Node.js 20 (para buildear el frontend)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

2. Firewall

ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

3. DNS

En tu panel DNS de strimlabs.com, crea un registro A:

modbot.strimlabs.com  →  TU_IP_DEL_SERVIDOR

Espera a que propague (puedes verificar con dig modbot.strimlabs.com).

4. Estructura del proyecto

El repositorio tiene esta estructura:

strimlabs.com/
├── api/                  ← API compartida (core + services)
│   ├── core/             ← Plataforma: auth, billing, settings, db
│   ├── services/modbot/  ← Servicio ModBot: channels, blacklist, history, stats
│   ├── main.py
│   ├── Dockerfile
│   └── Dockerfile.prod
├── ModBot/
│   ├── bot/              ← Bots (Twitch + Discord)
│   ├── web/              ← Frontend React del dashboard
│   ├── nginx/            ← Configs nginx
│   ├── deploy.sh
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── .env / .env.example
├── landing/              ← Landing page corporativa
└── shared/               ← Assets compartidos

5. Subir el codigo

# Opcion A: Git
cd /opt
git clone TU_REPO strimlabs

# Opcion B: rsync desde tu maquina local
rsync -avz --exclude node_modules --exclude .env --exclude __pycache__ \
  D:/Proyectos/strimlabs.com/ root@TU_IP:/opt/strimlabs/

6. Configurar variables de entorno

cd /opt/strimlabs/ModBot
cp .env.example .env
nano .env

Editar con valores reales de produccion:

# PostgreSQL
POSTGRES_HOST=sl-postgres
POSTGRES_PORT=5432
POSTGRES_DB=strimlabs
POSTGRES_USER=strimlabs
POSTGRES_PASSWORD=UN_PASSWORD_SEGURO_GENERADO

# Twitch (dev.twitch.tv → tu app)
TWITCH_CLIENT_ID=tu_client_id
TWITCH_CLIENT_SECRET=tu_client_secret
TWITCH_REDIRECT_URI=https://modbot.strimlabs.com/api/auth/twitch/callback

# Twitch Bot
TWITCH_BOT_TOKEN=oauth:tu_bot_token
TWITCH_BOT_NICK=strimlabs_bot

# Discord (discord.com/developers → tu app)
DISCORD_CLIENT_ID=tu_client_id
DISCORD_CLIENT_SECRET=tu_client_secret
DISCORD_REDIRECT_URI=https://modbot.strimlabs.com/api/auth/discord/callback
DISCORD_BOT_REDIRECT_URI=https://modbot.strimlabs.com/api/channels/discord-bot/callback
DISCORD_BOT_TOKEN=tu_bot_token

# JWT (generar uno unico)
JWT_SECRET=$(openssl rand -hex 32)
JWT_EXPIRE_HOURS=8
ADMIN_PASSWORD=un_password_admin_seguro

# Stripe (produccion)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...

# MercadoPago (produccion)
MP_ACCESS_TOKEN=APP_USR-...
MP_WEBHOOK_SECRET=...

# Perspective API
PERSPECTIVE_API_KEY=tu_api_key

# URLs (PRODUCCION)
FRONTEND_URL=https://modbot.strimlabs.com
API_URL=https://modbot.strimlabs.com/api
API_BASE=http://sl-api:8000

7. Registrar OAuth callbacks

Twitch (dev.twitch.tv)

- OAuth Redirect URL: https://modbot.strimlabs.com/api/auth/twitch/callback

Discord (discord.com/developers/applications)

- Redirects:
  - https://modbot.strimlabs.com/api/auth/discord/callback
  - https://modbot.strimlabs.com/api/channels/discord-bot/callback
- Bot: activar MESSAGE CONTENT privileged intent
- OAuth2 scopes: identify, email, bot
- Bot permissions: Moderate Members, Ban Members, Manage Messages, Read Message History, View Channels

Stripe

- Webhook endpoint: https://modbot.strimlabs.com/api/billing/stripe/webhook
- Eventos: checkout.session.completed, customer.subscription.deleted, customer.subscription.updated

MercadoPago

- Notification URL: https://modbot.strimlabs.com/api/billing/mp/webhook

8. Deploy inicial

cd /opt/strimlabs/ModBot
chmod +x deploy.sh

# Edita deploy.sh y cambia EMAIL a tu email real
nano deploy.sh

# Deploy inicial (HTTP, sin SSL todavia)
./deploy.sh initial

Esto hace:
1. Buildea el frontend React (web/dist/)
2. Copia la config nginx HTTP-only
3. Levanta los 6 contenedores (postgres, api, twitch-bot, discord-bot, nginx, certbot)

Nota: docker-compose.prod.yml referencia ../api (la API esta en la raiz del repo, no dentro de ModBot/).

9. Verificar que funciona en HTTP

# Verificar contenedores
docker compose -f docker-compose.prod.yml ps

# Test health check
curl http://modbot.strimlabs.com/api/health
# Debe responder: {"status":"ok"}

# Ver logs si algo falla
docker logs sl-api
docker logs sl-nginx
docker logs sl-postgres

10. Activar SSL

./deploy.sh ssl

Esto:
1. Pide un certificado Let's Encrypt via webroot challenge
2. Cambia la config nginx a HTTPS
3. Recarga nginx

Verificar:
curl https://modbot.strimlabs.com/api/health

11. Verificar todos los servicios

# API
curl https://modbot.strimlabs.com/api/health

# Frontend — abrir en navegador
# https://modbot.strimlabs.com → pagina de Login

# Twitch bot
docker logs sl-twitch-bot

# Discord bot
docker logs sl-discord-bot

# Base de datos
docker exec sl-postgres psql -U strimlabs -c "SELECT count(*) FROM users;"

12. Renovacion SSL automatica

El contenedor certbot ya renueva automaticamente cada 12h. Para recargar nginx despues de renovar, agrega un cron:

crontab -e

Agregar:
0 5 * * * docker exec sl-nginx nginx -s reload

13. Updates futuros

Cuando hagas cambios al codigo:

cd /opt/strimlabs/ModBot
git pull  # o rsync de nuevo
./deploy.sh update

14. Backups de la base de datos

# Backup manual
docker exec sl-postgres pg_dump -U strimlabs strimlabs > backup_$(date +%Y%m%d).sql

# Cron diario (agregar a crontab)
0 3 * * * docker exec sl-postgres pg_dump -U strimlabs strimlabs > /opt/backups/modbot_$(date +\%Y\%m\%d).sql
