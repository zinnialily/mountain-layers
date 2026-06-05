# 2026-06-05 — Nest Deployment (complete)

## Changes made on Nest server

**System packages installed** (not pre-installed on fresh Debian 13 container):
- `git`, `python3-pip`, `python3-venv`, `curl`, `build-essential`
- `caddy` (from cloudsmith apt repo, v2.11.4)

**Python environment:**
- Used Python 3.13.5 (system default; 3.11 not available in Debian trixie repos)
- Created `.venv` with CPU-only torch, gradio, opencv-headless
- `requirements-nest.txt` added to repo for reproducibility

**MiDaS patch — `MiDaS/midas/blocks.py`:**
- Added `trust_repo=True` to both `torch.hub.load` calls
- Without this, systemd's non-interactive shell gets `EOFError` when torch asks "do you trust rwightman/gen-efficientnet-pytorch?"

**Systemd service — `/etc/systemd/system/mountain-layers.service`:**
- Runs `demo.py` with `PORT=7860`, restarts on failure
- Models load at startup (~30–60s); Gradio then binds `0.0.0.0:7860`

**Caddy — `/etc/caddy/Caddyfile`:**
- Listens on `:80`, reverse-proxies to `localhost:7860`
- TLS is NOT handled by our Caddy (Hack Club's central proxy owns the cert)

## Domain registration
- Added `mountain.zinnialily.hackclub.app → 7860` in Nest dashboard
- Central proxy (ZeroSSL cert, Caddy at `65.108.74.29`) routes HTTPS → our port 7860

## Divergences from original plan
1. Python 3.11 unavailable → used 3.13 (worked fine)
2. git/pip not pre-installed → apt-get install
3. Nest CLI not available inside container → used dashboard UI for domain setup
4. ACME TLS on our VM failed → central Hack Club proxy handles TLS instead
5. `torch.hub.load` non-interactive crash → patched `trust_repo=True` in MiDaS

## Final result
`https://mountain.zinnialily.hackclub.app` — HTTP 200, Gradio app live
