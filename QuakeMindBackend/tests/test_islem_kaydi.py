"""Islem kaydi (J-165) ve kamera tavsiyesi.

Yalniz ilgili yonlendiriciler ayri bir SQLite dosyasiyla kurulur; gercek
veritabanina dokunulmaz. YOLO ve metin modeli kosmaz: sahteleriyle degistirilir.
"""
import base64
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

_GECICI = tempfile.mkdtemp(prefix="qm_islem_kaydi_")
os.environ["QUAKEMIND_SQLITE"] = str(Path(_GECICI) / "test.sqlite3")

import cekirdek as ck  # noqa: E402
import depo as depo_paketi  # noqa: E402
import kimlik  # noqa: E402
import islem_kaydi  # noqa: E402
from uclar import bildirim, gorev, ihbar, islem, kamera, metin, oturum, sozlesme  # noqa: E402

SIFRE = "test-sifresi-123"


@pytest.fixture(scope="module")
def ortam():
    depo_paketi._depo = None  # bu modul kendi dosyasini acsin
    d = depo_paketi.depo_ac()
    d._yaz("INSERT OR IGNORE INTO ekipler (id, ad, guncellendi, kisi_sayisi) VALUES ('EKP-K', 'Kayit ekibi', 0, 4)")
    hesap = {}
    for ad, rol in [("koordinator", "koordinator"), ("saha", "saha"), ("afetzede", "afetzede")]:
        k = kimlik.kullanici_kaydet(f"{ad}@kayit.local", ad.capitalize(), SIFRE)
        d.rol_ata(k["id"], rol)
        hesap[ad] = d.kullanici_id(k["id"])
    d.ekip_uyelerini_ayarla("EKP-K", [hesap["saha"]["id"]])
    hesap["saha"] = d.kullanici_id(hesap["saha"]["id"])
    uygulama = FastAPI()
    for m in (bildirim, gorev, ihbar, islem, kamera, metin, oturum, sozlesme):
        uygulama.include_router(m.yonlendirici)
    return TestClient(uygulama), hesap, d


def _baslik(hesap: dict) -> dict:
    return {"Authorization": f"Bearer {kimlik.erisim_jetonu_uret(hesap)}"}


def _son(istemci, h, tur):
    y = istemci.get("/api/islem-kayitlari", params={"tur": tur, "sinir": 1}, headers=_baslik(h["koordinator"]))
    assert y.status_code == 200, y.text
    kayitlar = y.json()["kayitlar"]
    assert kayitlar, f"{tur} kaydi yok"
    return kayitlar[0]


def test_kayit_degistirilemez_ve_silinemez(ortam):
    _, h, d = ortam
    no = d.islem_kaydi_ekle(h["koordinator"], "sos_kapatildi", "deneme")
    with pytest.raises(sqlite3.DatabaseError):
        d._yaz("UPDATE islem_kayitlari SET ozet = 'degisti' WHERE id = ?", (no,))
    with pytest.raises(sqlite3.DatabaseError):
        d._yaz("DELETE FROM islem_kayitlari WHERE id = ?", (no,))


def test_kaydi_yalniz_koordinasyon_okur(ortam):
    istemci, h, _ = ortam
    assert istemci.get("/api/islem-kayitlari").status_code == 401
    for rol in ("saha", "afetzede"):
        assert istemci.get("/api/islem-kayitlari", headers=_baslik(h[rol])).status_code == 403
    assert istemci.get("/api/islem-kayitlari", params={"tur": "uydurma"},
                       headers=_baslik(h["koordinator"])).status_code == 422


