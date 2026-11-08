# -*- coding: utf-8 -*-
"""Goruntu kaynagi ile OSM arasindaki olculmus oteleme (co-registration).

NEDEN. Hizli mudahale ortofotolari her zaman OSM ile oturmuyor. Antakya'da
bina genisligi 10-15 m; birkac metrelik kayma hasar noktasini KOMSU sokaga,
kapanmayi da YANLIS yola yaziyor.

NEDEN CALISMA ANINDA OLCMUYORUZ (olculdu, 26 Eylul). Once her analizde
otomatik faz korelasyonu denendi. Uc referans, uc farkli cevap verdi:

    Esri Wayback 2021 (deprem oncesi)  ->   4,0 m
    Maxar 2023-02-08                   ->  10,2 m
    Maxar 2023-02-11                   ->  96,9 m   (acikca sacma)

Maxar karolari EGIK bakisli: binalar yatiyor, catilar sokagi ortuyor, bu
yuzden referans olarak guvenilmez -- iki Maxar sahnesinin birbiriyle 90 m
uyusmamasi bunun kaniti. Uygulanan 10,2 m'lik duzeltme ISI KOTULESTIRDI
(asagidaki olcum). Ustelik her analizde 3 ek goruntu indirmek analizi
yavaslatiyordu; CLAUDE.md 3: pahali is istek yolunda calismaz.

BUGUNKU KURAL. Kayma sahne basina BIR KEZ, OSM'e karsi olculur
(`araclar_hizalama_olc.py`), kunyesiyle bu tabloya yazilir, calisma aninda
yalnizca TABLODAN OKUNUR. Maliyet sifir, sonuc her kosuda ayni.

ESIK. `ESIK_M`in altindaki kayma UYGULANMAZ, yalnizca rapora yazilir: OSM
eksen cizgisinin kendi dogrulugu bu mertebede (Antakya'da ~3-5 m), yani daha
kucuk bir duzeltme gurultuyu "duzeltmek"ten baska is yapmaz.
"""
from __future__ import annotations

import numpy as np

# Bu esigin altinda olcum RAPORLANIR ama UYGULANMAZ (yukaridaki gerekce).
ESIK_M = 5.0

# Sahne -> olculmus oteleme. Anahtar, karo adresinde gecen ayirt edici parca.
# `doguM` / `kuzeyM`: goruntunun IÇERIGINI OSM'e oturtmak icin ne kadar
# kaydirmak gerekir (artı = doguya / kuzeye).
OLCULEN_KAYMALAR: list[dict] = [
    {
        "anahtar": "63eb7815ca43600005f4d91e",  # OAM: Hatay - Defne - Elektrik Mah.
        "ad": "Hatay - Defne - Elektrik Mah. (OAM, cekim 2023-02-09)",
        "doguM": 0.0,
        "kuzeyM": -2.4,
        "olcum": {
            "yontem": "OSM yol maskesi tarama (cati kirmiziligi R-B en dusuk)",
            "tarih": "2026-09-26",
            "zoom": 18,
            "gsdM": 0.482,
            "enIyiPiksel": {"dx": 0, "dy": 5},
            "skorAraligi": {"enIyi": 5.52, "sifirKaymada": 6.43, "enKotu": 16.75},
            "not": (
                "2,4 m esigin (5,0 m) altinda -> UYGULANMAZ. Ayni tarama, daha once "
                "uygulanan 8,7 m'lik duzeltmeyi 10,73 ile acikca kotu buluyor."
            ),
        },
    },
]


def sahne_kaymasi(karo_adresi: str | None) -> dict | None:
    """Karo adresine karsilik gelen olculmus kayma kaydi; yoksa None."""
    if not karo_adresi:
        return None
    for kayit in OLCULEN_KAYMALAR:
        if kayit["anahtar"] in karo_adresi:
            return kayit
    return None


