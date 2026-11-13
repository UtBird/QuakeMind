"""EMSR648'de hasarli yol bulunan 1 km'lik hucreler -- yumusak maliyet deneyi icin.

J-30'daki drone sahnelerinden yalniz K-D1'de gercek yol hasari vardi; Hatay'daki
iki drone sahnesinde EMSR hic yol hasari isaretlememisti. Bolgeler arasi
sinama (Hatay <-> Kahramanmaras) icin model maskesi, EMSR'nin hasarli yol
isaretledigi yerlerde gerekir. Bu betik o yerleri 1 km'lik izgara hucrelerine
boler ve maske ureticisinin (benchmark/colab/make_model_masks.py --zones-json)
okudugu bolge listesini yazar.

Kural (onceden sabit): bir hucre, icine en az bir hasarli EMSR yol kosesi
dusuyorsa listeye girer. Hucre merkezi izgara hucresinin merkezidir -- hasar
kumesinin agirlik merkezi DEGIL; boylece hucre konumu sonuca gore secilmemis
olur.

    python benchmark/emsr_hucreleri.py      # -> benchmark/data/emsr_hucreleri.json
"""
import json
import math
from pathlib import Path

BENCH = Path(__file__).resolve().parent
VERI = BENCH / "data"
CIKTI = VERI / "emsr_hucreleri.json"
HUCRE_KM = 1.0

ILLER = {
    "hatay": {"onek": "HE", "paket": "EMSR648_AOI11_GRA_MONIT01_r1_RTP01_v2_vector.zip"},
    "kahramanmaras": {"onek": "KE", "paket": "EMSR648_AOI04_GRA_MONIT01_r1_RTP01_v1_vector.zip"},
}


def hucreler(il: str) -> list[dict]:
    yer = json.loads((VERI / f"{il}_copernicus_ground_truth.json").read_text(encoding="utf-8"))
    noktalar = [(c[0], c[1]) for s in yer["damagedRoadSegments"] for c in s.get("coords", [])]
    lat0 = min(p[0] for p in noktalar)
    lon0 = min(p[1] for p in noktalar)
    orta_enlem = sum(p[0] for p in noktalar) / len(noktalar)
    km_lon = 111.32 * math.cos(math.radians(orta_enlem))
    km_lat = 110.57

    dolu = {}
    for lat, lon in noktalar:
        ix = int((lon - lon0) * km_lon / HUCRE_KM)
        iy = int((lat - lat0) * km_lat / HUCRE_KM)
        dolu[(ix, iy)] = dolu.get((ix, iy), 0) + 1

    cikti = []
    for n, ((ix, iy), kose_sayisi) in enumerate(sorted(dolu.items(), key=lambda x: (x[0][1], x[0][0])), 1):
        merkez_lon = lon0 + (ix + 0.5) * HUCRE_KM / km_lon
        merkez_lat = lat0 + (iy + 0.5) * HUCRE_KM / km_lat
        cikti.append({
            "id": f"{ILLER[il]['onek']}-{n:02d}",
            "label": f"{il} EMSR hucresi {ix},{iy}",
            "city": il,
            "center": [round(merkez_lat, 6), round(merkez_lon, 6)],
            "radiusKm": HUCRE_KM / 2,
            "emsrPackage": ILLER[il]["paket"],
            "emsrKoseSayisi": kose_sayisi,
        })
    return cikti


def main() -> int:
    tum = []
    for il in ILLER:
        h = hucreler(il)
        print(f"{il}: {len(h)} hucre")
        tum.extend(h)
    CIKTI.write_text(json.dumps(tum, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(tum)} hucre -> {CIKTI}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
