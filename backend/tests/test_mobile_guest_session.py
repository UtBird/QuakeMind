"""Android acil modunun gercek oturum, yenileme ve SOS sozlesmesi."""

import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import depo  # noqa: E402
from depo.sqlite_surucu import SqliteDepo  # noqa: E402
from uclar import guvenlik, ihbar, oturum, sozlesme  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    veritabani = SqliteDepo(str(tmp_path / "misafir-test.sqlite3"))
    monkeypatch.setattr(depo, "_depo", veritabani)
    api = FastAPI()
    api.include_router(oturum.yonlendirici)
    api.include_router(sozlesme.yonlendirici)
    api.include_router(ihbar.yonlendirici)
    api.include_router(guvenlik.yonlendirici)
    with TestClient(api) as istemci:
        yield istemci
    veritabani.kapat()


def test_misafir_oturumu_sos_ve_yenileme(client):
    guest = client.post("/api/oturum/misafir")
    assert guest.status_code == 201
    kayit = guest.json()
    assert kayit["kullanici"]["rol"] == "afetzede"
    assert kayit["kullanici"]["misafir"] is True
    assert kayit["erisimJetonu"]
    cookie = guest.cookies.get("qm_yenileme")
    assert cookie
    assert "httponly" in guest.headers["set-cookie"].lower()

    headers = {"Authorization": f"Bearer {kayit['erisimJetonu']}"}
    assert client.get("/api/oturum/ben", headers=headers).json()["kullanici"]["id"] == kayit["kullanici"]["id"]
    sos = client.post("/api/sos", headers=headers, json={"lat": 40.99, "lon": 29.03, "metin": "Acil yardim"})
    assert sos.status_code == 201
    assert sos.json()["durum"] == "bekliyor"
    mine = client.get("/api/sos", headers=headers)
    assert mine.status_code == 200
    assert [item["id"] for item in mine.json()] == [sos.json()["id"]]

    # Aynı cihaz yeniden acildiginda ikinci bir misafir hesabi olusmaz.
    second = client.post("/api/oturum/misafir")
    assert second.status_code == 201
    assert second.json()["kullanici"]["id"] == kayit["kullanici"]["id"]

    renewed = client.post("/api/oturum/yenile")
    assert renewed.status_code == 200
    assert renewed.json()["kullanici"]["misafir"] is True
    assert renewed.json()["kullanici"]["id"] == kayit["kullanici"]["id"]


def test_misafir_ayri_kullanicinin_sosunu_goremez(client):
    birinci = TestClient(client.app)
    ikinci = TestClient(client.app)
    with birinci, ikinci:
        first = birinci.post("/api/oturum/misafir").json()
        second = ikinci.post("/api/oturum/misafir").json()
        assert first["kullanici"]["id"] != second["kullanici"]["id"]

        first_headers = {"Authorization": f"Bearer {first['erisimJetonu']}"}
        second_headers = {"Authorization": f"Bearer {second['erisimJetonu']}"}
        assert birinci.post("/api/sos", headers=first_headers, json={"lat": 40.99, "lon": 29.03}).status_code == 201
        assert ikinci.get("/api/sos", headers=second_headers).json() == []
        assert ikinci.get("/api/oturum/ben").status_code == 401


def test_misafir_mevcut_hesabi_dusurmez(client):
    kayit = client.post("/api/oturum/kayit", json={
        "eposta": "uye@example.com", "adSoyad": "Test Uye", "sifre": "super-guclu-sifre"
    })
    assert kayit.status_code == 201
    assert kayit.json()["kullanici"]["misafir"] is False

    guest = client.post("/api/oturum/misafir")
    assert guest.json()["kullanici"]["id"] == kayit.json()["kullanici"]["id"]
    assert guest.json()["kullanici"]["misafir"] is False