def test_sevk_gorev_ve_sos_kapatma_kaydedilir(ortam):
    istemci, h, d = ortam
    sos_id = d.sos_ekle(lon=36.16, lat=36.2, oncelik="kritik", mahalle="Test Mah.")["id"]
    y = istemci.post("/api/gorevler", json={"hedefTur": "sos", "hedefId": sos_id, "ekipId": "EKP-K"},
                     headers=_baslik(h["koordinator"]))
    assert y.status_code == 201, y.text
    k = _son(istemci, h, "sevk")
    assert k["hedefId"] == sos_id and k["yapanAd"] == "Koordinator" and "Kayit ekibi" in k["ozet"]

    g_id = y.json()["id"]
    assert istemci.post(f"/api/gorevler/{g_id}/durum", json={"durum": "yolda"},
                        headers=_baslik(h["saha"])).status_code == 200
    k = _son(istemci, h, "gorev_durumu")
    assert k["yapanRol"] == "saha" and "yola çıktı" in k["ozet"]

    assert istemci.post(f"/api/sos/{sos_id}/kapat", headers=_baslik(h["saha"])).status_code == 200
    k = _son(istemci, h, "sos_kapatildi")
    assert k["yapanRol"] == "saha" and "Test Mah." in k["ozet"] and k["ayrinti"]["bitenGorevler"] == [g_id]


def test_ekip_tanimi_ve_uyeler_kaydedilir(ortam):
    istemci, h, _ = ortam
    y = istemci.post("/api/ekipler", json={"ad": "Yeni ekip", "kurum": "AFAD", "kisiSayisi": 3},
                     headers=_baslik(h["koordinator"]))
    assert y.status_code == 201, y.text
    ekip_id = y.json()["id"]
    assert _son(istemci, h, "ekip_eklendi")["hedefId"] == ekip_id

    y = istemci.put(f"/api/ekipler/{ekip_id}", json={"ad": "Yeni ekip", "kurum": "AFAD", "kisiSayisi": 5},
                    headers=_baslik(h["koordinator"]))
    assert y.status_code == 200, y.text
    k = _son(istemci, h, "ekip_degisti")
    assert k["ayrinti"]["degisen"] == {"kisi_sayisi": [3, 5]} and "kişi sayısı 3 → 5" in k["ozet"]

    y = istemci.put(f"/api/ekipler/{ekip_id}/uyeler", json={"kullaniciIdleri": [h["saha"]["id"]]},
                    headers=_baslik(h["koordinator"]))
    assert y.status_code == 200, y.text
    k = _son(istemci, h, "ekip_uyeleri")
    assert k["ayrinti"]["eklenen"] == [h["saha"]["id"]] and "Saha" in k["ozet"]


def test_ihbar_ve_bildirim_kaydedilir(ortam):
    istemci, h, d = ortam
    ihbar_id = d.ihbar_ekle(tur="ihtiyac", lon=36.16, lat=36.2, mahalle="Su Mah.")["id"]
    assert istemci.post(f"/api/ihbarlar/{ihbar_id}/durum", json={"durum": "kapandi"},
                        headers=_baslik(h["koordinator"])).status_code == 200
    k = _son(istemci, h, "ihbar_durumu")
    assert k["hedefId"] == ihbar_id and "İhtiyaç ihbarı kapatıldı" in k["ozet"]

    y = istemci.post("/api/bildirimler", json={"baslik": "Artçı uyarısı", "metin": "Binalara girmeyin.", "onem": "uyari"},
                     headers=_baslik(h["koordinator"]))
    assert y.status_code == 201, y.text
    assert "Artçı uyarısı" in _son(istemci, h, "bildirim_yayinlandi")["ozet"]
    assert istemci.post(f"/api/bildirimler/{y.json()['id']}/kaldir",
                        headers=_baslik(h["koordinator"])).status_code == 200
    assert _son(istemci, h, "bildirim_geri_cekildi")["hedefId"] == y.json()["id"]


def _jpeg_b64() -> str:
    ok, buf = cv2.imencode(".jpg", np.full((60, 80, 3), 200, np.uint8))
    assert ok
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()


