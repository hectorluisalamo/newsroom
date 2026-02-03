#!/usr/bin/env bash
set -euo pipefail

if [ -f "config/sources.yaml" ]; then
  echo "config/ already populated. Skipping."
  exit 0
fi

mkdir -p config/voices
cp config.example/sources.yaml config/sources.yaml
cp config.example/qa.yaml config/qa.yaml
cp config.example/cluster.yaml config/cluster.yaml
cp config.example/voices/science_tech.md config/voices/science_tech.md

echo "Initialized config/ from config.example/"
echo "For production config, use scripts/sync_private_config.sh"
