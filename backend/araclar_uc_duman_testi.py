"""Uc duman testi -- API bolunmeden once ve sonra ayni davranisi kanitlamak icin.

TASIMA_PLANI.md Faz 5: fastapi_app.py router modullerine bolunurken hicbir
ucun davranisi degismemeli. Bu arac her uca guvenli bir istek atar ve yanitin
(durum kodu, ust duzey anahtarlar) imzasini kaydeder; iki kayit karsilastirilir.

Agir ya da dis servise giden uclar (analiz, OSM cizgesi, OpenAerialMap) bilincli
olarak gecersiz govdeyle cagrilir: 422 donmesi yonlendirmenin ve dogrulamanin
ayni kaldigini kanitlar, model kosturulmaz.

    python araclar_uc_duman_testi.py kaydet once.json   [--adres http://127.0.0.1:8001]
    python araclar_uc_duman_testi.py karsilastir once.json sonra.json

Depodaki referans imza: testler/uc_imzalari.json (22 Eylul, J-51 sonrasi:
J-50'de /api/sos `durumSecildi` alanini kazandi, yakin yerler ve rota uclari
eklendi; J-51'de afetzede ihbar uclari eklendi; J-44'te yakin yerler `yurume`
alanini kazandi ve yurume rotasi ucu eklendi; J-54'te sevk gorevi uclari eklendi,
SOS ve ihbar `gorevler`, ekip kurum/tur/kisi sayisi, ozet ekip sayilarini kazandi).
Bir ucun davranisini BILEREK degistirdiginde bu dosyayi yeniden kaydet ve
degisikligi commit mesajinda yaz.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

ADRES = "http://127.0.0.1:8001"
# Test hesabi ortam degiskeninden okunur; sifre koda yazilmaz.
#   QM_TEST_EPOSTA (varsayilan koordinator@quakemind.local) ve QM_TEST_SIFRE
KOORDINATOR = {
    "eposta": os.environ.get("QM_TEST_EPOSTA", "koordinator@quakemind.local"),
    "sifre": os.environ.get("QM_TEST_SIFRE", ""),
}


def istek(yontem, yol, govde=None, jeton=None, zaman_asimi=120):
    veri = json.dumps(govde).encode("utf-8") if govde is not None else None
    basliklar = {"content-type": "application/json"}
    if jeton:
        basliklar["authorization"] = f"Bearer {jeton}"
    r = urllib.request.Request(ADRES + yol, data=veri, method=yontem, headers=basliklar)
    try:
        with urllib.request.urlopen(r, timeout=zaman_asimi) as y:
            govde_ham = y.read()
            durum = y.status
            tip = y.headers.get("content-type", "")
    except urllib.error.HTTPError as e:
        govde_ham = e.read()
        durum = e.code
        tip = e.headers.get("content-type", "")
    return durum, tip, govde_ham


def imza(durum, tip, ham):
    """Yanitin karsilastirilabilir ozeti: kod + ust duzey yapi."""
    if "json" not in tip:
        return {"durum": durum, "tip": tip.split(";")[0], "boyutVar": len(ham) > 0}
    try:
        veri = json.loads(ham)
    except Exception:
        return {"durum": durum, "tip": "bozuk-json"}
    if isinstance(veri, dict):
        return {"durum": durum, "anahtarlar": sorted(veri.keys())}
    if isinstance(veri, list):
        ornek = veri[0] if veri else None
        return {
            "durum": durum,
            "liste": True,
            "ogeAnahtarlari": sorted(ornek.keys()) if isinstance(ornek, dict) else None,
        }
    return {"durum": durum, "deger": type(veri).__name__}


def senaryolar(jeton):
    J = jeton
    return [
        # --- genel ---
        ("GET", "/", None, None),
        ("GET", "/api/status", None, None),
        ("GET", "/api/postgis/status", None, None),
        # --- eski kimlik (kaldirilmayacak, davranisi korunmali) ---
        # Her kosuda benzersiz e-posta: ayni adres ikinci kosuda 400 doner.
        ("POST", "/api/auth/register", {"name": "Duman Test", "email": f"duman_{int(time.time()*1000)}@ornek.com", "password": "x12345678", "role": "survivor"}, None),
        ("POST", "/api/auth/login", {"email": "duman_giris@ornek.com", "password": "x12345678", "role": "responder"}, None),
        ("GET", "/api/auth/me?token=gecersiz", None, None),
        # --- yeni kimlik ---
        ("GET", "/api/oturum/ben", None, J),
        ("GET", "/api/oturum/ben", None, None),
        ("POST", "/api/oturum/giris", {"eposta": "yok@ornek.com", "sifre": "x"}, None),
        ("POST", "/api/oturum/rol", {"kullaniciId": "yok", "rol": "saha"}, J),
        ("POST", "/api/oturum/yenile", {}, None),
        # --- sozlesme uclari ---
        ("GET", "/api/ozet", None, J),
        ("GET", "/api/ozet", None, None),
        ("GET", "/api/sos", None, J),
        ("GET", "/api/ekipler", None, J),
        ("GET", "/api/hasar-noktalari", None, J),
        ("GET", "/api/sos/yok/en-yakin-ekip", None, J),
        ("POST", "/api/sos/yok/ata", {"ekipId": "EKP-01"}, J),
        ("POST", "/api/sos/yok/kapat", None, J),
        ("POST", "/api/ekipler/yok/konum", {"lon": 36.1, "lat": 36.2}, J),
        # --- sevk gorevleri ve ekip tanimi (J-54); kayit acmayan istekler ---
        ("GET", "/api/gorevler", None, J),
        ("GET", "/api/gorevler", None, None),
        ("GET", "/api/gorevler/aday-ekipler?hedefTur=sos&hedefId=yok", None, J),
        ("POST", "/api/gorevler", {"hedefTur": "sos", "hedefId": "yok", "ekipId": "yok"}, J),
        ("POST", "/api/gorevler", {"hedefTur": "sos", "hedefId": "yok", "ekipId": "yok"}, None),
        ("POST", "/api/gorevler/yok/durum", {"durum": "yolda"}, J),
        ("GET", "/api/ekibim", None, J),
        ("POST", "/api/ekipler", {"ad": ""}, J),
        ("GET", "/api/ekipler/uye-adaylari", None, J),
        ("PUT", "/api/ekipler/yok/uyeler", {"kullaniciIdleri": []}, J),
        # --- eski SOS / ekip / bildirim / sohbet ---
        ("GET", "/api/sos/alerts", None, None),
        ("POST", "/api/sos/alert", {"latitude": 36.2, "longitude": 36.16, "message": "duman testi"}, None),
        ("POST", "/api/sos/alert/yok/status", {"status": "resolved"}, None),
        ("GET", "/api/team/claims", None, None),
        ("POST", "/api/team/claim", {}, None),
        ("POST", "/api/team/claim/yok/release", None, None),
        ("POST", "/api/team/claim/yok/route", {}, None),
        ("GET", "/api/notifications/active", None, None),
        ("POST", "/api/notifications/send_emergency", {}, None),
        ("GET", "/api/chat/messages?token=gecersiz", None, None),
        ("POST", "/api/chat/send", {}, None),
        # --- kamera ---
        ("GET", "/api/camera/reports", None, None),
        ("POST", "/api/camera/analyze", {"modelType": "hybrid"}, None),
        # --- metin ---
        ("GET", "/api/nlp/locations", None, None),
        ("POST", "/api/nlp/analyze", {}, None),
        # --- risk ---
        ("GET", "/api/risk/fault_lines", None, None),
        ("GET", "/api/risk/all_quakes?limit=5", None, None),
        ("POST", "/api/risk/predict", {"city": "Antakya", "manualLatitude": 36.202, "manualLongitude": 36.161}, None),
        # --- yol hasari (agir olanlar gecersiz govdeyle) ---
        ("POST", "/api/road_damage/analyze", {}, None),
        ("GET", "/api/road_damage/status/yok", None, None),
        ("GET", "/api/road_damage/segments/yok", None, None),
        ("GET", "/api/road_damage/gorsel/yok/imageOriginal", None, None),
        ("GET", "/api/road_damage/gorsel/yok/..%2Fgizli", None, None),
        ("POST", "/api/road_damage/route", {}, None),
        ("POST", "/api/road_damage/route", {"analysisId": "yok", "startLat": 36.2, "startLon": 36.16, "endLat": 36.21, "endLon": 36.17}, None),
        ("POST", "/api/road_damage/simulate_closures", {}, None),
        ("POST", "/api/road_damage/closures_from_mask", {}, None),
        ("POST", "/api/road_damage/closures_from_emsr", {}, None),
        ("POST", "/api/road_damage/naive_compare", {}, None),
        ("POST", "/api/road_damage/reference_compare", {}, None),
        ("POST", "/api/road_damage/safe_route", {}, None),
        ("POST", "/api/road_damage/calculate_custom_route", {}, None),
        ("POST", "/api/road_damage/report_blockage", {}, None),
        ("GET", "/api/road_damage/recent?minutes=5", None, None),
        ("GET", "/api/road_damage/nearest_debris?latitude=36.2&longitude=36.16&limit=3", None, None),
        ("GET", "/api/road_damage/heatmap?latitude=36.202&longitude=36.161&radiusKm=5", None, None),
        ("GET", "/api/road_damage/assembly?latitude=36.202&longitude=36.161&radiusKm=2&allowOnlineFallback=false", None, None),
        # --- afetzede ekrani (J-42, J-43); sona eklendi, onceki siralar kaymasin ---
        ("GET", "/api/live", None, None),  # cerezsiz akis 401 donmeli
        ("GET", "/api/bildirimler/aktif", None, J),
        ("GET", "/api/bildirimler/aktif", None, None),
        ("GET", "/api/altlik/yerler", None, J),
        ("GET", "/api/altlik/yerler", None, None),
        # Gecersiz ihtiyac: 422, kayit acilmaz.
        ("POST", "/api/sos", {"lon": 36.16, "lat": 36.2, "ihtiyaclar": ["uydurma"]}, J),
        # --- bildirim ucu (J-45); hicbiri kayit acmaz ---
        ("POST", "/api/bildirimler", {"baslik": "duman", "metin": "duman testi"}, None),  # 401
        ("POST", "/api/bildirimler", {"baslik": "duman", "metin": "duman testi", "onem": "critical"}, J),  # 422
        ("GET", "/api/bildirimler", None, J),
        ("POST", "/api/bildirimler/yok/kaldir", None, J),  # 404
        # --- afetzede haritasi (J-50) ---
        ("GET", "/api/yakin-yerler?lat=36.2086&lon=36.1547", None, J),
        ("GET", "/api/yakin-yerler?lat=36.2086&lon=36.1547", None, None),  # 401
        # Kimliksiz: 401, dis rota servisine istek gitmez.
        ("POST", "/api/afetzede/sokak-rotasi", {"baslangicLat": 36.2, "baslangicLon": 36.16, "hedefLat": 36.21, "hedefLon": 36.17}, None),
        # --- afetzede ihbarlari (J-51); hicbiri kayit acmaz, model kosmaz ---
        ("POST", "/api/afetzede/fotograf-analiz", {"imageBase64": "x" * 200, "model": "catlak"}, None),  # 401
        ("POST", "/api/afetzede/fotograf-analiz", {"imageBase64": "x" * 200, "model": "yanlis"}, J),  # 422
        ("POST", "/api/afetzede/metin-analiz", {"metin": "duman testi"}, None),  # 401
        ("POST", "/api/afetzede/metin-analiz", {"metin": "abc"}, J),  # 422 (en az 5 harf)
        ("POST", "/api/ihbarlar", {"tur": "ihtiyac", "konumKaynagi": "gps"}, None),  # 401
        ("POST", "/api/ihbarlar", {"tur": "ihtiyac", "ihtiyaclar": ["uydurma"], "lon": 36.16, "lat": 36.2, "konumKaynagi": "gps"}, J),  # 422
        # Bos pencere (1970): liste her zaman bos, imza veriye bagli degil.
        ("GET", "/api/ihbarlar?baslangic=0&bitis=1", None, J),
        ("GET", "/api/ihbarlar", None, None),  # 401
        ("GET", "/api/ihbarlar/yok/fotograf", None, J),  # 404
        ("POST", "/api/ihbarlar/yok/durum", {"durum": "goruldu"}, J),  # 404
        # --- afetzede yurume rotasi (J-44), kendi yol agimiz ---
        ("POST", "/api/afetzede/rota", {"baslangicLat": 36.2, "baslangicLon": 36.16, "hedefLat": 36.21, "hedefLon": 36.17}, None),  # 401
        # Ankara: yol agi uretilmedi -> 404 (dis servise gitmez)
        ("POST", "/api/afetzede/rota", {"baslangicLat": 39.92, "baslangicLon": 32.85, "hedefLat": 39.93, "hedefLon": 32.86}, J),
        ("POST", "/api/afetzede/rota", {"baslangicLat": 36.2086, "baslangicLon": 36.1547, "hedefLat": 36.214354, "hedefLon": 36.136576}, J),
        # --- haritanin basvuru katmanlari (J-56) ---
        # Kutu verilmezse bes bolgeyi kapsayan kutu; sayilar veriye bagli oldugu
        # icin imzada yalniz durum ve anahtarlar karsilastirilir.
        ("GET", "/api/katman/kapanmalar", None, J),
        ("GET", "/api/katman/kapanmalar", None, None),  # 401
        ("GET", "/api/katman/depremler?enAz=6", None, J),
        ("GET", "/api/katman/faylar?kutu=36.0,36.0,37.0,37.0", None, J),
        ("GET", "/api/katman/faylar?kutu=0,0,90,90", None, J),  # 422: kutu cok genis
        ("GET", "/api/katman/toplanma?kutu=36.1,36.15,36.25,36.25", None, J),
    ]


def kaydet(dosya):
    if not KOORDINATOR["sifre"]:
        print("QM_TEST_SIFRE ortam degiskeni gerekli (koordinator hesabinin sifresi).")
        return 2
    durum, _, ham = istek("POST", "/api/oturum/giris", KOORDINATOR)
    if durum != 200:
        print(f"giris basarisiz ({durum}); demo hesap var mi?")
        return 2
    jeton = json.loads(ham)["erisimJetonu"]

    sonuc = []
    for yontem, yol, govde, j in senaryolar(jeton):
        d, tip, h = istek(yontem, yol, govde, j)
        kayit = {"istek": f"{yontem} {yol}{' +jeton' if j else ''}", **imza(d, tip, h)}
        sonuc.append(kayit)
        print(f"{kayit['durum']:>4}  {kayit['istek']}")
    json.dump(sonuc, open(dosya, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n{len(sonuc)} istek kaydedildi -> {dosya}")
    return 0


def karsilastir(once, sonra):
    a = json.load(open(once, encoding="utf-8"))
    b = json.load(open(sonra, encoding="utf-8"))
    fark = 0
    for x, y in zip(a, b):
        if x != y:
            fark += 1
            print(f"FARK  {x['istek']}\n  once : {x}\n  sonra: {y}")
    if len(a) != len(b):
        fark += 1
        print(f"FARK  istek sayisi {len(a)} -> {len(b)}")
    print(f"\n{len(a)} istekten {fark} tanesinde fark var.")
    return 1 if fark else 0


if __name__ == "__main__":
    argumanlar = sys.argv[1:]
    if "--adres" in argumanlar:
        i = argumanlar.index("--adres")
        ADRES = argumanlar[i + 1]
        del argumanlar[i : i + 2]
    if len(argumanlar) >= 2 and argumanlar[0] == "kaydet":
        raise SystemExit(kaydet(argumanlar[1]))
    if len(argumanlar) >= 3 and argumanlar[0] == "karsilastir":
        raise SystemExit(karsilastir(argumanlar[1], argumanlar[2]))
    print(__doc__)
    raise SystemExit(2)
