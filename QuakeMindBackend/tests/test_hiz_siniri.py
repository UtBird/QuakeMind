"""J-167 Grup B: giris denemesi siniri (S-1), SOS seli (S-2), API belgeleri (S-4),
canli akista askiya alma (S-6).

Ayri gecici SQLite; gercek veritabanina dokunulmaz. Esikler testte kucultulur
ya da buyutulur, kural ayni kalir.
"""
import os
import sys
import tempfile
import time
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

_GECICI = tempfile.mkdtemp(prefix="qm_hiz_siniri_")
os.environ["QUAKEMIND_SQLITE"] = str(Path(_GECICI) / "test.sqlite3")

import depo as depo_paketi  # noqa: E402
import hiz_siniri  # noqa: E402
import kimlik  # noqa: E402
from uclar import canli, oturum, sozlesme  # noqa: E402

SIFRE = "test-sifresi-123"


@pytest.fixture(scope="module")
def uygulama():
    depo_paketi._depo = None
    depo_paketi.depo_ac()
    u = FastAPI()
    for m in (oturum, sozlesme, canli):
        u.include_router(m.yonlendirici)
    return u


@pytest.fixture
def istemci(uygulama):
    # Her test kendi cerez kavanozuyla: bir testin oturumu digerine tasinmasin.
    return TestClient(uygulama)


def _hesap(ad, rol="afetzede"):
    d = depo_paketi.aktif_depo()
    k = kimlik.kullanici_kaydet(f"{ad}@hiz.local", ad, SIFRE)
    d.rol_ata(k["id"], rol)
    return d.kullanici_id(k["id"])


def _giris(istemci, eposta, sifre, kapi="afetzede", **ek):
    return istemci.post("/api/oturum/giris", json={"eposta": eposta, "sifre": sifre, "kapi": kapi}, **ek)


def _baslik(h):
    return {"Authorization": f"Bearer {kimlik.erisim_jetonu_uret(h)}"}


# --- S-1 -----------------------------------------------------------------------

def test_altinci_yanlis_denemede_429_ve_dogru_sifre_de_kilitli(istemci, monkeypatch):
    monkeypatch.setattr(hiz_siniri, "GIRIS_IP_SINIRI", 1000)
    _hesap("kilit")
    for _ in range(5):
        assert _giris(istemci, "kilit@hiz.local", "yanlis-sifre-x").status_code == 401
    y = _giris(istemci, "kilit@hiz.local", "yanlis-sifre-x")
    assert y.status_code == 429
    assert 1 <= int(y.headers["Retry-After"]) <= hiz_siniri.GIRIS_PENCERE_SN
    assert "dakika sonra" in y.json()["detail"]
    assert _giris(istemci, "kilit@hiz.local", SIFRE).status_code == 429


def test_olmayan_hesap_ayni_davranir(istemci, monkeypatch):
    """Var/yok farki sizmasin: olmayan e-posta da ayni sayida denemede ayni iletiyle kilitlenir."""
    monkeypatch.setattr(hiz_siniri, "GIRIS_IP_SINIRI", 1000)
    _hesap("varolan")
    yanitlar = {}
    for eposta in ("varolan@hiz.local", "hayalet@hiz.local"):
        kodlar = [_giris(istemci, eposta, "yanlis-sifre-x").status_code for _ in range(6)]
        son = _giris(istemci, eposta, "yanlis-sifre-x")
        yanitlar[eposta] = (kodlar, son.status_code, son.json()["detail"])
    assert yanitlar["varolan@hiz.local"] == yanitlar["hayalet@hiz.local"]


def test_sure_dolunca_acilir_ve_basari_sayaci_sifirlar(istemci, monkeypatch):
    monkeypatch.setattr(hiz_siniri, "GIRIS_IP_SINIRI", 1000)
    # Her hatali deneme bcrypt yuzunden ~0,4 sn surer; pencere bes denemeyi kapsamali.
    monkeypatch.setattr(hiz_siniri, "GIRIS_PENCERE_SN", 4)
    _hesap("bekleyen")
    for _ in range(5):
        _giris(istemci, "bekleyen@hiz.local", "yanlis-sifre-x")
    son_hata = time.time()
    assert _giris(istemci, "bekleyen@hiz.local", SIFRE).status_code == 429
    time.sleep(max(0.0, son_hata + 4.2 - time.time()))  # penceredeki butun hatalar dussun
    assert _giris(istemci, "bekleyen@hiz.local", SIFRE).status_code == 200
    # Basarili giristen sonra eski hatalar sayilmaz.
    monkeypatch.setattr(hiz_siniri, "GIRIS_PENCERE_SN", 900)
    for _ in range(4):
        assert _giris(istemci, "bekleyen@hiz.local", "yanlis-sifre-x").status_code == 401
    assert _giris(istemci, "bekleyen@hiz.local", SIFRE).status_code == 200


