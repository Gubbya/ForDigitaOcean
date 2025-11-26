#!/bin/bash
# Creates self-signed certs for local testing and places them in ./nginx/ssl
set -euo pipefail
ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
NGINX_DIR="$ROOT_DIR/nginx"
SSL_DIR="$NGINX_DIR/ssl"

mkdir -p "$SSL_DIR"

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$SSL_DIR/privkey.pem" -out "$SSL_DIR/fullchain.pem" \
  -subj "/CN=localhost"

chmod 600 "$SSL_DIR/privkey.pem"
chmod 644 "$SSL_DIR/fullchain.pem"

echo "Created self-signed certs in $SSL_DIR"

echo "To use these: uncomment the ssl volume in docker-compose.yml and restart nginx service."
