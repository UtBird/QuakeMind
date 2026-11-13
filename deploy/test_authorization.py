"""Deployment checks for the real HTTP authentication boundary."""

import uuid

import pytest
from fastapi.testclient import TestClient

import depo
import fastapi_app


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(depo, "_depo", depo.SqliteDepo(str(tmp_path / "auth.sqlite3")))
    api = TestClient(fastapi_app.app, base_url="https://testserver")
    try:
        yield api
    finally:
        api.close()


def test_anonymous_heatmap_is_rejected(client):
    response = client.get("/api/road_damage/heatmap", params={"latitude": 36.2, "longitude": 36.16})
    assert response.status_code == 401


def test_citizen_cannot_access_staff_heatmap(client):
    signup = client.post("/api/oturum/kayit", json={
        "eposta": f"citizen-{uuid.uuid4().hex}@example.invalid",
        "adSoyad": "Test", "sifre": "a-valid-test-password", "rol": "yonetici",
    })
    assert signup.status_code == 201
    assert signup.json()["kullanici"]["rol"] == "afetzede"
    response = client.get("/api/road_damage/heatmap", params={"latitude": 36.2, "longitude": 36.16},
                          headers={"Authorization": f"Bearer {signup.json()['erisimJetonu']}"})
    assert response.status_code == 403
