"""Islem kaydi (J-165): kim, ne zaman, ne yapti.

Uclar islemi yaptiktan SONRA `kaydet` cagirir. Kayit yazilamazsa islem geri
alinmaz (analiz sonucu kullaniciya yine doner); hata sunucu gunlugune yazilir.
Bu bilincli bir secim: kayit defteri afet aninda asil isi durdurmamali.

Kayit silinmez ve degistirilmez; depo tetikleyicileri bunu zorlar
(`depo/sqlite_surucu.py`, `islem_kayitlari`). Fotograf saklanmaz, yalniz
sonucun ozeti (model, tespit sayisi, en yuksek guven, sure).
"""
from __future__ import annotations

import threading
import time
from typing import Any, Optional

import canli_yayin
from depo import aktif_depo

# Konsolun da bildigi turler. Yeni tur eklemek = buraya bir satir + konsolda ad.
TURLER = (
    "kamera_analizi",
    "metin_analizi",
    "hasar_analizi_basladi",
    "hasar_analizi_bitti",
    "hasar_analizi_hata",
    "tatbikat_basladi",
    "tatbikat_bitti",
    "tatbikat_hata",
    "tatbikat_kapatildi",
    "sevk",
    "gorev_durumu",
    "sos_kapatildi",
    "ihbar_durumu",
    "ekip_eklendi",
    "ekip_degisti",
    "ekip_uyeleri",
    "bildirim_yayinlandi",
    "bildirim_geri_cekildi",
    # Yol kapanmasi durumu (kapali / acildi / yanlis alarm) (J-190).
    "kapanma_durumu",
    # J-166: giris gecmisi, konum paylasimi, kisisel veri goruntuleme.
    "giris_basarili",
    "giris_basarisiz",
    "cikis",
    "kayit_oldu",
    "konum_paylasimi_basladi",
    "goruntuleme",
)


def kaydet(
    yapan: Optional[dict],
    tur: str,
    ozet: str,
    *,
    hedef_tur: Optional[str] = None,
    hedef_id: Optional[str] = None,
    ayrinti: Optional[dict[str, Any]] = None,
) -> Optional[int]:
    """Kaydi yazar, acik konsollara "islem-kaydi" duyurur. Hata yutulur."""
    if tur not in TURLER:
        raise ValueError(f"Bilinmeyen islem turu: {tur}")
    try:
        kimlik_no = aktif_depo().islem_kaydi_ekle(
            yapan, tur, ozet, hedef_tur=hedef_tur, hedef_id=hedef_id, ayrinti=ayrinti
        )
    except Exception as e:  # noqa: BLE001 -- kayit asil isi durdurmaz
        print(f"islem kaydi yazilamadi ({tur}): {e}", flush=True)
        return None
    try:
        # Yalniz tur gider: ayrinti ve kisi akisa konmaz (afetzede de abonedir).
        canli_yayin.yayinla("islem-kaydi", tur=tur)
    except Exception as e:  # noqa: BLE001
        print(f"islem kaydi duyurulamadi: {e}", flush=True)
    return kimlik_no


def yuzde(x: Optional[float]) -> str:
    return "—" if x is None else f"%{round(x)}"


def istemci_bilgisi(istek) -> dict:
    """Giris kaydi icin: baglanan adres ve tarayici (J-166).

    `ip` dogrudan baglanan adrestir. Vekil (Nginx) arkasinda bu vekilin
    adresidir; vekilin ekledigi `X-Forwarded-For` ayrica `yonlendirilen` diye
    yazilir. Istemci bu basligi kendisi de uydurabilir: dogrulanmamis bilgidir.
    """
    if istek is None:
        return {}
    bilgi = {
        "ip": istek.client.host if istek.client else None,
        "tarayici": (istek.headers.get("user-agent") or "")[:200] or None,
    }
    ileten = istek.headers.get("x-forwarded-for")
    if ileten:
        bilgi["yonlendirilen"] = ileten[:200]
    return bilgi


# Kisisel veri goruntuleme (J-166). Konsol listeleri canli akisla sik tazelenir;
# her tazeleme yazilsaydi kayit bir saatte binlerce satir olurdu. Ayni kisi ayni
# seyi GORUNTULEME_ARALIGI_SN icinde bir kez yazilir. Sayac surec icidir (tek
# uvicorn worker, CLAUDE.md 4); yeniden baslayinca ilk bakis yine yazilir.
GORUNTULEME_ARALIGI_SN = 10 * 60
_son_goruntuleme: dict[tuple, float] = {}
_goruntuleme_kilidi = threading.Lock()
KAYIT_TUTULAN_ROLLER = ("saha", "koordinator", "yonetici")

KAYNAK_ADI = {
    "sos_listesi": "SOS listesi",
    "ihbar_listesi": "İhbar listesi",
    "ihbar_fotografi": "İhbar fotoğrafı",
    "kullanici_listesi": "Kullanıcı listesi",
    "hesap_defteri": "Hesap defteri",
    "islem_kaydi": "İşlem kaydı",
    "konum_gecmisi": "Ekip konum geçmişi",
}


def goruntuleme(
    kul: dict,
    kaynak: str,
    *,
    hedef_tur: Optional[str] = None,
    hedef_id: Optional[str] = None,
    ayrinti: Optional[dict[str, Any]] = None,
) -> Optional[int]:
    """Konsol rolunden birinin kisisel veri iceren bir seyi actigini yazar.
    Afetzedenin kendi kaydina bakmasi yazilmaz."""
    if kaynak not in KAYNAK_ADI:
        raise ValueError(f"Bilinmeyen goruntuleme kaynagi: {kaynak}")
    if kul.get("rol") not in KAYIT_TUTULAN_ROLLER:
        return None
    anahtar = (kul.get("id"), kaynak, hedef_id)
    simdi = time.time()
    with _goruntuleme_kilidi:
        if simdi - _son_goruntuleme.get(anahtar, 0.0) < GORUNTULEME_ARALIGI_SN:
            return None
        _son_goruntuleme[anahtar] = simdi
        # Sozluk sinirsiz buyumesin: suresi gecenler atilir.
        if len(_son_goruntuleme) > 5000:
            for a, z in list(_son_goruntuleme.items()):
                if simdi - z >= GORUNTULEME_ARALIGI_SN:
                    del _son_goruntuleme[a]
    ad = KAYNAK_ADI[kaynak]
    return kaydet(
        kul,
        "goruntuleme",
        f"{ad} görüntülendi" + (f" ({hedef_id})" if hedef_id else ""),
        hedef_tur=hedef_tur,
        hedef_id=hedef_id,
        ayrinti={"kaynak": kaynak, **(ayrinti or {})},
    )
