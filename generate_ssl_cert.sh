#!/bin/bash
# Script to generate self-signed SSL certificates for development/testing
# For production, use certificates from a trusted CA (e.g., Let's Encrypt)

set -e

CERT_DIR="ssl"
CERT_FILE="$CERT_DIR/cert.pem"
KEY_FILE="$CERT_DIR/key.pem"

echo "Generating self-signed SSL certificate for development..."

# Create SSL directory if it doesn't exist
mkdir -p "$CERT_DIR"

# Generate private key and certificate
openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -days 365 \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1,IP:0.0.0.0"

# Set appropriate permissions
chmod 600 "$KEY_FILE"
chmod 644 "$CERT_FILE"

echo "SSL certificates generated successfully!"
echo ""
echo "Certificate file: $CERT_FILE"
echo "Private key file: $KEY_FILE"
echo ""
echo "To use HTTPS, set these environment variables:"
echo "  export SSL_CERTFILE=$CERT_FILE"
echo "  export SSL_KEYFILE=$KEY_FILE"
echo "  export SSL_PORT=3000"
echo ""
echo "Then start Gunicorn with:"
echo "  gunicorn --bind 0.0.0.0:3000 --workers 1 --preload app:app"
echo ""
echo "Access the application at: https://localhost:3000"
echo ""
echo "Note: Browsers will show a security warning for self-signed certificates."
echo "This is normal for development. Click 'Advanced' and 'Proceed to localhost' to continue."
