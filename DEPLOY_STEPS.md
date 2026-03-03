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
   ├── strimlabs.com       → 127.0.0.1:3300  (contenedor: sl_prod_landing)
   └── app.strimlabs.com   → 127.0.0.1:3301  (contenedor: sl_prod_web)
                                 │
                                 └── /api/* → sl_prod_api:8000 (red Docker interna)
                                                │
                                                └── sl_prod_postgres:5432 (red Docker interna)

   sl_prod_twitch_bot  ──→ sl_prod_api:8000 (red Docker interna)
   sl_prod_discord_bot ──→ sl_prod_api:8000 (red Docker interna)
```

### Contenedores

| Contenedor          | Imagen             | Puerto expuesto      | Función                      |
|---------------------|--------------------|----------------------|------------------------------|
| sl_prod_postgres    | postgres:16-alpine | — (solo interno)     | Base de datos                |
| sl_prod_api         | python:3.12-slim   | — (solo interno)     | FastAPI (2 workers)          |
| sl_prod_twitch_bot  | python:3.12-slim   | —                    | Bot moderación Twitch        |
| sl_prod_discord_bot | python:3.12-slim   | —                    | Bot moderación Discord       |
| sl_prod_landing     | nginx:alpine       | 127.0.0.1:3300       | Landing page (strimlabs.com) |
| sl_prod_web         | nginx:alpine       | 127.0.0.1:3301       | Dashboard + proxy API        |

### Contenedores existentes en el servidor (no se tocan)

| Contenedor       | Puerto              |
|------------------|---------------------|
| cg_qa_api        | 127.0.0.1:3102      |
| cg_qa_frontend   | 127.0.0.1:3103      |
| cg_qa_landing    | 127.0.0.1:3104      |
| tp_qa_api        | 127.0.0.1:3109      |
| tp_qa_frontend   | 127.0.0.1:3110      |
| si_prod_www      | 127.0.0.1:3201      |
| portainer        | 127.0.0.1:9000      |

> Strimlabs usa el rango **33xx** para evitar conflictos.

---

## Paso 1 — Verificar Docker en el servidor

Docker ya debería estar instalado (Plesk lo usa). Conéctate por SSH y verifica:

```bash
ssh root@TU_IP

docker --version
docker compose version
```

Si `docker compose` (v2) no funciona:

```bash
apt update && apt install -y docker-compose-plugin
```

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

## Paso 3 — Crear subdominio en Plesk

### 3.1 — Dominio principal: strimlabs.com

Ya está configurado en Plesk. El proxy se configura en el Paso 7.

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
git clone https://github.com/joserzgz/strimlabs.git strimlabs
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

### Valores importantes a generar:

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
API_BASE=http://sl_prod_api:8000
POSTGRES_HOST=sl_prod_postgres
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
NAME                  STATUS              PORTS
sl_prod_postgres      running (healthy)
sl_prod_api           running
sl_prod_twitch_bot    running
sl_prod_discord_bot   running
sl_prod_landing       running             127.0.0.1:3300->80/tcp
sl_prod_web           running             127.0.0.1:3301->80/tcp
```

### Verificar manualmente:

```bash
# Health check del API (a través del proxy interno del contenedor web)
curl http://127.0.0.1:3301/api/health
# → {"status":"ok"}

# Landing page
curl -s http://127.0.0.1:3300 | head -5

# Ver logs
docker logs sl_prod_api
docker logs sl_prod_twitch_bot
docker logs sl_prod_discord_bot
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
    proxy_pass http://127.0.0.1:3300;
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
    proxy_pass http://127.0.0.1:3301;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 30s;
    proxy_connect_timeout 5s;
}
```

4. Click **OK** / **Apply**

> **Nota:** El contenedor `sl_prod_web` ya tiene nginx interno que:
> - Sirve los archivos estáticos del SPA
> - Proxea `/api/*` al contenedor `sl_prod_api` por la red interna Docker
>
> Plesk solo necesita proxear todo el tráfico al puerto 3301.

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
docker exec sl_prod_postgres psql -U strimlabs -c "SELECT count(*) FROM users;"
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

> Los datos de PostgreSQL se conservan en el volumen Docker `sl_prod_pgdata`.

---

## Restaurar un backup

```bash
# Descomprimir y restaurar
gunzip -c backups/strimlabs_20260302_030000.sql.gz | \
  docker exec -i sl_prod_postgres psql -U strimlabs strimlabs
```

---

## Troubleshooting

### Los contenedores no arrancan

```bash
docker compose -f docker-compose.prod.yml logs
```

### La API no responde

```bash
docker logs sl_prod_api
# Verificar que PostgreSQL está healthy
docker exec sl_prod_postgres pg_isready -U strimlabs
```

### El bot de Twitch no se conecta

```bash
docker logs sl_prod_twitch_bot
# Verificar que TWITCH_BOT_TOKEN es válido
# Verificar que la API responde internamente
docker exec sl_prod_twitch_bot curl -s http://sl_prod_api:8000/api/health
```

### Error 502 Bad Gateway en Plesk

- Verificar que los contenedores están corriendo: `docker ps | grep sl_prod`
- Verificar que los puertos están escuchando: `ss -tlnp | grep -E '3300|3301'`
- Verificar los logs de nginx de Plesk: `/var/log/nginx/error.log`

### Reconstruir desde cero (sin perder datos)

```bash
cd /opt/strimlabs
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build --force-recreate
```

---

## Referencia rápida de puertos

| Proyecto         | Rango  | Contenedores                       |
|------------------|--------|------------------------------------|
| Control Gastos   | 31xx   | cg_qa_api, cg_qa_frontend, cg_qa_landing |
| TechPro AI       | 31xx   | tp_qa_api, tp_qa_frontend          |
| SIEM Web         | 32xx   | si_prod_www                        |
| **Strimlabs**    | **33xx** | **sl_prod_landing, sl_prod_web** |
