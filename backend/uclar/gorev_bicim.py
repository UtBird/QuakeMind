"""Sevk gorevi ve ekip ciktilari (J-54).

SOS, ihbar ve ekip uclari ayni bicimi kullanir; dongusel ice aktarma olmasin
diye burada durur. Mesafeler sunucuda hesaplanir (istemci hesap yapmaz).

Yoldan uzaklik ve tahmini sure (J-55, `arac_rotasi.py`): acik gorevde ekip
konumunu bildirmisse arac aginda hesaplanir (`yol`, `rota`). Hiz yol turune
gore varsayimdir, anlik trafik yok. Ag yoksa ya da ekip bolge disindaysa
`yol` bos kalir ve ekran kus ucusunu (`kalanM`) yazar.

"Ekip nereden geliyor" sorusu icin en yakin yer adi altligin yer listesinden
(OSM, `veri/altlik/yerler.json`) bulunur. Liste yalniz altligi uretilmis
bolgeleri kapsar; 5 km icinde yer yoksa ad verilmez, uydurulmaz.
"""

from __future__ import annotations

import json
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np

import arac_rotasi
import canli_yayin
from depo import aktif_depo
from depo.sqlite_surucu import ACIK_GOREV, mesafe_m

YERLER = Path(__file__).resolve().parents[1] / "veri" / "altlik" / "yerler.json"
YER_ADI_SINIRI_M = 5000.0

EKIP_TURLERI = ("arama-kurtarma", "saglik", "itfaiye", "lojistik", "diger")
EKIP_DURUMLARI = ("musait", "hizmet-disi")


def ms(sn: Optional[float]) -> Optional[float]:
    return None if sn is None else round(float(sn) * 1000.0)


def gorev_yayinla(g: dict, hedef_durumu: Optional[str] = None) -> None:
    """Canli akisa 'gorev' mesaji: konsol olayi, ekibi ve gorev listesini
    tazeler; afetzedeye yalniz kendi olayininki gider (uclar/canli.py)."""
    canli_yayin.yayinla(
        "gorev",
        id=g["id"],
        hedefTur=g["hedef_tur"],
        hedefId=g["hedef_id"],
        ekipId=g["ekip_id"],
        durum=g["durum"],
        hedefDurumu=hedef_durumu,
    )


@lru_cache(maxsize=1)
def _yerler():
    if not YERLER.exists():
        return None
    veri = json.loads(YERLER.read_text(encoding="utf-8"))
    yerler = veri["yerler"] if isinstance(veri, dict) else veri
    if not yerler:
        return None
    return (
        [y["ad"] for y in yerler],
        np.radians([y["lat"] for y in yerler]),
        np.radians([y["lon"] for y in yerler]),
    )


def yer_adi(lon: Optional[float], lat: Optional[float]) -> Optional[str]:
    """Noktaya en yakin yer adi (mahalle, koy, ilce); 5 km icinde yoksa None."""
    if lon is None or lat is None:
        return None
    y = _yerler()
    if y is None:
        return None
    adlar, enlem, boylam = y
    f1, g1 = np.radians(lat), np.radians(lon)
    a = np.sin((enlem - f1) / 2) ** 2 + np.cos(f1) * np.cos(enlem) * np.sin((boylam - g1) / 2) ** 2
    d = 2 * 6371000.0 * np.arcsin(np.sqrt(a))
    i = int(np.argmin(d))
    return adlar[i] if d[i] <= YER_ADI_SINIRI_M else None


def _konum(lon, lat, zaman=None) -> Optional[dict]:
    if lon is None or lat is None:
        return None
    k = {"lon": lon, "lat": lat, "yerAdi": yer_adi(lon, lat)}
    if zaman is not None:
        k["zaman"] = ms(zaman)
    return k


def gorev_cikti(
    g: dict,
    hedef_konumu: Optional[tuple[float, float]] = None,
    adimlar: Optional[list[dict]] = None,
    afetzede: bool = False,
) -> dict:
    """Bir sevk gorevi. `ekipKonumu` ve `kalanM` yalniz gorev acikken verilir:
    bitmis gorevde ekip artik baska yerdedir."""
    acik = g["durum"] in ACIK_GOREV
    ekip_konumu = _konum(g.get("ekip_lon"), g.get("ekip_lat"), g.get("ekip_konum_zamani")) if acik else None
    kalan = None
    yol = None
    if ekip_konumu and hedef_konumu:
        kalan = round(mesafe_m(ekip_konumu["lon"], ekip_konumu["lat"], *hedef_konumu))
        # Olay yerindeki ekip icin rota aranmaz.
        if g["durum"] != "olay-yerinde":
            yol = arac_rotasi.yoldan(*hedef_konumu, ekip_konumu["lon"], ekip_konumu["lat"])
    c = {
        "id": g["id"],
        "hedefTur": g["hedef_tur"],
        "hedefId": g["hedef_id"],
        "durum": g["durum"],
        "kisiSayisi": g["kisi_sayisi"],
        "ekDestek": bool(g.get("ek_destek")),
        "atandi": ms(g["atandi"]),
        "yolaCikti": ms(g.get("yola_cikti")),
        "vardi": ms(g.get("vardi")),
        "bitti": ms(g.get("bitti")),
        "ekip": {
            "id": g["ekip_id"],
            "ad": g.get("ekip_ad"),
            "kurum": g.get("ekip_kurum"),
            "tur": g.get("ekip_tur"),
        },
        # Ekibin atandigi andaki konumu: "nereden geliyor".
        "cikis": _konum(g.get("cikis_lon"), g.get("cikis_lat")),
        "ekipKonumu": ekip_konumu,
        "kalanM": kalan,
        # Yoldan: uzaklik, tahmini sure (dk), rotadaki kapanma ve hasar ozeti.
        "yol": {k: v for k, v in yol.items() if k != "rota"} if yol else None,
        "rota": yol.get("rota") if yol else None,
    }
    # Kimin atadigi, ic not ve adimlarin kimden geldigi konsol icindir.
    if not afetzede:
        c["not"] = g.get("not_metni")
        c["sonuc"] = g.get("sonuc")
        c["olaySuruyor"] = bool(g.get("olay_suruyor"))
        c["atayanAd"] = g.get("atayan_ad")
        if adimlar is not None:
            c["adimlar"] = [
                {
                    "durum": a["durum"],
                    "zaman": ms(a["zaman"]),
                    "kisiAd": a.get("kisi_ad"),
                    "kaynak": a["kaynak"],
                    "not": a.get("not_metni"),
                }
                for a in adimlar
            ]
    return c


