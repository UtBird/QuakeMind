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

def load_simple_model(model_path, arch="Segformer", encoder="mit_b4"):
    """arch/encoder: segmentation_models_pytorch mimari sınıfı adı ve kodlayıcı adı.
    Varsayılanlar üretimde kullanılan SegFormer/MiT-B4 ile birebir aynı; Tablo 14'ün
    diğer mimarileri (U-Net, FPN, DeepLabV3+ MiT-B4; LinkNet, PSPNet ResNet-34) için
    farklı checkpoint yüklenirken bu parametreler geçilir (bkz. table14_segformer_closure.py)."""
    cache_key = f"{model_path}|{arch}|{encoder}"
    if cache_key in _model_cache:
        return _model_cache[cache_key]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_cls = getattr(smp, arch)
    model = model_cls(encoder_name=encoder, encoder_weights=None, in_channels=3, classes=1).to(device)
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


def tile_quality_score(bgr_image, blur_threshold=100.0, cloud_fraction_threshold=0.4):
    """Karo kalite eşiği V0 (Bölüm 3.3) için CPU-only, model-öncesi bir on-filtre.

    İki bileşen ölçer:
      - `blur_variance`: gri tonlamalı görüntünün Laplacian varyansı; düşük değer
        bulanıklığa işaret eder (Pech-Pacheco vd. 2000'den beri yaygın bir sezgisel).
      - `cloud_fraction`: HSV uzayında yüksek parlaklık (V>200) + düşük doygunluk
        (S<40) koşulunu sağlayan piksellerin oranı; bulut/aşırı pozlanmış alanları
        yaklaşık olarak yakalar.

    Eşikler (blur_threshold=100, cloud_fraction_threshold=0.4) literatürden alınan
    kaba varsayılanlardır ve KATE-PD/QQB gibi etiketli bir karo kümesi üzerinde
    IoU'ya etkisiyle doğrulanmamıştır — bkz. makale Tablo 21, "Karo kalite eşiği V0"
    satırı ve DURUM.md B-6 madde 31.
    """
    gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
    blur_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]
    cloud_mask = (value > 200) & (saturation < 40)
    cloud_fraction = float(np.mean(cloud_mask))

    passes = (blur_variance >= blur_threshold) and (cloud_fraction <= cloud_fraction_threshold)
    return {
        "blur_variance": blur_variance,
        "cloud_fraction": cloud_fraction,
        "passes_quality_gate": passes,
    }


def run_inference(img, road_mask_binary, model, device, damage_booster, threshold,
                  use_imagenet_norm=False, postprocess_level=1, progress_callback=None):
    """
    Runs the Segformer model with overlapping patches and blending.

    Args:
        use_imagenet_norm: True ise ImageNet normalize uygular (yeni model için).
        postprocess_level: 0=Kapalı, 1=Hafif, 2=Güçlü
        progress_callback: Opsiyonel `fn(done_patches, total_patches)` -- patch
            dongusu CPU'da dakikalarca surebildigi icin cagiran tarafin gercek
            ilerleme gosterebilmesini saglar. Hicbir sey donmez, hatalari
            yutulur (ilerleme raporu analizi bozmamali).
    """
    w, h = img.size
    img_np = np.array(img.convert("RGB"))

    patch_size = 512
    # ORTUSME. Varsayilan %50 (stride 256): parca sinir artefaktlarini siler
    # ama 1280x1280 goruntude 25 parca demek ve cikarim suresinin tamami bu.
    # `QM_CIKARIM_ADIMI` ile degistirilebilir; DEGISTIRMEDEN ONCE maske farki
    # olculmeli (asagidaki olcum kayitli).
    try:
        stride = max(64, min(patch_size, int(os.environ.get("QM_CIKARIM_ADIMI", "256"))))
    except ValueError:
        stride = 256

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

    y_positions = list(range(0, padded_h - patch_size + 1, stride))
    x_positions = list(range(0, padded_w - patch_size + 1, stride))
    total_patches = max(1, len(y_positions) * len(x_positions))
    done_patches = 0

    # YIGIN BOYUTU. Parcalar toplu da kosabilir; cikti BIREBIR AYNI kalir
    # (dogrulandi: maske ayni, ham olasilikta en buyuk fark 6e-06).
    #
    # AMA CPU'DA ISE YARAMIYOR -- olculdu (26 Eylul, 1280x1280, U-Net MiT-B4):
    #     yigin 1: 8,49 sn   yigin 2: 9,32   yigin 4: 10,02   yigin 8: 9,79
    # Yiginlamak %18 YAVASLATIYOR: PyTorch tek cagri icinde zaten paralel
    # calisiyor, is parcacigi sayisi da sinirli (bkz. worker._is_parcacigi_
    # sinirla), yigin yalnizca bellek baskisi ekliyor. Bu yuzden varsayilan 1.
    #
    # GPU'da tersi beklenir; `QM_CIKARIM_YIGINI` o zaman artirilir. Sayi
    # olcmeden degistirilmemeli.
    try:
        yigin = max(1, int(os.environ.get("QM_CIKARIM_YIGINI", "1")))
    except ValueError:
        yigin = 1

    konumlar = [(y, x) for y in y_positions for x in x_positions]
    for bas in range(0, len(konumlar), yigin):
        oba = konumlar[bas:bas + yigin]
        girdiler = []
        for y, x in oba:
            chunk = img_padded[y:y + patch_size, x:x + patch_size, :]
            t = torch.from_numpy(chunk).permute(2, 0, 1).float() / 255.0
            if use_imagenet_norm:
                t = (t - imagenet_mean.cpu()) / imagenet_std.cpu()
            girdiler.append(t)
        toplu = torch.stack(girdiler).to(device)

        with torch.inference_mode():
            cikti = model(toplu)
            tahmin = torch.sigmoid(cikti).squeeze(1).cpu().numpy()

        # Agirlikli toplama: SIRA KORUNUR, boylece kayan nokta toplamasi da
        # eski dongudekiyle ayni sirada yapilir.
        for i, (y, x) in enumerate(oba):
            chunk_pred = tahmin[i]
            raw_probs[y:y + patch_size, x:x + patch_size] += chunk_pred * weight_window
            weight_map[y:y + patch_size, x:x + patch_size] += weight_window

        done_patches += len(oba)
        if progress_callback is not None:
            try:
                progress_callback(done_patches, total_patches)
            except Exception:
                pass

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