def test_ip_siniri_ve_guvenilmeyen_vekil_basligi(istemci, monkeypatch):
    monkeypatch.setattr(hiz_siniri, "GIRIS_IP_SINIRI", 3)
    monkeypatch.delenv("QUAKEMIND_VEKIL_GUVENILIR", raising=False)
    # Guvenilmeyen X-Forwarded-For: IP siniri uygulanmaz (baslik uydurulabilir,
    # vekil arkasinda herkes ayni adresten gelir).
    for i in range(5):
        y = _giris(istemci, f"sahte{i}@hiz.local", "yanlis", headers={"X-Forwarded-For": "9.9.9.9"})
        assert y.status_code == 401
    # Guvenilir vekil: basliktaki adres sayilir; farkli hesaplara yayilan deneme durur.
    monkeypatch.setenv("QUAKEMIND_VEKIL_GUVENILIR", "1")
    kodlar = [
        _giris(istemci, f"yayilan{i}@hiz.local", "yanlis", headers={"X-Forwarded-For": "8.8.8.8, 10.0.0.1"}).status_code
        for i in range(4)
    ]
    assert kodlar == [401, 401, 401, 429]


def test_kayit_ip_siniri(istemci, monkeypatch):
    monkeypatch.setattr(hiz_siniri, "KAYIT_IP_SINIRI", 2)
    monkeypatch.setenv("QUAKEMIND_VEKIL_GUVENILIR", "1")
    kodlar = [
        istemci.post("/api/oturum/kayit", json={"eposta": f"kayit{i}@hiz.local", "adSoyad": "Kayit", "sifre": SIFRE},
                     headers={"X-Forwarded-For": "7.7.7.7"}).status_code
        for i in range(3)
    ]
    assert kodlar == [201, 201, 429]


# --- S-2 -----------------------------------------------------------------------

def _sos(istemci, h, lon=36.16, oncelik="orta", **ek):
    return istemci.post("/api/sos", json={"lon": lon, "lat": 36.2, "oncelik": oncelik, **ek}, headers=_baslik(h))


def test_otuz_hizli_sos_tek_acik_satir(istemci, monkeypatch):
    monkeypatch.setattr(hiz_siniri, "SOS_HESAP_SINIRI", 1000)
    monkeypatch.setattr(hiz_siniri, "SOS_IP_SINIRI", 1000)
    d = depo_paketi.aktif_depo()
    h = _hesap("selci")
    kodlar = [_sos(istemci, h, lon=36.16 + i * 0.0001, oncelik="kritik" if i == 10 else "orta",
                   ihtiyaclar=["su"] if i == 5 else None).status_code for i in range(30)]
    assert kodlar[0] == 201 and set(kodlar[1:]) == {200}
    satirlar = d._oku("SELECT * FROM sos_cagrilari WHERE kullanici_id = ?", (h["id"],))
    assert len(satirlar) == 1
    tek = sozlesme._sos_cikti(satirlar[0])
    assert tek["guncellemeSayisi"] == 29
    assert tek["oncelik"] == "kritik"            # yalniz daha acile cikar
    assert round(tek["lon"], 4) == 36.1629        # son konum
    assert tek["ihtiyaclar"] == ["su"]            # birlesir, kaybolmaz
    # Isi haritasi kisiyi bir kez sayar.
    sos_noktasi = d._tek("SELECT COUNT(*) AS n FROM hasar_noktalari WHERE kaynak = 'sos' AND zaman = ?",
                         (satirlar[0]["zaman"],))
    assert sos_noktasi["n"] == 1

    # Kapandiktan sonra yeni SOS yeni satir acar.
    d.sos_kapat(satirlar[0]["id"])
    y = _sos(istemci, h)
    assert y.status_code == 201 and y.json()["id"] != satirlar[0]["id"]