def gorevleri_ekle(hedef_tur: str, kayitlar: list[dict], ciktilar: list[dict], afetzede: bool = False) -> list[dict]:
    """Her olay ciktisina `gorevler` listesini (yeniden eskiye) ekler.
    `kayitlar` ve `ciktilar` ayni sirada olmalidir."""
    idler = [k["id"] for k in kayitlar]
    depo = aktif_depo()
    gorevler = depo.gorev_listele(hedef_tur=hedef_tur, hedef_idler=idler) if idler else []
    adimlar = depo.gorev_adimlari([g["id"] for g in gorevler]) if gorevler and not afetzede else {}
    grup: dict[str, list[dict]] = defaultdict(list)
    for g in gorevler:
        grup[g["hedef_id"]].append(g)
    for k, c in zip(kayitlar, ciktilar):
        c["gorevler"] = [
            gorev_cikti(g, (k["lon"], k["lat"]), None if afetzede else adimlar.get(g["id"], []), afetzede)
            for g in grup.get(k["id"], [])
        ]
    return ciktilar


def hedef_ozeti(hedef_tur: str, hedef: Optional[dict]) -> Optional[dict]:
    """Ekip listesinde "neye gidiyor": olayin turu, yeri ve kisa etiketi."""
    if hedef is None:
        return None
    return {
        "tur": "sos" if hedef_tur == "sos" else hedef.get("tur"),
        "id": hedef["id"],
        "lon": hedef["lon"],
        "lat": hedef["lat"],
        "mahalle": hedef.get("mahalle"),
        "oncelik": hedef.get("oncelik"),
        "etiket": hedef.get("etiket"),
        "durum": hedef.get("durum"),
    }


def hedef_bul(hedef_tur: str, hedef_id: str) -> Optional[dict]:
    depo = aktif_depo()
    return depo.sos_bul(hedef_id) if hedef_tur == "sos" else depo.ihbar_bul(hedef_id)


def ekip_cikti(e: dict, acik_gorev: Optional[dict] = None, uyeler: Optional[list[dict]] = None) -> dict:
    """Ekip ve su anki gorevi. `musait`: elle hizmet disi yapilmamis ve acik
    gorevi yok. Gorevdeki ekip musait gorunmez (J-54 oncesi gorunuyordu)."""
    gorev = None
    if acik_gorev is not None:
        hedef = hedef_bul(acik_gorev["hedef_tur"], acik_gorev["hedef_id"])
        ozet = hedef_ozeti(acik_gorev["hedef_tur"], hedef)
        cikti = gorev_cikti(acik_gorev, (hedef["lon"], hedef["lat"]) if hedef else None)
        gorev = {
            "id": cikti["id"],
            "durum": cikti["durum"],
            "kisiSayisi": cikti["kisiSayisi"],
            "atandi": cikti["atandi"],
            "yolaCikti": cikti["yolaCikti"],
            "vardi": cikti["vardi"],
            "kalanM": cikti["kalanM"],
            "yol": cikti["yol"],
            "rota": cikti["rota"],
            "hedefTur": cikti["hedefTur"],
            "hedefId": cikti["hedefId"],
            "hedef": ozet,
        }
    return {
        "id": e["id"],
        "ad": e["ad"],
        "kurum": e.get("kurum"),
        "tur": e.get("tur"),
        "kisiSayisi": e.get("kisi_sayisi"),
        "lon": e["lon"],
        "lat": e["lat"],
        "konumZamani": ms(e.get("konum_zamani")),
        "yerAdi": yer_adi(e["lon"], e["lat"]),
        "durum": e["durum"],
        "musait": e["durum"] == "musait" and gorev is None,
        "gorev": gorev,
        "uyeler": [{"id": u["id"], "adSoyad": u["ad_soyad"]} for u in (uyeler or [])],
        "guncellendi": ms(e["guncellendi"]),
    }


def ekipler_cikti(ekipler: list[dict]) -> list[dict]:
    depo = aktif_depo()
    acik = {g["ekip_id"]: g for g in depo.gorev_listele(yalniz_acik=True)}
    uyeler: dict[str, list[dict]] = defaultdict(list)
    for u in depo.saha_kullanicilari():
        if u.get("ekip_id"):
            uyeler[u["ekip_id"]].append(u)
    return [ekip_cikti(e, acik.get(e["id"]), uyeler.get(e["id"], [])) for e in ekipler]
