# -*- coding: utf-8 -*-
"""Tatbikat bolgesinin OSM verisini YEREL PBF'ten bir kez cikarir.

NEDEN. Simulasyon Overpass'a bagli kalamaz: olculdu (26 Eylul) -- dort aynanin
dordu de ulasilamiyordu (baglanti hatasi, 21-30 sn). Overpass dustugunde yol
maskesi bos geliyor, "0 kapali yol" cikiyor ve kosu sessizce anlamsizlasiyor
(J-68). Ayni alanda iki kosunun ayni sonucu vermesi de Overpass'in o anki
haline baglanmamali (CLAUDE.md 8).

NE URETIR.
  data/osm/roads.gpkg     yol geometrileri + oneway / highway / maxspeed /
                          lanes / junction etiketleri (maske, graf ve DONUS
                          maliyeti bunlardan hesaplanir)
  data/osm/tesisler.gpkg  ekip ussu olabilecek gercek tesisler

Tek gecis: PBF taramasinin kendisi ~210 sn ve kutu buyuklugunden bagimsiz,
bu yuzden butun calisma bolgesi TEK seferde cikarilir (alan basina ayri gecis
8 x 210 sn ederdi).

Kullanim (pyrosm'un kurulu oldugu ortamla):
    venv/Scripts/python.exe araclar_yerel_osm_kur.py
"""
import argparse
import time
from pathlib import Path

APP = Path(__file__).resolve().parent / "apps" / "road_damage"
CIKTI = APP / "data" / "osm"

# Calisma bolgesi: Hatay (Antakya/Defne) + Gaziantep (Nurdagi/Islahiye/Sekeroba/
# Gokcedere) + Kahramanmaras merkez. Acik drone goruntusu olan butun alanlari
# ve ekip usleri icin ~4 km marji kapsar.
BOLGE = [36.05, 36.10, 37.00, 37.65]   # bati, guney, dogu, kuzey

# Ekip ussu olabilecek tesisler; tatbikat.ekipler() ile ayni tercih sirasi.
TESIS_ETIKETLERI = {
    "amenity": ["fire_station", "hospital", "police", "clinic"],
    "emergency": True,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pbf", default="D:/quakemind_osm_data/turkey-latest.osm.pbf")
    ap.add_argument("--bolge", nargs=4, type=float, default=BOLGE,
                    metavar=("BATI", "GUNEY", "DOGU", "KUZEY"))
    a = ap.parse_args()

    from pyrosm import OSM

    CIKTI.mkdir(parents=True, exist_ok=True)
    print(f"PBF   : {a.pbf}")
    print(f"bolge : {a.bolge}")

    t = time.perf_counter()
    osm = OSM(a.pbf, bounding_box=list(a.bolge))
    nodes, edges = osm.get_network(network_type="driving", nodes=True)
    print(f"yol   : {len(edges)} kenar, {len(nodes)} dugum  ({time.perf_counter()-t:.0f} sn)")

    tut = [c for c in ("u", "v", "length", "oneway", "highway", "maxspeed",
                       "lanes", "junction", "name", "id", "geometry") if c in edges.columns]
    yollar = edges[tut].copy()
    for c in yollar.columns:
        if c != "geometry":
            yollar[c] = yollar[c].astype(str).where(yollar[c].notna(), None)
    yol_yolu = CIKTI / "roads.gpkg"
    yollar.to_file(yol_yolu, driver="GPKG", layer="roads")
    print(f"yazildi: {yol_yolu}  ({yol_yolu.stat().st_size/1e6:.1f} MB)")

    t = time.perf_counter()
    try:
        poi = osm.get_pois(custom_filter=TESIS_ETIKETLERI)
        if poi is not None and not poi.empty:
            sutun = [c for c in ("id", "name", "amenity", "emergency", "geometry") if c in poi.columns]
            poi = poi[sutun].copy()
            poi["geometry"] = poi.geometry.centroid
            for c in poi.columns:
                if c != "geometry":
                    poi[c] = poi[c].astype(str).where(poi[c].notna(), None)
            t_yolu = CIKTI / "tesisler.gpkg"
            poi.to_file(t_yolu, driver="GPKG", layer="tesisler")
            print(f"tesis : {len(poi)} kayit -> {t_yolu}  ({time.perf_counter()-t:.0f} sn)")
        else:
            print("tesis : bulunamadi")
    except Exception as e:
        print(f"tesis : cikarilamadi ({type(e).__name__}: {e})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
