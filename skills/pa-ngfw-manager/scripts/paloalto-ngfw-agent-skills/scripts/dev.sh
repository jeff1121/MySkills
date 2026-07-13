#!/usr/bin/env bash
set -euo pipefail

echo "==> Installing pa-agent in editable mode with dev dependencies..."
pip install -e ".[dev]"

echo "==> Creating .env template if not exists..."
if [ ! -f .env ]; then
    cat > .env <<'EOF'
# PAN-OS Connection
PANOS_HOST=https://10.0.0.1
PANOS_API_KEY=
PANOS_USERNAME=
PANOS_PASSWORD=
PANOS_VSYS=vsys1
PANOS_VERIFY_TLS=false
PANOS_TIMEOUT=30
PANOS_RATE_LIMIT=10

# Backup
BACKUP_DIR=./backups

# S3/MinIO (optional)
# S3_ENDPOINT_URL=http://localhost:9000
# S3_BUCKET=pa-backups
# S3_PREFIX=
# AWS_ACCESS_KEY_ID=minioadmin
# AWS_SECRET_ACCESS_KEY=minioadmin
# S3_REGION=us-east-1
# S3_USE_SSL=false
EOF
    echo "    Created .env template — edit with your values"
fi

echo "==> Done! Run 'pa-agent --help' to get started."