def test_ihbar_tekrari_kalici_ve_ayni_kullaniciya_ozel(client, monkeypatch):
    auth = client.post("/api/oturum/misafir").json()
    headers = {
        "Authorization": f"Bearer {auth['erisimJetonu']}",
        "Idempotency-Key": "android-incident-123456",
    }
    payload = {
        "tur": "metin", "konumKaynagi": "gps", "lat": 40.99, "lon": 29.03,
        "metin": "Yol kenarinda hasar var",
    }
    yayinlar = []
    monkeypatch.setattr(ihbar.canli_yayin, "yayinla", lambda *args, **kw: yayinlar.append((args, kw)))

    first = client.post("/api/ihbarlar", headers=headers, json=payload)
    assert first.status_code == 201
    again = client.post("/api/ihbarlar", headers=headers, json=payload)
    assert again.status_code == 201
    assert again.json()["id"] == first.json()["id"]
    assert len(yayinlar) == 1
    assert len(client.get("/api/ihbarlar", headers=headers).json()) == 1

    changed = client.post("/api/ihbarlar", headers=headers, json={**payload, "metin": "Farkli ihbar"})
    assert changed.status_code == 409
    assert len(client.get("/api/ihbarlar", headers=headers).json()) == 1

    # Ayrı kullanıcı aynı anahtarı güvenle kullanabilir.
    with TestClient(client.app) as other:
        other_auth = other.post("/api/oturum/misafir").json()
        other_headers = {"Authorization": f"Bearer {other_auth['erisimJetonu']}",
                         "Idempotency-Key": headers["Idempotency-Key"]}
        result = other.post("/api/ihbarlar", headers=other_headers, json=payload)
        assert result.status_code == 201
        assert result.json()["id"] != first.json()["id"]
        assert len(other.get("/api/ihbarlar", headers=other_headers).json()) == 1


def test_ihbar_tekrari_sinir_dolsa_da_eski_yaniti_verir(client, monkeypatch):
    auth = client.post("/api/oturum/misafir").json()
    headers = {"Authorization": f"Bearer {auth['erisimJetonu']}", "Idempotency-Key": "test-key-987654321"}
    payload = {"tur": "ihtiyac", "konumKaynagi": "gps", "lat": 40.99, "lon": 29.03,
               "ihtiyaclar": ["su"], "kisiSayisi": 2}
    monkeypatch.setattr(ihbar, "KISI_BASI_SINIR", 1)
    first = client.post("/api/ihbarlar", headers=headers, json=payload)
    assert first.status_code == 201
    assert client.post("/api/ihbarlar", headers=headers, json=payload).json()["id"] == first.json()["id"]
    assert client.post("/api/ihbarlar", headers={**headers, "Idempotency-Key": "test-key-222222222"},
                       json=payload).status_code == 429


def test_kullanicinin_girdigi_koordinat_gercekten_manuel_olarak_kaydedilir(client):
    auth = client.post("/api/oturum/misafir").json()
    headers = {"Authorization": f"Bearer {auth['erisimJetonu']}"}
    ihbar = client.post("/api/ihbarlar", headers=headers, json={
        "tur": "ihtiyac", "konumKaynagi": "manuel", "lat": 40.98,
        "lon": 29.01, "ihtiyaclar": ["su"],
    })
    assert ihbar.status_code == 201
    assert ihbar.json()["konumKaynagi"] == "manuel"
    assert ihbar.json()["lat"] == 40.98
    assert ihbar.json()["lon"] == 29.01
    assert client.post("/api/ihbarlar", headers=headers, json={
        "tur": "ihtiyac", "konumKaynagi": "manuel", "lat": 92.0,
        "lon": 29.01, "ihtiyaclar": ["su"],
    }).status_code == 422

    sos = client.post("/api/sos", headers=headers, json={
        "konumKaynagi": "manuel", "lat": 40.98, "lon": 29.01,
    })
    assert sos.status_code == 201
    assert sos.json()["konumKaynagi"] == "manuel"


def test_ihbar_db_unique_anahtari_ve_hasar_yazimi_tek_transaction(client):
    auth = client.post("/api/oturum/misafir").json()
    user_id = auth["kullanici"]["id"]
    store = depo.aktif_depo()
    hasar = {"kaynak": "metin", "skor": 0.9, "guven": 0.8, "etiket": "Hasar"}
    first = store.ihbar_ekle(
        tur="metin", lon=29.03, lat=40.99, kullanici_id=user_id,
        metin="hasar", istemci_anahtari="same-key-123456", istek_ozeti="hash-1", hasar_noktasi=hasar,
    )
    with pytest.raises(sqlite3.IntegrityError):
        store.ihbar_ekle(
            tur="metin", lon=29.03, lat=40.99, kullanici_id=user_id,
            metin="hasar", istemci_anahtari="same-key-123456", istek_ozeti="hash-1", hasar_noktasi=hasar,
        )
    assert len(store.ihbar_listele(kullanici_id=user_id)) == 1
    assert len(store.hasar_listele(kaynak="metin")) == 1
    assert store.ihbar_bul(first["id"])["hasar_id"] == store.hasar_listele(kaynak="metin")[0]["id"]


