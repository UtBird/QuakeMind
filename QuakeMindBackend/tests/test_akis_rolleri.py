"""Uçtan uca akış düzeltmeleri (J-174): canlı akışın role göre süzülmesi ve
ihtiyaç geçen yazılı ihbarın ihtiyaç alanları.

Bütün akışın gerçek API'de sınaması `araclar_akis_senaryosu.py` (48 adım)."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


@pytest.fixture(scope="module", autouse=True)
def gecici_depo():
    os.environ["QUAKEMIND_SQLITE"] = str(Path(tempfile.mkdtemp(prefix="qm_akis_")) / "t.sqlite3")
    import depo as depo_paketi

    depo_paketi._depo = None
    depo_paketi.depo_ac()
    yield


def _mesaj(tip, **alan):
    return {"tip": tip, "zaman": 1, **alan}


def test_islem_kaydi_isareti_yalniz_koordinasyona():
    from uclar.canli import role_gore

    m = _mesaj("islem-kaydi", tur="gorev_durumu")
    assert role_gore(m, {"id": "k", "rol": "koordinator"}) == m
    assert role_gore(m, {"id": "y", "rol": "yonetici"}) == m
    # Saha islem kayitlarini okuyamaz (403); isaret de ona gitmez.
    assert role_gore(m, {"id": "s", "rol": "saha"}) is None
    assert role_gore(m, {"id": "a", "rol": "afetzede"}) is None


def test_saha_operasyon_mesajlarini_alir():
    from uclar.canli import role_gore

    saha = {"id": "s", "rol": "saha"}
    for m in (
        _mesaj("yeni-sos", id="sos-1", lon=36.1, lat=36.2),
        _mesaj("gorev", id="g", hedefTur="sos", hedefId="sos-1", ekipId="EKP-01", durum="atandi"),
        _mesaj("ihbar", id="ihb-1"),
        _mesaj("ekip-konumu", ekipId="EKP-01"),
    ):
        assert role_gore(m, saha) == m


def _metin_kaydi(analiz):
    import json

    return {
        "id": "ihb-1", "tur": "metin", "lon": 36.1, "lat": 36.2, "zaman": 1.0, "durum": "yeni",
        "metin": "x", "ek": json.dumps({"analiz": analiz}),
    }


def test_metin_ihbarinda_ihtiyac_ve_kisi_sayisi():
    from uclar.ihbar import _cikti

    analiz = {
        "ilgisiz": False,
        "kategori": "Acil Yardım İhtiyacı",
        "ihtiyaclar": [{"ihtiyac": "barinma"}, {"ihtiyac": "su"}, {"ihtiyac": "su"}, {"ihtiyac": "bilinmeyen"}],
        "kisiler": [{"sayi": 3}, {"sayi": 30}],
    }
    c = _cikti(_metin_kaydi(analiz))
    # Sira sozlesmedeki sira; tekrar ve bilinmeyen ihtiyac yok.
    assert c["ihtiyaclar"] == ["su", "barinma"]
    assert c["kisiSayisi"] == 30
    assert c["analiz"] == analiz


def test_ilgisiz_ya_da_ihtiyacsiz_metin():
    from uclar.ihbar import _cikti

    c = _cikti(_metin_kaydi({"ilgisiz": True, "ihtiyaclar": [{"ihtiyac": "su"}], "kisiler": []}))
    assert "ihtiyaclar" not in c
    c = _cikti(_metin_kaydi({"ilgisiz": False, "ihtiyaclar": [], "kisiler": []}))
    assert c["ihtiyaclar"] == [] and c["kisiSayisi"] is None
    c = _cikti(_metin_kaydi(None))
    assert "ihtiyaclar" not in c