def piksel_otelemesi(kayit: dict, gsd_m: float) -> tuple[int, int]:
    """(dx, dy) piksel: `img.transform(AFFINE, (1,0,dx,0,1,dy))` icin.

    PIL'de bu donusum `cikti(x,y) = girdi(x+dx, y+dy)` demek; yani ICERIK
    (-dx, -dy) kadar kayar. Dogu artı x, kuzey eksi y oldugu icin isaretler
    burada terslenir.
    """
    dx = -int(round(kayit["doguM"] / gsd_m))
    dy = int(round(kayit["kuzeyM"] / gsd_m))
    return dx, dy


def faz_korelasyonu(goruntu_np, referans_np) -> tuple[int, int, float]:
    """Iki goruntu arasindaki oteleme (faz korelasyonu).

    Donus: (dx, dy, guven). Artik ANALIZ YOLUNDA KULLANILMIYOR (yukaridaki
    gerekce); olcum aracinda ve testlerde duruyor.
    """
    g = goruntu_np.mean(axis=2).astype(np.float64)
    r = referans_np.mean(axis=2).astype(np.float64)
    if g.shape != r.shape:
        raise ValueError("hizalama icin goruntuler ayni boyutta olmali")
    gecerli = g > 12
    if gecerli.mean() < 0.2:
        raise ValueError("gecerli alan cok kucuk")
    g = np.where(gecerli, g, g[gecerli].mean())

    def pencere(a):
        a = a - a.mean()
        return a * (np.hanning(a.shape[0])[:, None] * np.hanning(a.shape[1])[None, :])

    F = np.fft.fft2(pencere(g)) * np.conj(np.fft.fft2(pencere(r)))
    F /= np.abs(F) + 1e-9
    kor = np.fft.ifft2(F).real
    yy, xx = np.unravel_index(np.argmax(kor), kor.shape)
    H, W = kor.shape
    dy = yy - H if yy > H // 2 else yy
    dx = xx - W if xx > W // 2 else xx
    return int(dx), int(dy), float(kor.max() / (np.abs(kor).mean() + 1e-12))


def osm_taramasi(goruntu_np, yol_maskesi, yaricap_px: int = 24) -> dict:
    """Goruntuyu OSM yol maskesine gore tarar; en iyi otelemeyi dondurur.

    Olcut: maske altindaki ORTALAMA KIRMIZILIK (R - B). Antakya'da catilar
    kirmizi, yol ve moloz gri-bej; maske gercek yola oturdugunda bu deger
    en dusuk olur. Olcut EGIK bakisli goruntuda (Maxar) yanildigi icin
    yalnizca DIK bakisli ortofotolarda kullanilir.
    """
    a = goruntu_np.astype(np.float32)
    kirmizilik = a[:, :, 0] - a[:, :, 2]
    ucus = a.mean(axis=2) > 12          # ucus izi disindaki siyah alan
    yol = yol_maskesi > 0
    en_az_piksel = max(5000, int(yol.sum() * 0.1))

    sonuc = []
    for dy in range(-yaricap_px, yaricap_px + 1):
        for dx in range(-yaricap_px, yaricap_px + 1):
            m = np.roll(np.roll(yol, dy, 0), dx, 1) & ucus
            if int(m.sum()) < en_az_piksel:
                continue
            sonuc.append((float(kirmizilik[m].mean()), dx, dy))
    if not sonuc:
        raise ValueError("tarama icin yeterli yol pikseli yok")
    en_iyi, en_kotu = min(sonuc), max(sonuc)
    sifir = next((s for s in sonuc if s[1] == 0 and s[2] == 0), en_iyi)
    # maskeyi (dx,dy) kaydirmak = goruntuyu (-dx,-dy) kaydirmak
    return {
        "goruntuDx": -en_iyi[1],
        "goruntuDy": -en_iyi[2],
        "enIyi": en_iyi[0],
        "sifirKaymada": sifir[0],
        "enKotu": en_kotu[0],
    }
