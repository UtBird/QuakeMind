"""Metin modelinin işçi süreci (J-170, CLAUDE.md §3: model API sürecinde durmaz).

Tek işçi; model açılışta yüklenir ve ısıtılır, sonra bellekte kalır. API süreci
metni gönderip sonucu bekler. Çıkarım kısa (ölçüldü: ortanca ~50 ms) olduğu
için 202 + SSE değil, isteğin içinde beklenir; uzun işler (hasar analizi,
tatbikat) 202 + SSE düzeninde kalır.

Açılış ısınmayı BEKLEMEZ: ilk istek ısınma sürerken gelirse kuyrukta bekler.
"""
from __future__ import annotations

import multiprocessing
import os
from concurrent.futures import Future, ProcessPoolExecutor
from typing import Optional

_havuz: Optional[ProcessPoolExecutor] = None
_isinma: Optional[Future] = None
ISTEK_ZAMAN_ASIMI_SN = 60


class MetinModeliYok(RuntimeError):
    pass


def _isci_baslat():
    # İşçi CPU'yu tek başına tüketmesin (J-66'daki gibi): API ve hasar işçisine yer kalsın.
    import torch

    torch.set_num_threads(int(os.environ.get("QUAKEMIND_METIN_IS_PARCACIGI", "2")))
    from metin_analizi import yerel_analizci

    yerel_analizci()


def _isit():
    from metin_analizi import yerel_analizci

    a = yerel_analizci()
    a.isit()
    return {"yuklemeSn": a.yukleme_sn, "model": a.model_adi}


def _coz(metin: str) -> dict:
    from metin_analizi import yerel_analizci

    return yerel_analizci().coz(metin)


def baslat() -> None:
    global _havuz, _isinma
    if _havuz is not None:
        return
    _havuz = ProcessPoolExecutor(max_workers=1, mp_context=multiprocessing.get_context("spawn"),
                                 initializer=_isci_baslat)
    _isinma = _havuz.submit(_isit)

    def bitti(f: Future):
        try:
            r = f.result()
            print(f"Metin modeli hazir ({r['model']}, yukleme {r['yuklemeSn']} sn).", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"Metin modeli yuklenemedi: {e}", flush=True)

    _isinma.add_done_callback(bitti)


def durdur() -> None:
    global _havuz
    if _havuz is not None:
        _havuz.shutdown(wait=False, cancel_futures=True)
        _havuz = None


def hazir_mi() -> Optional[bool]:
    """None: işçi kurulmadı; False: ısınıyor ya da yüklenemedi; True: hazır."""
    if _havuz is None or _isinma is None:
        return None
    return _isinma.done() and _isinma.exception() is None


def coz(metin: str) -> dict:
    if _havuz is None:
        raise MetinModeliYok("Metin modeli işçisi kurulmadı.")
    try:
        return _havuz.submit(_coz, metin).result(timeout=ISTEK_ZAMAN_ASIMI_SN)
    except Exception as e:  # noqa: BLE001
        raise MetinModeliYok(f"Metin modeli çalışmadı: {e}") from e
