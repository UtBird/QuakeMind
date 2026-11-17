# -*- coding: utf-8 -*-
"""Yerel adres dizinini kurar (J-170): metindeki adres dışarıya sorulmadan çözülsün.

Kaynaklar (hepsi yerelde, ağ yok):
  * il ve ilçe merkezleri  -- apps/disaster_nlp/src/tr_locations.py
  * mahalle, köy, kasaba   -- veri/altlik/yerler.json (OSM place düğümleri, 5 bölge)
  * adlı sokak ve caddeler -- apps/road_damage/data/osm/roads.gpkg (yerel OSM kopyası)

Her sokak, parçalarının orta noktalarından en yakın mahalleye (3 km içinde) ve
en yakın ilçe merkezine bağlanır. Aynı adlı sokak farklı mahallelerde ayrı kayıt
olur ("Atatürk Caddesi" 1 203 parça, onlarca yerde).

Çıktı: metin_analizi/veri/adres_dizini.json.gz (depoya girer; OSM verisi ODbL,
künye dosyada). Süre: bu makinede ~1 dk.

    python araclar_adres_dizini_kur.py
"""
from __future__ import annotations

import gzip
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

KOK = Path(__file__).resolve().parent
sys.path.insert(0, str(KOK))
sys.path.insert(0, str(KOK / "apps" / "disaster_nlp"))

from metin_analizi.normal import katla  # noqa: E402
from src.tr_locations import DISTRICT_COORDS, PROVINCE_COORDS  # noqa: E402

YERLER = KOK / "veri" / "altlik" / "yerler.json"
YOLLAR = KOK / "apps" / "road_damage" / "data" / "osm" / "roads.gpkg"
CIKTI = KOK / "metin_analizi" / "veri" / "adres_dizini.json.gz"

BOLGE_IL = {"antakya": "Hatay", "maras": "Kahramanmaraş", "antep": "Gaziantep",
            "malatya": "Malatya", "adiyaman": "Adıyaman"}
MAHALLE_TURLERI = {"suburb": "mahalle", "neighbourhood": "mahalle", "quarter": "mahalle",
                   "village": "köy", "town": "kasaba", "city": "şehir"}
MAHALLE_YARICAPI_M = 3000


def mesafe_m(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    h = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 6371000 * 2 * math.asin(math.sqrt(h))


def sokak_tipi(ad_katli: str) -> str:
    son = ad_katli.split()[-1] if ad_katli else ""
    if son in ("caddesi", "cadde", "cad", "cd"):
        return "cadde"
    if son in ("bulvari", "bulvar"):
        return "bulvar"
    if son in ("yolu", "yol"):
        return "yol"
    if son in ("sokak", "sokagi", "sk", "sok"):
        return "sokak"
    return "diğer"


def main():
    t0 = time.time()
    iller = [{"ad": ad, "lat": round(lat, 5), "lon": round(lon, 5)} for ad, (lat, lon) in PROVINCE_COORDS.items()]
    ilceler = [{"ad": ilce, "il": il, "lat": round(lat, 5), "lon": round(lon, 5)}
               for (il, ilce), (lat, lon) in DISTRICT_COORDS.items()]

    def en_yakin_ilce(lat, lon, il=None):
        adaylar = [x for x in ilceler if il is None or x["il"] == il]
        if not adaylar:
            return None
        return min(adaylar, key=lambda x: mesafe_m(lat, lon, x["lat"], x["lon"]))

    yerler = []
    for y in json.loads(YERLER.read_text(encoding="utf-8")):
        il = BOLGE_IL.get(y.get("bolge"))
        ilce = en_yakin_ilce(y["lat"], y["lon"], il)
        yerler.append({
            "ad": y["ad"], "tur": MAHALLE_TURLERI.get(y.get("tur"), y.get("tur")),
            "lat": round(y["lat"], 5), "lon": round(y["lon"], 5),
            "ilce": ilce["ad"] if ilce else None, "il": il,
        })
    mahalleler = [(i, y) for i, y in enumerate(yerler) if y["tur"] in ("mahalle", "köy")]

    import pyogrio  # noqa: E402

    tablo = pyogrio.read_dataframe(YOLLAR, columns=["name"], where="name IS NOT NULL")
    noktalar = tablo.geometry.interpolate(0.5, normalized=True)
    gruplar: dict[tuple, list] = defaultdict(list)
    for ad, nk in zip(tablo["name"], noktalar):
        if not ad or nk is None or nk.is_empty:
            continue
        lat, lon = nk.y, nk.x
        # En yakın mahalle (3 km içinde); yoksa yalnız ilçe.
        en_iyi, en_iyi_m = None, MAHALLE_YARICAPI_M
        for i, m in mahalleler:
            if abs(m["lat"] - lat) > 0.04 or abs(m["lon"] - lon) > 0.05:
                continue
            d = mesafe_m(lat, lon, m["lat"], m["lon"])
            if d < en_iyi_m:
                en_iyi, en_iyi_m = i, d
        ilce = en_yakin_ilce(lat, lon)
        anahtar = (ad.strip(), en_iyi, ilce["ad"] if ilce else None)
        gruplar[anahtar].append((lat, lon))

    sokaklar = []
    for (ad, yer_i, ilce), pts in gruplar.items():
        lat = sum(p[0] for p in pts) / len(pts)
        lon = sum(p[1] for p in pts) / len(pts)
        yayilim = max(mesafe_m(lat, lon, p[0], p[1]) for p in pts)
        il = yerler[yer_i]["il"] if yer_i is not None else next((x["il"] for x in ilceler if x["ad"] == ilce), None)
        sokaklar.append({
            "ad": ad, "tip": sokak_tipi(katla(ad)), "lat": round(lat, 5), "lon": round(lon, 5),
            "yayilimM": round(yayilim), "parca": len(pts), "yer": yer_i, "ilce": ilce, "il": il,
        })

    dizin = {
        "_kunye": {
            "uretim": time.strftime("%Y-%m-%d"),
            "kaynak": "OpenStreetMap katkıcıları (ODbL 1.0): yerel kopya roads.gpkg ve altlık yer adları; "
                      "il/ilçe merkezleri tr_locations.py",
            "kapsam": "sokaklar: Hatay, Kahramanmaraş, Gaziantep (yerel OSM kutusu); mahalleler: 5 altlık bölgesi; "
                      "il/ilçe: tr_locations",
            "arac": "araclar_adres_dizini_kur.py",
        },
        "iller": iller,
        "ilceler": ilceler,
        "yerler": yerler,
        "sokaklar": sokaklar,
    }
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(CIKTI, "wt", encoding="utf-8") as f:
        json.dump(dizin, f, ensure_ascii=False, separators=(",", ":"))
    print(f"il {len(iller)}, ilçe {len(ilceler)}, yer {len(yerler)}, sokak kaydı {len(sokaklar)} "
          f"({len(tablo)} adlı parça) -> {CIKTI} {CIKTI.stat().st_size // 1024} KB, {time.time() - t0:.0f} sn")


if __name__ == "__main__":
    main()