def test_kamera_analizi_kaydedilir_ve_catlak_bosaltma_demez(ortam, monkeypatch):
    istemci, h, _ = ortam
    sahte = [{"label": "Çatlak", "sinif": "crack", "confidence": 75.0, "model": "catlak.pt",
              "box": [1.0, 2.0, 70.0, 50.0], "siddet": "belirsiz", "severity": "UNRATED"}]
    monkeypatch.setattr(kamera, "yolo_tespit", lambda img, t: (list(sahte), ["catlak.pt (Çatlak Tespiti)"], False))
    y = istemci.post("/api/camera/analyze", json={"modelType": "catlak", "imageBase64": _jpeg_b64()},
                     headers=_baslik(h["saha"]))
    assert y.status_code == 200, y.text
    govde = y.json()
    assert govde["status"] == "CRACK_FOUND"
    assert "boşalt" not in govde["advice"].lower()
    assert (govde["imageWidth"], govde["imageHeight"]) == (80, 60)
    k = _son(istemci, h, "kamera_analizi")
    assert k["yapanRol"] == "saha" and "1 çatlak" in k["ozet"] and k["ayrinti"]["en"] == 80
    assert "imageBase64" not in str(k["ayrinti"])  # fotograf saklanmaz


def test_kamera_tavsiyesi_siddeti_yalniz_bina_sinifindan_alir():
    assert kamera.kamera_tavsiyesi([])[0] == "NO_DETECTION"
    assert kamera.kamera_tavsiyesi([{"siddet": "belirsiz"}])[0] == "CRACK_FOUND"
    assert kamera.kamera_tavsiyesi([{"siddet": "yok"}])[0] == "SAFE_SURFACE"
    durum, metin_ = kamera.kamera_tavsiyesi([{"siddet": "belirsiz"}, {"siddet": "agir"}])
    assert durum == "CRITICAL_EVACUATE" and "uzman" in metin_


def test_metin_analizi_kaydedilir(ortam, monkeypatch):
    istemci, h, _ = ortam
    from metin_analizi import isci

    def sahte_coz(metin):
        return {"ilgili": True, "kategori": "Enkaz Bildirimi", "aciliyet": 5, "guven": 0.9,
                "kategoriKaynagi": "model", "konum": [36.2, 36.15], "konumMetin": "Test Mah., Hatay",
                "konumDuzeyi": "mahalle", "sinyaller": [{"sinyal": "enkaz_altinda"}], "sureMs": 30}

    monkeypatch.setattr(isci, "coz", sahte_coz)
    y = istemci.post("/api/nlp/analyze", json={"text": "Test Mahallesinde enkaz altında kalanlar var"},
                     headers=_baslik(h["koordinator"]))
    assert y.status_code == 200, y.text
    k = _son(istemci, h, "metin_analizi")
    assert "Enkaz" in k["ozet"] and "(mahalle)" in k["ozet"]
    assert k["ayrinti"]["metin"].startswith("Test Mahallesinde") and k["ayrinti"]["sinyaller"] == ["enkaz_altinda"]


def test_sayfalama(ortam):
    istemci, h, _ = ortam
    ilk = istemci.get("/api/islem-kayitlari", params={"sinir": 2}, headers=_baslik(h["koordinator"])).json()
    assert len(ilk["kayitlar"]) == 2 and ilk["devami"]
    sonraki = istemci.get("/api/islem-kayitlari", params={"sinir": 2, "once": ilk["kayitlar"][-1]["id"]},
                          headers=_baslik(h["koordinator"])).json()
    assert all(k["id"] < ilk["kayitlar"][-1]["id"] for k in sonraki["kayitlar"])


