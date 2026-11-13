"""Kalici depo katmani.

TASIMA_PLANI.md Faz 1. Uygulama bu arayuze baglanir; surucu asagidaki sirayla
secilir:

  1. PostGIS  -- `QUAKEMIND_DB` (ya da POSTGIS_URL) verilmis ve baglanti kuruluyorsa
  2. SQLite   -- yerel dosya (kurulum gerektirmez)

Bugun makinede PostgreSQL servisi yok; bu yuzden yerelde SQLite surucusu calisir
ve sunucu yeniden baslasa bile kullanicilar, SOS cagrilari ve ekipler kaybolmaz.
Uretimde ayni arayuzun PostGIS surucusu kullanilir (bkz. `postgis_surucu.py`,
henuz yazilmadi -- MIMARI.md 3'teki tablolar oraya baglanacak).
"""

from __future__ import annotations

import os
from pathlib import Path

from .sqlite_surucu import SqliteDepo

__all__ = ["SqliteDepo", "depo_ac", "aktif_depo"]

_depo: "SqliteDepo | None" = None


def depo_ac(yol: "str | Path | None" = None) -> SqliteDepo:
    """Depoyu acar (yoksa olusturur). Uygulama acilisinda bir kez cagrilir."""
    global _depo
    if _depo is not None:
        return _depo

    if yol is None:
        varsayilan = Path(__file__).resolve().parent.parent / "veri" / "quakemind.sqlite3"
        yol = os.environ.get("QUAKEMIND_SQLITE", str(varsayilan))

    Path(yol).parent.mkdir(parents=True, exist_ok=True)
    _depo = SqliteDepo(str(yol))
    return _depo


def aktif_depo() -> SqliteDepo:
    """Acilmis depoyu dondurur; acilmamissa acar."""
    return _depo or depo_ac()