def test_sos_dakikalik_siniri(istemci, monkeypatch):
    monkeypatch.setattr(hiz_siniri, "SOS_HESAP_SINIRI", 3)
    monkeypatch.setattr(hiz_siniri, "SOS_IP_SINIRI", 1000)  # onceki testin adres sayaci karismasin
    h = _hesap("sinirli")
    kodlar = [_sos(istemci, h).status_code for _ in range(4)]
    assert kodlar == [201, 200, 200, 429]
    y = _sos(istemci, h)
    assert y.status_code == 429 and "112" in y.json()["detail"] and "Retry-After" in y.headers


def test_guncelleme_yaniti_afetzedeye_ic_bilgi_vermez(istemci, monkeypatch):
    monkeypatch.setattr(hiz_siniri, "SOS_HESAP_SINIRI", 1000)
    monkeypatch.setattr(hiz_siniri, "SOS_IP_SINIRI", 1000)
    h = _hesap("gizli")
    _sos(istemci, h)
    y = _sos(istemci, h)
    assert y.status_code == 200 and y.json()["guncellendi"] is True
    assert "kimden" not in str(y.json()) and "kisiAd" not in str(y.json())


# --- S-4 -----------------------------------------------------------------------

def test_api_belgeleri_varsayilan_kapali():
    import fastapi_app

    assert fastapi_app.app.docs_url is None
    assert fastapi_app.app.redoc_url is None
    assert fastapi_app.app.openapi_url is None
    c = TestClient(fastapi_app.app)  # lifespan kosmaz (with yok)
    assert c.get("/docs").status_code == 404
    assert c.get("/openapi.json").status_code == 404


# --- S-6 -----------------------------------------------------------------------

def test_askiya_alinan_hesabin_akisi_kapanir(monkeypatch):
    """Akis ureteci dogrudan surulur: TestClient akisi sonuna kadar okuyup verir,
    burada ise akis ancak test icinde hesap askiya alininca biter."""
    import asyncio

    monkeypatch.setattr(canli, "OTURUM_DENETIM_SN", 0.2)
    d = depo_paketi.aktif_depo()
    h = _hesap("akisci", "koordinator")
    jeton, ozet = kimlik.yenileme_jetonu_uret(h["id"])
    d.oturum_ac(h["id"], ozet, kimlik.YENILEME_OMRU_SN)

    class SahteIstek:
        async def is_disconnected(self):
            return False

    async def sur():
        yanit = await canli.canli_akis(SahteIstek(), jeton)
        parcalar = []
        akis = yanit.body_iterator
        parcalar.append(await asyncio.wait_for(akis.__anext__(), 2))  # ": akis acildi"
        d.askiya_al(h["id"], True)
        try:
            while True:
                parca = await asyncio.wait_for(akis.__anext__(), 3)
                parcalar.append(parca if isinstance(parca, str) else parca.decode())
        except StopAsyncIteration:
            pass
        return parcalar

    t0 = time.monotonic()
    parcalar = asyncio.run(sur())
    assert any("oturum-bitti" in p for p in parcalar), parcalar
    assert time.monotonic() - t0 < 3  # denetim araligi kadar surede kapandi


def test_gecerli_oturumun_akisi_surer():
    d = depo_paketi.aktif_depo()
    h = _hesap("surekli", "koordinator")
    jeton, ozet = kimlik.yenileme_jetonu_uret(h["id"])
    d.oturum_ac(h["id"], ozet, kimlik.YENILEME_OMRU_SN)
    assert canli._akis_suruyor_mu(jeton, {"id": h["id"], "rol": "koordinator"})
    # Rol degisirse akis yeniden kurulmali (eski rolun suzgeciyle surmesin).
    assert not canli._akis_suruyor_mu(jeton, {"id": h["id"], "rol": "yonetici"})


# --- P-5 -----------------------------------------------------------------------

def test_hazir_ucu(monkeypatch):
    """Oturumsuz; yalniz evet/hayir. Analiz iscisi yoksa 503, varsa 200."""
    import cekirdek as ck
    from uclar import genel

    u = FastAPI()
    u.include_router(genel.yonlendirici)
    c = TestClient(u)
    monkeypatch.setattr(ck, "road_damage_pool", None)
    y = c.get("/api/hazir")
    assert y.status_code == 503 and y.json() == {"hazir": False, "veritabani": True, "analizIscisi": False}
    monkeypatch.setattr(ck, "road_damage_pool", object())
    y = c.get("/api/hazir")
    assert y.status_code == 200 and y.json()["hazir"] is True
