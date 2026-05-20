#!/usr/bin/env bash
set -e

mkdir -p checkpoints MiDaS/weights outputs uploads

if [ ! -f "checkpoints/sam_vit_b_01ec64.pth" ]; then
    echo "Downloading SAM checkpoint (~375MB)..."
    curl -L -o checkpoints/sam_vit_b_01ec64.pth \
        https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
fi

if [ ! -f "MiDaS/weights/midas_v21_small_256.pt" ]; then
    echo "Downloading MiDaS weights (~82MB)..."
    curl -L -o MiDaS/weights/midas_v21_small_256.pt \
        https://github.com/isl-org/MiDaS/releases/download/v2_1/midas_v21_small_256.pt
fi

uvicorn main:app --host 0.0.0.0 --port "${PORT:-10000}"
