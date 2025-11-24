#!/usr/bin/env bash
# Check health and image info for all services defined in docker-compose.yml
# Usage: ./scripts/check_health.sh
set -eu

# Ensure we're in repo root where docker-compose.yml lives
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
cd "$REPO_ROOT"

echo "Checking docker-compose configuration..."
docker compose config >/dev/null 2>&1 || { echo "docker compose config failed"; exit 1; }

services=$(docker compose ps --services || true)
if [ -z "$services" ]; then
  echo "No services found (is docker compose up?). Exiting."; exit 0
fi

for s in $services; do
  echo "== Service: $s =="
  cid=$(docker compose ps -q "$s" 2>/dev/null || true)
  if [ -z "$cid" ]; then
    echo "  Status: not running"
    echo
    continue
  fi

  image=$(docker inspect --format='{{.Config.Image}}' "$cid" 2>/dev/null || true)
  image_id=$(docker inspect --format='{{.Image}}' "$cid" 2>/dev/null || true)
  status=$(docker inspect --format='{{.State.Status}}' "$cid" 2>/dev/null || true)
  health=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no-health{{end}}' "$cid" 2>/dev/null || true)
  restarts=$(docker inspect --format='{{.RestartCount}}' "$cid" 2>/dev/null || true)

  echo "  Container ID: $cid"
  echo "  Image: ${image:-unknown}"
  echo "  ImageID: ${image_id:-unknown}"
  echo "  Status: ${status:-unknown}"
  echo "  Health: ${health:-unknown}"
  echo "  Restarts: ${restarts:-0}"

  echo "  Recent logs (tail 50):"
  docker logs --tail 50 "$cid" 2>&1 || true
  echo
done

# Show local images mentioned in .env for quick reference
echo "Local images (matching .env vars):"
if [ -f .env ]; then
  grep -E '^(HELLO_IMAGE|NGINX_IMAGE)=' .env || true
  echo
  awk -F= '/=/{print $1"="$2}' .env | while IFS== read -r key val; do
    echo "  $key -> $val"
    docker images --format '  {{.Repository}}:{{.Tag}}  {{.ID}}  {{.Size}}' | grep "$(echo "$val" | cut -d':' -f1)" || true
  done
fi

echo "Health check complete."

