# Mountain Layers

The goal of this project is to create a 3D model of a mountain by generating depth-sorted cut layers using SAM (Segment Anything) and MiDaS (depth estimation). The generated layers can be printed and stacked to create a 3D effect.

## Setup

To get started, follow these steps:

1. Create a Python virtual environment:
python -m venv .venv
source .venv/bin/activate  # For Unix/macOS
.venv\Scripts\activate.bat  # For Windows

2. Install the required packages:
pip install -r requirements.txt

3. Make the `start.sh` script executable:
chmod +x start.sh

4. Run the `start.sh` script to clone MiDaS, download the model checkpoints, and launch the Uvicorn server (which serves the FastAPI app (might not be necessary anymore)):
./start.sh

   The script will download the following model checkpoints:
   - SAM: `checkpoints/sam_vit_b_01ec64.pth` from [Meta](https://github.com/facebookresearch/segment-anything#model-checkpoints)
   - MiDaS: `MiDaS/weights/midas_v21_small_256.pt` from [MiDaS releases](https://github.com/isl-org/MiDaS/releases)

## Usage

### Gradio Demo

To run the Gradio demo:

```bash
python demo.py
```

This will load the models (which takes a moment on the first run) and open a local web UI at `http://localhost:7860`. From there:

1. Upload a photo of a mountain
2. Click **Generate Layers**
3. The output layers will appear in the gallery below

The layer images are also saved to the `outputs/` folder as `layer_00.png`, `layer_01.png`, etc., ordered from foreground to background.

#### Sharing the Demo

To share the demo with others on the same network, change the last line of `demo.py` to:

```python
app.launch(share=True)
```

Gradio will provide a temporary public URL that anyone can open in a browser.

### FastAPI Server

The project also includes a FastAPI server (`main.py`) that exposes an `/process` endpoint for generating layers. The `index.html` file contains a hardcoded endpoint URL (`https://mountain-layers.onrender.com/process`) for testing the server.

The core logic for generating the layers resides in the `processing.py` file.

## Deployment

An attempt was made to deploy the FastAPI server on Render, but the following issues were encountered:

- The server exceeded the 512MB memory limit of the free tier.
- If I went with API calls, it'd start costing money, and I wanted to make this project free. I looked at HuggingFace and to see if HackClub had anything for free, but I was not able to find anything. 

Therefore, the Render deployment is on hold. The `start.sh` script is still configured for deployment (it uses the `$PORT` environment variable), but the focus has shifted to running the project locally.

## Challenges and Lessons Learned

- The initial segmentation sometimes grouped different mountains into a single layer, which worked well for simple images but not for complex mountain ranges.
- Sorting segments by area didn't always yield the desired result, as the sky often occupied the most space.
- Hosting the demo on GitHub Pages was not feasible due to the lack of support for running Python code.
- The FastAPI server deployment on Render encountered memory limitations and started incurring costs.
- Gradio proved to be a valuable tool for creating a demo UI without the need for deployment.

## Future Work

- Improve the segmentation algorithm to handle more complex mountain scenes
- Explore alternative layer splitting strategies
- Investigate cost-effective hosting options for the FastAPI server with higher memory limits

## Acknowledgments

This project would not have been possible without the following projects and libraries:

- [Segment Anything](https://github.com/facebookresearch/segment-anything) by Meta AI Research
- [MiDaS](https://github.com/isl-org/MiDaS) by Intel ISL
- [Gradio](https://gradio.app/) for the intuitive demo interface