def test_ihbar_idempotency_sutunlari_eski_dbde_eklenir(tmp_path):
    db_path = tmp_path / "eski.sqlite3"
    with sqlite3.connect(db_path) as conn:
        conn.execute("""CREATE TABLE ihbarlar (
            id TEXT PRIMARY KEY, tur TEXT NOT NULL, lon REAL NOT NULL, lat REAL NOT NULL,
            zaman REAL NOT NULL, durum TEXT NOT NULL, kullanici_id TEXT,
            metin TEXT, mahalle TEXT, etiket TEXT, skor REAL, guven REAL,
            hasar_id TEXT, ek TEXT, isleyen_id TEXT, isleyen_ad TEXT, guncellendi REAL
        )""")
    store = SqliteDepo(str(db_path))
    try:
        columns = {row[1] for row in store._baglanti.execute("PRAGMA table_info(ihbarlar)")}
        assert {"istemci_anahtari", "istek_ozeti"} <= columns
        indexes = {row[1] for row in store._baglanti.execute("PRAGMA index_list(ihbarlar)")}
        assert "ux_ihbar_istemci_anahtari" in indexes
    finally:
        store.kapat()


def test_guvenlik_durumu_kisisel_kalici_ve_sos_olmayan_beyan(client):
    assert client.post("/api/afetzede/guvende-durumu", json={"status": "SAFE"}).status_code == 401
    first_auth = client.post("/api/oturum/misafir").json()
    header = {"Authorization": f"Bearer {first_auth['erisimJetonu']}"}
    assert client.get("/api/afetzede/guvende-durumu", headers=header).json() is None
    changed = client.post("/api/afetzede/guvende-durumu", headers=header, json={
        "status": "NEED_HELP", "latitude": 40.99, "longitude": 29.03, "note": "Yardim gerekli",
    })
    assert changed.status_code == 200
    assert changed.json()["status"] == "NEED_HELP"
    assert changed.json()["updatedAt"] > 0
    assert changed.json()["note"] == "Yardim gerekli"
    assert client.get("/api/afetzede/guvende-durumu", headers=header).json() == changed.json()
    assert client.get("/api/sos", headers=header).json() == []

    with TestClient(client.app) as other:
        other_auth = other.post("/api/oturum/misafir").json()
        other_header = {"Authorization": f"Bearer {other_auth['erisimJetonu']}"}
        assert other.get("/api/afetzede/guvende-durumu", headers=other_header).json() is None
        assert other.post("/api/afetzede/guvende-durumu", headers=other_header,
                          json={"status": "SAFE"}).status_code == 200
        assert client.get("/api/afetzede/guvende-durumu", headers=header).json()["status"] == "NEED_HELP"

    assert client.post("/api/afetzede/guvende-durumu", headers=header,
                       json={"status": "UNKNOWN", "latitude": 40.99}).status_code == 422
    assert client.post("/api/afetzede/guvende-durumu", headers=header,
                       json={"status": "SAFE", "latitude": 101, "longitude": 29}).status_code == 422
    assert client.post("/api/afetzede/guvende-durumu", headers=header,
                       json={"status": "safe"}).status_code == 422
    assert client.get("/api/afetzede/guvende-durumu", headers=header).json()["status"] == "NEED_HELP"


def test_production_api_registers_mobile_routes():
    from fastapi_app import app

    # FastAPI yeni surumlerde include_router'u `_IncludedRouter` olarak
    # tembel genisletir; kamusal OpenAPI sozlesmesini dogrula.
    routes = {
        (method.upper(), path)
        for path, operations in app.openapi()["paths"].items()
        for method in operations if method.lower() in {"get", "post", "put", "delete", "patch"}
    }
    for method, path in (
        ("POST", "/api/oturum/misafir"),
        ("POST", "/api/ihbarlar"),
        ("POST", "/api/afetzede/guvende-durumu"),
        ("GET", "/api/afetzede/guvende-durumu"),
        ("GET", "/api/live"),
        ("POST", "/api/risk/predict"),
    ):
        assert (method, path) in routes
