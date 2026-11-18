"""Uctan uca akis senaryosu (J-174): afetzede -> koordinasyon -> saha -> afetzede.

Calisan bir API'ye (varsayilan 127.0.0.1:8001) gercek HTTP istekleriyle gider ve
dort hesabin canli akisini (SSE) ayni anda dinler: koordinator, saha, iki ayri
afetzede. Her adim GECTI / KALDI yazar. VERITABANI YAZAR: yalniz kopya
veritabaniyla calisan bir sunucuya karsi kosulmali.

Adimlar:
  1. SOS (afetzede A) -> koordinasyon listesinde ve akisinda; afetzede B goremez.
  2. Yazili ihbar: metin analizi -> metindeki adresle ihbar -> konsolda kategori,
     analiz ve hasar noktasi; afetzede A'nin kendi listesinde.
  3. Ihtiyac ihbari (erzak) ve fotograf ihbari (gercek deprem fotografi, YOLO).
  4. Koordinasyon "gordum" -> afetzede A akisinda ve listesinde "goruldu".
  5. Sevk: SOS'a ekip -> saha ekibim'de gorev, afetzede A akisinda gorev.
  6. Saha: yolda -> olay yerinde -> bitti -> SOS kapanir; afetzede A gorur.
  7. Yazili ihbara sevk ve bitis -> ihbar kapanir.
  8. Yetki: saha sevk edemez, afetzede baskasinin ihbarini goremez / durum
     degistiremez, afetzede B baskasinin ekibini/olayini akista almaz.

    python araclar_akis_senaryosu.py --api http://127.0.0.1:8001
"""
from __future__ import annotations

import argparse
import base64
import http.cookiejar
import json
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
FOTO = BASE / "apps/camera_detection/data/tatbikat_foto/antakya_city_center_after_7_8_magnitude_earthq.jpg"

SONUC: list[tuple[str, bool, str]] = []


def kontrol(ad: str, kosul: bool, ayrinti: str = "") -> bool:
    SONUC.append((ad, bool(kosul), ayrinti))
    print(("GECTI " if kosul else "KALDI ") + ad + (f"  [{ayrinti}]" if ayrinti and not kosul else ""), flush=True)
    return bool(kosul)


