"""Rol yonetimi kurallari (J-155): `/api/oturum/kullanicilar` ve `/api/oturum/rol`.

Yalniz oturum yonlendiricisi ayri bir SQLite dosyasiyla kurulur; fastapi_app
(ve modeller) yuklenmez, gercek veritabanina dokunulmaz.
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

_GECICI = tempfile.mkdtemp(prefix="qm_rol_testi_")
os.environ["QUAKEMIND_SQLITE"] = str(Path(_GECICI) / "test.sqlite3")

import depo as depo_paketi  # noqa: E402
import kimlik  # noqa: E402
from uclar import oturum  # noqa: E402

SIFRE = "test-sifresi-123"


@pytest.fixture(scope="module")
def ortam():
    depo_paketi._depo = None  # bu modul kendi dosyasini acsin
    d = depo_paketi.depo_ac()
    hesap = {}
    for ad, rol in [("yonetici", "yonetici"), ("yonetici2", "yonetici"),
                    ("koordinator", "koordinator"), ("saha", "saha"),
                    ("afetzede", "afetzede"), ("afetzede2", "afetzede")]:
        k = kimlik.kullanici_kaydet(f"{ad}@test.local", ad, SIFRE)
        d.rol_ata(k["id"], rol)
        hesap[ad] = d.kullanici_id(k["id"])
    uygulama = FastAPI()
    uygulama.include_router(oturum.yonlendirici)
    return TestClient(uygulama), hesap, d


def _baslik(hesap: dict) -> dict:
    return {"Authorization": f"Bearer {kimlik.erisim_jetonu_uret(hesap)}"}


def _rol(istemci, veren, hedef, rol):
    return istemci.post("/api/oturum/rol", headers=_baslik(veren),
                        json={"kullaniciId": hedef["id"], "rol": rol})


def test_liste_koordinasyona_acik_digerlerine_kapali(ortam):
    istemci, h, _ = ortam
    y = istemci.get("/api/oturum/kullanicilar", headers=_baslik(h["koordinator"]))
    assert y.status_code == 200
    govde = y.json()
    assert govde["verebilecegiRoller"] == ["afetzede", "saha"]
    # Sifre ya da ozeti hicbir alanda donmez (sifreDegismeli yalniz bayrak).
    gizli = {"sifre", "sifre_ozeti", "sifreOzeti", "geciciSifre"}
    assert all(not (gizli & set(k)) for k in govde["kullanicilar"])
    assert "$2" not in y.text  # bcrypt ozeti metinde de yok
    for rol in ("saha", "afetzede"):
        assert istemci.get("/api/oturum/kullanicilar", headers=_baslik(h[rol])).status_code == 403
    assert istemci.get("/api/oturum/kullanicilar").status_code == 401


def test_koordinator_afetzedeyi_saha_yapar_ve_geri_alir(ortam):
    istemci, h, d = ortam
    y = _rol(istemci, h["koordinator"], h["afetzede"], "saha")
    assert y.status_code == 200 and y.json()["oncekiRol"] == "afetzede"
    assert d.kullanici_id(h["afetzede"]["id"])["rol"] == "saha"
    # ekibe bagla, sonra afetzedeye dusur: ekipten de cikmali
    d._yaz("INSERT OR IGNORE INTO ekipler (id, ad, guncellendi) VALUES ('EKP-T', 'Test ekibi', 0)")
    d.ekip_uyelerini_ayarla("EKP-T", [h["afetzede"]["id"]])
    assert d.kullanici_id(h["afetzede"]["id"])["ekip_id"] == "EKP-T"
    assert _rol(istemci, h["koordinator"], h["afetzede"], "afetzede").status_code == 200
    k = d.kullanici_id(h["afetzede"]["id"])
    assert k["rol"] == "afetzede" and k["ekip_id"] is None


def test_koordinator_koordinasyon_rolu_veremez_ve_dokunamaz(ortam):
    istemci, h, _ = ortam
    assert _rol(istemci, h["koordinator"], h["afetzede2"], "koordinator").status_code == 403
    assert _rol(istemci, h["koordinator"], h["afetzede2"], "yonetici").status_code == 403
    assert _rol(istemci, h["koordinator"], h["yonetici"], "afetzede").status_code == 403


def test_saha_ve_afetzede_rol_veremez(ortam):
    istemci, h, _ = ortam
    assert _rol(istemci, h["saha"], h["afetzede2"], "saha").status_code == 403
    assert _rol(istemci, h["afetzede2"], h["afetzede2"], "yonetici").status_code == 403


def test_kimse_kendi_rolunu_degistiremez(ortam):
    istemci, h, _ = ortam
    assert _rol(istemci, h["yonetici"], h["yonetici"], "afetzede").status_code == 409
    assert _rol(istemci, h["koordinator"], h["koordinator"], "saha").status_code == 409


def test_yonetici_her_rolu_verir_ve_oturumlari_duser(ortam):
    istemci, h, d = ortam
    d.oturum_ac(h["afetzede2"]["id"], "test-ozet", 3600)
    assert d.oturum_bul("test-ozet") is not None
    y = _rol(istemci, h["yonetici"], h["afetzede2"], "koordinator")
    assert y.status_code == 200 and y.json()["durum"] == "guncellendi"
    assert d.oturum_bul("test-ozet") is None
    assert _rol(istemci, h["yonetici"], h["yonetici2"], "koordinator").status_code == 200


def test_ayni_rol_degismedi_doner_bilinmeyen_rol_422(ortam):
    istemci, h, _ = ortam
    y = _rol(istemci, h["yonetici"], h["saha"], "saha")
    assert y.status_code == 200 and y.json()["durum"] == "degismedi"
    assert _rol(istemci, h["yonetici"], h["saha"], "kral").status_code == 422
    yok = {"id": "yok"}
    assert _rol(istemci, h["yonetici"], yok, "saha").status_code == 404


# ---- giris kapisi ve ekip hesabi acma (J-156) ------------------------------

def _giris(istemci, eposta, sifre, kapi=None):
    govde = {"eposta": eposta, "sifre": sifre}
    if kapi is not None:
        govde["kapi"] = kapi
    return istemci.post("/api/oturum/giris", json=govde)


def test_giris_kapisi_rolle_eslesmeli(ortam):
    istemci, h, _ = ortam
    assert _giris(istemci, "saha@test.local", SIFRE, "ekip").status_code == 200
    yanlis = _giris(istemci, "saha@test.local", SIFRE, "koordinasyon")
    assert yanlis.status_code == 403 and "Saha ekibi" in yanlis.json()["detail"]
    assert _giris(istemci, "koordinator@test.local", SIFRE, "koordinasyon").status_code == 200
    assert _giris(istemci, "koordinator@test.local", SIFRE, "afetzede").status_code == 403
    # yanlis sifrede kapi ne olursa olsun tek mesaj (hesap var mi sizmasin)
    assert _giris(istemci, "saha@test.local", "yanlis-sifre", "koordinasyon").status_code == 401
    # kapisiz giris (mobil istemci) eskisi gibi
    assert _giris(istemci, "saha@test.local", SIFRE).status_code == 200
    assert _giris(istemci, "saha@test.local", SIFRE, "kral").status_code == 422


def test_kayit_her_zaman_afetzede_ve_giris_isler(ortam):
    istemci, _, d = ortam
    y = istemci.post("/api/oturum/kayit", json={"eposta": "yeni@test.local", "adSoyad": "Yeni",
                                                "sifre": SIFRE, "rol": "yonetici"})
    assert y.status_code == 201 and y.json()["kullanici"]["rol"] == "afetzede"
    assert d.kullanici_eposta("yeni@test.local")["son_giris"] is not None


def test_koordinator_saha_hesabi_acar_ekibe_baglar(ortam):
    istemci, h, d = ortam
    d._yaz("INSERT OR IGNORE INTO ekipler (id, ad, guncellendi) VALUES ('EKP-H', 'Hesap ekibi', 0)")
    y = istemci.post("/api/oturum/kullanicilar", headers=_baslik(h["koordinator"]),
                     json={"eposta": "Uye1@Test.local", "adSoyad": "Üye Bir", "rol": "saha",
                           "ekipId": "EKP-H"})
    assert y.status_code == 201
    govde = y.json()
    sifre = govde["geciciSifre"]
    assert len(sifre) == 12 and govde["kullanici"]["ekipId"] == "EKP-H"
    assert govde["kullanici"]["eposta"] == "uye1@test.local"
    assert _giris(istemci, "uye1@test.local", sifre, "ekip").status_code == 200
    # ayni e-posta ikinci kez acilmaz
    assert istemci.post("/api/oturum/kullanicilar", headers=_baslik(h["koordinator"]),
                        json={"eposta": "uye1@test.local", "adSoyad": "Başka Kişi", "rol": "saha"}).status_code == 409


def test_hesap_acma_yetkileri(ortam):
    istemci, h, _ = ortam
    def ac(veren, rol, eposta, **ek):
        return istemci.post("/api/oturum/kullanicilar", headers=_baslik(veren),
                            json={"eposta": eposta, "adSoyad": "Ad Soyad", "rol": rol, **ek})
    assert ac(h["koordinator"], "koordinator", "k2@test.local").status_code == 403
    assert ac(h["koordinator"], "afetzede", "a9@test.local").status_code == 422
    assert ac(h["saha"], "saha", "s9@test.local").status_code == 403
    assert ac(h["yonetici"], "koordinator", "k3@test.local").status_code == 201
    assert ac(h["yonetici"], "koordinator", "k4@test.local", ekipId="EKP-H").status_code == 422
    assert ac(h["koordinator"], "saha", "s10@test.local", ekipId="yok").status_code == 404


def test_sifre_sifirlama(ortam):
    istemci, h, d = ortam
    hedef = d.kullanici_eposta("saha@test.local")
    d.oturum_ac(hedef["id"], "sifirlama-ozet", 3600)
    y = istemci.post(f"/api/oturum/kullanicilar/{hedef['id']}/sifre", headers=_baslik(h["koordinator"]))
    assert y.status_code == 200
    yeni = y.json()["geciciSifre"]
    assert d.oturum_bul("sifirlama-ozet") is None
    assert _giris(istemci, "saha@test.local", SIFRE, "ekip").status_code == 401
    assert _giris(istemci, "saha@test.local", yeni, "ekip").status_code == 200
    # koordinator yoneticinin sifresine dokunamaz, kimse kendininkine buradan dokunamaz
    assert istemci.post(f"/api/oturum/kullanicilar/{h['yonetici']['id']}/sifre",
                        headers=_baslik(h["koordinator"])).status_code == 403
    assert istemci.post(f"/api/oturum/kullanicilar/{h['koordinator']['id']}/sifre",
                        headers=_baslik(h["koordinator"])).status_code == 409


# ---- aski, ilk giriste sifre, kayit defteri, tek kaydet (J-157) -----------

def _hesap_ac(istemci, veren, eposta, ekip=None):
    govde = {"eposta": eposta, "adSoyad": "Geçici Kişi", "rol": "saha"}
    if ekip:
        govde["ekipId"] = ekip
    y = istemci.post("/api/oturum/kullanicilar", headers=_baslik(veren), json=govde)
    assert y.status_code == 201, y.text
    return y.json()


def test_gecici_sifreyle_giren_once_sifre_degistirir(ortam):
    istemci, h, d = ortam
    acilan = _hesap_ac(istemci, h["koordinator"], "ilk@test.local")
    y = _giris(istemci, "ilk@test.local", acilan["geciciSifre"], "ekip")
    assert y.status_code == 200 and y.json()["kullanici"]["sifreDegismeli"] is True
    jeton = {"Authorization": f"Bearer {y.json()['erisimJetonu']}"}
    # /ben serbest, korunan uclar kapali
    assert istemci.get("/api/oturum/ben", headers=jeton).status_code == 200
    kapali = istemci.get("/api/oturum/kullanicilar", headers=jeton)
    assert kapali.status_code == 403 and kapali.json()["detail"].startswith("SIFRE_DEGISMELI")
    # yanlis eski sifre, kisa ve ayni sifre reddedilir
    assert istemci.post("/api/oturum/sifre", headers=jeton,
                        json={"eskiSifre": "yanlis", "yeniSifre": "yeni-sifre-123"}).status_code == 400
    assert istemci.post("/api/oturum/sifre", headers=jeton,
                        json={"eskiSifre": acilan["geciciSifre"], "yeniSifre": "kisa"}).status_code == 422
    assert istemci.post("/api/oturum/sifre", headers=jeton,
                        json={"eskiSifre": acilan["geciciSifre"],
                              "yeniSifre": acilan["geciciSifre"]}).status_code == 422
    t = istemci.post("/api/oturum/sifre", headers=jeton,
                     json={"eskiSifre": acilan["geciciSifre"], "yeniSifre": "yeni-sifre-123"})
    assert t.status_code == 200 and t.json()["kullanici"]["sifreDegismeli"] is False
    assert _giris(istemci, "ilk@test.local", "yeni-sifre-123", "ekip").json()["kullanici"]["sifreDegismeli"] is False
    islemler = [k["islem"] for k in d.hesap_kayitlari(acilan["kullanici"]["id"])]
    assert islemler[:2] == ["sifre-degistirildi", "hesap-acildi"]


def test_askidaki_hesap_giremez_ve_jetonu_duser(ortam):
    istemci, h, d = ortam
    hedef = d.kullanici_eposta("afetzede2@test.local")
    # afetzede2 baska testte koordinator yapildi; yonetici askiya alir
    jeton = {"Authorization": f"Bearer {kimlik.erisim_jetonu_uret(hedef)}"}
    y = istemci.patch(f"/api/oturum/kullanicilar/{hedef['id']}", headers=_baslik(h["yonetici"]),
                      json={"askida": True})
    assert y.status_code == 200 and y.json()["kullanici"]["askida"] is True
    assert _giris(istemci, "afetzede2@test.local", SIFRE).status_code == 403
    assert istemci.get("/api/oturum/ben", headers=jeton).status_code == 401
    y = istemci.patch(f"/api/oturum/kullanicilar/{hedef['id']}", headers=_baslik(h["yonetici"]),
                      json={"askida": False})
    assert y.status_code == 200
    assert _giris(istemci, "afetzede2@test.local", SIFRE).status_code == 200
    islemler = [k["islem"] for k in d.hesap_kayitlari(hedef["id"])][:2]
    assert islemler == ["etkinlestirildi", "askiya-alindi"]


def test_tek_kaydet_ekip_ata_ve_cikar(ortam):
    istemci, h, d = ortam
    d._yaz("INSERT OR IGNORE INTO ekipler (id, ad, guncellendi) VALUES ('EKP-K', 'Kaydet ekibi', 0)")
    acilan = _hesap_ac(istemci, h["koordinator"], "kaydet@test.local")
    kid = acilan["kullanici"]["id"]
    assert acilan["kullanici"]["ekipId"] is None
    y = istemci.patch(f"/api/oturum/kullanicilar/{kid}", headers=_baslik(h["koordinator"]),
                      json={"ekipId": "EKP-K", "adSoyad": "Kaydet Kişi"})
    assert y.status_code == 200
    assert y.json()["kullanici"]["ekipId"] == "EKP-K" and sorted(y.json()["degisen"]) == ["ad", "ekip"]
    # gonderilmeyen alan degismez
    y = istemci.patch(f"/api/oturum/kullanicilar/{kid}", headers=_baslik(h["koordinator"]), json={})
    assert y.json()["kullanici"]["ekipId"] == "EKP-K" and y.json()["degisen"] == []
    # acik null: ekipten cikar
    y = istemci.patch(f"/api/oturum/kullanicilar/{kid}", headers=_baslik(h["koordinator"]),
                      json={"ekipId": None})
    assert y.json()["kullanici"]["ekipId"] is None
    # afetzedeye ekip verilemez; reddedilince hicbir alan degismez
    y = istemci.patch(f"/api/oturum/kullanicilar/{kid}", headers=_baslik(h["koordinator"]),
                      json={"rol": "afetzede", "ekipId": "EKP-K", "adSoyad": "Degismemeli"})
    assert y.status_code == 422
    k = d.kullanici_id(kid)
    assert k["rol"] == "saha" and k["ad_soyad"] == "Kaydet Kişi"
    # koordinator koordinasyon rolu veremez
    assert istemci.patch(f"/api/oturum/kullanicilar/{kid}", headers=_baslik(h["koordinator"]),
                         json={"rol": "koordinator"}).status_code == 403


def test_kayit_defteri_ucu(ortam):
    istemci, h, _ = ortam
    y = istemci.get("/api/oturum/hesap-kayitlari", headers=_baslik(h["koordinator"]))
    assert y.status_code == 200 and len(y.json()) > 0
    ilk = y.json()[0]
    assert {"zaman", "yapanAd", "hedefAd", "islem"} <= set(ilk)
    assert istemci.get("/api/oturum/hesap-kayitlari", headers=_baslik(h["saha"])).status_code == 403
