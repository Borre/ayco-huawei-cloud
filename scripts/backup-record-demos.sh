#!/bin/bash
# scripts/backup-record-demos.sh — Record demo backups using ffmpeg + Xvfb
# Captures 3 demo videos as Plan B if live demo fails

set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
PROJECT_DIR="$SCRIPT_DIR/.."
BACKUP_DIR="$PROJECT_DIR/backups"
mkdir -p "$BACKUP_DIR"

DATE=$(date +%Y%m%d_%H%M%S)

echo "=== AYCO Demo Backup Recording ==="
echo "    Output: $BACKUP_DIR/"
echo ""

# Check dependencies
for cmd in ffmpeg xdpyinfo; do
  if ! command -v "$cmd" &> /dev/null; then
    echo "WARN: $cmd not found. Install with: sudo apt install ffmpeg xvfb"
    echo "      Skipping recording."
    exit 0
  fi
done

# Record function
record_demo() {
  local name="$1"
  local duration="$2"
  local output="$BACKUP_DIR/${name}_${DATE}.mp4"
  
  echo "Recording: $name (${duration}s) -> $output"
  ffmpeg -y -f x11grab -video_size 1920x1080 -framerate 15 \
    -i "${DISPLAY:-:0}" -t "$duration" \
    -c:v libx264 -preset ultrafast -crf 28 \
    "$output" 2>/dev/null &
  
  echo "  PID: $!"
}

# Record each demo segment
record_demo "demo1-risk-scoring" 600    # 10 min
record_demo "demo2-data-platform" 420   # 7 min
record_demo "demo3-contract-ai" 780     # 13 min

echo ""
echo "=== Recording started. Press Ctrl+C to stop all ==="
echo "    Files will be in: $BACKUP_DIR/"
wait
