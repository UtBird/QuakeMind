"""Islem kaydi ucu (J-165). Yalniz koordinator ve yonetici okur; yazan uc yok."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

import kimlik
from depo import aktif_depo
from islem_kaydi import TURLER

yonlendirici = APIRouter(prefix="/api", tags=["islem-kaydi"])


@yonlendirici.get("/islem-kayitlari")
def islem_kayitlari(
    tur: Optional[list[str]] = Query(None),
    hedefTur: Optional[str] = None,
    hedefId: Optional[str] = None,
    yapanId: Optional[str] = None,
    once: Optional[int] = None,
    sinir: int = 100,
    _kul: dict = Depends(kimlik.rol_gerektir("koordinator", "yonetici")),
):
    """Yeniden eskiye islem kaydi. `once`: bir onceki sayfanin en eski kimligi."""
    import islem_kaydi

    # Kaydin kendisini kimin okudugu da yazilir (10 dk'da bir).
    islem_kaydi.goruntuleme(_kul, "islem_kaydi")
    bilinmeyen = [t for t in (tur or []) if t not in TURLER]
    if bilinmeyen:
        raise HTTPException(status_code=422, detail=f"Bilinmeyen tur: {', '.join(bilinmeyen)}")
    sinir = max(1, min(sinir, 500))
    kayitlar = aktif_depo().islem_kayitlari(
        turler=tur, hedef_tur=hedefTur, hedef_id=hedefId, yapan_id=yapanId, once_id=once, sinir=sinir
    )
    return {
        "kayitlar": [
            {
                "id": k["id"],
                "zaman": int(k["zaman"] * 1000),
                "yapanId": k["yapan_id"],
                "yapanAd": k["yapan_ad"],
                "yapanRol": k["yapan_rol"],
                "tur": k["tur"],
                "hedefTur": k["hedef_tur"],
                "hedefId": k["hedef_id"],
                "ozet": k["ozet"],
                "ayrinti": k["ayrinti"],
                "hash": k.get("hash"),
                "oncekiHash": k.get("onceki_hash"),
            }
            for k in kayitlar
        ],
        # Sayfa doluysa daha eskisi olabilir.
        "devami": len(kayitlar) == sinir,
    }


@yonlendirici.get("/islem-kayitlari/dogrula")
def islem_zincirini_dogrula(
    tam: bool = False,
    kul: dict = Depends(kimlik.rol_gerektir("koordinator", "yonetici")),
):
    """Hash zincirini dogrular (J-166).

    Varsayilan artimli: son sağlam denetimden sonra eklenenler (ve denetim
    noktasinin kendisi). `tam=true` bastan sona; 100 bin kayitta ~3 sn olculdu,
    bu yuzden yalniz istenince. Her sonuc silinmeyen denetim tablosuna yazilir.
    Bozuksa ilk bozuk kaydin numarasi ve nedeni doner."""
    import time

    depo = aktif_depo()
    nokta = None if tam else depo.son_saglam_denetim()
    t0 = time.perf_counter()
    sonuc = depo.islem_zinciri_dogrula((nokta["son_id"], nokta["son_hash"]) if nokta else None)
    sure_ms = round((time.perf_counter() - t0) * 1000)
    kapsam = "artimli" if nokta else "tam"
    depo.zincir_denetimi_ekle(kul, kapsam, sonuc, sure_ms)
    return {
        **sonuc,
        "kapsam": kapsam,
        "sureMs": sure_ms,
        "baslangicId": nokta["son_id"] if nokta else None,
        "oncekiDenetim": (
            {"zaman": int(nokta["zaman"] * 1000), "yapanAd": nokta["yapan_ad"], "kapsam": nokta["kapsam"]}
            if nokta else None
        ),
    }


@yonlendirici.get("/islem-kayitlari/son-denetim")
def son_zincir_denetimi(_kul: dict = Depends(kimlik.rol_gerektir("koordinator", "yonetici"))):
    """Son dogrulamanin sonucu; dogrulama yapmaz (ekran acilisinda ucuz)."""
    d = aktif_depo().son_denetim()
    if d is None:
        return None
    return {
        "zaman": int(d["zaman"] * 1000),
        "yapanAd": d["yapan_ad"],
        "kapsam": d["kapsam"],
        "saglam": bool(d["saglam"]),
        "dogrulanan": d["dogrulanan"],
        "sonId": d["son_id"],
        "sonHash": d["son_hash"],
        "bozukId": d["bozuk_id"],
        "neden": d["neden"],
        "sureMs": d["sure_ms"],
    }
