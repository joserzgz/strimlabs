# Strimlabs — Guía de Despliegue en Producción

> Servidor dedicado Debian 12 + Plesk + Docker
> Dominio: strimlabs.com

---

## Arquitectura

```
Internet
   │
   ▼
Plesk (nginx reverse proxy + SSL automático)
   │
   ├── strimlabs.com       → 127.0.0.1:3000  (contenedor: sl-landing)
   └── app.strimlabs.com   → 127.0.0.1:3001  (contenedor: sl-modbot-web)
                                 │
                                 └── /api/* → sl-api:8000 (red Docker interna)
                                                │
                                                └── sl-postgres:5432 (red Docker interna)

   sl-twitch-bot  ──→ sl-api:8000 (red Docker interna)
   sl-discord-bot ──→ sl-api:8000 (red Docker interna)
```

### Contenedores

| Contenedor       | Imagen                | Puerto expuesto     | Función                        |
|------------------|-----------------------|---------------------|--------------------------------|
| sl-postgres      | postgres:16-alpine    | — (solo interno)    | Base de datos                  |
| sl-api           | python:3.12-slim      | — (solo interno)    | FastAPI (2 workers)            |
| sl-twitch-bot    | python:3.12-slim      | —                   | Bot moderación Twitch          |
| sl-discord-bot   | python:3.12-slim      | —                   | Bot moderación Discord         |
| sl-landing       | nginx:alpine          | 127.0.0.1:3000      | Landing page (strimlabs.com)   |
| sl-modbot-web    | nginx:alpine          | 127.0.0.1:3001      | Dashboard + proxy API          |

---

## Paso 1 — Instalar Docker en el servidor

Conéctate por SSH al servidor:

```bash
ssh root@TU_IP
```

Instalar Docker CE (si no está instalado via Plesk):

```bash
# Instalar Docker oficial
curl -fsSL https://get.docker.com | sh

# Habilitar para que arranque con el sistema
systemctl enable docker
systemctl start docker

# Verificar
docker --version
docker compose version
```

> **Nota:** Si Plesk ya tiene la extensión Docker instalada, Docker ya estará disponible.
> Solo verifica que `docker compose` (v2) funcione.

---

## Paso 2 — Configurar DNS

En el panel de DNS de tu dominio (o en Plesk > DNS), crea estos registros A:

| Tipo | Host                  | Valor          |
|------|-----------------------|----------------|
| A    | strimlabs.com         | TU_IP_SERVIDOR |
| A    | app.strimlabs.com     | TU_IP_SERVIDOR |

Verifica que propaguen:

```bash
dig +short strimlabs.com
dig +short app.strimlabs.com
```

---

## Paso 3 — Crear subdominios en Plesk

### 3.1 — Dominio principal: strimlabs.com

Este ya debería estar configurado. Solo necesitamos asegurarnos de que el proxy esté correctamente configurado (se hace en el Paso 6).

### 3.2 — Subdominio: app.strimlabs.com

1. En Plesk → **Websites & Domains**
2. Click en **Add Subdomain**
3. Nombre: `app`
4. Document root: puede quedarse el default (no se usará, todo va por proxy)
5. Click **OK**

---

## Paso 4 — Subir el código al servidor

### Opción A: Git (recomendada)

```bash
cd /opt
git clone TU_REPO_URL strimlabs
cd /opt/strimlabs
```

### Opción B: rsync desde tu máquina local

```bash
rsync -avz --exclude node_modules --exclude .env --exclude __pycache__ \
  --exclude .git --exclude dist \
  ./  root@TU_IP:/opt/strimlabs/
```

---

## Paso 5 — Configurar variables de entorno

```bash
cd /opt/strimlabs

# Copiar template de producción
cp .env.production .env

# Editar con tus valores reales
nano .env
```

### Valores importantes a configurar:

