"""Zaman seridi verisi (J-167 F-4): konsolun alt seridindeki olay yogunlugu.

Serit son 30 gunu gosterir; her dilimde gelen SOS ve ihbar sayisi. Sayim SQL'de
yapilir (CLAUDE.md 10). Konsol bu ucu yoklamaz: yeni SOS ya da ihbar canli
akista gelince sorgu tazelenir (kural 4).
"""
from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

import kimlik
from depo import aktif_depo

yonlendirici = APIRouter()

EN_COK_DILIM = 2000


@yonlendirici.get("/api/olay-yogunlugu")
def olay_yogunlugu(
    baslangic: float = Query(..., description="saniye (epoch)"),
    bitis: Optional[float] = Query(None, description="saniye; yoksa simdi"),
    dilimSn: float = Query(3600, ge=60, le=86400),
    _kul: dict = Depends(kimlik.rol_gerektir("koordinator", "yonetici", "saha")),
):
    son = bitis if bitis is not None else time.time()
    if son <= baslangic:
        raise HTTPException(status_code=422, detail="bitis baslangictan sonra olmali")
    if (son - baslangic) / dilimSn > EN_COK_DILIM:
        raise HTTPException(status_code=422, detail=f"en cok {EN_COK_DILIM} dilim")
    sayilar = aktif_depo().olay_yogunlugu(baslangic, son, dilimSn)
    return {"baslangic": baslangic, "bitis": son, "dilimSn": dilimSn, **sayilar}
