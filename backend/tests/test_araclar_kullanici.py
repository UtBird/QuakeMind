"""Sunucuda hesap araci: ilk yonetici, sifre sifirlama (J-182).

Ayri gecici SQLite; gercek veritabanina dokunulmaz."""
import os
import re
import sys
import tempfile
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


@pytest.fixture()
def arac():
    os.environ["QUAKEMIND_SQLITE"] = str(Path(tempfile.mkdtemp(prefix="qm_hesap_")) / "t.sqlite3")
    import depo as depo_paketi

    depo_paketi._depo = None
    import araclar_kullanici

    return araclar_kullanici, depo_paketi.depo_ac()


def _sifre(cikti: str) -> str:
    return re.search(r"gecici sifre : (\S+)", cikti).group(1)


def test_ilk_yonetici_gecici_sifreyle_bir_kez(arac, capsys):
    import kimlik

    a, d = arac
    assert a.main(["ilk-yonetici", "Yonetici@Kurum.gov.tr", "Ilk Yonetici"]) == 0
    sifre = _sifre(capsys.readouterr().out)
    assert len(sifre) == 12 and sifre != "degistir1234"
    k = d.kullanici_eposta("yonetici@kurum.gov.tr")
    assert k["rol"] == "yonetici" and k["sifre_degismeli"]
    assert kimlik.sifre_dogrula(sifre, k["sifre_ozeti"])
    kayit = d.hesap_kayitlari(k["id"], 10)
    assert kayit and kayit[0]["islem"] == "hesap-acildi"

    # Ikinci kez calismaz: yonetici varsa hesaplar konsoldan acilir.
    assert a.main(["ilk-yonetici", "baska@kurum.gov.tr", "Baska Kisi"]) == 1
    assert d.kullanici_eposta("baska@kurum.gov.tr") is None


def test_kayitli_afetzede_ilk_yonetici_olur_sifresi_yenilenir(arac, capsys):
    import kimlik

    a, d = arac
    k = kimlik.kullanici_kaydet("kisi@kurum.gov.tr", "Kisi", "kendi-sifresi-123")
    assert a.main(["ilk-yonetici", "kisi@kurum.gov.tr", "Kisi"]) == 0
    sifre = _sifre(capsys.readouterr().out)
    yeni = d.kullanici_eposta("kisi@kurum.gov.tr")
    assert yeni["id"] == k["id"] and yeni["rol"] == "yonetici" and yeni["sifre_degismeli"]
    assert kimlik.sifre_dogrula(sifre, yeni["sifre_ozeti"])
    assert not kimlik.sifre_dogrula("kendi-sifresi-123", yeni["sifre_ozeti"])


def test_sifre_sifirla_ve_komut_satirinda_sifre_yok(arac, capsys):
    import kimlik

    a, d = arac
    a.main(["ilk-yonetici", "y@kurum.gov.tr", "Yonetici"])
    eski = _sifre(capsys.readouterr().out)
    assert a.main(["sifre-sifirla", "y@kurum.gov.tr"]) == 0
    yeni = _sifre(capsys.readouterr().out)
    k = d.kullanici_eposta("y@kurum.gov.tr")
    assert yeni != eski and kimlik.sifre_dogrula(yeni, k["sifre_ozeti"]) and k["sifre_degismeli"]
    assert a.main(["sifre-sifirla", "yok@kurum.gov.tr"]) == 1

    # Sifre arguman olarak verilemez.
    assert a.main(["ekle", "s@kurum.gov.tr", "Saha", "saha", "sifre123"]) == 2
    assert d.kullanici_eposta("s@kurum.gov.tr") is None
    assert a.main(["ekle", "s@kurum.gov.tr", "Saha", "saha"]) == 0
    assert d.kullanici_eposta("s@kurum.gov.tr")["sifre_degismeli"]


def test_bos_sunucuda_butun_roller_acilir(arac, capsys):
    """Canliya ilk cikis: bos veritabani -> ilk yonetici araclan, gerisi konsoldan."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from uclar import oturum

    a, d = arac
    u = FastAPI()
    u.include_router(oturum.yonlendirici)
    c = TestClient(u)

    # Bos sunucuda kimse giremez; kayit ucu rol vermez.
    assert c.post("/api/oturum/giris", json={"eposta": "y@kurum.gov.tr", "sifre": "x"}).status_code == 401

    a.main(["ilk-yonetici", "y@kurum.gov.tr", "Ilk Yonetici"])
    gecici = _sifre(capsys.readouterr().out)
    g = c.post("/api/oturum/giris", json={"eposta": "y@kurum.gov.tr", "sifre": gecici})
    assert g.status_code == 200 and g.json()["kullanici"]["sifreDegismeli"] is True
    j = {"Authorization": f"Bearer {g.json()['erisimJetonu']}"}

    # Gecici sifreyle hesap acamaz; once sifresini degistirir.
    acma = {"eposta": "k@kurum.gov.tr", "adSoyad": "Koordinator", "rol": "koordinator"}
    assert c.post("/api/oturum/kullanicilar", json=acma, headers=j).status_code == 403
    s = c.post("/api/oturum/sifre", json={"eskiSifre": gecici, "yeniSifre": "yeni-uzun-sifre-2026"}, headers=j)
    assert s.status_code == 200, s.text
    j = {"Authorization": f"Bearer {s.json()['erisimJetonu']}"} if "erisimJetonu" in s.json() else j

    k = c.post("/api/oturum/kullanicilar", json=acma, headers=j)
    assert k.status_code == 201, k.text
    saha = c.post("/api/oturum/kullanicilar",
                  json={"eposta": "s@kurum.gov.tr", "adSoyad": "Saha Ekibi", "rol": "saha"}, headers=j)
    assert saha.status_code == 201
    # Koordinator, aldigi gecici sifreyle girebilir (degistirmesi istenir).
    kg = c.post("/api/oturum/giris", json={"eposta": "k@kurum.gov.tr", "sifre": k.json()["geciciSifre"]})
    assert kg.status_code == 200 and kg.json()["kullanici"]["rol"] == "koordinator"
