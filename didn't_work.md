'''def bottom_heavy_score(mask):
    h,w=mask.shape
    #split into top and bottom
    top=mask[:h//2, :]
    bottom=mask[h//2:, :]
    #rations
    top_ratio=np.mean(top)
    bottom_ratio=np.mean(bottom)

    return bottom_ratio - top_ratio'''


    #just testing to make sure the sam.pth works right using the k2 mountain
import cv2
import matplotlib.pyplot as plt
import numpy as np
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator

def mountain_score(mask):
    h, w = mask.shape
    mask = mask.astype(np.uint8)

    ys, xs = np.where(mask)
    if len(ys) == 0 or np.sum(mask) < 500:
        return -1

    vertical_score = np.mean(ys) / h

    bbox_area = (np.max(ys) - np.min(ys) + 1) * (np.max(xs) - np.min(xs) + 1)
    compactness = np.sum(mask) / (bbox_area + 1e-6)

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_overlap = np.sum(edges * mask) / (np.sum(mask) + 1e-6)

    return (
        2.0 * vertical_score +
        1.5 * compactness +
        2.0 * edge_overlap
    )

image=cv2.imread("K2-Mountain.jpg")
image=cv2.cvtColor(image,cv2.COLOR_BGR2RGB) # RGB -> BGR is format for opencv

sam = sam_model_registry["vit_b"](
    checkpoint="checkpoints/sam_vit_b_01ec64.pth"
)
mask_generator=SamAutomaticMaskGenerator(sam)
masks=mask_generator.generate(image)

print (f"generated {len(masks)} masks")

#there r a lot of masks, and u can't output all of them...for rn i'm only displaying top 3 bottom heavy masks
masks = sorted(
    masks,
    key=lambda x: mountain_score(x["segmentation"]),
    reverse=True
)

fig,ax=plt.subplots(1,3,figsize=(15,5))

for i in range(3):
    mask=masks[i]["segmentation"]
    overlay=image.copy()
    overlay[mask]=[255,0,0] #red overlay for rn 
    ax[i].imshow(overlay)
    ax[i].set_title(f"mask {i}")
    ax[i].axis("off")
plt.show()