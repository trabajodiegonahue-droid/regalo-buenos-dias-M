#!/usr/bin/env bash
# Genera teclas-iphone.mp4 desde cero.
# Requiere: node + playwright (Chromium), ffmpeg, python3 + numpy.
set -euo pipefail
cd "$(dirname "$0")"
B="${1:-build}"
mkdir -p "$B"

node render.js "$B" 4                                   # cuadros -> segmentos de video
python3 audio.py "$B/timeline.json" "$B/audio.wav"     # efectos + música
ffmpeg -y -loglevel error -f concat -safe 0 -i "$B/segments.txt" -c copy "$B/video.mp4"
ffmpeg -y -loglevel error -i "$B/video.mp4" -i "$B/audio.wav" \
  -af "loudnorm=I=-18:TP=-1.5:LRA=11" -c:v copy -c:a aac -b:a 160k -ar 44100 \
  -shortest -movflags +faststart teclas-iphone.mp4
echo "Listo: $(pwd)/teclas-iphone.mp4"
