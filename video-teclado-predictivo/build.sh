#!/usr/bin/env bash
# Genera teclado-predictivo.mp4 desde cero.
# Requiere: node + playwright (Chromium), ffmpeg, python3 + numpy + kokoro-onnx + soundfile,
# y el modelo de Kokoro (kokoro-v1.0.onnx + voices-v1.0.bin) en la carpeta indicada.
#   ./build.sh <carpeta_modelo_kokoro> [voz: em_alex | ef_dora]
set -euo pipefail
cd "$(dirname "$0")"
MODEL="${1:?indica la carpeta del modelo Kokoro}"
VOZ="${2:-em_alex}"
B=build
mkdir -p "$B"

python3 voice.py "$MODEL" . "$VOZ"                    # voz en off + voice-timeline.js
node render.js "$B" 4                                 # cuadros -> segmentos de video
python3 sfx.py "$B/timeline.json" "$B/sfx.wav"         # efectos sutiles (sin música)
ffmpeg -y -loglevel error -f concat -safe 0 -i "$B/segments.txt" -c copy "$B/video.mp4"
ffmpeg -y -loglevel error -i "$B/video.mp4" -i voice.wav -i "$B/sfx.wav" -filter_complex \
  "[1:a]aresample=44100,highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=80[v];[2:a]volume=0.55[s];[v][s]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=9,aformat=channel_layouts=stereo[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 160k -ar 44100 -shortest -movflags +faststart teclado-predictivo.mp4
echo "Listo: $(pwd)/teclado-predictivo.mp4"
