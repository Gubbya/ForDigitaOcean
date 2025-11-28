#!/usr/bin/env bash
set -euo pipefail

# prepare_deploy_dirs.sh
# Create the minimal host directories expected by `docker-compose.yml`.
# Usage: ./scripts/prepare_deploy_dirs.sh [APP_DIR]

APP_DIR="${1:-.}"
NGINX_DIR="$APP_DIR/nginx"

echo "Preparing deploy directories under: $APP_DIR"

mkdir -p "$NGINX_DIR"
mkdir -p "$NGINX_DIR/conf.d"
mkdir -p "$NGINX_DIR/logs"
mkdir -p "$NGINX_DIR/webroot"
mkdir -p "$NGINX_DIR/ssl"
mkdir -p "$NGINX_DIR/letsencrypt"

if [ "$(id -u)" -eq 0 ]; then
  if id -u www-data >/dev/null 2>&1; then
    chown -R www-data:www-data "$NGINX_DIR" || true
    echo "Set ownership to www-data:www-data for $NGINX_DIR"
  fi
fi

echo "Created directories:"
ls -la "$NGINX_DIR"
