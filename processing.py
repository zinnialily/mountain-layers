import cv2
import torch
import numpy as np
import sys
import os

from segment_anything import sam_model_registry, SamAutomaticMaskGenerator

sys.path.append(os.path.join(os.path.dirname(__file__), "MiDaS"))
from MiDaS.midas.model_loader import load_model

device = None
mask_generator = None
model = None
transform = None


def init_models():
    global device, mask_generator, model, transform

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"using device: {device}")

    sam = sam_model_registry["vit_b"](
        checkpoint="checkpoints/sam_vit_b_01ec64.pth"
    )
    sam.to(device)

    torch.set_num_threads(2)

    mask_generator = SamAutomaticMaskGenerator(
        sam,
        points_per_side=16,
        pred_iou_thresh=0.88,
        stability_score_thresh=0.95,
        min_mask_region_area=1500
    )

    model, transform, _, _ = load_model(
        device,
        "MiDaS/weights/midas_v21_small_256.pt",
        model_type="midas_v21_small_256",
        optimize=False
    )
    model.eval()
    print("models loaded")


def generate_layers(image_path):
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError("image failed to load")

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    scale = 0.5
    image = cv2.resize(image, None, fx=scale, fy=scale)

    h, w = image.shape[:2]

    masks = mask_generator.generate(image)

    image_transformed = transform({"image": image / 255.0})["image"]
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

    filtered_masks = []

    for m in masks:
        mask = m["segmentation"]
        area = np.sum(mask)
        if area < 3000:
            continue
        depth_score = np.mean(depth_map[mask])
        m["depth_score"] = depth_score
        filtered_masks.append(m)

    print(f"filtered to {len(filtered_masks)} masks")

    sorted_masks = sorted(filtered_masks, key=lambda x: x["depth_score"], reverse=False)

    layered_output = np.ones((h, w, 3), dtype=np.uint8) * 255
    num_layers = len(sorted_masks)

    for i, m in enumerate(sorted_masks):
        mask = m["segmentation"]
        shade = int(255 * (i / max(1, num_layers)))
        layered_output[mask] = [shade, shade, shade]

    contour_canvas = np.ones((h, w, 3), dtype=np.uint8) * 255
    physical_layers = []

    for idx, m in enumerate(sorted_masks):
        mask = m["segmentation"].astype(np.uint8) * 255
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        simplified_contours = []

        for cnt in contours:
            epsilon = 0.003 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            simplified_contours.append(approx)
            cv2.drawContours(contour_canvas, [approx], -1, (0, 0, 0), 2)

        physical_layers.append({
            "layer_index": idx,
            "depth": float(m["depth_score"]),
            "contours": [c.tolist() for c in simplified_contours]
        })

    os.makedirs("outputs", exist_ok=True)

    shade_channel = layered_output[:, :, 0]
    unique_shades = np.unique(shade_channel)
    unique_shades = unique_shades[unique_shades != 255]

    for idx, shade_val in enumerate(unique_shades):
        layer_img = np.ones((h, w, 3), dtype=np.uint8) * 255
        mask = shade_channel == shade_val

        extended_mask = mask.copy()
        for x in range(w):
            col_rows = np.where(mask[:, x])[0]
            if len(col_rows) > 0:
                extended_mask[col_rows.min():, x] = True

        layer_img[extended_mask] = [shade_val, shade_val, shade_val]

        cv2.imwrite(
            f"outputs/layer_{idx:02d}.png",
            cv2.cvtColor(layer_img, cv2.COLOR_RGB2BGR)
        )

    print(f"saved {len(unique_shades)} layers to outputs/")

    return {
        "depth_map": depth_map.tolist(),
        "physical_layers": physical_layers,
        "num_layers": len(sorted_masks)
    }


if __name__ == "__main__":
    init_models()
    generate_layers("images/red_Mountain.jpg")
