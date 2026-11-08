"""Senaryo bolgeleri icin SegFormer hasar maskesi uretir (Colab T4 icin).

NEDEN AYRI BIR ADIM
    Model tabanli kapanma, modelin deprem sonrasi goruntuyu dogal
    cozunurlugune yakin gormesini gerektiriyor (J-20: z=15 / 3,86 m/px'te
    model hasari neredeyse hic gormuyor, z=18 / 0,48 m/px'te 25 kat fazla
    goruyor). 3 km yaricapli bir bolge z=18'de ~12 500 x 12 500 piksel ve
    ~2 300 yama demek; kullanicinin bilgisayarinda GPU olmadigi icin bu
    bolge basina saatler suruyor. Cikarim burada, GPU'da, BIR KEZ yapilir;
    cikan maskeler benchmark/data/model_masks/<BOLGE>/ altina konur ve
    senaryo (`full_scenario.py --closure-source model`) onlarla yerelde
    hizla kosar.

AYNI KOD, AYNI PARAMETRELER
    Cikarim, backend'in kendi `run_inference` fonksiyonuyla yapilir
    (apps/road_damage/utils/inference.py -- Colab defterine birebir
    kopyalanir) ve /analyze'in varsayilan parametreleri kullanilir.
    Model agirligi SHA-256 ile dogrulanir; farkliysa kosu durur.

CIKTI (bolge basina)
    damage_mask.png   0/255  -- modelin hasar tahmini (goruntu olmayan
                               piksellerde sifirlanir)
    valid_mask.png    0/255  -- deprem sonrasi goruntunun GERCEKTEN
                               bulundugu pikseller
    preview.jpg              -- goz kontrolu icin kucultulmus bindirme
    meta.json                -- sinirlar, zoom, kullanilan sahneler, model
                               parmak izi, parametreler, sureler

Yerel deneme (kucuk alan, CPU):
    python benchmark/colab/make_model_masks.py --zones H-Z1 --radius-km 0.15 --out <klasor>
"""
import argparse
import concurrent.futures as cf
import hashlib
import io
import json
import math
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import requests
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO_BACKEND = HERE.parent.parent      # benchmark/colab -> backend
IN_REPO = (REPO_BACKEND / "apps" / "road_damage").is_dir()
if IN_REPO:  # yerel depo
    sys.path.insert(0, str(REPO_BACKEND))
    from apps.road_damage.utils.inference import (  # noqa: E402
        DEFAULT_ROAD_MODEL_FILENAME, DEFAULT_ROAD_MODEL_REPO, load_simple_model, run_inference,
    )
    from apps.road_damage.utils.assembly import bbox_from_center  # noqa: E402
    LOCAL_MODEL_PATH = REPO_BACKEND / "apps" / "road_damage" / "models" / DEFAULT_ROAD_MODEL_FILENAME
else:  # Colab: defterin yanina yazilan birebir kopyalar
    from inference import (  # noqa: E402
        DEFAULT_ROAD_MODEL_FILENAME, DEFAULT_ROAD_MODEL_REPO, load_simple_model, run_inference,
    )
    from qm_geo import bbox_from_center  # noqa: E402
    LOCAL_MODEL_PATH = HERE / "models" / DEFAULT_ROAD_MODEL_FILENAME

EVENT_DATE = "2023-02-06"          # Kahramanmaras depremleri
POST_EVENT_END = "2023-06-30"      # "deprem sonrasi" penceresinin sonu
ZOOM = 18                          # ~0,48 m/px (36-38 derece enlemde)
TILE = 256
OAM_META_URL = "https://api.openaerialmap.org/meta"
USER_AGENT = "QuakeMind-research/1.0 (TUBITAK 2209-A; model mask generation)"

# /analyze'in varsayilanlari (fastapi_app.RoadDamageRequest / worker.py) --
# canli sistemle AYNI karar esigi kullanilsin.
INFERENCE_PARAMS = {
    "damage_booster": 3.5,
    "threshold": 0.40,
    "use_imagenet_norm": True,
    "postprocess_level": 2,
}


# --------------------------------------------------------------------------
# Karo matematigi (Web Mercator, XYZ)
# --------------------------------------------------------------------------
def deg2tile(lat, lon, z):
    n = 2 ** z
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return x, y


def tile2deg(x, y, z):
    """(x, y) karosunun KUZEYBATI kosesi."""
    n = 2 ** z
    lon = x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lat, lon


