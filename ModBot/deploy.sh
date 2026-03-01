#!/usr/bin/env bash
set -euo pipefail

# ── ModBot production deploy script ──────────────────────────
# Usage: ./deploy.sh [initial|update|ssl]

DOMAIN="modbot.strimlabs.com"
EMAIL="admin@strimlabs.com"  # Change to your email
COMPOSE="docker compose -f docker-compose.prod.yml"

case "${1:-update}" in

  initial)
    echo "═══ Initial deployment ═══"

    # Build web frontend
    echo "→ Building web frontend..."
    cd web && npm ci && npm run build && cd ..

    # Use initial nginx config (HTTP only, no SSL)
    echo "→ Using initial HTTP-only nginx config..."
    cp nginx/conf.d/initial.conf nginx/active.conf

    # Start services
    echo "→ Starting services..."
    $COMPOSE up -d --build

    echo ""
    echo "══════════════════════════════════════════════"
    echo "  Services running on HTTP. Now run:"
    echo "  ./deploy.sh ssl"
    echo "══════════════════════════════════════════════"
    ;;

  ssl)
    echo "═══ Generating SSL certificate ═══"

    # Request certificate
    docker compose -f docker-compose.prod.yml run --rm certbot \
      certbot certonly --webroot \
      -w /var/www/certbot \
      -d "$DOMAIN" \
      --email "$EMAIL" \
      --agree-tos \
      --no-eff-email

    # Switch to HTTPS nginx config
    echo "→ Switching to HTTPS config..."
    cp nginx/conf.d/modbot.conf nginx/active.conf

    # Reload nginx
    docker exec sl-nginx nginx -s reload

    echo ""
    echo "══════════════════════════════════════════════"
    echo "  SSL active! https://$DOMAIN"
    echo "══════════════════════════════════════════════"
    ;;

  update)
    echo "═══ Updating deployment ═══"

    echo "→ Building web frontend..."
    cd web && npm ci && npm run build && cd ..

    echo "→ Rebuilding and restarting services..."
    $COMPOSE up -d --build

    echo ""
    echo "══════════════════════════════════════════════"
    echo "  Update complete! https://$DOMAIN"
    echo "══════════════════════════════════════════════"
    ;;

  *)
    echo "Usage: ./deploy.sh [initial|update|ssl]"
    exit 1
    ;;
esac
