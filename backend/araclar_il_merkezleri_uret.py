"""Il merkezleri uretimi: deprem riski ekraninin 81 il secicisi icin.

Risk ekrani eskiden yalniz bes harita bolgesini sunuyordu; eski web 81 ili
yalniz adla gonderiyor, sunucu konumu her istekte Nominatim'den ariyordu (dis
servis, istek yolunda). Bu arac il merkezlerini yerel OSM kopyasindan bir kez
uretir (kural 3); sunucu hazir dosyayi verir (uclar/risk.py).

Yontem: OSM'deki 81 il siniri (boundary=administrative, admin_level=4) ve
`place=city` noktalari okunur; her ilin merkezi sinirinin icindeki `city`
noktasidir. Birden fazlaysa adi ilin adiyla ayni olan, o da yoksa nufusu en
buyuk olan alinir. `capital=4` etiketi kullanilmaz: Turkiye verisinde yalniz
uc ilde var.

    python araclar_il_merkezleri_uret.py

Olculdu (19 Ekim 2026, turkey-latest.osm.pbf): 81 sinir, 82 city noktasi;
iki nokta yalniz Adana'da (Adana, Ceyhan). Okuma ~50 sn.
"""
import datetime
import json
import os
import sys
import time
import unicodedata
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
CIKTI = BACKEND / "veri" / "il_merkezleri.json"
IL_SAYISI = 81


def main():
    sys.path.insert(0, str(BACKEND))
    import geopandas as gpd
    import pyogrio
    from apps.road_damage.utils.network import LOCAL_PBF_PATH

    os.environ.setdefault("OSM_MAX_TMPFILE_SIZE", "3000")  # dugum indeksi RAM'de (MB)
    pbf = Path(LOCAL_PBF_PATH)
    if not pbf.exists():
        print(f"OSM kopyasi yok: {pbf} (QUAKEMIND_LOCAL_OSM_PBF)")
        return 1

    t0 = time.time()
    sinir = pyogrio.read_dataframe(
        str(pbf), layer="multipolygons", columns=["osm_id", "name"],
        where="admin_level='4' AND boundary='administrative'")
    nokta = pyogrio.read_dataframe(
        str(pbf), layer="points", columns=["osm_id", "name", "other_tags"], where="place='city'")
    sure = round(time.time() - t0, 1)

    nokta["nufus"] = nokta["other_tags"].str.extract(r'"population"=>"(\d+)"')[0].astype(float)
    eslesen = gpd.sjoin(nokta, sinir.rename(columns={"name": "il", "osm_id": "il_osm"}),
                        predicate="within")

    iller = []
    for il, g in eslesen.groupby("il"):
        ayni_ad = g[g["name"] == il]
        secilen = (ayni_ad if len(ayni_ad) else g.sort_values("nufus", ascending=False)).iloc[0]
        iller.append({
            "il": il,
            "merkez": secilen["name"],
            "lat": round(secilen.geometry.y, 5),
            "lon": round(secilen.geometry.x, 5),
            # OSM `population` etiketi; buyuksehirde ilin tamami (Konya 2,16 milyon).
            "nufus": None if secilen["nufus"] != secilen["nufus"] else int(secilen["nufus"]),
            "osm": f"node/{secilen['osm_id']}",
            "sinirOsm": f"relation/{secilen['il_osm']}",
        })

    eksik = sorted(set(sinir["name"]) - {i["il"] for i in iller})
    if len(iller) != IL_SAYISI or eksik:
        # Eksik il uydurulmaz (kural 1): dosya yazilmaz, eksik soylenir.
        print(f"{len(iller)} il bulundu, {IL_SAYISI} bekleniyordu; merkezsiz: {eksik}")
        return 1

    iller.sort(key=lambda i: unicodedata.normalize("NFKD", i["il"]).casefold())
    cikti = {
        "kaynak": {
            "ad": "OpenStreetMap", "atif": "© OpenStreetMap katkıcıları", "lisans": "ODbL 1.0",
            "dosya": pbf.name,
            "dosyaTarihi": datetime.date.fromtimestamp(pbf.stat().st_mtime).isoformat(),
            "yontem": "il siniri (admin_level=4) icindeki place=city noktasi",
        },
        "uretim": datetime.datetime.now().isoformat(timespec="seconds"),
        "iller": iller,
    }
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(cikti, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(iller)} il merkezi -> {CIKTI.relative_to(BACKEND)} | okuma {sure} sn", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
