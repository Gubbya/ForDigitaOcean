#!/bin/bash
# Simple deploy + validation helper for droplet use.
# - pulls images, starts stack, checks basic health endpoints
set -euo pipefail
ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

# pull and bring up
if command -v docker-compose >/dev/null 2>&1; then
  docker-compose pull || true
  docker-compose up -d --remove-orphans
else
  docker compose pull || true
  docker compose up -d --remove-orphans
fi

sleep 3

# simple checks
echo "Containers:"
docker ps --filter name=fordigitaocean_ --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo
# local checks
echo "Local health checks (from droplet):"
curl -I --max-time 5 http://127.0.0.1/_health || true
curl -I --max-time 5 http://127.0.0.1/ || true

# Redis check
if docker ps -a --format '{{.Names}}' | grep -q redis; then
  echo "Checking redis ping..."
  docker exec -it $(docker ps --filter ancestor=redis:7-alpine --format '{{.Names}}' | head -n1) redis-cli ping || true
fi

echo "Done. If any checks failed, inspect logs: docker logs <container>"
