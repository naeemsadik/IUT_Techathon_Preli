#!/usr/bin/env bash
# Demo launcher — bash counterpart of scripts/demo.ps1.
#
# Usage:
#   ./scripts/demo.sh                  # backend + simulator
#   ./scripts/demo.sh --with-bot       # backend + simulator + Discord bot
#   ./scripts/demo.sh --stop           # stop everything started here

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$REPO_ROOT/logs_demo"
MARKER="$LOG_DIR/.demo-pids.txt"

WITH_BOT=0
STOP=0
for arg in "$@"; do
    case "$arg" in
        --with-bot) WITH_BOT=1 ;;
        --stop)     STOP=1 ;;
        *) echo "Unknown arg: $arg"; exit 1 ;;
    esac
done

mkdir -p "$LOG_DIR"

stop_demo() {
    if [ ! -f "$MARKER" ]; then
        echo "[stop] No marker file. Nothing to stop."
        return
    fi
    while read -r pid; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "[stop] Killing PID $pid"
            kill "$pid" 2>/dev/null || true
        fi
    done < "$MARKER"
    rm -f "$MARKER"
}

start_demo() {
    if [ ! -d "$REPO_ROOT/.venv" ]; then
        echo "[setup] Creating venv and installing requirements..."
        python3 -m venv "$REPO_ROOT/.venv"
        "$REPO_ROOT/.venv/bin/pip" install -r "$REPO_ROOT/requirements.txt"
    fi
    PYTHON="$REPO_ROOT/.venv/bin/python"
    PIDS=()

    echo "[start] Backend (uvicorn) on http://127.0.0.1:8000"
    "$PYTHON" -m uvicorn iut_server.app.main:app --host 127.0.0.1 --port 8000 \
        > "$LOG_DIR/backend.out.log" 2> "$LOG_DIR/backend.err.log" &
    PIDS+=($!)
    sleep 2

    echo "[start] Simulator"
    "$PYTHON" -m simulator.simulator \
        > "$LOG_DIR/simulator.out.log" 2> "$LOG_DIR/simulator.err.log" &
    PIDS+=($!)

    if [ "$WITH_BOT" = "1" ]; then
        echo "[start] Discord bot"
        "$PYTHON" -m bot.bot \
            > "$LOG_DIR/bot.out.log" 2> "$LOG_DIR/bot.err.log" &
        PIDS+=($!)
    fi

    printf '%s\n' "${PIDS[@]}" > "$MARKER"

    cat <<EOF
============================================================
Demo stack is up.
  Backend:   http://127.0.0.1:8000/docs
  Frontend:  cd frontend && npm run dev
  Simulator: running in background, logs in $LOG_DIR/

To stop everything:
  ./scripts/demo.sh --stop
============================================================
EOF
}

if [ "$STOP" = "1" ]; then
    stop_demo
else
    start_demo
fi
