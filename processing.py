import cv2
import torch
import numpy as np
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "MiDaS"))
from MiDaS.midas.model_loader import load_model

device = None
model = None
transform = None

NUM_LAYERS = 5


def init_models():
    global device, model, transform

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"using device: {device}")

    torch.set_num_threads(2)

    model, transform, _, _ = load_model(
        device,
        "MiDaS/weights/midas_v21_small_256.pt",
        model_type="midas_v21_small_256",
        optimize=False
    )
    model.eval()
    print("MiDaS loaded")


def generate_layers(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("image failed to load")

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_rgb = cv2.resize(image_rgb, None, fx=0.5, fy=0.5)
    h, w = image_rgb.shape[:2]

    image_transformed = transform({"image": image_rgb / 255.0})["image"]
    input_batch = torch.from_numpy(image_transformed).unsqueeze(0).to(device)

    with torch.no_grad():
        prediction = model.forward(input_batch)
        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=(h, w),
            mode="bicubic",
            align_corners=False,
        ).squeeze()

    depth_map = prediction.cpu().numpy()
    depth_map = cv2.normalize(depth_map, None, 0, 1, cv2.NORM_MINMAX)

    os.makedirs("outputs", exist_ok=True)

    physical_layers = []

    for i in range(NUM_LAYERS):
        low = i / NUM_LAYERS
        high = (i + 1) / NUM_LAYERS
        band_mask = (depth_map >= low) & (depth_map < high)

        # RGBA: transparent above the silhouette, opaque block from silhouette top to image bottom
        layer_img = np.zeros((h, w, 4), dtype=np.uint8)

        for x in range(w):
            col_rows = np.where(band_mask[:, x])[0]
            if len(col_rows) > 0:
                top_row = col_rows.min()
                layer_img[top_row:, x, :3] = image_rgb[top_row:, x]
                layer_img[top_row:, x, 3] = 255

        cv2.imwrite(
            f"outputs/layer_{i:02d}.png",
            cv2.cvtColor(layer_img, cv2.COLOR_RGBA2BGRA)
        )

        physical_layers.append({
            "layer_index": i,
            "depth_low": float(low),
            "depth_high": float(high),
        })

    print(f"saved {NUM_LAYERS} layers to outputs/")

    return {
        "depth_map": depth_map.tolist(),
        "physical_layers": physical_layers,
        "num_layers": NUM_LAYERS
    }


if __name__ == "__main__":
    init_models()
    generate_layers("images/red_Mountain.jpg")