def test_hasar_analizi_ve_tatbikat_bitisi_kaydedilir(ortam):
    istemci, h, _ = ortam
    yapan = {"id": h["koordinator"]["id"], "ad_soyad": "Koordinator", "rol": "koordinator"}
    sonuc = {"city": "Hatay", "blockedRoads": 8, "openRoads": 120, "damageRate": 0.0412,
             "imageryLabel": "Drone ortofoto", "imageryZoom": 18, "model": {"ad": "unet-mitb4"}}
    ck._analiz_sonucunu_kaydet("an-1", {"onek": "hasar_analizi", "yapan": yapan}, None, sonuc)
    k = _son(istemci, h, "hasar_analizi_bitti")
    assert k["hedefId"] == "an-1" and "8 kapalı" in k["ozet"] and k["ayrinti"]["model"] == "unet-mitb4"
    ck._analiz_sonucunu_kaydet("sim_1", {"onek": "tatbikat", "yapan": yapan}, "çıkarım çöktü", None)
    k = _son(istemci, h, "tatbikat_hata")
    assert k["hedefId"] == "sim_1" and "çıkarım çöktü" in k["ozet"]


def test_hash_zinciri_degisikligi_yakalar(ortam):
    istemci, h, d = ortam
    y = istemci.get("/api/islem-kayitlari/dogrula", headers=_baslik(h["koordinator"]))
    assert y.status_code == 200 and y.json()["saglam"] and y.json()["dogrulanan"] > 0
    assert istemci.get("/api/islem-kayitlari/dogrula", headers=_baslik(h["saha"])).status_code == 403
    # Dosyaya dogrudan erisen biri tetikleyiciyi kaldirip bir satiri degistirirse zincir bozulur.
    d._yaz("DROP TRIGGER islem_kaydi_degismez")
    d._yaz("UPDATE islem_kayitlari SET ozet = 'kurcalandi' WHERE id = 2")
    sonuc = d.islem_zinciri_dogrula()
    assert not sonuc["saglam"] and sonuc["bozukId"] == 2


def test_konum_gecmisi_tutulur(ortam):
    # Kendi ekibi ve saha hesabi: baska testler ortak saha hesabini ekipten ekibe tasiyor.
    istemci, _, _ = ortam
    d = depo_paketi.aktif_depo()
    d._yaz("INSERT OR IGNORE INTO ekipler (id, ad, guncellendi) VALUES ('EKP-IZ', 'Iz ekibi', 0)")
    k = kimlik.kullanici_kaydet("iz-saha@kayit.local", "Iz Saha", SIFRE)
    d.rol_ata(k["id"], "saha")
    d.ekip_uyelerini_ayarla("EKP-IZ", [k["id"]])
    saha = d.kullanici_id(k["id"])
    for lon in (36.10, 36.11):
        assert istemci.post("/api/ekipler/EKP-IZ/konum", json={"lon": lon, "lat": 36.2},
                            headers=_baslik(saha)).status_code == 200
    iz = d.ekip_konum_gecmisi("EKP-IZ")
    assert [round(n["lon"], 2) for n in iz] == [36.10, 36.11]
    assert iz[-1]["gonderen_rol"] == "saha" and iz[-1]["gonderen_ad"] == "Iz Saha"



# --- J-166 ------------------------------------------------------------------

def _hesap(d, ad, rol):
    k = kimlik.kullanici_kaydet(f"{ad}@j166.local", ad, SIFRE)
    d.rol_ata(k["id"], rol)
    return d.kullanici_id(k["id"])


