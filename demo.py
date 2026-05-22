import gradio as gr
import os
import glob
import shutil
from processing import generate_layers, init_models

init_models()
#create directories online bc they r ignored in gitignore
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)


def process(image_path):
    # clear previous outputs if there were any (if one were to rerun again)
    for f in glob.glob("outputs/layer_*.png"):
        os.remove(f)

    shutil.copy(image_path, "uploads/image-upload.jpg")
    result = generate_layers("uploads/image-upload.jpg")

    layer_files = sorted(glob.glob("outputs/layer_*.png")) #you can't js do regular sorting b/c 1<10<2 stringwise regularly but it's a risk i'm willing to take

    return layer_files, f"{result['num_layers']} layers detected" 


with gr.Blocks(title="Mountain Layers") as app:
    gr.Markdown("## Mountain Layers\nUpload a mountain photo to convert terrain into depth-based slice layers for reconstruction") #may be better wording later on

    with gr.Row():
        image_input = gr.Image(type="filepath", label="Input Image")

    run_btn = gr.Button("Generate Layers")

    status = gr.Textbox(label="Status", interactive=False)
    gallery = gr.Gallery(label="Output Layers", columns=4, object_fit="contain")

    run_btn.click(fn=process, inputs=image_input, outputs=[gallery, status])

if __name__ == "__main__":
    app.launch(share=True)
