"""Deprem riski (J-173): eszamanli istekte dogru il, yetki, sinir, siralama."""
import os
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

MODEL = BASE_DIR / "apps" / "earthquake_risk" / "models" / "risk_catboost.cbm"
pytestmark = pytest.mark.skipif(not MODEL.exists(), reason="risk modeli bu makinede egitilmemis")


@pytest.fixture(scope="module")
def ortam():
    os.environ["QUAKEMIND_SQLITE"] = str(Path(tempfile.mkdtemp(prefix="qm_risk_")) / "t.sqlite3")
    import importlib

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import cekirdek as ck
    import depo as depo_paketi
    import kimlik

    if ck.risk_engine is None:
        with ck.temporary_sys_path(ck.RISK_ROOT), ck.temporary_cwd(ck.RISK_ROOT):
            mod = importlib.import_module("risk_engine")
            ck.risk_engine = mod.EarthquakeRiskEngine(csv_path=str(ck.RISK_ROOT / "data" / "query.csv"))
    depo_paketi._depo = None
    d = depo_paketi.depo_ac()
    k = kimlik.kullanici_kaydet("risk@test.local", "risk", "test-sifresi-123")
    d.rol_ata(k["id"], "koordinator")
    jeton = {"Authorization": f"Bearer {kimlik.erisim_jetonu_uret(d.kullanici_id(k['id']))}"}
    from uclar import risk

    u = FastAPI()
    u.include_router(risk.yonlendirici)
    return TestClient(u), jeton


ILLER = [("Hatay", 36.202, 36.161), ("Konya", 37.871, 32.484), ("Erzurum", 39.904, 41.267),
         ("Van", 38.501, 43.373), ("İzmir", 38.419, 27.128), ("Malatya", 38.355, 38.309)]


def test_eszamanli_isteklerde_dogru_il(ortam):
    c, j = ortam

    def sor(il):
        ad, lat, lon = il
        y = c.post("/api/risk/predict", json={"city": ad, "manualLatitude": lat, "manualLongitude": lon}, headers=j)
        assert y.status_code == 200, y.text
        g = y.json()
        return g["city"] == ad and abs(g["coordinates"]["lat"] - lat) < 1e-9 and abs(g["coordinates"]["lon"] - lon) < 1e-9

    with ThreadPoolExecutor(6) as h:
        assert all(h.map(sor, ILLER * 4))


def test_yanit_bilesenleri_ve_dayanak(ortam):
    c, j = ortam
    g = c.post("/api/risk/predict", json={"city": "Hatay", "manualLatitude": 36.202, "manualLongitude": 36.161},
               headers=j).json()
    m = g["metrics"]
    beklenen = 100 * (0.4 * m["shortRisk"] + 0.3 * m["longHazard"] + 0.3 * m["faultScore"])
    assert abs(g["riskScore"] - beklenen) < 0.01
    assert g["dayanak"]["kisaVadeKaynagi"] in ("yerel", "ulke")
    assert g["dayanak"]["uzunVadeAnaSok"] >= 0 and g["riskLevel"] in ("DÜŞÜK", "ORTA", "YÜKSEK", "ÇOK YÜKSEK")


def test_yetki_ve_sinirlar(ortam):
    c, j = ortam
    for yol in ("/api/risk/fault_lines", "/api/risk/all_quakes?limit=3", "/api/risk/siralama"):
        assert c.get(yol).status_code == 401, yol
    assert c.post("/api/risk/predict", json={"city": "x", "manualLatitude": 52.5, "manualLongitude": 13.4},
                  headers=j).status_code == 422  # Turkiye disi
    assert c.post("/api/risk/predict", json={"city": "Uydurma"}, headers=j).status_code == 422  # konum yok
    y = c.get("/api/risk/all_quakes", params={"limit": 3, "sortBy": "magnitude"}, headers=j)
    assert y.status_code == 200 and y.json()["returned"] == 3
    assert c.get("/api/risk/all_quakes", params={"startDate": "olmaz"}, headers=j).status_code == 422


def test_siralama(ortam):
    c, j = ortam
    y = c.get("/api/risk/siralama", headers=j)
    assert y.status_code == 200
    iller = y.json()["iller"]
    assert len(iller) == 81 and [x["skor"] for x in iller] == sorted((x["skor"] for x in iller), reverse=True)


def test_skoru_belirleyen_depremler(ortam):
    """J-191: yanit skora giren depremleri konumlariyla tasir; sayilar dayanakla tutar."""
    c, j = ortam
    g = c.post("/api/risk/predict", json={"city": "Manisa", "manualLatitude": 38.6191, "manualLongitude": 27.4289},
               headers=j).json()
    d = g["dayanak"]
    ana = g["anaSoklar"]
    assert len(ana) == d["uzunVadeAnaSok"]
    assert all(x["magnitude"] >= 6.0 and x["distanceKm"] <= d["yaricapKm"]["uzun"] for x in ana)
    assert [x["magnitude"] for x in ana] == sorted((x["magnitude"] for x in ana), reverse=True)
    son = g["sonYilDepremler"]
    assert len(son) == min(60, d["kisaVadeYerelDeprem"])
    assert all(x["distanceKm"] <= d["yaricapKm"]["kisa"] and "latitude" in x and "longitude" in x for x in son)


def test_ulke_ana_soklari(ortam):
    c, j = ortam
    assert c.get("/api/risk/ana-soklar").status_code == 401
    y = c.get("/api/risk/ana-soklar", headers=j)
    assert y.status_code == 200
    v = y.json()
    assert v["depremler"] and all(x["magnitude"] >= v["esikM"] for x in v["depremler"])