def test_giris_gecmisi(ortam):
    istemci, h, _ = ortam
    d = depo_paketi.aktif_depo()
    saha = _hesap(d, "girisci", "saha")
    giris = lambda eposta, sifre, kapi: istemci.post(  # noqa: E731
        "/api/oturum/giris", json={"eposta": eposta, "sifre": sifre, "kapi": kapi},
        headers={"User-Agent": "deneme-tarayici/1.0"})

    assert giris("girisci@j166.local", "yanlis-sifre-1", "ekip").status_code == 401
    k = _son(istemci, h, "giris_basarisiz")
    assert k["hedefId"] == saha["id"] and k["ayrinti"]["neden"] == "şifre hatalı"
    assert k["ayrinti"]["tarayici"] == "deneme-tarayici/1.0" and "sifre" not in str(k["ayrinti"]).replace("şifre", "")

    assert giris("yok-boyle@j166.local", "herhangi-sifre", "ekip").status_code == 401
    k = _son(istemci, h, "giris_basarisiz")
    assert k["yapanId"] is None and k["ayrinti"]["neden"] == "böyle bir hesap yok"
    assert k["ayrinti"]["eposta"] == "yok-boyle@j166.local"

    assert giris("girisci@j166.local", SIFRE, "koordinasyon").status_code == 403
    assert _son(istemci, h, "giris_basarisiz")["ayrinti"]["neden"] == "yanlış giriş kapısı"

    y = giris("girisci@j166.local", SIFRE, "ekip")
    assert y.status_code == 200, y.text
    k = _son(istemci, h, "giris_basarili")
    assert k["yapanId"] == saha["id"] and k["ayrinti"]["kapi"] == "ekip" and k["ayrinti"]["ip"]

    assert istemci.post("/api/oturum/cikis").status_code == 200  # cerez TestClient'ta
    assert _son(istemci, h, "cikis")["yapanId"] == saha["id"]

    d.askiya_al(saha["id"], True)
    assert giris("girisci@j166.local", SIFRE, "ekip").status_code == 403
    assert _son(istemci, h, "giris_basarisiz")["ayrinti"]["neden"] == "hesap askıda"


def test_kayit_olan_afetzede_kaydedilir(ortam):
    istemci, h, _ = ortam
    y = istemci.post("/api/oturum/kayit", json={"eposta": "yeni-afet@j166.local", "adSoyad": "Yeni Afet",
                                                 "sifre": SIFRE})
    assert y.status_code == 201, y.text
    k = _son(istemci, h, "kayit_oldu")
    assert k["yapanRol"] == "afetzede" and "yeni-afet@j166.local" in k["ozet"]


def test_goruntuleme_on_dakikada_bir_yazilir(ortam, monkeypatch):
    istemci, h, _ = ortam
    monkeypatch.setattr(islem_kaydi, "_son_goruntuleme", {})
    sorgu = {"tur": "goruntuleme", "sinir": 500}
    once = len(istemci.get("/api/islem-kayitlari", params=sorgu, headers=_baslik(h["koordinator"])).json()["kayitlar"])
    for _ in range(3):
        assert istemci.get("/api/sos", headers=_baslik(h["koordinator"])).status_code == 200
    kayitlar = istemci.get("/api/islem-kayitlari", params=sorgu, headers=_baslik(h["koordinator"])).json()["kayitlar"]
    sos = [k for k in kayitlar if k["ayrinti"]["kaynak"] == "sos_listesi" and k["yapanId"] == h["koordinator"]["id"]]
    assert len(sos) == 1  # uc kez acildi, bir kez yazildi
    # Islem kaydini okumak da yazilir (ilk okuma), sonraki okumalar 10 dk icinde yazilmaz.
    assert len(kayitlar) - once >= 1
    # Afetzedenin kendi kaydina bakmasi yazilmaz.
    assert istemci.get("/api/sos", headers=_baslik(h["afetzede"])).status_code == 200
    kayitlar2 = istemci.get("/api/islem-kayitlari", params=sorgu, headers=_baslik(h["koordinator"])).json()["kayitlar"]
    assert not [k for k in kayitlar2 if k["yapanRol"] == "afetzede"]