# --------------------------------------------------------------------------
# OpenAerialMap
# --------------------------------------------------------------------------
def search_post_event_scenes(bbox, session):
    """Bolgeyi kesen deprem sonrasi sahneler. Siralama deterministiktir:
    once Maxar (D-01: yayinda kullanilabilir acik veri), sonra en ERKEN
    tarih (moloz henuz kaldirilmamis), sonra kimlik."""
    west, south, east, north = bbox
    params = {
        "bbox": f"{west},{south},{east},{north}",
        "acquisition_from": EVENT_DATE,
        "acquisition_to": POST_EVENT_END,
        "limit": 100,
    }
    resp = session.get(OAM_META_URL, params=params, timeout=60)
    resp.raise_for_status()
    scenes = []
    for item in resp.json().get("results", []):
        tms = item.get("tms") or (item.get("properties") or {}).get("tms")
        date = item.get("acquisition_start") or item.get("acquisition_end") or ""
        if not tms or date[:10] < EVENT_DATE:
            continue
        scenes.append({
            "id": item.get("_id") or item.get("uuid"),
            "title": item.get("title"),
            "provider": item.get("provider"),
            "date": date[:10],
            "tms": tms,
        })
    scenes.sort(key=lambda s: (0 if "maxar" in (s["provider"] or "").lower() else 1,
                               s["date"], str(s["id"])))
    return scenes


def fetch_tile(session, tms, z, x, y, retries=4):
    """RGBA karo -> (rgb uint8, valid uint8) ya da None (sahne bu karoyu
    kapsamiyor). OAM, kapsama disini seffaf/bos karo olarak dondurur."""
    url = tms.replace("{z}", str(z)).replace("{x}", str(x)).replace("{y}", str(y))
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=60)
        except requests.RequestException:
            time.sleep(1.5 * (attempt + 1))
            continue
        if r.status_code == 404:
            return None
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2.0 * (attempt + 1))
            continue
        if r.status_code != 200 or not r.content:
            return None
        img = Image.open(io.BytesIO(r.content))
        rgba = np.array(img.convert("RGBA"))
        if rgba.shape[:2] != (TILE, TILE):
            rgba = np.array(img.convert("RGBA").resize((TILE, TILE), Image.BILINEAR))
        valid = (rgba[:, :, 3] > 0).astype(np.uint8)
        if not valid.any():
            return None
        return rgba[:, :, :3], valid
    return None


def build_mosaic(bbox, scenes, session, z=ZOOM, workers=16, progress=None):
    """Bolge sinirlarini kaplayan karolari, sahne onceligine gore piksel
    piksel doldurarak birlestirir. Bir pikseli ilk dolduran sahne kazanir."""
    west, south, east, north = bbox
    fx0, fy0 = deg2tile(north, west, z)
    fx1, fy1 = deg2tile(south, east, z)
    x0, y0, x1, y1 = int(fx0), int(fy0), int(fx1), int(fy1)
    nx_, ny_ = x1 - x0 + 1, y1 - y0 + 1
    H, W = ny_ * TILE, nx_ * TILE
    rgb = np.zeros((H, W, 3), dtype=np.uint8)
    valid = np.zeros((H, W), dtype=np.uint8)
    tiles_from_scene = {s["id"]: 0 for s in scenes}

    def work(tx, ty):
        tile_rgb = np.zeros((TILE, TILE, 3), dtype=np.uint8)
        tile_valid = np.zeros((TILE, TILE), dtype=np.uint8)
        used = []
        for sc in scenes:
            got = fetch_tile(session, sc["tms"], z, tx, ty)
            if got is None:
                continue
            s_rgb, s_valid = got
            fill = (s_valid > 0) & (tile_valid == 0)
            if fill.any():
                tile_rgb[fill] = s_rgb[fill]
                tile_valid[fill] = 1
                used.append(sc["id"])
            if tile_valid.all():
                break
        return tx, ty, tile_rgb, tile_valid, used

    jobs = [(tx, ty) for ty in range(y0, y1 + 1) for tx in range(x0, x1 + 1)]
    done = 0
    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        for tx, ty, t_rgb, t_valid, used in pool.map(lambda j: work(*j), jobs):
            oy, ox = (ty - y0) * TILE, (tx - x0) * TILE
            rgb[oy:oy + TILE, ox:ox + TILE] = t_rgb
            valid[oy:oy + TILE, ox:ox + TILE] = t_valid
            for sid in used:
                tiles_from_scene[sid] += 1
            done += 1
            if progress and (done % 200 == 0 or done == len(jobs)):
                progress(done, len(jobs))

    n_lat, w_lon = tile2deg(x0, y0, z)
    s_lat, e_lon = tile2deg(x1 + 1, y1 + 1, z)
    bounds = {"west": w_lon, "south": s_lat, "east": e_lon, "north": n_lat}
    return rgb, valid, bounds, tiles_from_scene, (nx_, ny_)


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------
def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_kunye_model(kunye_adi):
    """Model kunyesinden (J-36) yukler ve KARAR AYARINI kunyeden alir.

    Eski yol (`load_verified_model`) tek bir agirliga ve INFERENCE_PARAMS'taki
    sabit ayara bagliydi (esik 0,40 / guclendirme 3,5 / son isleme 2). Kunye
    yolu, egitim defterinin olctugu ayarla kosar -- maskeler makaledeki
    olcumle ayni kuralda uretilsin diye.
    """
    sys.path.insert(0, str(REPO_BACKEND)) if "REPO_BACKEND" in globals() else None
    from apps.road_damage.utils import model_kunyesi as mk

    kunye = mk.kunye_oku(kunye_adi)
    model, device = mk.model_yukle(kunye)
    karar = kunye["karar"]
    ayar = {
        "damage_booster": karar["guclendirme"],
        "threshold": karar["esik"],
        "use_imagenet_norm": kunye["girdi"]["normalizasyon"] == "imagenet",
        "postprocess_level": karar["sonIsleme"],
    }
    return model, device, kunye["agirlik"]["sha256"], kunye, ayar


