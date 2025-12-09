#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH=${ATLAS_OPS_CONFIG_PATH:-/data/atlas_ops.config.yaml}
mkdir -p /data

if [ ! -f "$CONFIG_PATH" ]; then
  atlas-ops install backend \
    --config "$CONFIG_PATH" \
    --host "${ATLAS_OPS_HOST:-0.0.0.0}" \
    --port "${ATLAS_OPS_PORT:-8000}" \
    --db-url "${ATLAS_OPS_DB_URL:-sqlite:////data/atlas_ops.db}" \
    --shared-token "${ATLAS_OPS_SHARED_TOKEN:-changeme}" \
    --no-interactive \
    --force
fi

atlas-ops db migrate --config "$CONFIG_PATH"

exec atlas-ops serve --config "$CONFIG_PATH"
