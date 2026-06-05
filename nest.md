# Deploying Mountain Layers to Hack Club Nest

Live URL: **https://mountain.zinnialily.hackclub.app**

---

## Original Plan

1. SSH into the Nest container (`ssh zinnialily@hackclub.app`)
2. Install system dependencies (git, Python pip/venv, Caddy)
3. Clone the repo from GitHub
4. Create a Python virtual environment and install packages
5. Download model weights (SAM + MiDaS) via `start.sh` logic
6. Run `demo.py` as a systemd service on port 7860
7. Configure Caddy to reverse-proxy port 80 → 7860
8. Register the domain via the Nest dashboard

---

## Actual Steps (and where things diverged)

### Step 1 — SSH access ✓
```
ssh zinnialily@hackclub.app
```
Connected directly to the LXC container as root.

### Step 2 — Install system dependencies
**Divergence:** `git`, `pip3`, and `python3-venv` were not pre-installed on the Debian 13 (trixie) container.
```bash
apt-get update -qq
apt-get install -y git python3-pip python3-venv curl
```
Also installed Caddy from the official Caddy apt repository:
```bash
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt-get update -qq && apt-get install -y caddy
```

### Step 3 — Clone the repo
```bash
cd /root
git clone https://github.com/zinnialily/mountain-layers.git
cd mountain-layers
```

### Step 4 — Python virtual environment and packages
**Divergence:** The server runs Python 3.13.5, not Python 3.11 as required by `.python-version`. Python 3.11 is not available in Debian trixie repos. Tested with 3.13 — all packages installed successfully.

Created a `requirements-nest.txt` with CPU-only PyTorch (no CUDA on Nest) and `opencv-python-headless` (no GUI on server):
```
--extra-index-url https://download.pytorch.org/whl/cpu
torch
torchvision
gradio
opencv-python-headless
numpy
scipy
timm
pillow
python-multipart
segment_anything @ git+https://github.com/facebookresearch/segment-anything.git@dca509fe793f601edb92606367a655c15ac00fdf
```

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements-nest.txt
```

### Step 5 — Download model weights
Ran the setup steps from `start.sh` manually (skipping the `python demo.py` launch):
```bash
mkdir -p checkpoints outputs uploads
git clone --depth 1 https://github.com/isl-org/MiDaS.git MiDaS
mkdir -p MiDaS/weights
curl -L -o checkpoints/sam_vit_b_01ec64.pth \
    https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
curl -L -o MiDaS/weights/midas_v21_small_256.pt \
    https://github.com/isl-org/MiDaS/releases/download/v2_1/midas_v21_small_256.pt
```

### Step 6 — Fix MiDaS `torch.hub.load` trust issue
**Divergence (bug):** Running `demo.py` as a systemd service (non-interactive) caused `torch.hub.load` in `MiDaS/midas/blocks.py` to fail with `EOFError` — it was trying to interactively ask "do you trust this repo?".

**Fix:** Patched `MiDaS/midas/blocks.py` on the server to add `trust_repo=True` to both `torch.hub.load` calls (lines 167 and 203).

### Step 7 — Set up systemd service
```bash
cat > /etc/systemd/system/mountain-layers.service << 'EOF'
[Unit]
Description=Mountain Layers Gradio App
After=network.target

[Service]
Type=simple
WorkingDirectory=/root/mountain-layers
ExecStart=/root/mountain-layers/.venv/bin/python demo.py
Environment=PORT=7860
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable mountain-layers
systemctl start mountain-layers
```

Gradio loads the SAM and MiDaS models on startup (~30–60 seconds), then binds to port 7860.

### Step 8 — Configure Caddy (local reverse proxy)
**Divergence:** Initially configured Caddy to serve `https://zinnialily.hackclub.app` with automatic TLS. This failed — `zinnialily.hackclub.app` DNS is a CNAME to `hackclub.app` which routes through Hack Club's central proxy at `65.108.74.29`, so the ACME challenge could never reach our VM directly.

Reconfigured Caddy to plain HTTP on port 80 (TLS handled centrally):
```
/etc/caddy/Caddyfile:
:80 {
    reverse_proxy localhost:7860
}
```

This is used for the port-80 path only; the Nest dashboard routes port 7860 directly.

### Step 9 — Register domain in Nest dashboard
**Divergence:** Expected to use `nest caddy add` CLI, but the Nest CLI is not installed inside user containers. Used the Nest web dashboard instead:

1. Go to **https://dashboard.hackclub.app**
2. Navigate to **Domains**
3. Add domain `mountain.zinnialily.hackclub.app` with target port `7860`

Hack Club's central Caddy at `65.108.74.29` (with TLS via ZeroSSL) now proxies HTTPS traffic to our container on port 7860.

---

## Result

**https://mountain.zinnialily.hackclub.app** — live, serving the Gradio Mountain Layers demo.

- Upload a mountain photo → click **Generate Layers** → view depth-sorted layer PNGs
- Service auto-restarts on failure via systemd
- Models are kept loaded in memory (no cold-start per request)