def load_verified_model(expected_sha256):
    model, device = load_simple_model(str(LOCAL_MODEL_PATH))
    if model is None:
        raise RuntimeError(f"Model yuklenemedi: {LOCAL_MODEL_PATH}")
    actual = sha256_of(LOCAL_MODEL_PATH)
    if expected_sha256 and actual != expected_sha256:
        raise RuntimeError(
            "MODEL AGIRLIGI FARKLI -- kosu durduruldu.\n"
            f"  beklenen: {expected_sha256}\n  bulunan : {actual}\n"
            "Maskeler yereldeki modelle ayni agirlikla uretilmeli; aksi halde "
            "makaledeki sonuclar baska bir modele ait olur.")
    return model, device, actual


def library_versions():
    import importlib.metadata as md
    out = {"python": platform.python_version()}
    for pkg in ("torch", "segmentation-models-pytorch", "timm", "numpy", "opencv-python",
                "opencv-python-headless", "Pillow"):
        try:
            out[pkg] = md.version(pkg)
        except Exception:
            pass
    return out


def preview_base(img, max_side=2048):
    """Tam cozunurluklu mozaigin kucuk kopyasi -- cikarimdan ONCE alinir ki
    buyuk RGB dizisi cikarim sirasinda bellekte tutulmasin (z=22'de tek bir
    bolge ~370 MP; Colab'in ~12 GB RAM'inde tasma riski)."""
    w, h = img.size
    scale = min(1.0, max_side / max(h, w))
    size = (max(1, int(w * scale)), max(1, int(h * scale)))
    return img.resize(size, Image.BILINEAR)


def save_preview(base, damage, valid, path):
    size = base.size
    arr = np.array(base).astype(np.float32)
    dmg = np.array(Image.fromarray(damage * 255).resize(size, Image.NEAREST)) > 0
    val = np.array(Image.fromarray(valid * 255).resize(size, Image.NEAREST)) > 0
    arr[~val] *= 0.25                          # goruntu olmayan alan koyu
    arr[dmg] = arr[dmg] * 0.3 + np.array([255, 0, 0]) * 0.7   # hasar kirmizi
    Image.fromarray(arr.clip(0, 255).astype(np.uint8)).save(path, quality=85)


