def generate_layers(image_path):
    import cv2
    import torch
    import numpy as np
    import matplotlib.pyplot as plt
    import sys

    from segment_anything import sam_model_registry, SamAutomaticMaskGenerator

    #setup midas import
    sys.path.append("MiDaS")

    from midas.model_loader import load_model

    # load image
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError("image failed to load")

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    #resize for speed
    scale = 0.5

    image = cv2.resize(
        image,
        None,
        fx=scale,
        fy=scale
    )

    h, w = image.shape[:2]

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print(f"using device: {device}")


    #load sam
    sam = sam_model_registry["vit_b"](
        checkpoint="checkpoints/sam_vit_b_01ec64.pth"
    )

    sam.to(device)

    mask_generator = SamAutomaticMaskGenerator(
        sam,
        points_per_side=16,
        pred_iou_thresh=0.88,
        stability_score_thresh=0.92,
        min_mask_region_area=2000
    )


    masks = mask_generator.generate(image)

    #midas loading
    model, transform, net_w, net_h = load_model(
        device,
        "MiDaS/weights/midas_v21_small_256.pt",
        model_type="midas_v21_small_256",
        optimize=False
    )

    model.eval()

    #print("computing depth map")

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

    # normalize depth map
    depth_map = cv2.normalize(
        depth_map,
        None,
        0,
        1,
        cv2.NORM_MINMAX
    )

    #filter+ score masks
    filtered_masks = []

    for m in masks:

        mask = m["segmentation"]

        area = np.sum(mask)
        # skip tiny masks
        if area < 5000: #idk if i want to keep this
            continue 
        # average depth inside mask
        depth_score = np.mean(depth_map[mask])

        m["depth_score"] = depth_score

        filtered_masks.append(m)

    print(f"filtered to {len(filtered_masks)} masks")
    #sort far -> near
    sorted_masks = sorted(
        filtered_masks,
        key=lambda x: x["depth_score"],
        reverse=False
    )

    #layered visualization
    layered_output = np.ones((h, w, 3), dtype=np.uint8) * 255

    num_layers = len(sorted_masks)

    for i, m in enumerate(sorted_masks):

        mask = m["segmentation"]

        # darker = farther away
        shade = int(255 * (i / max(1, num_layers)))

        color = [shade, shade, shade]

        layered_output[mask] = color

    #contour extraction
    contour_canvas = np.ones((h, w, 3), dtype=np.uint8) * 255

    physical_layers = []

    for idx, m in enumerate(sorted_masks):

        mask = m["segmentation"].astype(np.uint8) * 255

        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        simplified_contours = []

        for cnt in contours:

            epsilon = 0.003 * cv2.arcLength(cnt, True)

            approx = cv2.approxPolyDP(
                cnt,
                epsilon,
                True
            )

            simplified_contours.append(approx)

            cv2.drawContours(
                contour_canvas,
                [approx],
                -1,
                (0, 0, 0),
                2
            )

        physical_layers.append({
            "layer_index": idx,
            "depth": m["depth_score"],
            "contours": simplified_contours
        })

    #display effects
    plt.figure(figsize=(18, 6))

    plt.subplot(1, 3, 1)
    plt.imshow(image)
    plt.title("original image")
    plt.axis("off")

    plt.subplot(1, 3, 2)
    plt.imshow(depth_map, cmap="plasma")
    plt.title("midas depth map")
    plt.axis("off")

    plt.subplot(1, 3, 3)
    plt.imshow(layered_output)
    plt.title("depth sorted layers")
    plt.axis("off")

    plt.tight_layout()
    plt.show()

    # show contours
    plt.figure(figsize=(8, 8))

    plt.imshow(contour_canvas)

    plt.title("physical cutout contours")

    plt.axis("off")

    plt.show()

    # export png layers
    for idx, m in enumerate(sorted_masks):

        mask = m["segmentation"]

        layer_img = np.ones((h, w, 3), dtype=np.uint8) * 255

        layer_img[mask] = [0, 0, 0]

        cv2.imwrite(
            f"layer_{idx:02d}.png",
            cv2.cvtColor(layer_img, cv2.COLOR_RGB2BGR)
        )

    print("done.")

    return {
        "depth_map": depth_map,
        "physical_layers": physical_layers,
        "num_layers": len(sorted_masks)
    }