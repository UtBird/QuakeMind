"""Afetzedenin çevresindeki tehlike: kapalı yollar ve hasar bildirilen bölgeler (J-180).

Koordinatörün ısı haritası (`/api/road_damage/heatmap`) ve kapanma katmanı
(`/api/katman/kapanmalar`) yalnız saha ve üstüne açık: ısı SOS çağrılarının
konumundan da beslenir ve afetzede başkasının çağrısını göremez (J-42).

Burada afetzedeye uygun bir sürüm var:
  * Kapalı yollar -- uydu analizinden bulunan kapalı yol parçaları. Kişisel veri
    değil; çizgisi varsa çizgi, yoksa orta nokta.
  * Hasar bölgeleri -- yaklaşık 250 m'lik karelerde hasar bildirimi sayısı.
    SOS SAYILMAZ; yalnız uydu, fotoğraf ve metin. Yalnız EN_AZ ve üstü
    bildirimli kareler döner: tek bir kişinin bildirimi konum olarak açılmaz.
    Sayım SQL'de (CLAUDE.md §10).

Kapsam afetzedenin konumu çevresiyle sınırlı (en çok 5 km): ülke çapında
döküm vermez.
"""
from __future__ import annotations

import json
import math
import time
from typing import Optional

from fastapi import APIRouter, Depends, Query

import kimlik
from depo import aktif_depo

yonlendirici = APIRouter()

#: Kare kenarı (derece). Enlemde ~250 m; Türkiye boylamlarında ~200 m.
HUCRE_DERECE = 0.0025
#: Bir karenin dönmesi için en az bildirim (k-anonimlik).
EN_AZ = 3
EN_COK_YARICAP_KM = 5.0
VARSAYILAN_GUN = 30


def _cizgi(ek) -> Optional[list]:
    if not ek:
        return None
    try:
        veri = json.loads(ek) if isinstance(ek, str) else ek
    except (TypeError, ValueError):
        return None
    cizgi = veri.get("cizgi") if isinstance(veri, dict) else None
    return cizgi if isinstance(cizgi, list) and len(cizgi) >= 2 else None


def _kutu(lat: float, lon: float, km: float) -> tuple[float, float, float, float]:
    dlat = km / 111.32
    dlon = km / (111.32 * max(0.2, math.cos(math.radians(lat))))
    return lon - dlon, lat - dlat, lon + dlon, lat + dlat


def _seviye(sayi: int) -> int:
    """1: 3–5 bildirim · 2: 6–14 · 3: 15 ve üstü (çok bildirim)."""
    return 3 if sayi >= 15 else 2 if sayi >= 6 else 1


@yonlendirici.get("/api/afetzede/cevre")
def afetzede_cevresi(
    lat: float = Query(..., ge=34.0, le=43.5),
    lon: float = Query(..., ge=24.5, le=46.0),
    yaricapKm: float = Query(3.0, gt=0, le=EN_COK_YARICAP_KM),
    gun: int = Query(VARSAYILAN_GUN, ge=1, le=365),
    _kul: dict = Depends(kimlik.kullanici),
):
    """Giriş yapmış her rol. Konumun çevresindeki kapalı yollar ve hasar
    bölgeleri; hasar bölgelerinde SOS yok ve en az 3 bildirim şartı var."""
    kutu = _kutu(lat, lon, yaricapKm)
    baslangic = time.time() - gun * 86400
    depo = aktif_depo()

    # Kapanmada zaman siniri yok: yurume rotasi (yol_agi.hasar_verisi) bilinen
    # butun kapanmalardan kacinir; haritada gorulen kume onunla ayni olmali.
    # Kapanma kendiliginden acilmaz, veride "acildi" durumu yok.
    kapanmalar = depo.kapanma_listele(kutu=kutu, sinir=3000)
    hucreler = depo.hasar_hucreleri(kutu, baslangic, HUCRE_DERECE, EN_AZ)

    # Aynı yol parçası birden çok analizde tekrar kaydedilebilir; afetzedeye
    # aynı parçayı bir kez göster (sayı da tekrarları saymasın). Liste yeniden
    # eskiye sıralı geldiği için kalan kayıt en yenisidir.
    kapali, gorulen = [], set()
    for k in kapanmalar:
        anahtar = (round(float(k["lon"]), 6), round(float(k["lat"]), 6))
        if anahtar in gorulen:
            continue
        gorulen.add(anahtar)
        kapali.append({"id": k["id"], "lon": k["lon"], "lat": k["lat"], "cizgi": _cizgi(k.get("ek"))})

    h = HUCRE_DERECE
    return {
        "kutu": list(kutu),
        "kapaliYollar": kapali,
        "hasarBolgeleri": [
            {
                # Karenin köşeleri [güney, batı, kuzey, doğu]; istemci kare çizer.
                "kare": [
                    round(30.0 + c["gy"] * h, 6),
                    round(20.0 + c["gx"] * h, 6),
                    round(30.0 + (c["gy"] + 1) * h, 6),
                    round(20.0 + (c["gx"] + 1) * h, 6),
                ],
                "sayi": int(c["sayi"]),
                "seviye": _seviye(int(c["sayi"])),
                "kaynaklar": {
                    "uydu": int(c["uydu"] or 0),
                    "fotograf": int(c["kamera"] or 0),
                    "metin": int(c["metin"] or 0),
                },
                "sonZaman": round(float(c["son_zaman"]) * 1000),
            }
            for c in hucreler
        ],
        "kaynak": {
            "kapaliYollar": (
                "Uydu görüntüsünden hasar analizi (QuakeMind modeli); bilinen bütün kapalı yol parçaları. "
                "Yürüme rotası bunlardan kaçınır."
            ),
            "hasarBolgeleri": (
                f"Son {gun} günde uydu, fotoğraf ve metin ihbarlarından gelen hasar bildirimleri; "
                f"yaklaşık 250 m'lik karelerde, en az {EN_AZ} bildirim olan kareler. SOS çağrıları dahil değil."
            ),
            "uyari": "Bildirimlere dayanır; kapalı görünmeyen yol da tehlikeli olabilir. Resmî uyarılara uyun.",
        },
        "esik": {"enAzBildirim": EN_AZ, "kareDerece": HUCRE_DERECE, "gun": gun},
    }