# --------------------------------------------------------------------------
# Ana akis
# --------------------------------------------------------------------------
def process_zone(zone, out_root, model, device, model_sha, radius_km, session,
                 zoom=ZOOM, mask_suffix="", ayar=None, kunye_adi=None):
    zid = zone["id"]
    mask_id = f"{zid}{mask_suffix}"
    lat, lon = zone["center"]
    radius = radius_km if radius_km is not None else zone["radiusKm"]
    if zone.get("bbox") and radius_km is None:
        # Drone sahnesi bolgeleri: maske sahnenin KENDI kapsama kutusu uzerinde
        # uretilir (bolge merkezinden turetilen kare yerine).
        bbox = tuple(zone["bbox"])
    else:
        bbox = bbox_from_center(lat, lon, radius)
    print(f"\n=== {mask_id} {zone['label']}  (z={zoom}) ===", flush=True)

    scenes = search_post_event_scenes(bbox, session)
    if zone.get("sceneIds"):
        # Sahne SABITLENDI: yalniz belirtilen sahneler, verilen sirayla. Drone
        # bolgelerinde Maxar'in onceligi istenmez -- farkli tarih ve 10 kat
        # kaba cozunurluk ayni maskeye karismasin.
        by_id = {sc["id"]: sc for sc in scenes}
        scenes = [by_id[i] for i in zone["sceneIds"] if i in by_id]
    if not scenes:
        print("  ATLANDI: deprem sonrasi sahne yok.", flush=True)
        return {"zoneId": mask_id, "status": "skipped", "reason": "no post-event scenes"}
    for s in scenes:
        print(f"  sahne: {s['date']}  {s['provider']:<10} {s['title']}", flush=True)

    t0 = time.perf_counter()
    rgb, valid, bounds, per_scene, (ntx, nty) = build_mosaic(
        bbox, scenes, session, z=zoom,
        progress=lambda d, n: print(f"  karo {d}/{n}", flush=True))
    t_fetch = time.perf_counter() - t0
    h, w = valid.shape
    valid_frac = float(valid.mean())
    print(f"  mozaik {w}x{h} px ({ntx}x{nty} karo), goruntu kapsamasi %{100 * valid_frac:.1f}", flush=True)
    if valid_frac == 0.0:
        return {"zoneId": mask_id, "status": "skipped", "reason": "scenes returned no pixels"}

    image = Image.fromarray(rgb)
    del rgb  # PIL kendi kopyasini tutuyor; buyuk dizi cikarim sirasinda bellekte kalmasin
    small = preview_base(image)

    last = [0]

    def on_patch(done, total):
        pct = int(100 * done / max(1, total))
        if pct >= last[0] + 10 or done == total:
            last[0] = pct
            print(f"  cikarim %{pct} ({done}/{total} yama)", flush=True)

    t1 = time.perf_counter()
    _raw, _boosted, pred, _inter, _img = run_inference(
        image, np.zeros((h, w), dtype=np.uint8), model, device,
        progress_callback=on_patch, **(ayar or INFERENCE_PARAMS))
    t_inf = time.perf_counter() - t1
    del _raw, _boosted, _inter, _img

    # Goruntu olmayan piksellerde tahmin anlamsizdir (siyah dolgu) -- sifirla.
    damage = (pred > 0).astype(np.uint8) & valid

    del image
    out = out_root / mask_id
    out.mkdir(parents=True, exist_ok=True)
    Image.fromarray(damage * 255).save(out / "damage_mask.png", optimize=True)
    Image.fromarray(valid * 255).save(out / "valid_mask.png", optimize=True)
    save_preview(small, damage, valid, out / "preview.jpg")

    mid_lat = (bounds["south"] + bounds["north"]) / 2.0
    mpp = 40075016.686 * math.cos(math.radians(mid_lat)) / (TILE * 2 ** zoom)
    meta = {
        "maskId": mask_id,
        "zoneId": zid, "zoneLabel": zone["label"], "city": zone["city"],
        "center": {"lat": lat, "lon": lon}, "radiusKm": radius,
        "zoneBbox": {"west": bbox[0], "south": bbox[1], "east": bbox[2], "north": bbox[3]},
        "bounds": bounds, "width": w, "height": h,
        "zoom": zoom, "metresPerPixel": round(mpp, 4),
        "sceneNativeGsdM": zone.get("sceneGsdM"),
        "projectionNote": ("Web Mercator karolari; yerel boru hatti enlemi dogrusal "
                           "izdusumler (canli /analyze ile ayni). 6 km'lik bolgede en kotu "
                           "sapma ~0,5 m (~1 piksel)."),
        "eventDate": EVENT_DATE, "postEventWindowEnd": POST_EVENT_END,
        "scenes": [{**{k: s[k] for k in ("id", "title", "provider", "date")},
                    "tilesUsed": per_scene.get(s["id"], 0)} for s in scenes],
        "validPixelFraction": round(valid_frac, 6),
        "damagePixelFraction": round(float(damage.mean()), 6),
        "damagePixelFractionOfObserved": round(float(damage.sum() / max(1, valid.sum())), 6),
        "model": {"repo": DEFAULT_ROAD_MODEL_REPO, "file": DEFAULT_ROAD_MODEL_FILENAME,
                  "sha256": model_sha, "architecture": "smp.Segformer(mit_b4, classes=1)"},
        "damageBooster": INFERENCE_PARAMS["damage_booster"],
        "threshold": INFERENCE_PARAMS["threshold"],
        "useImagenetNorm": INFERENCE_PARAMS["use_imagenet_norm"],
        "postProcessLevel": INFERENCE_PARAMS["postprocess_level"],
        "invalidPixelsZeroed": True,
        "inferenceDevice": str(device),
        "libraries": library_versions(),
        "timingsSec": {"fetch": round(t_fetch, 1), "inference": round(t_inf, 1)},
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  hasar: gorulen alanin %{100 * meta['damagePixelFractionOfObserved']:.2f}'i  |  "
          f"indirme {t_fetch:.0f}s, cikarim {t_inf:.0f}s  ->  {out}", flush=True)
    return {"zoneId": mask_id, "status": "done", "dir": str(out),
            "validPixelFraction": meta["validPixelFraction"],
            "damagePixelFractionOfObserved": meta["damagePixelFractionOfObserved"],
            "timingsSec": meta["timingsSec"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zones-json", default=None,
                    help="Bolge listesi (Colab). Verilmezse yerel scenario_dataset.py okunur.")
    ap.add_argument("--zones", nargs="*", default=None, help="Yalniz bu bolgeler (orn. H-Z1 K-Z1)")
    ap.add_argument("--radius-km", type=float, default=None,
                    help="Deneme icin bolge yaricapini ez (varsayilan: bolgenin kendi yaricapi)")
    ap.add_argument("--dataset", choices=["v2", "drone"], default="v2",
                    help="Yerel bolge listesi: v2 = Senaryo v2 (8 ilce), drone = Help.NGO drone sahneleri")
    ap.add_argument("--zoom", type=int, default=ZOOM,
                    help="Karo zoom'u (18 = ~0,48 m/px; drone sahnelerinin dogal siniri 22 = ~3 cm/px)")
    ap.add_argument("--mask-suffix", default="",
                    help="Cikti klasoru soneki; ayni bolgenin farkli zoom'larini yan yana tutmak icin (orn. -z20)")
    ap.add_argument("--out", default="model_masks")
    ap.add_argument("--expected-model-sha256", default=None)
    ap.add_argument("--kunye", default=None,
                    help="Model kunyesi adi (modeller/uydu/<ad>.json). Verilirse agirlik ve "
                         "karar ayari kunyeden gelir; verilmezse eski davranis (varsayilan "
                         "agirlik + INFERENCE_PARAMS).")
    args = ap.parse_args(argv)

    if args.zones_json:
        zones = json.loads(Path(args.zones_json).read_text(encoding="utf-8"))
    elif args.dataset == "drone":
        from benchmark.scenario_dataset_drone import ZONES
        zones = ZONES
    else:
        from benchmark.scenario_dataset import ZONES
        zones = ZONES
    if args.zones:
        zones = [z for z in zones if z["id"] in set(args.zones)]
    if not zones:
        raise RuntimeError("Islenecek bolge yok.")

    ayar = None
    if args.kunye:
        model, device, model_sha, kunye, ayar = load_kunye_model(args.kunye)
        print(f"model hazir: {kunye['ad']} ({kunye['mimari']['sinif']}/{kunye['mimari']['kodlayici']}), "
              f"{device}, sha256 {model_sha[:16]}..., ayar {ayar}", flush=True)
    else:
        model, device, model_sha = load_verified_model(args.expected_model_sha256)
        print(f"model hazir: {device}, sha256 {model_sha[:16]}...", flush=True)

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    adapter = requests.adapters.HTTPAdapter(pool_connections=32, pool_maxsize=32)
    session.mount("https://", adapter)

    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    manifest = []
    for zone in zones:
        try:
            manifest.append(process_zone(zone, out_root, model, device, model_sha, args.radius_km,
                                         session, args.zoom, args.mask_suffix, ayar, args.kunye))
        except Exception as e:  # bir bolge patlarsa digerleri yine uretilsin
            print(f"  HATA: {type(e).__name__}: {e}", flush=True)
            manifest.append({"zoneId": f"{zone['id']}{args.mask_suffix}", "status": "error",
                             "error": f"{type(e).__name__}: {e}"})
    (out_root / f"manifest{args.mask_suffix}.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== OZET ===")
    for m in manifest:
        extra = ""
        if m["status"] == "done":
            extra = (f"kapsama %{100 * m['validPixelFraction']:.1f}, "
                     f"hasar %{100 * m['damagePixelFractionOfObserved']:.2f}")
        print(f"  {m['zoneId']:10} {m['status']:8} {extra or m.get('reason') or m.get('error', '')}")
    return 0 if all(m["status"] != "error" for m in manifest) else 1


if __name__ == "__main__":
    raise SystemExit(main())
