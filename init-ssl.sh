#!/usr/bin/env bash
# -------------------------------------------------------------------
# init-ssl.sh — One-shot SSL setup for managelibrary.app
#
# Run this ONCE on the production server after cloning the repo
# and creating .env.docker:
#
#   cd ~/library_checkout
#   bash init-ssl.sh
#
# What it does:
#   1. Installs certbot on the host (via snap)
#   2. Stops any containers occupying ports 80/443
#   3. Obtains a Let's Encrypt certificate (standalone mode)
#   4. Adds a renewal hook that reloads nginx inside Docker
#   5. Starts the full Docker Compose stack
# -------------------------------------------------------------------
set -euo pipefail

DOMAIN="managelibrary.app"
EMAIL="malikahon2005@gmail.com"
COMPOSE_FILE="$(cd "$(dirname "$0")" && pwd)/docker-compose.yml"

echo "==> Step 1: Ensure certbot is installed"
if ! command -v certbot &>/dev/null; then
    sudo snap install --classic certbot
    sudo ln -sf /snap/bin/certbot /usr/bin/certbot
    echo "    certbot installed via snap."
else
    echo "    certbot already installed."
fi

echo "==> Step 2: Free ports 80/443 (stop running containers)"
docker compose down 2>/dev/null || true

echo "==> Step 3: Obtain SSL certificate (standalone mode)"
sudo certbot certonly --standalone \
    -d "$DOMAIN" -d "www.$DOMAIN" \
    --agree-tos --no-eff-email \
    --email "$EMAIL"

echo "==> Step 4: Set up renewal deploy hook (reloads nginx)"
sudo mkdir -p /etc/letsencrypt/renewal-hooks/deploy
sudo tee /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh > /dev/null << EOF
#!/bin/bash
docker compose -f $COMPOSE_FILE exec -T nginx nginx -s reload
EOF
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh

echo "==> Step 5: Start the full stack"
docker compose up -d --build

echo ""
echo "Done! Verify with:"
echo "  curl -I https://$DOMAIN"
