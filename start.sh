#!/usr/bin/env bash
set -e

mkdir -p checkpoints outputs uploads

# Clone MiDaS source code if missing
if [ ! -f "MiDaS/midas/model_loader.py" ]; then
    echo "Cloning MiDaS repository..."
    git clone --depth 1 https://github.com/isl-org/MiDaS.git MiDaS
fi

mkdir -p MiDaS/weights

# Download SAM checkpoint
if [ ! -f "checkpoints/sam_vit_b_01ec64.pth" ]; then
    echo "Downloading SAM checkpoint (~375MB)..."
    curl -L -o checkpoints/sam_vit_b_01ec64.pth \
        https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
fi

# Download MiDaS weights
if [ ! -f "MiDaS/weights/midas_v21_small_256.pt" ]; then
    echo "Downloading MiDaS weights (~82MB)..."
    curl -L -o MiDaS/weights/midas_v21_small_256.pt \
        https://github.com/isl-org/MiDaS/releases/download/v2_1/midas_v21_small_256.pt
fi

python -m uvicorn main:app --host 0.0.0.0 --port $PORT