#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/server.pid"

if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    rm -f "$PID_FILE"
    echo "✅ InnKeeper Pro server stopped (PID $PID)"
  else
    echo "⚠️  Server not running (stale PID file removed)"
    rm -f "$PID_FILE"
  fi
else
  fuser -k 8080/tcp 2>/dev/null && echo "✅ Killed process on port 8080" || echo "ℹ️  No server running on port 8080"
fi
