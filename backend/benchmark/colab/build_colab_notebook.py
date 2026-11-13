"""QuakeMind_model_masks.ipynb defterini depodaki GUNCEL kaynaklardan uretir.

Defter; cikarim kodunu (apps/road_damage/utils/inference.py), bolge sinir
fonksiyonunu (assembly.bbox_from_center), maske ureticisini
(make_model_masks.py) ve iki senaryonun bolge listelerini BIREBIR gomer.
Bunlardan biri degisirse defter bu betikle yeniden uretilmelidir -- aksi
halde Colab'da, yerelde calisandan farkli bir kod kosar. Gomulen her
dosyanin SHA-256'si defterin ilk hucresine yazilir ve Colab'da dogrulanir.

    python benchmark/colab/build_colab_notebook.py
"""
import hashlib
import inspect
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent.parent
sys.path.insert(0, str(BACKEND))

from apps.road_damage.utils import assembly  # noqa: E402
from benchmark import scenario_dataset as V2  # noqa: E402
from benchmark import scenario_dataset_drone as DRONE  # noqa: E402

MODEL_SHA256 = "7d7fb8d822aaf241f1be2f002f3bff9e72b66331e941408c4ef77d4e1d2900ce"
SMP_VERSION = "0.5.0"
DRONE_ZOOMS = (21, 22)      # 18-20 yerelde (CPU) uretildi; 22 = sahnelerin dogal siniri
OUT = HERE / "QuakeMind_model_masks.ipynb"


def norm(text):
    # %%writefile hucre sonundaki satir sonunu koruyup korumamasi IPython
    # surumune bagli; iki tarafta da ayni bicime getirilir.
    return text.rstrip("\n") + "\n"


def sha(text):
    return hashlib.sha256(norm(text).encode("utf-8")).hexdigest()


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(keepends=True)}


def writefile(name, content):
    return code(f"%%writefile {name}\n{content}")


def zone_json(zones, keys):
    rows = []
    for z in zones:
        row = {k: z[k] for k in keys if k in z}
        row["center"] = list(z["center"])
        rows.append(row)
    return json.dumps(rows, ensure_ascii=False, indent=2)


inference_src = (BACKEND / "apps/road_damage/utils/inference.py").read_text(encoding="utf-8")
maker_src = (HERE / "make_model_masks.py").read_text(encoding="utf-8")
geo_src = ('"""assembly.bbox_from_center\'in birebir kopyasi (defter uretici tarafindan gomuldu)."""\n'
           "import math\n\n\n" + inspect.getsource(assembly.bbox_from_center))
drone_src = zone_json(DRONE.ZONES, ("id", "city", "label", "radiusKm", "bbox", "sceneIds",
                                    "sceneTitle", "sceneGsdM", "nativeZoom"))
v2_src = zone_json(V2.ZONES, ("id", "city", "label", "radiusKm"))

hashes = {
    "inference.py": sha(inference_src),
    "make_model_masks.py": sha(maker_src),
    "qm_geo.py": sha(geo_src),
    "zones_drone.json": sha(drone_src),
    "zones_v2.json": sha(v2_src),
}
drone_list = "\n".join(f"- **{z['id']}** {z['label']} — {z['sceneProvider']}, {z['sceneDate']}, "
                       f"{100 * z['sceneGsdM']:.1f} cm/px" for z in DRONE.ZONES)


def run_cell(zones_file, zoom, suffix, label):
    return code(f"""
import make_model_masks as mm
rc = mm.main(["--zones-json", "{zones_file}", "--zoom", "{zoom}", "--mask-suffix={suffix}",
              "--out", "model_masks", "--expected-model-sha256", "{MODEL_SHA256}"])
if rc != 0:
    raise RuntimeError("{label}: en az bir bolgede HATA var -- yukaridaki ciktiya bakin.")
""")


ZIP_CELL = code("""
import shutil
from google.colab import files
shutil.make_archive("model_masks", "zip", ".", "model_masks")
files.download("model_masks.zip")
""")

