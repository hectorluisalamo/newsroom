#!/usr/bin/env bash
set -euo pipefail

PRIVATE_CONFIG="${1:-../newsroom-config/config}"

if [ ! -d "$PRIVATE_CONFIG" ]; then
  echo "Private config not found at: $PRIVATE_CONFIG"
  echo "Usage: $0 [path-to-private-config-dir]"
  exit 1
fi

rsync -av --delete "$PRIVATE_CONFIG/" ./config/
echo "Synced private config from $PRIVATE_CONFIG"
