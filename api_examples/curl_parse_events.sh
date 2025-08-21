
#!/usr/bin/env bash
set -euo pipefail
ENDPOINT="${1:-https://YOUR_CLOUD_ENDPOINT/parse_events}"
curl -s -X POST "$ENDPOINT"   -H 'Content-Type: application/json'   -d '{"text":"M/W/F 10:00–10:50 AM — Algebra II, Room B209 — 08/26–12/13 (no class 11/28).","timezone":"America/Detroit","default_year":2025}'