cells = [
    md(f"""
# QuakeMind — Drone sahnelerinde en yüksek çözünürlükte hasar maskesi (Colab T4)

**Ne yapar:** Modelin uygulamada test edildiği üç **Help.NGO drone** sahnesinde
(deprem sonrası, 9 Şubat 2023) SegFormer hasar maskesi üretir:

{drone_list}

Yerelde (CPU) **z=18, 19, 20** zaten üretildi. Bu defter **z=21 (~6 cm/px)** ve
**z=22 (~3 cm/px, sahnelerin doğal çözünürlüğü)** için. z=22'nin üstü yeni bilgi
katmaz; karo sunucusu yalnızca büyütür.

**Dikkat — en yüksek zoom en iyi sonuç demek değil.** Model KATE-CD ile
(Maxar/Pléiades, **0,3–0,5 m/px**) eğitildi. z=22'de bir bina, modelin eğitimde
gördüğünden ~15 kat büyük görünür. Hangi zoom'un en iyi olduğuna yerelde
`benchmark/validate_model_masks.py` ile **EMSR648'e karşı ölçerek** karar
verilecek.

**Nasıl çalıştırılır**
1. **Çalışma zamanı → Çalışma zamanı türünü değiştir → T4 GPU**
2. **Çalışma zamanı → Tümünü çalıştır**
3. İki kez `model_masks.zip` iner (z=21 bitince ve z=22 bitince). **İkincisini** sakla;
   z=22 bellek yüzünden çökerse **birincisi** elinde kalır.
4. Zip'i yerelde **`backend/benchmark/data/model_masks/`** içine aç —
   `model_masks/H-D1-z22/damage_mask.png` gibi klasörler oluşmalı.
5. Yerelde:
   `python benchmark/validate_model_masks.py --dataset drone --suffixes=-z18,-z19,-z20,-z21,-z22`

**Tahmini süre (T4):** z=21 ~10-15 dk, z=22 ~30-60 dk.
**Bellek:** z=22'de tek sahne ~370 megapiksel; çıkarım ~9 GB RAM ister. Ücretsiz
Colab (~12,7 GB) sınırda. Çökerse z=21 sonuçlarıyla devam edilebilir.

**Değiştirme:** Bu defter `benchmark/colab/build_colab_notebook.py` ile üretildi.
Kodu burada düzenleme; depoda düzenleyip defteri yeniden üret.

Gömülü dosyaların SHA-256 parmak izleri:
```
{json.dumps(hashes, indent=2)}
```
Beklenen model ağırlığı: `{MODEL_SHA256}`
"""),
    md("## 1. GPU ve bellek kontrolü"),
    code("""
import torch, psutil
if not torch.cuda.is_available():
    raise RuntimeError("GPU YOK. Calisma zamani -> Calisma zamani turunu degistir -> T4 GPU secip yeniden baslatin.")
print("GPU :", torch.cuda.get_device_name(0))
print(f"RAM : {psutil.virtual_memory().total / 1e9:.1f} GB (z=22 icin ~9 GB gerekir)")
"""),
    md(f"## 2. Kütüphane\n`segmentation-models-pytorch` yereldeki sürümle (**{SMP_VERSION}**) aynı olmalı."),
    code(f"!pip install -q segmentation-models-pytorch=={SMP_VERSION}"),
    md("## 3. Kod ve bölgeler (depodan birebir kopya)"),
    writefile("inference.py", inference_src),
    writefile("qm_geo.py", geo_src),
    writefile("make_model_masks.py", maker_src),
    writefile("zones_drone.json", drone_src),
    writefile("zones_v2.json", v2_src),
    code(f"""
import hashlib
expected = {json.dumps(hashes)}
for name, h in expected.items():
    got = hashlib.sha256((open(name, encoding="utf-8").read().rstrip("\\n") + "\\n").encode("utf-8")).hexdigest()
    assert got == h, f"{{name}} beklenenden farkli -- defteri depodan yeniden uretin"
print("Gomulu dosyalar dogrulandi.")
"""),
    md("## 4. Drone sahneleri — z=21 (~6 cm/px)\nModel ağırlığı HuggingFace'ten otomatik iner ve "
       "parmak izi kontrol edilir; farklıysa çalışma durur."),
    run_cell("zones_drone.json", 21, "-z21", "z=21"),
    md("### z=21 sonuçlarını hemen indir (z=22 çökerse elde kalsın)"),
    ZIP_CELL,
    md("## 5. Drone sahneleri — z=22 (~3 cm/px, doğal çözünürlük)"),
    run_cell("zones_drone.json", 22, "-z22", "z=22"),
    md("## 6. Göz kontrolü\nKırmızı: modelin hasar dediği yer. Koyu: görüntü olmayan alan."),
    code("""
import json, glob
from IPython.display import Image as IPImage, display
for meta_path in sorted(glob.glob("model_masks/*/meta.json")):
    m = json.load(open(meta_path, encoding="utf-8"))
    print(f"{m['maskId']:10} z={m['zoom']}  {100*m['metresPerPixel']:.1f} cm/px  "
          f"kapsama %{100*m['validPixelFraction']:.1f}  hasar %{100*m['damagePixelFractionOfObserved']:.2f}  "
          f"sure indirme {m['timingsSec']['fetch']}s / cikarim {m['timingsSec']['inference']}s")
    display(IPImage(meta_path.replace("meta.json", "preview.jpg"), width=480))
"""),
    md("## 7. Tümünü indir (z=21 + z=22)"),
    ZIP_CELL,
    md("---\n## (İsteğe bağlı) Senaryo v2 — 8 ilçe, z=18\n"
       "Drone sahnelerinden bağımsız. Çalıştırmak için alttaki hücrenin başındaki `#` işaretlerini kaldır."),
    code(f"""
# import make_model_masks as mm
# rc = mm.main(["--zones-json", "zones_v2.json", "--zoom", "18", "--out", "model_masks",
#               "--expected-model-sha256", "{MODEL_SHA256}"])
"""),
]

nb = {
    "nbformat": 4, "nbformat_minor": 5,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"provenance": [], "gpuType": "T4"},
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
    },
    "cells": cells,
}
OUT.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"yazildi: {OUT}  ({len(cells)} hucre)")
for k, v in hashes.items():
    print(f"  {k:22} {v[:16]}...")