def test_konum_paylasimi_basladi_bir_kez_ve_gecmis_ucu(ortam):
    istemci, h, _ = ortam
    d = depo_paketi.aktif_depo()
    d._yaz("INSERT OR IGNORE INTO ekipler (id, ad, guncellendi) VALUES ('EKP-PAY', 'Paylasim ekibi', 0)")
    saha = _hesap(d, "paylasimci", "saha")
    d.ekip_uyelerini_ayarla("EKP-PAY", [saha["id"]])
    saha = d.kullanici_id(saha["id"])
    for lon in (36.10, 36.11, 36.12):
        assert istemci.post("/api/ekipler/EKP-PAY/konum", json={"lon": lon, "lat": 36.2, "dogrulukM": 12},
                            headers=_baslik(saha)).status_code == 200
    y = istemci.get("/api/islem-kayitlari", params={"tur": "konum_paylasimi_basladi", "sinir": 50},
                    headers=_baslik(h["koordinator"]))
    assert len([k for k in y.json()["kayitlar"] if k["hedefId"] == "EKP-PAY"]) == 1
    g = istemci.get("/api/ekipler/EKP-PAY/konum-gecmisi", headers=_baslik(h["koordinator"]))
    assert g.status_code == 200 and [round(n["lon"], 2) for n in g.json()] == [36.10, 36.11, 36.12]
    assert g.json()[0]["dogrulukM"] == 12 and g.json()[0]["gonderenAd"] == "paylasimci"
    assert istemci.get("/api/ekipler/EKP-PAY/konum-gecmisi", headers=_baslik(saha)).status_code == 403


def test_konum_gecmisi_silinemez(ortam):
    d = depo_paketi.aktif_depo()
    d.ekip_konum("EKP-K", 36.0, 36.0)
    with pytest.raises(sqlite3.DatabaseError):
        d._yaz("DELETE FROM ekip_konum_gecmisi")


def test_artimli_dogrulama_kuyruktan_silmeyi_yakalar(tmp_path):
    from depo.sqlite_surucu import SqliteDepo

    d = SqliteDepo(str(tmp_path / "zincir.sqlite3"))
    u = {"id": "u", "ad_soyad": "A", "rol": "koordinator"}
    for i in range(5):
        d.islem_kaydi_ekle(u, "sos_kapatildi", f"kayit {i}")
    tam = d.islem_zinciri_dogrula()
    assert tam["saglam"] and tam["dogrulanan"] == 5 and tam["sonId"] == 5
    d.zincir_denetimi_ekle(u, "tam", tam, 1)
    d.islem_kaydi_ekle(u, "sos_kapatildi", "kayit 5")
    nokta = d.son_saglam_denetim()
    art = d.islem_zinciri_dogrula((nokta["son_id"], nokta["son_hash"]))
    assert art["saglam"] and art["dogrulanan"] == 1
    # Dosyaya erisen biri tetikleyiciyi kaldirip denetim noktasini silerse artimli da yakalar.
    d._yaz("DROP TRIGGER islem_kaydi_silinmez")
    d._yaz("DELETE FROM islem_kayitlari WHERE id >= 5")
    art = d.islem_zinciri_dogrula((nokta["son_id"], nokta["son_hash"]))
    assert not art["saglam"] and art["bozukId"] == 5
    with pytest.raises(sqlite3.DatabaseError):
        d._yaz("DELETE FROM islem_zinciri_denetimleri")


def test_kamera_bilinmeyen_model_ve_eksik_model(ortam, monkeypatch):
    """J-167 S-3: bilinmeyen modelType 422; model dosyasi yoksa 'tespit yok' degil 503."""
    istemci, h, _ = ortam
    y = istemci.post("/api/camera/analyze", json={"modelType": "ikisi", "imageBase64": _jpeg_b64()},
                     headers=_baslik(h["koordinator"]))
    assert y.status_code == 422
    monkeypatch.setattr(kamera, "yolo_tespit", lambda img, t: ([], [], False))
    y = istemci.post("/api/camera/analyze", json={"modelType": "hybrid", "imageBase64": _jpeg_b64()},
                     headers=_baslik(h["koordinator"]))
    assert y.status_code == 503
    y = istemci.post("/api/camera/analyze", json={"modelType": "hybrid", "imageBase64": "bozuk"},
                     headers=_baslik(h["koordinator"]))
    assert y.status_code == 422
