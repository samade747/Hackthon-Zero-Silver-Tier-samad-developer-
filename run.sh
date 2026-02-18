#!/usr/bin/env bash
# run.sh — Silver Tier startup script
#
# Usage:
#   bash run.sh           — Start all 6 processes via PM2
#   bash run.sh stop      — Stop all processes
#   bash run.sh restart   — Restart all processes
#   bash run.sh status    — Show PM2 status
#   bash run.sh logs      — Stream all logs
#   bash run.sh setup-wa  — Run WhatsApp QR code setup (first time only)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
  echo "[run.sh] Loaded .env"
else
  echo "[run.sh] WARNING: No .env file found. Copy .env.example to .env and fill it in."
fi

ACTION="${1:-start}"

case "$ACTION" in
  start)
    echo "[run.sh] Installing MCP server dependencies..."
    (cd mcp_servers/email_mcp && npm install --silent)
    (cd mcp_servers/browser_mcp && npm install --silent)

    echo "[run.sh] Starting all Silver Tier processes via PM2..."
    pm2 start ecosystem.config.js

    echo "[run.sh] Saving PM2 process list..."
    pm2 save

    echo ""
    echo "[run.sh] All processes started. Run 'pm2 status' to check."
    echo "[run.sh] Run 'pm2 logs' to stream logs from all processes."
    echo ""
    pm2 status
    ;;

  stop)
    echo "[run.sh] Stopping all processes..."
    pm2 stop all
    ;;

  restart)
    echo "[run.sh] Restarting all processes..."
    pm2 restart all
    ;;

  status)
    pm2 status
    ;;

  logs)
    pm2 logs --lines 50
    ;;

  setup-wa)
    echo "[run.sh] Running WhatsApp QR code setup..."
    echo "A browser window will open — scan the QR code, then press Enter."
    python watchers/whatsapp_watcher.py --setup
    ;;

  *)
    echo "Usage: bash run.sh [start|stop|restart|status|logs|setup-wa]"
    exit 1
    ;;
esac
