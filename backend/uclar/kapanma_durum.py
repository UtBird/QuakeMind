"""Yol kapanmasının durumu: kapalı · açıldı · yanlış alarm (J-190).

Uydu analizi bir yolu kapalı bulur; bu modelin tahminidir. Saha ekibi ya da
koordinasyon yolun açıldığını ya da hiç kapanmadığını (yanlış alarm) gördüğünde
burada işaretler. Rota, harita ve afetzede ekranı yalnız "kapalı" durumdakine
bakar; değişiklik canlı akışla bütün ekranlara gider, işlem kaydına yazılır.

Kayıt silinmez: "açıldı" ve "yanlış" hem geri alınabilsin hem de modelin
yanlış alarm oranı ölçülebilsin diye durum olarak tutulur.
"""
from __future__ import annotations

import re
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

import canli_yayin
import islem_kaydi
import kimlik
from depo import aktif_depo

yonlendirici = APIRouter()

DURUM_ADI = {"kapali": "kapalı", "acildi": "açıldı", "yanlis": "yanlış alarm"}
KAPANMA_KIMLIGI = re.compile(r"kap-[0-9a-f]{6,32}")


class DurumIstegi(BaseModel):
    durum: Literal["kapali", "acildi", "yanlis"]
    not_: Optional[str] = Field(default=None, alias="not", max_length=300)


def _yayinla() -> None:
    # Haritadaki kapanma katmanı, rota motoru (imza değişir) ve afetzede çevre ekranı tazelenir.
    canli_yayin.yayinla("kapanma")


@yonlendirici.patch("/api/kapanmalar/{kapanma_id}")
def kapanma_durumu(
    kapanma_id: str,
    istek: DurumIstegi,
    kul: dict = Depends(kimlik.rol_gerektir("saha", "koordinator", "yonetici")),
):
    """Tek bir kapalı yol parçasının durumu. Aynı parça birden çok analizde
    kaydedildiyse hepsi birlikte değişir."""
    if not KAPANMA_KIMLIGI.fullmatch(kapanma_id):
        raise HTTPException(status_code=422, detail="Geçersiz kapanma kimliği.")
    depo = aktif_depo()
    k = depo.kapanma_bul(kapanma_id)
    if k is None:
        raise HTTPException(status_code=404, detail="Kapanma bulunamadı.")
    notu = (istek.not_ or "").strip() or None
    n = depo.kapanma_durum_yaz(kapanma_id, istek.durum, kul["id"], notu)
    islem_kaydi.kaydet(
        kul, "kapanma_durumu",
        f"Yol kapanması {DURUM_ADI.get(k.get('durum') or 'kapali')} → {DURUM_ADI[istek.durum]}",
        hedef_tur="kapanma", hedef_id=kapanma_id,
        ayrinti={"once": k.get("durum") or "kapali", "sonra": istek.durum, "kayit": n,
                 "analizId": k.get("analiz_id"), "not": notu},
    )
    _yayinla()
    return {"id": kapanma_id, "durum": istek.durum, "degisenKayit": n}


@yonlendirici.post("/api/kapanmalar/analiz/{analiz_id}/durum")
def analiz_kapanmalari_durumu(
    analiz_id: str,
    istek: DurumIstegi,
    kul: dict = Depends(kimlik.rol_gerektir("koordinator", "yonetici")),
):
    """Bir analizin bütün kapanmaları birden (ör. "bu analiz baştan yanlış:
    deprem öncesi görüntüyle yapılmış"). Yalnız koordinasyon."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{6,64}", analiz_id):
        raise HTTPException(status_code=422, detail="Geçersiz analiz kimliği.")
    notu = (istek.not_ or "").strip() or None
    n = aktif_depo().kapanma_analiz_durum_yaz(analiz_id, istek.durum, kul["id"], notu)
    if n == 0:
        raise HTTPException(status_code=404, detail="Bu analize ait kapanma yok.")
    islem_kaydi.kaydet(
        kul, "kapanma_durumu",
        f"Analizin {n} yol kapanması → {DURUM_ADI[istek.durum]}",
        hedef_tur="analiz", hedef_id=analiz_id,
        ayrinti={"sonra": istek.durum, "kayit": n, "not": notu},
    )
    _yayinla()
    return {"analizId": analiz_id, "durum": istek.durum, "degisenKayit": n}
