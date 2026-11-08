"""Tek canli akis (SSE) icin surec ici olay yolu.

MIMARI.md 6: istemci yoklama yapmaz; sunucu YALNIZCA degisiklik oldugunda
mesaj gonderir. Mesaj tipleri: yeni-sos, is-durumu, yeni-analiz, isi-surumu,
ekip-konumu, bildirim, ihbar (afetzede ihbari, J-51), gorev (sevk gorevi, J-54).

Yayinlayanlar farkli yerlerden gelir:
  - ilerleme tuketici is parcacigi (_drain_road_damage_progress)
  - ProcessPoolExecutor'un bitis geri cagrimi (_on_road_damage_job_done)
  - normal istek isleyicileri (SOS cagrisi acildiginda vb.)
Bu yuzden yayinlama is parcacigi guvenlidir: olay dongusu disindaki cagrilar
`call_soon_threadsafe` ile donguye tasinir.

ISTEK SINIRI: bu yol TEK surec icindedir. uvicorn birden cok worker ile
kosarsa her worker yalnizca kendi olaylarini gorur. Cok worker'a gecilince
`yayinla` govdesi Postgres LISTEN/NOTIFY'a baglanacak (MIMARI 6); abonelik ve
SSE ucu ayni kalir.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Optional

# Abone kuyruklari. Her SSE baglantisi bir kuyruk alir.
_aboneler: "set[asyncio.Queue]" = set()
_dongu: Optional[asyncio.AbstractEventLoop] = None

# Yavas bir istemci butun sunucuyu yavaslatmasin: kuyruk dolarsa en eski
# mesaj dusurulur ve baglanti canli kalir.
KUYRUK_SINIRI = 256

MESAJ_TIPLERI = (
    "yeni-sos", "is-durumu", "yeni-analiz", "isi-surumu", "ekip-konumu", "bildirim", "ihbar",
    "gorev",
    # Simulasyon modu: bir katman cizilmeye hazir (SIMULASYON_SOZLESMESI.md 3).
    "simulasyon-katman",
)


def dongu_ayarla(dongu: asyncio.AbstractEventLoop) -> None:
    """Uygulama acilisinda bir kez cagrilir."""
    global _dongu
    _dongu = dongu


def abone_ol() -> "asyncio.Queue":
    kuyruk: asyncio.Queue = asyncio.Queue(maxsize=KUYRUK_SINIRI)
    _aboneler.add(kuyruk)
    return kuyruk


def abonelik_bitir(kuyruk: "asyncio.Queue") -> None:
    _aboneler.discard(kuyruk)


def abone_sayisi() -> int:
    return len(_aboneler)


def _dagit(mesaj: dict) -> None:
    """Olay dongusu icinde calisir."""
    for kuyruk in list(_aboneler):
        try:
            kuyruk.put_nowait(mesaj)
        except asyncio.QueueFull:
            try:
                kuyruk.get_nowait()  # en eskiyi dusur
                kuyruk.put_nowait(mesaj)
            except Exception:
                pass


def yayinla(tip: str, **veri: Any) -> None:
    """Bir olayi butun abonelere gonderir. Her yerden (is parcacigi dahil)
    cagrilabilir; abone yoksa maliyeti yok denecek kadar azdir."""
    if tip not in MESAJ_TIPLERI:
        raise ValueError(f"Bilinmeyen mesaj tipi: {tip}")
    if "tip" in veri:
        # Mesajin kendi tipini govdedeki bir alan ezmesin.
        raise ValueError("Olay govdesinde 'tip' alani kullanilamaz; baska bir ad secin.")
    if not _aboneler or _dongu is None:
        return
    mesaj = {"tip": tip, "zaman": time.time(), **veri}
    try:
        if _dongu.is_running():
            _dongu.call_soon_threadsafe(_dagit, mesaj)
        else:
            _dagit(mesaj)
    except RuntimeError:
        # Kapanis sirasinda dongu gitmis olabilir; olay dusurulur.
        pass


def sse_bicimle(mesaj: dict) -> str:
    """Bir olayi SSE kare bicimine cevirir.

    `event:` alani da yazilir; istemci ister tek `onmessage` ile ister tipe
    gore dinleyiciyle okuyabilir.
    """
    govde = json.dumps(mesaj, ensure_ascii=False, default=str)
    return f"event: {mesaj['tip']}\ndata: {govde}\n\n"
