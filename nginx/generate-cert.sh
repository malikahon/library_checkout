#!/bin/sh
# generates a self-signed TLS certificate 
# mount the ssl_certs volume to /etc/nginx/ssl in the nginx service
# replace cert.pem and key.pem with real certificates for production use

SSL_DIR="/etc/nginx/ssl"
CERT="$SSL_DIR/cert.pem"
KEY="$SSL_DIR/key.pem"

if [ -f "$CERT" ] && [ -f "$KEY" ]; then
    echo "SSL certificates already exist — skipping generation."
    exit 0
fi

echo "Generating self-signed SSL certificate..."
mkdir -p "$SSL_DIR"

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$KEY" \
    -out "$CERT" \
    -subj "/C=US/ST=State/L=City/O=Organisation/CN=localhost"

echo "Self-signed certificate generated at $CERT"
