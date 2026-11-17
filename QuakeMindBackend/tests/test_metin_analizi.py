"""Metin analizi (J-170): yerel adres çözücü, yapılandırılmış çıkarım, uçlar.

Model koşmaz: adres ve çıkarım modelsiz; uçlarda işçi sahtesiyle değiştirilir.
Adres testleri depodaki gerçek dizini (metin_analizi/veri/adres_dizini.json.gz,
OSM) kullanır. Metinler sentetiktir; yer adları gerçektir.
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

_GECICI = tempfile.mkdtemp(prefix="qm_metin_")
os.environ["QUAKEMIND_SQLITE"] = str(Path(_GECICI) / "test.sqlite3")

import depo as depo_paketi  # noqa: E402
import hiz_siniri  # noqa: E402
import kimlik  # noqa: E402
from metin_analizi import adres, cikarim, isci  # noqa: E402
from metin_analizi.normal import katla  # noqa: E402


# --- adres --------------------------------------------------------------------

@pytest.mark.parametrize("metin,duzey,icerir", [
    ("Elektrik Mahallesi 5. sokakta bina çöktü", "sokak", "5. Sokak, Elektrik Mah."),
    ("Defne Elektrik Mahallesinde apartman göçtü", "mahalle", "Elektrik Mah., Defne"),
    ("Antakya Armutlu mahallesinde bina çökmüş", "mahalle", "Armutlu Mah., Antakya"),
    ("Armutlu Mahallesi 5. Sokak'ta iki kişi enkaz altında", "sokak", "5. Sokak, Armutlu Mah."),
    ("Nurdağı'nda bir apartmanda ses geliyor", "ilce", "Nurdağı, Gaziantep"),
    ("nurdagi cikisinda yol kapali", "ilce", "Nurdağı"),
])
def test_adres_duzeyi(metin, duzey, icerir):
    s = adres.coz(metin)
    assert s.duzey == duzey, (s.duzey, s.konum_metin, s.notlar)
    assert icerir in s.konum_metin
    assert s.konum and s.belirsizlik_m


def test_siradan_sozcukler_yer_adina_cekilmez():
    """'altından' Altındağ'a, 'bitmiş' Bitlis'e eşleşiyordu (bulanık eşleşme)."""
    for metin in ("enkaz altından ses geliyor", "kalp ilacı bitmiş", "Herkese geçmiş olsun"):
        s = adres.coz(metin)
        assert s.konum is None, (metin, s.konum_metin)


def test_ilce_merkezi_oldugu_soylenir_ve_ilce_tahmin_edilmez():
    s = adres.coz("İslahiye merkezde iki bina yan yatmış")
    assert s.duzey == "ilce" and any("ilçe merkezidir" in n for n in s.notlar)
    # Mahalle düzeyinde ilçe yalnız metinde yazıyorsa gösterilir.
    s = adres.coz("Sümerler mahallesinde çadırdayız")
    assert s.duzey == "mahalle" and "ilce" not in s.adres


def test_dizinde_olmayan_ad_uydurulmaz():
    s = adres.coz("Şekeroba'da okulun yanındaki bina çökmüş")
    assert s.konum is None
    s = adres.coz("Uydurmaköy Mahallesi'nde ev yıkıldı")
    assert s.konum is None and any("dizininde yok" in n for n in s.notlar)


def test_eslesme_araliklari_metne_karsilik_gelir():
    metin = "Antakya Armutlu mahallesinde bina çökmüş"
    s = adres.coz(metin)
    for e in s.eslesmeler:
        assert metin[e["bas"]:e["son"]] == e["metin"]


def test_normal():
    assert katla("Nurdağı'nda") == "nurdagi"
    assert katla("İSLAHİYE") == "islahiye"


# --- cikarim --------------------------------------------------------------------

def test_cikarim():
    c = cikarim.cikar("Armutlu Mahallesi 5. Sokak'ta bina çöktü, iki kişi enkaz altında, ses geliyor. "
                      "Su ve battaniye lazım, iki bebek var.")
    assert {"sayi": 2, "ne": "kişi"}.items() <= c["kisiler"][0].items()
    assert {x["ihtiyac"] for x in c["ihtiyaclar"]} >= {"su", "isinma"}
    assert {x["sinyal"] for x in c["sinyaller"]} >= {"enkaz_altinda", "ses_geliyor", "cokme", "savunmasiz"}
    c = cikarim.cikar("Sokak arası molozla kapandı, ambulans giremiyor")
    assert {x["sinyal"] for x in c["sinyaller"]} == {"yol_kapali"}  # ambulans yaralı sinyali değil


# --- uclar ------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ortam():
    depo_paketi._depo = None
    d = depo_paketi.depo_ac()
    hesap = {}
    for ad, rol in [("koordinator", "koordinator"), ("afetzede", "afetzede")]:
        k = kimlik.kullanici_kaydet(f"{ad}@metin.local", ad, "test-sifresi-123")
        d.rol_ata(k["id"], rol)
        hesap[ad] = d.kullanici_id(k["id"])
    from uclar import ihbar, metin

    u = FastAPI()
    u.include_router(ihbar.yonlendirici)
    u.include_router(metin.yonlendirici)
    return TestClient(u), hesap


def _baslik(h):
    return {"Authorization": f"Bearer {kimlik.erisim_jetonu_uret(h)}"}


SAHTE = {"ilgili": True, "kategori": "Enkaz Bildirimi", "aciliyet": 5, "guven": 0.8, "kategoriKaynagi": "model",
         "ikinciKategori": None, "kategoriUyarilari": [], "konum": [36.19532, 36.15143], "konumDuzeyi": "mahalle",
         "belirsizlikM": 800, "adres": {"mahalle": "Armutlu", "il": "Hatay"}, "konumMetin": "Armutlu Mah., Hatay",
         "adresEslesmeleri": [], "adresAdaylari": [], "adresNotlari": [], "kisiler": [], "ihtiyaclar": [],
         "sinyaller": [], "sureMs": 25}


def test_afetzede_analizi_yeni_alanlari_doner(ortam, monkeypatch):
    istemci, h = ortam
    monkeypatch.setattr(isci, "coz", lambda m: dict(SAHTE))
    y = istemci.post("/api/afetzede/metin-analiz", json={"metin": "Armutlu mahallesinde bina çöktü"},
                     headers=_baslik(h["afetzede"]))
    assert y.status_code == 200, y.text
    g = y.json()
    assert g["analizId"] and g["konum"] == {"lat": 36.19532, "lon": 36.15143}
    assert g["konumDuzeyi"] == "mahalle" and g["belirsizlikM"] == 800 and g["ilgisiz"] is False


def test_model_calismazsa_503(ortam, monkeypatch):
    istemci, h = ortam

    def patla(_m):
        raise isci.MetinModeliYok("deneme")

    monkeypatch.setattr(isci, "coz", patla)
    y = istemci.post("/api/nlp/analyze", json={"text": "Armutlu mahallesinde bina çöktü"},
                     headers=_baslik(h["koordinator"]))
    assert y.status_code == 503


def test_metin_uzunlugu_ve_hiz_siniri(ortam, monkeypatch):
    istemci, h = ortam
    monkeypatch.setattr(isci, "coz", lambda m: dict(SAHTE))
    assert istemci.post("/api/nlp/analyze", json={"text": "x" * 1001},
                        headers=_baslik(h["koordinator"])).status_code == 422
    monkeypatch.setattr(hiz_siniri, "METIN_HESAP_SINIRI", 2)
    kodlar = [istemci.post("/api/afetzede/metin-analiz", json={"metin": "Armutlu mahallesinde bina çöktü"},
                           headers=_baslik(h["afetzede"])).status_code for _ in range(3)]
    assert kodlar[-1] == 429


# --- kullanıcı bulgusu (17 Kasım): "Cumhuriyet meydanında ölüler var 2 tane" --------

def test_meydan_adres_turudur():
    s = adres.coz("Cumhuriyet meydanında ölüler var 2 tane")
    assert s.duzey == "sokak" and "Cumhuriyet Meydanı" in s.konum_metin


def test_olu_isareti_ve_sonradan_gelen_sayi():
    c = cikarim.cikar("Cumhuriyet meydanında ölüler var 2 tane")
    assert [(k["sayi"], k["ne"]) for k in c["kisiler"]] == [(2, "ölü")]
    assert {x["sinyal"] for x in c["sinyaller"]} == {"olu"}
    # "öldü" yakalanır; "oldu"/"olmuş" (olmak) karışmaz; "tane"siz sayı kişi sayılmaz.
    assert "olu" in {x["sinyal"] for x in cikarim.cikar("Annem öldü, ev yıkıldı")["sinyaller"]}
    assert cikarim.cikar("Ne oldu bilmiyoruz, bina olmuş mu")["sinyaller"] == []
    assert cikarim.cikar("çocuk 5 yaşında, su lazım")["kisiler"] == []


def test_ilgisiz_denen_metinde_agir_isaret_uyarisi():
    """Karar değişmez (J-111); koordinatöre 'kontrol et' uyarısı çıkar."""
    import metin_analizi as ma

    class SahteSiniflandirici:
        model_name = "sahte"

        def classifier(self, _m):
            return [[{"label": "Alakasiz", "score": 0.65}]]

        def classify_detay(self, _m, predictions=None):
            return {"kategori": "Alakasız", "guven": 0.65, "kaynak": "model", "hamEtiket": "Alakasiz", "hamSkor": 0.65}

    a = object.__new__(ma.MetinAnalizci)
    a.siniflandirici = SahteSiniflandirici()
    a._s = type("S", (), {"_normalize_label": staticmethod(lambda x: x), "CATEGORY_MAPPING": {}})
    a.dizin = adres.dizin()
    a.model_adi = "sahte"
    s = a.coz("Cumhuriyet meydanında ölüler var 2 tane")
    assert s["ilgili"] is False and s["aciliyet"] is None
    assert len(s["kategoriUyarilari"]) == 1 and "ölüler" in s["kategoriUyarilari"][0]["metin"]
    assert s["konumDuzeyi"] == "sokak"
