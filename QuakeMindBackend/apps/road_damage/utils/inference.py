import os
from pathlib import Path

import torch
import cv2
import numpy as np
import segmentation_models_pytorch as smp
from huggingface_hub import hf_hub_download


DEFAULT_ROAD_MODEL_REPO = "Utbird/dispath_optimized_mitb4_focal_dice30"
DEFAULT_ROAD_MODEL_FILENAME = "optimized_mitb4_focal_dice30.pth"


def _ensure_model_file(model_path):
    resolved_path = Path(model_path)
    if resolved_path.exists():
        return resolved_path

    if resolved_path.name != DEFAULT_ROAD_MODEL_FILENAME:
        return resolved_path

    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    downloaded_path = hf_hub_download(
        repo_id=DEFAULT_ROAD_MODEL_REPO,
        filename=DEFAULT_ROAD_MODEL_FILENAME,
        local_dir=str(resolved_path.parent),
    )
    return Path(downloaded_path)


_model_cache = {}

def load_simple_model(model_path):
    cache_key = str(model_path)
    if cache_key in _model_cache:
        return _model_cache[cache_key]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = smp.Segformer(encoder_name="mit_b4", encoder_weights=None, in_channels=3, classes=1).to(device)
    resolved_model_path = _ensure_model_file(model_path)
    if resolved_model_path.exists():
        model.load_state_dict(torch.load(resolved_model_path, map_location=device))
        model.eval()
        _model_cache[cache_key] = (model, device)
        return model, device
    return None, device


def _create_weight_window(size):
    """Merkeze doğru artan ağırlık penceresi oluşturur (overlap blending için)."""
    x = np.linspace(0, 1, size)
    # Kenarlardan merkeze doğru yumuşak geçiş
    weight_1d = np.minimum(x, 1 - x)
    weight_1d = np.clip(weight_1d * 4, 0, 1)  # Daha keskin geçiş
    weight_2d = np.outer(weight_1d, weight_1d).astype(np.float32)
    return weight_2d


def _postprocess_mask(pred_mask_binary, level=1):
    """
    Morfolojik post-processing.
    level=0: Kapalı (ham çıktı)
    level=1: Hafif (sadece çok küçük gürültü temizlenir)
    level=2: Güçlü (agresif temizlik)
    """
    if level == 0:
        return pred_mask_binary

    cleaned = pred_mask_binary.copy()

    if level == 1:
        # Hafif: sadece çok küçük noktaları temizle
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)
        min_area = 30
    else:  # level >= 2
        # Güçlü: agresif temizlik (yeni model için ideal)
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel_open)
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel_close)
        min_area = 150

    # Küçük bileşenleri sil
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(cleaned, connectivity=8)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] < min_area:
            cleaned[labels == i] = 0

    return cleaned


def run_inference(img, road_mask_binary, model, device, damage_booster, threshold,
                  use_imagenet_norm=False, postprocess_level=1):
    """
    Runs the Segformer model with overlapping patches and blending.
    
    Args:
        use_imagenet_norm: True ise ImageNet normalize uygular (yeni model için).
        postprocess_level: 0=Kapalı, 1=Hafif, 2=Güçlü
    """
    w, h = img.size
    img_np = np.array(img.convert("RGB"))

    patch_size = 512
    stride = 256  # %50 overlap — patch sınır artefaktlarını ortadan kaldırır

    # ImageNet normalizasyon değerleri
    imagenet_mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1).to(device)
    imagenet_std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1).to(device)

    # Ağırlık penceresi (kenarlar düşük, merkez yüksek)
    weight_window = _create_weight_window(patch_size)

    # Padding
    pad_h = max(patch_size - h, (stride - (h - patch_size) % stride) % stride)
    pad_w = max(patch_size - w, (stride - (w - patch_size) % stride) % stride)
    img_padded = np.pad(img_np, ((0, pad_h), (0, pad_w), (0, 0)), mode='reflect')

    padded_h, padded_w = img_padded.shape[:2]
    raw_probs = np.zeros((padded_h, padded_w), dtype=np.float32)
    weight_map = np.zeros((padded_h, padded_w), dtype=np.float32)

    for y in range(0, padded_h - patch_size + 1, stride):
        for x in range(0, padded_w - patch_size + 1, stride):
            chunk = img_padded[y:y + patch_size, x:x + patch_size, :]

            input_tensor = torch.from_numpy(chunk).permute(2, 0, 1).float() / 255.0
            if use_imagenet_norm:
                input_tensor = (input_tensor - imagenet_mean.cpu()) / imagenet_std.cpu()
            input_tensor = input_tensor.unsqueeze(0).to(device)

            with torch.no_grad():
                output = model(input_tensor)
                chunk_pred = torch.sigmoid(output).squeeze().cpu().numpy()

            # Ağırlıklı toplama (blending)
            raw_probs[y:y + patch_size, x:x + patch_size] += chunk_pred * weight_window
            weight_map[y:y + patch_size, x:x + patch_size] += weight_window

    # Normalize (ağırlıklara böl)
    raw_probs = raw_probs / np.maximum(weight_map, 1e-6)

    # Padding'i kaldır
    raw_probs = raw_probs[:h, :w]

    # Boosted probabilities & threshold
    boosted_probs = np.clip(raw_probs * damage_booster, 0, 1)
    pred_mask_binary = (boosted_probs > threshold).astype(np.uint8)

    # Post-processing: morfolojik temizlik
    pred_mask_binary = _postprocess_mask(pred_mask_binary, level=postprocess_level)

    intersection = cv2.bitwise_and(pred_mask_binary, road_mask_binary)
    return raw_probs, boosted_probs, pred_mask_binary, intersection, img_np