class Hesap:
    def __init__(self, api: str, ad: str):
        self.api, self.ad = api, ad
        self.cerez = http.cookiejar.CookieJar()
        self.acici = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cerez))
        self.jeton = None
        self.olaylar: list[dict] = []

    def istek(self, yontem, yol, govde=None):
        r = urllib.request.Request(self.api + yol, method=yontem,
                                   data=json.dumps(govde).encode() if govde is not None else None)
        r.add_header("Content-Type", "application/json")
        if self.jeton:
            r.add_header("Authorization", f"Bearer {self.jeton}")
        try:
            with self.acici.open(r, timeout=120) as y:
                ham = y.read()
                return y.status, (json.loads(ham) if ham else None)
        except urllib.error.HTTPError as h:
            ham = h.read().decode(errors="replace")
            try:
                return h.code, json.loads(ham)
            except ValueError:
                return h.code, ham

    def giris(self, eposta, sifre, kapi):
        k, g = self.istek("POST", "/api/oturum/giris", {"eposta": eposta, "sifre": sifre, "kapi": kapi})
        if k != 200:
            raise SystemExit(f"{self.ad} giris yapamadi: {k} {g}")
        self.jeton = g["erisimJetonu"]
        self.kullanici = g.get("kullanici") or {}
        return g

    def dinle(self):
        """Canli akis (SSE): cerezle baglanir, olaylari biriktirir."""
        def dongu():
            r = urllib.request.Request(self.api + "/api/live")
            try:
                with self.acici.open(r, timeout=600) as y:
                    for satir in y:
                        s = satir.decode().strip()
                        if s.startswith("data:"):
                            try:
                                self.olaylar.append(json.loads(s[5:].strip()))
                            except ValueError:
                                pass
            except Exception as e:  # akis kapaninca
                self.olaylar.append({"tip": "_hata", "metin": str(e)})
        threading.Thread(target=dongu, daemon=True).start()

    def olay_var(self, tip, kosul=lambda m: True, bekle=4.0) -> bool:
        son = time.time() + bekle
        while time.time() < son:
            if any(m.get("tip") == tip and kosul(m) for m in self.olaylar):
                return True
            time.sleep(0.1)
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://127.0.0.1:8001")
    a = ap.parse_args()
    api = a.api

    koord, saha, afz, afz2 = (Hesap(api, x) for x in ("koordinator", "saha", "afetzede-A", "afetzede-B"))
    koord.giris("demo@quakemind.local", "degistir1234", "koordinasyon")
    saha.giris("saha-demo@quakemind.local", "degistir1234", "ekip")
    for h, e in ((afz, "senaryo-a@akis.local"), (afz2, "senaryo-b@akis.local")):
        h.istek("POST", "/api/oturum/kayit", {"eposta": e, "adSoyad": h.ad, "sifre": "senaryo-sifresi-1"})
        h.giris(e, "senaryo-sifresi-1", "afetzede")
    for h in (koord, saha, afz, afz2):
        h.dinle()
    time.sleep(1.5)

    # Saha ekibi bossa senaryo ona is verir; acik gorevi varsa once kapatir.
    k, ekibim = saha.istek("GET", "/api/ekibim")
    kontrol("saha ekibim acilir", k == 200 and ekibim and ekibim.get("ekip"), str(k))
    ekip_id = ekibim["ekip"]["id"]
    if ekibim.get("gorev"):
        k, _ = saha.istek("POST", f"/api/gorevler/{ekibim['gorev']['id']}/durum",
                          {"durum": "tamamlandi", "olaySuruyor": True})
        kontrol("0 saha onceki gorevi bitirdi (olay suruyor)", k == 200, str(k))

    # --- 1. SOS --------------------------------------------------------------------
    k, sos = afz.istek("POST", "/api/sos", {"lon": 36.1612, "lat": 36.2021, "oncelik": "yuksek",
                                            "metin": "Bina çöktü, annem içeride", "kisiSayisi": 2})
    # Acik SOS varsa ayni kayit guncellenir ve 200 doner (S-2, tasarim geregi).
    kontrol("1 SOS gonderildi (201 yeni / 200 acik olan guncellendi)", k in (200, 201), f"{k} {sos}")
    sos_id = sos["id"]
    k, liste = koord.istek("GET", "/api/sos")
    kontrol("1 SOS koordinasyon listesinde", any(s["id"] == sos_id for s in liste))
    kontrol("1 SOS koordinasyon akisina dustu", koord.olay_var("yeni-sos", lambda m: m.get("id") == sos_id))
    kontrol("1 SOS saha akisina dustu (konumlu)", saha.olay_var("yeni-sos", lambda m: m.get("id") == sos_id))
    k, liste_b = afz2.istek("GET", "/api/sos")
    kontrol("1 afetzede B baskasinin SOS'unu listede goremez", not any(s["id"] == sos_id for s in (liste_b or [])))
    kontrol("1 afetzede B baskasinin SOS'unu akista almaz",
            not afz2.olay_var("yeni-sos", lambda m: m.get("id") == sos_id, bekle=1.0))
    k, kendi = afz.istek("GET", "/api/sos")
    kontrol("1 afetzede A kendi SOS'unu gorur", any(s["id"] == sos_id for s in kendi))

    # --- 2. yazili ihbar ----------------------------------------------------------------
    metin = "Armutlu Mahallesi 5. Sokak'ta bina çöktü, iki kişi enkaz altında, ses geliyor."
    k, an = afz.istek("POST", "/api/afetzede/metin-analiz", {"metin": metin})
    kontrol("2 metin analizi (200)", k == 200, f"{k} {an}")
    kontrol("2 kategori enkaz ve adres sokak duzeyinde",
            an.get("kategori") == "Enkaz Bildirimi" and an.get("konumDuzeyi") == "sokak",
            f"{an.get('kategori')} / {an.get('konumDuzeyi')}")
    k, ih = afz.istek("POST", "/api/ihbarlar", {"tur": "metin", "analizId": an["analizId"], "metin": metin,
                                                "konumKaynagi": "metin"})
    kontrol("2 yazili ihbar olustu (201)", k == 201, f"{k} {ih}")
    metin_id = ih["id"]
    kontrol("2 ihbar konumu metindeki adres", abs(ih["lat"] - an["konum"]["lat"]) < 1e-6)
    kontrol("2 koordinasyon akisina ihbar dustu", koord.olay_var("ihbar", lambda m: m.get("id") == metin_id))
    k, il = koord.istek("GET", "/api/ihbarlar")
    kk = next((x for x in il if x["id"] == metin_id), None)
    kontrol("2 koordinasyon listesinde, analiz ve isleyen alani ile",
            kk is not None and (kk.get("analiz") or {}).get("kategori") == "Enkaz Bildirimi" and "isleyenAd" in kk)
    k, hasar = koord.istek("GET", "/api/hasar-noktalari")
    kontrol("2 enkaz ihbari hasar noktasi uretti (isi haritasi)",
            any(h.get("kaynak") == "metin" and abs(h["lat"] - ih["lat"]) < 1e-6 for h in (hasar or [])))
    k, kendi = afz.istek("GET", "/api/ihbarlar")
    ka = next((x for x in kendi if x["id"] == metin_id), None)
    kontrol("2 afetzede A kendi ihbarini gorur, isleyen alani yok", ka is not None and "isleyenAd" not in ka)

    # --- 3. ihtiyac ve fotograf ---------------------------------------------------------
    k, ihy = afz.istek("POST", "/api/ihbarlar", {"tur": "ihtiyac", "ihtiyaclar": ["su", "gida", "isinma"],
                                                 "kisiSayisi": 4, "metin": "Çadırdayız",
                                                 "konumKaynagi": "gps", "lon": 36.1588, "lat": 36.2034,
                                                 "konumDogrulukM": 20})
    kontrol("3 ihtiyac ihbari (erzak) olustu", k == 201 and ihy.get("ihtiyaclar") == ["su", "gida", "isinma"],
            f"{k} {ihy}")
    ihtiyac_id = ihy["id"]
    kontrol("3 ihtiyac koordinasyon akisina dustu", koord.olay_var("ihbar", lambda m: m.get("id") == ihtiyac_id))
    foto = "data:image/jpeg;base64," + base64.b64encode(FOTO.read_bytes()).decode()
    t = time.perf_counter()
    k, fa = afz.istek("POST", "/api/afetzede/fotograf-analiz", {"imageBase64": foto, "model": "bina"})
    kontrol("3 fotograf analizi (200)", k == 200, f"{k} {str(fa)[:200]}")
    print(f"    fotograf analizi {time.perf_counter() - t:.1f} sn, {len((fa or {}).get('tespitler', []))} tespit")
    if k == 200:
        k, ihf = afz.istek("POST", "/api/ihbarlar", {"tur": "fotograf", "analizId": fa["analizId"],
                                                     "metin": "Apartman", "konumKaynagi": "gps",
                                                     "lon": 36.1600, "lat": 36.2010, "konumDogrulukM": 15})
        kontrol("3 fotograf ihbari olustu", k == 201, f"{k} {ihf}")
        k, ff = koord.istek("GET", f"/api/ihbarlar/{ihf['id']}/fotograf")
        kontrol("3 koordinasyon fotografi gorur", k == 200 and ff and ff.get("veri"))
        k, _ = afz2.istek("GET", f"/api/ihbarlar/{ihf['id']}/fotograf")
        kontrol("3 afetzede B baskasinin fotografini goremez", k in (403, 404), str(k))

    # --- 4. gordum ------------------------------------------------------------------
    k, d = koord.istek("POST", f"/api/ihbarlar/{ihtiyac_id}/durum", {"durum": "goruldu"})
    kontrol("4 koordinasyon gordum", k == 200 and d.get("durum") == "goruldu", f"{k} {d}")
    kontrol("4 afetzede A akisinda goruldu",
            afz.olay_var("ihbar", lambda m: m.get("id") == ihtiyac_id and m.get("durum") == "goruldu"))
    kontrol("4 afetzede B bu olayi almaz",
            not afz2.olay_var("ihbar", lambda m: m.get("id") == ihtiyac_id, bekle=1.0))
    k, _ = afz.istek("POST", f"/api/ihbarlar/{ihtiyac_id}/durum", {"durum": "kapandi"})
    kontrol("4 afetzede ihbar durumu degistiremez", k == 403, str(k))

    # --- 5. sevk ----------------------------------------------------------------------
    k, _ = saha.istek("POST", "/api/gorevler", {"hedefTur": "sos", "hedefId": sos_id, "ekipId": ekip_id})
    kontrol("5 saha sevk edemez", k == 403, str(k))
    k, g = koord.istek("POST", "/api/gorevler", {"hedefTur": "sos", "hedefId": sos_id, "ekipId": ekip_id,
                                                 "kisiSayisi": 4, "not": "Kat 3"})
    kontrol("5 koordinasyon SOS'a ekip gonderdi", k == 201, f"{k} {g}")
    if k != 201:
        raise SystemExit("sevk olmadan devam edilemez")
    gorev_id = g["id"]
    kontrol("5 saha akisina gorev dustu", saha.olay_var("gorev", lambda m: m.get("hedefId") == sos_id))
    k, eb = saha.istek("GET", "/api/ekibim")
    kontrol("5 saha ekibim'de gorev ve olayin ayrintisi var",
            (eb.get("gorev") or {}).get("id") == gorev_id and (eb["gorev"].get("olay") or {}).get("id") == sos_id)
    kontrol("5 afetzede A akisinda gorev", afz.olay_var("gorev", lambda m: m.get("hedefId") == sos_id))
    kontrol("5 afetzede B bu gorevi almaz", not afz2.olay_var("gorev", lambda m: m.get("hedefId") == sos_id, bekle=1.0))
    k, kendi = afz.istek("GET", "/api/sos")
    s1 = next(s for s in kendi if s["id"] == sos_id)
    kontrol("5 afetzede kendi SOS'unda gelen ekibi gorur", bool(s1.get("gorevler")), str(s1.get("gorevler"))[:120])

    # --- 6. saha ilerletir ------------------------------------------------------------------
    for durum in ("yolda", "olay-yerinde"):
        k, gg = saha.istek("POST", f"/api/gorevler/{gorev_id}/durum", {"durum": durum})
        kontrol(f"6 saha {durum}", k == 200 and gg.get("durum") == durum, f"{k} {gg}")
    k, kon = saha.istek("POST", f"/api/ekipler/{ekip_id}/konum", {"lon": 36.1605, "lat": 36.2018, "dogrulukM": 12})
    kontrol("6 saha konum paylasti", k == 200, f"{k} {kon}")
    kontrol("6 afetzede A ekip konumunu akista alir",
            afz.olay_var("ekip-konumu", lambda m: m.get("hedefId") == sos_id))
    k, gg = saha.istek("POST", f"/api/gorevler/{gorev_id}/durum", {"durum": "tamamlandi", "not": "2 kişi çıkarıldı"})
    kontrol("6 saha isi bitirdi", k == 200, f"{k} {gg}")
    k, liste = koord.istek("GET", "/api/sos")
    s2 = next((s for s in liste if s["id"] == sos_id), {})
    kontrol("6 SOS kapandi", s2.get("durum") == "kapandi", s2.get("durum"))
    kontrol("6 afetzede A tamamlandi bilgisini alir",
            afz.olay_var("gorev", lambda m: m.get("hedefId") == sos_id and m.get("durum") == "tamamlandi"))

    # --- 7. yazili ihbara sevk -------------------------------------------------------------
    k, g2 = koord.istek("POST", "/api/gorevler", {"hedefTur": "ihbar", "hedefId": metin_id, "ekipId": ekip_id,
                                                  "kisiSayisi": 4})
    kontrol("7 yazili ihbara ekip gonderildi", k == 201, f"{k} {g2}")
    if k == 201:
        saha.istek("POST", f"/api/gorevler/{g2['id']}/durum", {"durum": "yolda"})
        k, _ = saha.istek("POST", f"/api/gorevler/{g2['id']}/durum", {"durum": "tamamlandi"})
        k, il = koord.istek("GET", "/api/ihbarlar")
        i2 = next((x for x in il if x["id"] == metin_id), {})
        kontrol("7 ihbar ekip bitirince kapandi", i2.get("durum") == "kapandi", i2.get("durum"))
        # Kapanis ayri "ihbar" iletisiyle degil "gorev" iletisiyle gelir; istemci
        # bu iletide kendi ihbarini yeniden ceker (konsol canli/mesajlar.ts).
        kontrol("7 afetzede A gorevin bittigini akista alir",
                afz.olay_var("gorev", lambda m: m.get("hedefId") == metin_id and m.get("durum") == "tamamlandi"))
        k, kendi = afz.istek("GET", "/api/ihbarlar")
        kendi_i = next((x for x in (kendi or []) if x["id"] == metin_id), {})
        kontrol("7 afetzede A kendi listesinde kapandi gorur", kendi_i.get("durum") == "kapandi", f"{k} {kendi_i.get('durum')}")

    # --- 8. erzak karsilandi ----------------------------------------------------------------
    k, d = koord.istek("POST", f"/api/ihbarlar/{ihtiyac_id}/durum", {"durum": "kapandi"})
    kontrol("8 ihtiyac karsilandi (kapandi)", k == 200 and d.get("durum") == "kapandi", f"{k} {d}")
    k, d = koord.istek("POST", f"/api/ihbarlar/{ihtiyac_id}/durum", {"durum": "goruldu"})
    kontrol("8 kapanan ihbar geri acilmaz (409)", k == 409, str(k))

    kontrol("9 saha akisina islem kaydi isareti gitmez", not saha.olay_var("islem-kaydi", lambda m: True, bekle=0.5))
    kontrol("9 koordinasyon akisina islem kaydi isareti gider", koord.olay_var("islem-kaydi", lambda m: True, bekle=0.5))

    gecen = sum(1 for _, g, _ in SONUC if g)
    print(f"\n{gecen}/{len(SONUC)} adim gecti")
    kalan = [(a, x) for a, g, x in SONUC if not g]
    for a, x in kalan:
        print("  KALDI:", a, x[:200])
    for h in (koord, saha, afz, afz2):
        tipler = {}
        for m in h.olaylar:
            tipler[m.get("tip")] = tipler.get(m.get("tip"), 0) + 1
        print(f"  akis {h.ad}: {tipler}")
    raise SystemExit(0 if not kalan else 1)


if __name__ == "__main__":
    main()
