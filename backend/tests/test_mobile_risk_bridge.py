"""Flutter klasoru kaldirildiginda Android risk endpointi calismali."""

import importlib
import math
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import cekirdek as ck  # noqa: E402
from uclar import risk  # noqa: E402


def test_bridge_yalniz_backend_veri_kokunu_kullanir():
    bridge = importlib.import_module("risk_bridge")
    assert bridge.BACKEND_ROOT == BASE_DIR
    assert bridge.RISK_ROOT == BASE_DIR / "apps" / "earthquake_risk"
    assert "mobile/tool" not in str(bridge.__file__).replace("\\", "/").lower()


def test_manual_coordinates_risk_endpoint_returns_real_contract_shape(monkeypatch):
    """Android'in `{city:'Türkiye',manualLatitude,...}` istegi geocoding istemez."""
    bridge = importlib.import_module("risk_bridge")
    monkeypatch.setattr(bridge, "GEOJSON_PATHS", [])
    fake_risk_engine = types.ModuleType("risk_engine")
    fake_risk_engine.haversine = lambda lat, lon, lats, lons: np.hypot(np.array(lats) - lat, np.array(lons) - lon) * 111
    fake_risk_engine.nearest_fault_distance = lambda lat, lon: 12.5
    fake_risk_engine.fault_hazard_score = lambda distance: 0.2
    fake_risk_engine.FAULT_LINES = []
    monkeypatch.setitem(sys.modules, "risk_engine", fake_risk_engine)

    class Model:
        last_lat = None
        last_lon = None
        df_full = pd.DataFrame({
            "time": pd.to_datetime(["2026-11-06T12:00:00", "2026-11-07T12:00:00"]),
            "latitude": [40.99, 41.0], "longitude": [29.02, 29.03],
            "mag": [3.1, 4.2], "depth": [7.1, 10.4], "place": ["Bolge A", "Bolge B"],
        })

        def predict_city_risk(self, city, manual_coords):
            assert city == "Türkiye"
            assert manual_coords == (40.99, 29.02)
            self.last_lat, self.last_lon = manual_coords
            return "Nihai Risk Skoru: 42.00%  ORTA"

        def _compute_short_term_ml_risk(self, lat, lon):
            return 0.3

        def _compute_long_term_hazard(self, lat, lon, **kwargs):
            return 0.4

    monkeypatch.setattr(ck, "risk_engine", Model())
    api = FastAPI()
    api.include_router(risk.yonlendirici)
    resp = TestClient(api).post("/api/risk/predict", json={
        "city": "Türkiye", "manualLatitude": 40.99, "manualLongitude": 29.02,
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert math.isclose(data["riskScore"], 42.0)
    assert data["coordinates"] == {"lat": 40.99, "lon": 29.02}
    assert data["source"] == "backend_exact"
    assert data["usedManualCoordinates"] is True
    assert len(data["mapEvents"]) == 2