```bash
# Genera password de PostgreSQL
openssl rand -base64 32
# Copia el resultado en POSTGRES_PASSWORD=

# Genera JWT secret
openssl rand -hex 32
# Copia el resultado en JWT_SECRET=

# Cambia ADMIN_PASSWORD por algo seguro
```

### URLs de producción (ya configuradas en el template):

```
FRONTEND_URL=https://app.strimlabs.com
API_URL=https://app.strimlabs.com/api
API_BASE=http://sl-api:8000
TWITCH_REDIRECT_URI=https://app.strimlabs.com/api/auth/twitch/callback
DISCORD_REDIRECT_URI=https://app.strimlabs.com/api/auth/discord/callback
DISCORD_BOT_REDIRECT_URI=https://app.strimlabs.com/api/channels/discord-bot/callback
```

---

## Paso 6 — Construir e iniciar los contenedores

```bash
cd /opt/strimlabs
chmod +x deploy.sh
./deploy.sh start
```

Esto construye las imágenes Docker (incluyendo los frontends con multi-stage build) y levanta todos los servicios.

### Verificar que están corriendo:

```bash
docker compose -f docker-compose.prod.yml ps
```

Deberías ver 6 contenedores en estado "Up":

```
sl-postgres     running (healthy)
sl-api          running
sl-twitch-bot   running
sl-discord-bot  running
sl-landing      running    0.0.0.0:3000->80/tcp
sl-modbot-web   running    0.0.0.0:3001->80/tcp
```

### Verificar manualmente:

```bash
# Health check del API
curl http://127.0.0.1:3001/api/health
# → {"status":"ok"}

# Landing page
curl -s http://127.0.0.1:3000 | head -5

# Ver logs
docker logs sl-api
docker logs sl-twitch-bot
docker logs sl-discord-bot
```

---

## Paso 7 — Configurar proxy reverso en Plesk

Plesk manejará el SSL y redirigirá el tráfico a los contenedores Docker.

### 7.1 — Para strimlabs.com (landing)

1. En Plesk → **Websites & Domains** → **strimlabs.com**
2. Click en **Apache & nginx Settings** (o **Hosting & DNS** → **Apache & nginx Settings**)
3. Scroll hasta **Additional nginx directives**
4. En la sección que aplica a HTTPS y HTTP, pega:

```nginx
location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

5. **Importante:** Marca la opción **"Proxy mode"** si está disponible, o desactiva **"Serve static files directly by nginx"** para que todo pase por el proxy.
6. Click **OK** / **Apply**

### 7.2 — Para app.strimlabs.com (dashboard + API)

1. En Plesk → **Websites & Domains** → **app.strimlabs.com**
2. Click en **Apache & nginx Settings**
3. En **Additional nginx directives**, pega:

```nginx
location / {
    proxy_pass http://127.0.0.1:3001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 30s;
    proxy_connect_timeout 5s;
}
```

4. Click **OK** / **Apply**

> **Nota:** El contenedor `sl-modbot-web` ya tiene nginx interno que:
> - Sirve los archivos estáticos del SPA
> - Proxea `/api/*` al contenedor `sl-api` por la red interna Docker
>
> Plesk solo necesita proxear todo el tráfico al puerto 3001.

---

## Paso 8 — Activar SSL en Plesk

### 8.1 — SSL para strimlabs.com

1. En Plesk → **Websites & Domains** → **strimlabs.com**
2. Click en **SSL/TLS Certificates**
3. Click en **Install** junto a **Let's Encrypt**
4. Marca: **Secure the domain** y **Include www.strimlabs.com**
5. Email: tu email
6. Click **Get it Free** / **Install**

### 8.2 — SSL para app.strimlabs.com

1. En Plesk → **Websites & Domains** → **app.strimlabs.com**
2. Click en **SSL/TLS Certificates**
3. Click en **Install** junto a **Let's Encrypt**
4. Marca: **Secure the subdomain**
5. Click **Get it Free** / **Install**

> Plesk renovará los certificados automáticamente.

### Verificar:

```bash
curl https://strimlabs.com
curl https://app.strimlabs.com/api/health
```

---

## Paso 9 — Registrar OAuth Callbacks

### Twitch (https://dev.twitch.tv/console)

En tu aplicación de Twitch:
- **OAuth Redirect URL:** `https://app.strimlabs.com/api/auth/twitch/callback`

### Discord (https://discord.com/developers/applications)

En tu aplicación de Discord:
- **Redirects:**
  - `https://app.strimlabs.com/api/auth/discord/callback`
  - `https://app.strimlabs.com/api/channels/discord-bot/callback`
- **Bot → Privileged Intents:** Activar `MESSAGE CONTENT INTENT`
- **Bot Permissions:** Moderate Members, Ban Members, Manage Messages, Read Message History, View Channels

### Stripe (https://dashboard.stripe.com)

- **Developers → Webhooks → Add endpoint**
- URL: `https://app.strimlabs.com/api/billing/stripe/webhook`
- Eventos: `checkout.session.completed`, `customer.subscription.deleted`, `customer.subscription.updated`
- Copia el **Signing secret** (`whsec_...`) en tu `.env` como `STRIPE_WEBHOOK_SECRET`

### MercadoPago

- **Configuración → Webhooks (IPN)**
- URL: `https://app.strimlabs.com/api/billing/mp/webhook`

---

## Paso 10 — Verificar todo

```bash
# Estado de contenedores
./deploy.sh status

# API health
curl https://app.strimlabs.com/api/health

# Landing
curl -I https://strimlabs.com

# Logs de cada servicio
./deploy.sh logs api
./deploy.sh logs twitch-bot
./deploy.sh logs discord-bot

# Base de datos
docker exec sl-postgres psql -U strimlabs -c "SELECT count(*) FROM users;"
```

Abre en el navegador:
- `https://strimlabs.com` → Landing page
- `https://app.strimlabs.com` → Login del dashboard

---

## Mantenimiento

### Actualizar la aplicación

```bash
cd /opt/strimlabs
./deploy.sh update
```

Esto hace `git pull` + rebuild de contenedores.

### Ver logs

```bash
# Todos los servicios
./deploy.sh logs

# Solo un servicio específico
./deploy.sh logs api
./deploy.sh logs twitch-bot
./deploy.sh logs discord-bot
./deploy.sh logs postgres
```

### Backup de base de datos

```bash
# Manual
./deploy.sh backup

# Automático diario (agregar a crontab)
crontab -e
```

Agregar esta línea:

```
0 3 * * * cd /opt/strimlabs && ./deploy.sh backup
```

### Reiniciar servicios

```bash
./deploy.sh restart
```

### Detener todo

```bash
./deploy.sh stop
```

> Los datos de PostgreSQL se conservan en el volumen Docker `pgdata`.

---

## Restaurar un backup

```bash
# Descomprimir y restaurar
gunzip -c backups/strimlabs_20260302_030000.sql.gz | \
  docker exec -i sl-postgres psql -U strimlabs strimlabs
```

---

## Troubleshooting

### Los contenedores no arrancan
```bash
docker compose -f docker-compose.prod.yml logs
```

### La API no responde
```bash
docker logs sl-api
# Verificar que PostgreSQL está healthy
docker exec sl-postgres pg_isready -U strimlabs
```

### El bot de Twitch no se conecta
```bash
docker logs sl-twitch-bot
# Verificar que TWITCH_BOT_TOKEN es válido
# Verificar que la API responde internamente
docker exec sl-twitch-bot curl -s http://sl-api:8000/api/health
```

### Error 502 Bad Gateway en Plesk
- Verificar que los contenedores están corriendo: `docker ps`
- Verificar que los puertos están escuchando: `ss -tlnp | grep -E '3000|3001'`
- Verificar los logs de nginx de Plesk: `/var/log/nginx/error.log`

### Reconstruir desde cero (sin perder datos)
```bash
cd /opt/strimlabs
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build --force-recreate
```
