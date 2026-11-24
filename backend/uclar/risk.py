"""Deprem riski uclari (CatBoost; model dosyadan yuklenir, istek yolunda egitim yok).

J-173: hesap `risk_hizmeti.py`'de, is parcacigi guvenli ve onbellekli. Eskiden
`quakemind/tool/risk_bridge.build_payload` her istekte sureecin calisma klasorunu
ve sys.path'i degistiriyor, motorun ortak `last_lat` alanindan okuyordu:
eszamanli isteklerde yanit baska ilin koordinatini tasiyordu (40'ta 35, olculdu).
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

import cekirdek as ck
import kimlik
import risk_hizmeti

yonlendirici = APIRouter()
log = logging.getLogger("quakemind.risk")

#: Dis servise (Kandilli, USGS) istek atip deprem katalogunu yeniden yazan
#: islemler yalniz koordinasyona acik (J-152).
_KOORDINASYON = ("koordinator", "yonetici")

# Depoda, imajin icinde (J-188). Eskiden `veri/` altindaydi: o dizin .gitignore'da
# ve canlida kalici birimle ortulu oldugu icin sunucuda dosya yoktu, 81 il
# siralamasi bos donuyordu. OSM'den uretilir (araclar_il_merkezleri_uret.py);
# kaynak ve ODbL atfi dosyanin icinde.
IL_MERKEZLERI = Path(__file__).resolve().parents[1] / "apps" / "earthquake_risk" / "data" / "il_merkezleri.json"


class RiskIstegi(BaseModel):
    city: str = Field(..., min_length=1, max_length=80)
    manualLatitude: Optional[float] = Field(None, ge=34.0, le=43.5)
    manualLongitude: Optional[float] = Field(None, ge=24.5, le=46.0)
    refreshData: bool = False


@yonlendirici.post("/api/risk/predict")
def predict_risk(req: RiskIstegi, kul: dict = Depends(kimlik.kullanici)):
    """Risk skoru: giris yapmis her rol (J-152). Koordinat verilmezse il adi il
    merkezleri listesinden aranir; dis servise (Nominatim) GIDILMEZ (J-173).
    Turkiye kutusu disindaki koordinat 422 (model Turkiye katalogu ile egitildi)."""
    if req.refreshData and kul["rol"] in _KOORDINASYON:
        _tazele()
    if req.manualLatitude is not None and req.manualLongitude is not None:
        lat, lon = req.manualLatitude, req.manualLongitude
    else:
        il = risk_hizmeti.il_merkezi(req.city)
        if il is None:
            raise HTTPException(status_code=422, detail="Konum yok: koordinat ver ya da 81 ilden birini seç.")
        lat, lon = il["lat"], il["lon"]
    try:
        return risk_hizmeti.hesapla(req.city.strip(), float(lat), float(lon))
    except risk_hizmeti.RiskHazirDegil as e:
        log.warning("risk modeli hazir degil: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Risk modeli hazır değil. Sunucuda `python araclar_risk_egit.py` çalıştırılmalı.",
        ) from e
    except Exception as e:  # ayrinti sunucu kaydinda; istemciye ham hata metni gitmez
        log.exception("risk hesabi basarisiz (%s)", req.city)
        raise HTTPException(status_code=500, detail="Risk hesaplanamadı.") from e


@yonlendirici.get("/api/risk/iller")
def risk_illeri(_kul: dict = Depends(kimlik.kullanici)):
    """81 ilin merkez koordinati ve kaynak kunyesi (araclar_il_merkezleri_uret.py).

    Risk istegi koordinatla gider; sunucu konumu dis servisten aramaz."""
    if not IL_MERKEZLERI.exists():
        return {"iller": [], "kaynak": None,
                "not": "Il merkezleri uretilmedi: python araclar_il_merkezleri_uret.py"}
    return json.loads(IL_MERKEZLERI.read_text(encoding="utf-8"))


@yonlendirici.get("/api/risk/siralama")
def risk_siralamasi(_kul: dict = Depends(kimlik.kullanici)):
    """81 il merkezi, risk skoruna gore sirali (J-173). Panelin sorusu "hangi
    bolgede risk daha yuksek?" idi ama ekran tek tek il soruyordu. Ilk istek
    81 hesap (~2 sn), sonrakiler onbellekten."""
    if not IL_MERKEZLERI.exists():
        return {"iller": [], "not": "Il merkezleri uretilmedi: python araclar_il_merkezleri_uret.py"}
    iller = json.loads(IL_MERKEZLERI.read_text(encoding="utf-8"))["iller"]
    try:
        satirlar = []
        for il in iller:
            r = risk_hizmeti.hesapla(il["il"], float(il["lat"]), float(il["lon"]))
            m = r["metrics"]
            satirlar.append({
                "il": il["il"], "lat": il["lat"], "lon": il["lon"],
                "skor": r["riskScore"], "seviye": r["riskLevel"],
                "kisa": round(m["shortRisk"], 4), "uzun": round(m["longHazard"], 4),
                "fay": round(m["faultScore"], 4), "fayKm": round(m["faultDistanceKm"], 1),
                "kisaVadeKaynagi": r["dayanak"]["kisaVadeKaynagi"],
            })
    except risk_hizmeti.RiskHazirDegil as e:
        raise HTTPException(status_code=503, detail="Risk modeli hazır değil.") from e
    satirlar.sort(key=lambda x: -x["skor"])
    return {"iller": satirlar, "agirlik": risk_hizmeti.AGIRLIK}


@yonlendirici.get("/api/risk/ana-soklar")
def risk_ana_soklar(_kul: dict = Depends(kimlik.kullanici)):
    """Ulke geneli M>=6 ana soklar (J-191): risk ekraninin il secilmemis gorunumu."""
    try:
        return risk_hizmeti.ulke_ana_soklari()
    except risk_hizmeti.RiskHazirDegil as e:
        raise HTTPException(status_code=503, detail="Deprem kataloğu yüklenemedi.") from e


@yonlendirici.get("/api/risk/fault_lines")
def risk_fault_lines(_kul: dict = Depends(kimlik.kullanici)):
    """Eski web ve mobil icin elle yazilmis yaklasik fay cizgileri. J-173: giris
    ister (CLAUDE.md 5; eskiden oturumsuzdu). Konsol GEM faylarini
    /api/katman/faylar ile alir."""
    lines = ck._get_turkey_fault_lines()
    return {"faultLines": lines, "count": len(lines)}


@yonlendirici.get("/api/risk/all_quakes")
def risk_all_quakes(
    minMagnitude: float = Query(0.0, ge=0, le=10),
    startDate: Optional[str] = Query(None, max_length=32),
    endDate: Optional[str] = Query(None, max_length=32),
    limit: int = Query(500, ge=1, le=2000),
    sortBy: Literal["time", "magnitude"] = "time",
    _kul: dict = Depends(kimlik.kullanici),
):
    """Ulusal katalog (~20 bin kayit, 1933'ten), suzulmus ve sayfali. J-173: giris
    ister (eskiden oturumsuzdu); satir satir dongu yerine toplu donusum."""
    import pandas as pd

    motor = ck.risk_engine
    try:
        risk_hizmeti._hazirla(motor)
    except risk_hizmeti.RiskHazirDegil as e:
        raise HTTPException(status_code=503, detail="Deprem kataloğu yüklenemedi.") from e
    df = motor.df_full
    try:
        maske = df["mag"] >= minMagnitude
        for deger, karsilastir in ((startDate, "ge"), (endDate, "le")):
            if deger:
                ts = pd.Timestamp(deger)
                ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts
                maske &= getattr(df["time"], karsilastir)(ts)
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=422, detail="Tarih biçimi geçersiz (YYYY-AA-GG).") from e
    secim = df[maske]
    toplam = int(len(secim))
    secim = (secim.sort_values(["mag", "time"], ascending=[False, False]) if sortBy == "magnitude"
             else secim.sort_values("time", ascending=False)).head(limit)
    cikti = pd.DataFrame({
        "time": secim["time"].astype(str),
        "place": secim["place"].fillna("Bilinmeyen konum") if "place" in secim else "Bilinmeyen konum",
        "magnitude": secim["mag"].astype(float),
        "depth": secim["depth"].astype(float),
        "latitude": secim["latitude"].astype(float),
        "longitude": secim["longitude"].astype(float),
        "status": secim["status"].fillna("reviewed") if "status" in secim else "reviewed",
    })
    # Kaynak (PR #7, mobil): katalogda yazmiyorsa USGS bosluk dolgusu ya da ulusal katalog.
    varsayilan = (cikti["status"] == "usgs_gapfill").map({True: "USGS", False: "Ulusal deprem kataloğu"})
    cikti["source"] = secim["source"].where(secim["source"].notna(), varsayilan) if "source" in secim else varsayilan
    kayitlar = json.loads(cikti.to_json(orient="records", force_ascii=False))  # NaN -> null
    return {
        "quakes": kayitlar,
        "totalMatched": toplam,
        "returned": len(kayitlar),
        "datasetStart": str(df["time"].min()),
        "datasetEnd": str(df["time"].max()),
        "datasetTotal": int(len(df)),
    }


def _tazele() -> str:
    try:
        return risk_hizmeti.veriyi_tazele()
    except Exception as e:
        log.exception("risk verisi tazelenemedi")
        raise HTTPException(status_code=502, detail="Deprem verisi tazelenemedi (Kandilli/USGS).") from e


@yonlendirici.post("/api/risk/refresh_live_data")
def risk_refresh_live_data(_kul: dict = Depends(kimlik.rol_gerektir(*_KOORDINASYON))):
    """Kandilli (+ USGS) verisini ceker; yeni motor hazirlanip tek atamayla
    devreye girer (koşan istekler eski veriyle biter)."""
    return {"message": _tazele()}


def _onyukle():
    """Acilista arka planda: ilk risk istegi cerceve ve model yuklemesini
    (~1,5 sn, olculdu) beklemesin. Acilisi geciktirmez."""
    try:
        if ck.risk_engine is not None:
            risk_hizmeti._hazirla(ck.risk_engine)
            risk_hizmeti._diziler(ck.risk_engine)
    except Exception as e:
        print(f"risk on yukleme: {e}", flush=True)


if getattr(ck, "_IS_APP_PROCESS", False):
    threading.Thread(target=_onyukle, name="risk-onyukleme", daemon=True).start()
