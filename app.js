const fileInput     = document.getElementById('file-input');
const fileNameEl    = document.getElementById('file-name');
const controls      = document.getElementById('controls');
const previewCanvas = document.getElementById('preview-canvas');
const thresholdEl   = document.getElementById('threshold');
const thresholdVal  = document.getElementById('threshold-val');
const numLayersEl   = document.getElementById('num-layers');
const numLayersVal  = document.getElementById('num-layers-val');
const useColorEl    = document.getElementById('use-color');
const generateBtn   = document.getElementById('generate-btn');
const outputSection = document.getElementById('output');
const layersGrid    = document.getElementById('layers-grid');
const printAllBtn   = document.getElementById('print-all-btn');
const lastLayerLabel = document.getElementById('last-layer-label');

let srcImageData = null;
let imgWidth = 0;
let imgHeight = 0;

// ── load image ──────────────────────────────────────────────────────────────

fileInput.addEventListener('change', () => {
  const file = fileInput.files[0];
  if (!file) return;
  fileNameEl.textContent = file.name;

  const img = new Image();
  img.onload = () => {
    // cap at 800px wide to keep processing fast
    const scale = Math.min(1, 800 / img.width);
    imgWidth  = Math.round(img.width  * scale);
    imgHeight = Math.round(img.height * scale);

    const offscreen = document.createElement('canvas');
    offscreen.width  = imgWidth;
    offscreen.height = imgHeight;
    offscreen.getContext('2d').drawImage(img, 0, 0, imgWidth, imgHeight);
    srcImageData = offscreen.getContext('2d').getImageData(0, 0, imgWidth, imgHeight);

    controls.hidden = false;
    outputSection.hidden = true;
    layersGrid.innerHTML = '';
    drawPreview();
  };
  img.src = URL.createObjectURL(file);
});

// ── sliders ──────────────────────────────────────────────────────────────────

thresholdEl.addEventListener('input', () => {
  thresholdVal.textContent = thresholdEl.value;
  drawPreview();
});

numLayersEl.addEventListener('input', () => {
  numLayersVal.textContent = numLayersEl.value;
});

// ── preview: draw image + blue outline at silhouette ─────────────────────────

function drawPreview() {
  if (!srcImageData) return;
  const threshold = parseInt(thresholdEl.value);
  const mountainTop = findMountainTop(srcImageData, imgWidth, imgHeight, threshold);

  previewCanvas.width  = imgWidth;
  previewCanvas.height = imgHeight;
  const ctx = previewCanvas.getContext('2d');
  ctx.putImageData(srcImageData, 0, 0);

  ctx.strokeStyle = '#2563eb';
  ctx.lineWidth = 2;
  ctx.beginPath();
  for (let x = 0; x < imgWidth; x++) {
    const y = mountainTop[x];
    if (y >= imgHeight) continue;
    if (x === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();
}

// ── silhouette detection ──────────────────────────────────────────────────────

function findMountainTop(imageData, width, height, threshold) {
  const top = new Int32Array(width).fill(height);
  const d = imageData.data;
  for (let x = 0; x < width; x++) {
    for (let y = 0; y < height; y++) {
      const i = (y * width + x) * 4;
      const brightness = (d[i] + d[i + 1] + d[i + 2]) / 3;
      if (brightness < threshold) {
        top[x] = y;
        break;
      }
    }
  }
  return top;
}

// ── layer generation ──────────────────────────────────────────────────────────

// layer 0 = back (full silhouette), layer N-1 = front (just the peak)
function generateLayer(mountainTop, layerIndex, numLayers, useColor) {
  const bandStart = Math.floor(layerIndex * imgHeight / numLayers);
  const bandEnd   = Math.floor((layerIndex + 1) * imgHeight / numLayers);

  const canvas = document.createElement('canvas');
  canvas.width  = imgWidth;
  canvas.height = imgHeight;
  const ctx = canvas.getContext('2d');

  ctx.fillStyle = 'white';
  ctx.fillRect(0, 0, imgWidth, imgHeight);

  const dst = ctx.getImageData(0, 0, imgWidth, imgHeight);
  const src = srcImageData.data;
  const d   = dst.data;

  for (let x = 0; x < imgWidth; x++) {
    const mt = mountainTop[x];
    if (mt >= imgHeight) continue;  // no mountain in this column
    if (mt >= bandEnd) continue;    // mountain top is below this layer's band — belongs to a back layer

    const fillStart = Math.max(mt, bandStart);
    for (let y = fillStart; y < imgHeight; y++) {
      const idx = (y * imgWidth + x) * 4;
      if (useColor) {
        d[idx]     = src[idx];
        d[idx + 1] = src[idx + 1];
        d[idx + 2] = src[idx + 2];
      } else {
        d[idx] = d[idx + 1] = d[idx + 2] = 0;
      }
      d[idx + 3] = 255;
    }
  }

  ctx.putImageData(dst, 0, 0);
  return canvas;
}

// ── generate button ───────────────────────────────────────────────────────────

generateBtn.addEventListener('click', () => {
  if (!srcImageData) return;

  const threshold = parseInt(thresholdEl.value);
  const numLayers = parseInt(numLayersEl.value);
  const useColor  = useColorEl.checked;
  const mountainTop = findMountainTop(srcImageData, imgWidth, imgHeight, threshold);

  layersGrid.innerHTML = '';
  lastLayerLabel.textContent = numLayers;

  for (let i = 0; i < numLayers; i++) {
    const layerCanvas = generateLayer(mountainTop, i, numLayers, useColor);
    layerCanvas.className = 'layer-canvas';

    const label = document.createElement('p');
    label.className = 'layer-label';
    label.textContent = i === 0
      ? `Layer 1 — back`
      : i === numLayers - 1
        ? `Layer ${numLayers} — front`
        : `Layer ${i + 1}`;

    const downloadBtn = document.createElement('a');
    downloadBtn.className = 'download-btn';
    downloadBtn.textContent = 'Download PNG';
    downloadBtn.download = `layer_${String(i + 1).padStart(2, '0')}.png`;
    downloadBtn.href = layerCanvas.toDataURL('image/png');

    const card = document.createElement('div');
    card.className = 'layer-card';
    card.dataset.layerIndex = i;
    card.append(label, layerCanvas, downloadBtn);
    layersGrid.append(card);
  }

  outputSection.hidden = false;
  outputSection.scrollIntoView({ behavior: 'smooth' });
});

// ── print all ─────────────────────────────────────────────────────────────────

printAllBtn.addEventListener('click', () => {
  window.print();
});
