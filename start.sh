#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$SCRIPT_DIR/server.log"
PID_FILE="$SCRIPT_DIR/server.pid"
PORT=8080

if [ -f "$PID_FILE" ]; then
  kill $(cat "$PID_FILE") 2>/dev/null && echo "Stopped previous server"
  rm -f "$PID_FILE"
fi
fuser -k ${PORT}/tcp 2>/dev/null || true
sleep 1

echo ""
echo "╔════════════════════════════════════════╗"
echo "║   🏨  InnKeeper Pro — Starting Up     ║"
echo "╚════════════════════════════════════════╝"
echo ""

nohup python3 "$SCRIPT_DIR/app.py" > "$LOG" 2>&1 &
echo $! > "$PID_FILE"
sleep 3

if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
  echo "  ✅ Server running  (PID: $(cat $PID_FILE))"
  echo ""
  echo "  🌐 Open this URL in your browser:"
  echo "     ➜  http://$(hostname -I | awk '{print $1}'):${PORT}"
  echo "     ➜  http://localhost:${PORT}"
  echo ""
  echo "  📡 REST API:   http://localhost:${PORT}/api/"
  echo "  📋 Live logs:  tail -f $LOG"
  echo "  🛑 To stop:    bash $(dirname $SCRIPT_DIR)/stop.sh"
  echo ""
else
  echo "  ❌ Failed to start. Check logs below:"
  echo "---"
  cat "$LOG"
fi
