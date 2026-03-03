#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
#  Strimlabs — Deploy script (Plesk + Docker)
# ═══════════════════════════════════════════════════════════════
#  Usage: ./deploy.sh [start|update|stop|logs|backup]
# ═══════════════════════════════════════════════════════════════

COMPOSE="docker compose -f docker-compose.prod.yml"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$PROJECT_DIR"

case "${1:-help}" in

  start)
    echo "═══ Iniciando Strimlabs (primera vez) ═══"

    # Verificar que existe el .env
    if [ ! -f .env ]; then
      echo "ERROR: No se encontró el archivo .env"
      echo "Copia .env.production como .env y completa los valores:"
      echo "  cp .env.production .env && nano .env"
      exit 1
    fi

    echo "→ Construyendo y levantando todos los servicios..."
    $COMPOSE up -d --build

    echo ""
    echo "→ Esperando a que la API esté lista..."
    sleep 5

    # Verificar health
    if curl -sf http://127.0.0.1:3001/api/health > /dev/null 2>&1; then
      echo "  ✓ API respondiendo correctamente"
    else
      echo "  ! La API aún está iniciando. Verifica con:"
      echo "    docker logs sl-api"
    fi

    echo ""
    echo "══════════════════════════════════════════════"
    echo "  Servicios iniciados."
    echo "  Landing:   http://127.0.0.1:3000"
    echo "  Dashboard: http://127.0.0.1:3001"
    echo "  API:       http://127.0.0.1:3001/api/health"
    echo ""
    echo "  Configura el proxy reverso en Plesk"
    echo "  para strimlabs.com y app.strimlabs.com"
    echo "══════════════════════════════════════════════"
    ;;

  update)
    echo "═══ Actualizando Strimlabs ═══"

    echo "→ Descargando cambios..."
    git pull origin main

    echo "→ Reconstruyendo servicios..."
    $COMPOSE up -d --build

    echo "→ Limpiando imágenes antiguas..."
    docker image prune -f

    echo ""
    echo "══════════════════════════════════════════════"
    echo "  Actualización completa."
    echo "══════════════════════════════════════════════"
    ;;

  stop)
    echo "═══ Deteniendo servicios ═══"
    $COMPOSE down
    echo "  Servicios detenidos. Los datos de PostgreSQL se conservan."
    ;;

  restart)
    echo "═══ Reiniciando servicios ═══"
    $COMPOSE restart
    echo "  Servicios reiniciados."
    ;;

  logs)
    # Uso: ./deploy.sh logs [servicio]
    # Ejemplo: ./deploy.sh logs api
    SERVICE="${2:-}"
    if [ -n "$SERVICE" ]; then
      $COMPOSE logs -f --tail=100 "$SERVICE"
    else
      $COMPOSE logs -f --tail=50
    fi
    ;;

  status)
    echo "═══ Estado de servicios ═══"
    $COMPOSE ps
    echo ""
    echo "── Health check ──"
    curl -sf http://127.0.0.1:3001/api/health 2>/dev/null && echo " API: OK" || echo " API: DOWN"
    curl -sf http://127.0.0.1:3000 > /dev/null 2>&1 && echo " Landing: OK" || echo " Landing: DOWN"
    curl -sf http://127.0.0.1:3001 > /dev/null 2>&1 && echo " Dashboard: OK" || echo " Dashboard: DOWN"
    ;;

  backup)
    echo "═══ Backup de base de datos ═══"
    BACKUP_DIR="$PROJECT_DIR/backups"
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/strimlabs_${TIMESTAMP}.sql.gz"

    docker exec sl-postgres pg_dump -U "${POSTGRES_USER:-strimlabs}" "${POSTGRES_DB:-strimlabs}" \
      | gzip > "$BACKUP_FILE"

    echo "  Backup guardado en: $BACKUP_FILE"
    echo "  Tamaño: $(du -h "$BACKUP_FILE" | cut -f1)"

    # Mantener solo los últimos 7 backups
    ls -t "$BACKUP_DIR"/strimlabs_*.sql.gz | tail -n +8 | xargs -r rm
    echo "  (Se conservan los últimos 7 backups)"
    ;;

  *)
    echo "═══ Strimlabs Deploy Script ═══"
    echo ""
    echo "Uso: ./deploy.sh <comando>"
    echo ""
    echo "Comandos:"
    echo "  start    - Primera ejecución (construye e inicia todo)"
    echo "  update   - Actualizar (git pull + rebuild)"
    echo "  stop     - Detener todos los servicios"
    echo "  restart  - Reiniciar servicios"
    echo "  logs     - Ver logs (opción: logs <servicio>)"
    echo "  status   - Ver estado de servicios"
    echo "  backup   - Backup de la base de datos"
    echo ""
    echo "Ejemplos:"
    echo "  ./deploy.sh start"
    echo "  ./deploy.sh logs api"
    echo "  ./deploy.sh backup"
    ;;

esac
