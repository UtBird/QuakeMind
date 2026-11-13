"""Simülasyon (tatbikat) modu uçları.

Sözleşme: repo kökündeki `SIMULASYON_SOZLESMESI.md`. Arayüz bu uçlara bağlanır,
modellere değil.

Kurgu: kullanıcı bir alan ve bir model seçer → alanın **gerçek** deprem sonrası
görüntüsü çekilir → **kendi modelimiz gerçekten koşar** → çıkan hasar
maskesinden yol kapanmaları türetilir → aynı OD çiftleri üç grafik üzerinde
Dijkstra ve A* ile koşulur → 5 gerçek ekip üssü 5 senaryo afetzedesine bağlanır.

Pahalı işin tamamı istek yolunun dışındadır (CLAUDE.md 3): çıkarım mevcut
`road_damage_pool` işçi süreçlerinde koşar, istek 202 + iş kimliği döner,
ilerleme tek SSE akışından gelir (kural 4). Rota ve görev hesabı analiz
bittikten sonra ayrı bir iş parçacığında yapılır; API süreci bloklanmaz.
"""
import functools
import hashlib
import json
import threading
import time
import uuid
from pathlib import Path
from threading import Lock

import canli_yayin
import cekirdek as ck
import kimlik
from apps.road_damage.utils import model_kunyesi
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

yonlendirici = APIRouter()

# --- Tatbikat alanları ------------------------------------------------------
# Alanlar ARTIK ELLE YAZILMIYOR. `araclar_alan_katalogu.py` her açık drone
# sahnesinin uçuş izini tarar, gerçekten dolu olan en iyi pencereyi ÖLÇEREK
# seçer ve künyesiyle (sahne adı, çekim tarihi, sağlayıcı, doluluk, OSM yol
# oranı) `data/tatbikat_alanlari.json` dosyasına yazar. Buradaki her sayının
# kaynağı o ölçümdür (CLAUDE.md 1).
#
# Neden ölçülerek: drone mozaiğinin OAM kutusu bütün uçuş zarfıdır, içinin
# büyük bölümü siyahtır. Kutuyu elle yazmak "görüntünün %61'i boş" durumunu
# (J-65) yeniden üretiyordu.
#
# Dosya yoksa tek alanlık tarihsel liste kullanılır (aşağıdaki YEDEK_ALANLAR),
# böylece veri kurulmamış bir makinede uç yine de ayağa kalkar.
ALANLAR_DOSYASI = (
    Path(__file__).resolve().parents[1] / "apps" / "road_damage" / "data" / "tatbikat_alanlari.json"
)

YEDEK_ALANLAR = [
    {
        "id": "hatay-elektrik",
        "ad": "Hatay / Defne — Elektrik Mah.",
        "merkez": {"lat": 36.197694, "lon": 36.149322},
        "katmanlar": [
            {
                "id": "yakin",
                "ad": "Drone ortofoto",
                "kaynak": "oam",
                "oamBasligi": "Hatay - Defne - Elektrik Mah.",
                "bbox": [36.146753, 36.195466, 36.15189, 36.199922],
                "yaricapKm": 0.3,
                "saglayici": "Help.NGO (OpenAerialMap)",
                "cekimTarihi": "2023-02-09",
                "gercek": True,
                "not": "Uçuş izi kutunun %39'unu kaplar; gerisi görüntüde boştur.",
            },
        ],
    },
]


def _alanlari_yukle():
    """Ölçülen alan kataloğunu uç biçimine çevirir."""
    if not ALANLAR_DOSYASI.exists():
        return list(YEDEK_ALANLAR)
    try:
        ham = json.loads(ALANLAR_DOSYASI.read_text(encoding="utf-8"))
    except Exception:
        return list(YEDEK_ALANLAR)
    cikti = []
    for a in ham:
        kutu = a.get("analizBbox")
        if not kutu or len(kutu) != 4:
            continue
        uyari = []
        if (a.get("doluluk") or 1) < 0.5:
            uyari.append(f"uçuş izi karenin %{(a['doluluk'] or 0)*100:.0f}'ini kaplar")
        if (a.get("pencereM") or 500) < 480:
            uyari.append(f"alan {a['pencereM']:.0f} m (mozaik dar)")
        if a.get("osmYolOrani") in (None, 0):
            uyari.append("OSM yol oranı ölçülemedi")
        cikti.append({
            "id": a["parca"].lower().replace(" ", "-").replace("_", "-"),
            "ad": f"{a['il']} / {a['yer']}",
            "merkez": a["merkez"],
            "katmanlar": [{
                "id": "drone",
                "ad": "Drone ortofoto",
                "kaynak": "oam",
                "oamBasligi": a["sahneAdi"],
                # ADRES ÇİFTLENMESİN. OAM'in `tms` adresi ÇOĞU ZAMAN `{z}/{x}/{y}`
                # yer tutucularını kendisi taşır; körlemesine eklemek
                # `.../{z}/{x}/{y}/{z}/{x}/{y}.png` üretiyordu ve vekil bütün
                # karolar için 404 alıyordu — haritada zemin bomboş kalıyordu
                # (ölçüldü, 26 Eylül; J-75'te aynı hata bir kez düzeltilmişti).
                "oamTmsUrl": (a["tmsUrl"] if "{z}" in a["tmsUrl"]
                              else a["tmsUrl"].rstrip("/") + "/{z}/{x}/{y}.png"),
                "bbox": kutu,
                "yaricapKm": round((a.get("pencereM") or 500) / 2000.0, 3),
                "saglayici": f"{a.get('saglayici') or '?'} (OpenAerialMap)",
                "cekimTarihi": a.get("tarih"),
                "gercek": True,
                "doluluk": a.get("doluluk"),
                "pencereM": a.get("pencereM"),
                "osmYolOrani": a.get("osmYolOrani"),
                "not": "; ".join(uyari) if uyari else "Uçuş izi kareyi büyük ölçüde kaplar.",
            }],
        })
    return cikti or list(YEDEK_ALANLAR)


ALANLAR = _alanlari_yukle()

# Arayüzdeki üç seçenek → model künyesi (modeller/uydu/<ad>.json).
MODELLER = [
    {"id": "hizli", "ad": "Hızlı", "kunye": "segformer_mitb0_p2_t42"},
    {"id": "dengeli", "ad": "Dengeli", "kunye": "segformer_mitb2_p2_t42"},
    {"id": "eniyi", "ad": "En iyi", "kunye": "unet_mitb4_p2_t42"},
]

# Simülasyon işleri: analiz işinden ayrı tutulur, çünkü rota ve görevler analiz
# bittikten SONRA eklenir. Sınırlı FIFO, analiz iş deposuyla aynı desen.
simulasyon_isleri: dict = {}
simulasyon_sirasi: list = []
simulasyon_kilidi = Lock()
IS_SINIRI = 20
# Aynı parmak izi ikinci kez istenirse çıkarım yeniden koşmaz.
parmak_izi_haritasi: dict = {}


# VARSAYILANLAR KATALOGDAN GELIR. Sabit yazilinca bayatliyordu: "hatay-elektrik"
# ve "yakin" yalnizca YEDEK_ALANLAR'da var; olculmus katalogda karsiliklari
# "defne---elektrik" ve "drone". Govdesiz bir POST /api/simulasyon/kos bu yuzden
# 404 aliyordu (J-106, 27 Eylul 2026). Konsol kimlikleri hep acikca gonderdigi
# icin arayuzde gorunmuyordu.
_VARSAYILAN_ALAN = ALANLAR[0]["id"] if ALANLAR else YEDEK_ALANLAR[0]["id"]
_VARSAYILAN_KATMAN = (
    ALANLAR[0]["katmanlar"][0]["id"]
    if ALANLAR and ALANLAR[0].get("katmanlar")
    else YEDEK_ALANLAR[0]["katmanlar"][0]["id"]
)


class SimulasyonIstegi(BaseModel):
    alanId: str = _VARSAYILAN_ALAN
    katmanId: str = _VARSAYILAN_KATMAN
    modelId: str = "dengeli"
    esik: float | None = None
    # Ürünün kuralı: varsayılan 0 = "yalnız yolun üstündeki hasar kapatır"
    # (worker.py'deki `blockageRadiusM` varsayılanıyla aynı). Yarıçap kuralı
    # bir DENEYDİR (J-26) ve ancak açıkça istenince devreye girer; tatbikat da
    # uygulamanın varsayılanını değiştirmez (J-19). Farkı görmek için istekteki
    # `karsilastirYaricaplar` kıyas kutusu kullanılır.
    kapanmaYaricapiM: float = 0.0
    ekipSayisi: int = 5
    afetzedeSayisi: int = 5
    # Yer seviyesi kanallar: kac fotograf, kac ihbar metni yerlestirilecek.
    kameraSayisi: int = 4
    metinSayisi: int = 5
    tohum: int = 42
    hizKmh: float = 15.0
    # Kontrol koşusu: aynı model, aynı alan, DEPREM ÖNCESİ görüntü. Orada
    # bulduğu "hasar" yanlış alarm tabanıdır (CLAUDE.md 1: ölçmeden iddia yok).
    kontrolKosusu: bool = True
    # ARAŞTIRMA ALANI — arayüzde gösterilmez, varsayılanı boştur.
    # "Moloz yayılımı yokken / varken" kıyası: aynı maske, farklı r_h. Çıkarım
    # bir kez koşar, her yarıçap yalnız kapanma + rota hesabı ekler (ölçüldü:
    # yarıçap başına ~16 sn). Boş liste = kıyas yok, ek süre yok.
    #
    # Neden arayüzde yok: EMSR648 yer gerçeğiyle kalibre edildi (J-70) ve r_h
    # kesinliği 0,10-0,18 bandından çıkarmıyor — yarıçabı çevirmek duyarlılığı
    # artırırken yanlış alarmı aynı oranda artırıyor. Operatöre sonucu
    # düzeltmeyen bir düğme sunulmaz; ayar ölçüm ve makale için API'de kalır.
    karsilastirYaricaplar: list[float] = []


class SimulasyonBitirIstegi(BaseModel):
    isId: str


def _alan(alan_id):
    for a in ALANLAR:
        if a["id"] == alan_id:
            return a
    raise HTTPException(status_code=404, detail=f"Bilinmeyen alan: {alan_id}")


def _katman(alan, katman_id):
    for k in alan["katmanlar"]:
        if k["id"] == katman_id:
            return k
    raise HTTPException(status_code=404, detail=f"Bilinmeyen katman: {katman_id}")


def _model(model_id):
    for m in MODELLER:
        if m["id"] == model_id:
            return m
    raise HTTPException(status_code=404, detail=f"Bilinmeyen model: {model_id}")


def _kunye_ozeti(m):
    """Künye dosyası okunamazsa model listeden düşer; uydurma değer yazılmaz."""
    try:
        k = model_kunyesi.kunye_oku(m["kunye"])
    except Exception as e:
        return {**m, "hazir": False, "hata": str(e)}
    olcum = k.get("olcum") or {}
    return {
        "id": m["id"],
        "ad": m["ad"],
        "kunye": k["ad"],
        "mimari": f"{k['mimari']['sinif']} ({k['mimari']['kodlayici']})",
        "sinamaIoU": olcum.get("sinamaIoU"),
        "esik": k["karar"]["esik"],
        "agirlikSha256": k["agirlik"]["sha256"][:12],
        # Ölçülmediyse null gider; arayüz null ise süre yazmaz (CLAUDE.md 8).
        "ileriGecis512Sn": olcum.get("ileriGecis512Sn"),
        "olcumNotu": olcum.get("ileriGecisNotu"),
        "hazir": True,
    }


def _parmak_izi(istek: SimulasyonIstegi, kunye_adi, agirlik_sha, esik):
    ham = json.dumps({
        "alan": istek.alanId, "katman": istek.katmanId, "kunye": kunye_adi,
        "agirlik": agirlik_sha, "esik": esik, "yaricap": istek.kapanmaYaricapiM,
        "ekip": istek.ekipSayisi, "afetzede": istek.afetzedeSayisi,
        "tohum": istek.tohum, "hiz": istek.hizKmh,
        # Kıyas listesi de parmak izine girer: aynı koşu farklı kıyas listesiyle
        # istenirse önbellekten eksik sonuç dönmesin.
        "kiyas": sorted(float(x) for x in (istek.karsilastirYaricaplar or [])),
    }, sort_keys=True)
    return "sha1:" + hashlib.sha1(ham.encode("utf-8")).hexdigest()


def _is_sakla(is_id, veri):
    with simulasyon_kilidi:
        simulasyon_isleri[is_id] = veri
        simulasyon_sirasi.append(is_id)
        while len(simulasyon_sirasi) > IS_SINIRI:
            eski = simulasyon_sirasi.pop(0)
            eski_is = simulasyon_isleri.pop(eski, None)
            if eski_is:
                parmak_izi_haritasi.pop(eski_is.get("parmakIzi"), None)


@yonlendirici.get("/api/simulasyon/alanlar")
def simulasyon_alanlari(_kul: dict = Depends(kimlik.rol_gerektir("saha", "koordinator", "yonetici"))):
    """Tatbikat alanları ve her alanın katmanları (kaynak, çekim tarihi, GSD)."""
    return {"alanlar": ALANLAR}


@yonlendirici.get("/api/simulasyon/modeller")
def simulasyon_modelleri(_kul: dict = Depends(kimlik.rol_gerektir("saha", "koordinator", "yonetici"))):
    """Arayüzde seçilebilen modeller ve ölçülmüş değerleri."""
    return {"modeller": [_kunye_ozeti(m) for m in MODELLER]}


@yonlendirici.post("/api/simulasyon/kos", status_code=202)
def simulasyon_kos(
    istek: SimulasyonIstegi,
    _kul: dict = Depends(kimlik.rol_gerektir("koordinator", "yonetici")),
):
    """Tatbikatı başlatır. 202 + iş kimliği döner; çıkarım istek yolunda koşmaz.

    Aynı parmak izi (alan + katman + ağırlık + eşik + yarıçap + tohum) daha önce
    koşmuşsa yeniden koşulmaz, o işin kimliği döner.
    """
    alan = _alan(istek.alanId)
    katman = _katman(alan, istek.katmanId)
    model = _model(istek.modelId)
    try:
        kunye = model_kunyesi.kunye_oku(model["kunye"])
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Model künyesi okunamadı: {e}")
    esik = istek.esik if istek.esik is not None else kunye["karar"]["esik"]

    izi = _parmak_izi(istek, kunye["ad"], kunye["agirlik"]["sha256"], esik)
    with simulasyon_kilidi:
        onceki = parmak_izi_haritasi.get(izi)
        if onceki and simulasyon_isleri.get(onceki, {}).get("durum") in ("bitti", "calisiyor", "kuyrukta"):
            return {"isId": onceki, "parmakIzi": izi, "onbellekten": True}

    if ck.road_damage_pool is None:
        raise HTTPException(status_code=503, detail="Çıkarım işçi havuzu henüz hazır değil.")
    if ck._count_queued_road_damage_jobs() >= ck.ROAD_DAMAGE_MAX_QUEUED_JOBS:
        raise HTTPException(status_code=503, detail="Kuyruk dolu; birkaç saniye sonra tekrar deneyin.")

    from apps.road_damage import worker as road_damage_worker

    is_id = f"sim_{uuid.uuid4().hex[:12]}"
    talep = {
        "_analysisId": is_id,
        "city": alan["ad"],
        "latitude": alan["merkez"]["lat"],
        "longitude": alan["merkez"]["lon"],
        "source": katman["kaynak"],
        "oamPreferredTitle": katman.get("oamBasligi"),
        "waybackId": katman.get("waybackId"),
        "radiusKm": katman["yaricapKm"],
        "threshold": esik,
        # Künyedeki karar ayarı: güçlendirme ve son işleme yok — model makalede
        # ölçüldüğü gibi koşar.
        "damageBooster": kunye["karar"]["guclendirme"],
        "postProcessLevel": kunye["karar"]["sonIsleme"],
        "blockageRadiusM": istek.kapanmaYaricapiM,
        "modelAdi": kunye["ad"],
    }
    if katman.get("bbox"):
        talep.update({
            "bboxWest": katman["bbox"][0], "bboxSouth": katman["bbox"][1],
            "bboxEast": katman["bbox"][2], "bboxNorth": katman["bbox"][3],
        })

    ck._store_road_damage_job(is_id, {
        "status": "queued", "createdAt": time.time(), "progress": 0,
        "progressMessage": "Sırada bekliyor...",
    })
    _is_sakla(is_id, {
        "isId": is_id, "parmakIzi": izi, "durum": "kuyrukta", "baslangic": time.time(),
        "istek": istek.model_dump(), "alan": alan, "katman": katman,
        "model": _kunye_ozeti(model), "rota": None, "hata": None,
    })
    with simulasyon_kilidi:
        parmak_izi_haritasi[izi] = is_id

    gelecek = ck.road_damage_pool.submit(road_damage_worker.run_analysis_job, talep)
    # Önce çekirdeğin geri çağrısı: sonucu iş deposuna ve grafiği oturum
    # deposuna yazar. Sonra bizimki: rota ve görevleri onun bıraktığı grafikten
    # kurar. `add_done_callback` eklenme sırasında çağırır.
    gelecek.add_done_callback(functools.partial(ck._on_road_damage_job_done, is_id))
    gelecek.add_done_callback(functools.partial(_analiz_bitti, is_id))

    # Kontrol koşusu aynı kuyruğa arkadan girer: asıl sonuç önce çıkar, yanlış
    # alarm tabanı hazır olunca sonuca eklenir.
    if istek.kontrolKosusu and katman["id"] != "oncesi":
        kontrol = next((k for k in alan["katmanlar"] if k["id"] == "oncesi"), None)
        if kontrol is not None:
            kontrol_talep = {
                **talep, "_analysisId": f"{is_id}_kontrol",
                "source": kontrol["kaynak"], "oamPreferredTitle": kontrol.get("oamBasligi"),
                "waybackId": kontrol.get("waybackId"), "radiusKm": kontrol["yaricapKm"],
            }
            for k in ("bboxWest", "bboxSouth", "bboxEast", "bboxNorth"):
                kontrol_talep.pop(k, None)
            if kontrol.get("bbox"):
                kontrol_talep.update({
                    "bboxWest": kontrol["bbox"][0], "bboxSouth": kontrol["bbox"][1],
                    "bboxEast": kontrol["bbox"][2], "bboxNorth": kontrol["bbox"][3],
                })
            k_gelecek = ck.road_damage_pool.submit(road_damage_worker.run_analysis_job, kontrol_talep)
            k_gelecek.add_done_callback(functools.partial(_kontrol_bitti, is_id, kontrol))

    canli_yayin.yayinla("is-durumu", isId=is_id, isTipi="simulasyon",
                        durum="kuyrukta", ilerleme=0, mesaj="Tatbikat sıraya alındı.")
    return {"isId": is_id, "parmakIzi": izi, "onbellekten": False}


def _kontrol_bitti(is_id, katman, gelecek):
    """Deprem öncesi görüntüdeki koşunun sonucu: yanlış alarm tabanı."""
    try:
        sonuc = gelecek.result()
        veri = {
            "katmanId": katman["id"], "cekimTarihi": katman["cekimTarihi"],
            "saglayici": katman["saglayici"],
            "hasarliPikselOrani": sonuc.get("damageRate"),
            "hasarliPikselOraniGecerli": sonuc.get("damageRateValid"),
            "kapaliKenarSayisi": sonuc.get("blockedRoads"),
        }
    except Exception as e:
        veri = {"hata": f"{type(e).__name__}: {e}"}
    with simulasyon_kilidi:
        sim = simulasyon_isleri.get(is_id)
        if sim is not None:
            sim["oncesiKontrol"] = veri


def _analiz_bitti(is_id, gelecek):
    """Havuzun yönetim iş parçacığında koşar — burada ağır iş yapılmaz.

    Rota hesabı ayrı bir iş parçacığına verilir; yoksa havuzun geri çağrı
    zinciri (ve onunla birlikte sonraki işlerin tamamlanma bildirimi) beklerdi.
    """
    if gelecek.exception() is not None:
        with simulasyon_kilidi:
            i = simulasyon_isleri.get(is_id)
            if i:
                i["durum"] = "hata"
                i["hata"] = str(gelecek.exception())
        return
    threading.Thread(target=_rota_asamasi, args=(is_id,), daemon=True,
                     name=f"tatbikat-{is_id}").start()


def _rota_asamasi(is_id):
    """Analiz bittikten sonra: afetzedeler, ekipler, rotalar, görevler."""
    from apps.road_damage.utils import tatbikat, tatbikat_kanallar

    with simulasyon_kilidi:
        sim = simulasyon_isleri.get(is_id)
    if sim is None:
        return
    try:
        with ck.road_damage_jobs_lock:
            analiz = (ck.road_damage_jobs.get(is_id) or {}).get("result") or {}
        # Görüntü eksik indiyse koşu sessizce zayıflar (gerekçe tatbikat.py).
        _eksik = tatbikat.goruntu_eksik_mi(analiz, (sim.get("katman") or {}))
        if _eksik:
            raise RuntimeError(_eksik)

        sinir = analiz.get("bounds") or {}
        bounds = (sinir["west"], sinir["south"], sinir["east"], sinir["north"])
        canli_yayin.yayinla("simulasyon-katman", isId=is_id, katman="hasar",
                            sayi=analiz.get("blockedRoads"))

        maske = _maske_oku(is_id)
        if maske is None:
            raise RuntimeError("Hasar maskesi okunamadı.")

        istek = sim["istek"]
        merkez = sim["alan"]["merkez"]
        noktalar = tatbikat.hasar_noktalari(maske, bounds)
        # Eleme sonrası yeterli aday kalsın diye istenenin üç katı çıkarılır.
        kurbanlar = tatbikat.afetzedeler(
            maske, bounds, istek["afetzedeSayisi"] * 3, istek["tohum"])
        # DÜNYA = GÖRÜNTÜLENEN MAHALLE (26 Eylül, ölçüldü). Önce ekipler gerçek
        # tesislerdi (1,3–3,8 km uzakta) ve rota grafiği onları kapsıyordu;
        # sonuçta model rota ağının yalnız %0,64'ünü görüyor, kapanma hiçbir
        # rotaya denk gelmiyor ve üç kıyas kolu birebir aynı çıkıyordu — yani
        # tatbikat hiçbir şey ölçmüyordu. 500 m'lik enkaz haritası 3 km'lik
        # rotayı değiştiremez. Verinin desteklediği soru şu: mahalleye giren
        # ekip içerideki enkaza ne kadar sürede ulaşıyor? Ekipler artık
        # mahallenin gerçek giriş ağızlarında konuşlanır; kapsama %15'e çıktı
        # (aynı alan, aynı model). Gerekçe tatbikat.mahalle_grafigi'nde.
        tam_G, guvenli_G, kapali, rota_kutusu, kapsama, kapali_cizgiler = tatbikat.mahalle_grafigi(
            maske, bounds, kapanma_yaricapi_m=istek["kapanmaYaricapiM"],
            gecerli_maske=_gecerli_maske_oku(is_id),
        )
        takimlar = tatbikat.giris_noktalari(tam_G, bounds, istek["ekipSayisi"])
        if not kurbanlar or not takimlar:
            raise RuntimeError(
                f"Tatbikat kurulamadı: {len(takimlar)} giriş ağzı, {len(kurbanlar)} afetzede."
            )
        # Yolun ulaşamadığı afetzedeler elenir: hasar blobu stadyum sahasına ya
        # da kopuk bir yol parçasına düşerse BÜTÜN kollar 0 görevle bitiyordu
        # (ölçüldü, Şubat Stadyumu) — sorun kapanma değil, çizge kopukluğu.
        kurbanlar, elenen_afetzede, takimlar = tatbikat.ulasilabilir_afetzedeler(
            tam_G, takimlar, kurbanlar)
        if not kurbanlar or not takimlar:
            raise RuntimeError(
                f"Tatbikat kurulamadı: afetzedelerin hiçbirine yol ulaşmıyor "
                f"({len(elenen_afetzede)} nokta elendi)."
            )
        _n = min(len(takimlar), len(kurbanlar))
        kurbanlar, takimlar = kurbanlar[:_n], takimlar[:_n]
        canli_yayin.yayinla("simulasyon-katman", isId=is_id, katman="kapanma", sayi=len(kapali))

        sonuc = tatbikat.rota_kosusu(
            tam_G, guvenli_G, takimlar, kurbanlar,
            hasar_noktalari=noktalar, hiz_kmh=istek["hizKmh"],
            ceza_yaricapi_m=istek["kapanmaYaricapiM"], ekranda=istek["ekipSayisi"],
        )
        canli_yayin.yayinla("simulasyon-katman", isId=is_id, katman="rota",
                            sayi=len(sonuc["gorevler"]))

        # Kıyas kolları: kapanmayı önceden bilmenin kazandırdığı süre. Tatbikatta
        # dünya = modelin kapanmaları olduğu için QuakeMind kolu tanım gereği
        # kusursuz bilgilidir; sonuçtaki `not` alanı bunu yazar (gerekçe
        # tatbikat.py'de). Dönüş maliyeti açık: trafik sağdan akar.
        referans = None
        try:
            referans = tatbikat.kiyas_kollari(
                tam_G, kapali, takimlar, kurbanlar, hiz_kmh=istek["hizKmh"],
            )
        except Exception as e:
            referans = {"hata": f"{type(e).__name__}: {e}"}

        with simulasyon_kilidi:
            sim["referansAjanlar"] = referans
            sim["ekipler"] = takimlar
            sim["afetzedeler"] = kurbanlar
            sim["rota"] = sonuc
            sim["grafik"] = {
                "kutu": rota_kutusu,
                "dugum": tam_G.number_of_nodes(),
                "kenar": tam_G.number_of_edges(),
                "kapaliKenar": len(kapali),
                # Maskenin gördüğü kenar oranı: gerisi "açık" sayıldı, ölçülmedi.
                "maskeKapsamasi": kapsama,
            }
            sim["kapaliCizgiler"] = kapali_cizgiler
        canli_yayin.yayinla("simulasyon-katman", isId=is_id, katman="gorev",
                            sayi=len(sonuc["gorevler"]))

        # Yarıçap kıyası en sonda: asıl tatbikat bu noktada zaten çizilebilir
        # (katman mesajları gitti, sonuç ucu bölümleri dolu döner). `durum`
        # kıyas da bitince "bitti" olur — "bitti" her şey hazır demektir.
        yaricaplar = [float(x) for x in (istek.get("karsilastirYaricaplar") or []) if float(x) >= 0]
        if yaricaplar:
            try:
                kiyas = tatbikat.yaricap_kiyasi(
                    tam_G, bounds, maske, takimlar, kurbanlar, yaricaplar,
                    gecerli_maske=_gecerli_maske_oku(is_id), hiz_kmh=istek["hizKmh"],
                )
            except Exception as e:
                kiyas = {"hata": f"{type(e).__name__}: {e}"}
            with simulasyon_kilidi:
                sim["yaricapKiyasi"] = kiyas
            canli_yayin.yayinla("simulasyon-katman", isId=is_id, katman="kapanma",
                                sayi=len(kapali))

        # --- yer seviyesi kanallar ----------------------------------------
        # Uydu kanalı mahalleyi yukarıdan gördü; kamera (YOLO) ve metin
        # (BERTurk) aynı mahalleye yerden bakar. Gerçek fotoğraf ve gerçek
        # model çıktısı, ÜRETİLMİŞ konum — gerekçesi tatbikat_kanallar modül
        # başlığında. En sonda koşarlar: asıl tatbikat bu noktada zaten
        # çizilebilir, bu iki kanal onun üstüne biner.
        il = (sim["alan"]["ad"].split("/")[0]).strip()
        kanallar = {}
        # SIRA ONEMLI: kamera once koşar, konumlarını metin kanalına verir ki
        # iki kanalın işareti üst üste binmesin (J-110).
        def _kamera():
            return tatbikat_kanallar.kamera_kanali(
                maske, bounds, sayi=istek.get("kameraSayisi", 4), tohum=istek["tohum"],
                alan_anahtari=sim["alan"]["id"])

        def _metin():
            kam = kanallar.get("kamera") or {}
            dolu = [(z["lat"], z["lon"]) for z in (kam.get("kayitlar") or [])]
            return tatbikat_kanallar.metin_kanali(
                maske, bounds, il=il, sayi=istek.get("metinSayisi", 5), tohum=istek["tohum"],
                alan_anahtari=sim["alan"]["id"], kacinilacak=dolu)

        for ad, cagir in (("kamera", _kamera), ("metin", _metin)):
            try:
                kanallar[ad] = cagir()
            except Exception as e:
                # Bir kanal düşerse tatbikatın tamamı düşmez; hata kaydın
                # içinde durur ve arayüzde yazar (kural 1: eksikse eksik denir).
                kanallar[ad] = {"kayitlar": [], "hata": f"{type(e).__name__}: {e}"}
            canli_yayin.yayinla("simulasyon-katman", isId=is_id, katman=ad,
                                sayi=len(kanallar[ad]["kayitlar"]))
        with simulasyon_kilidi:
            sim["kanallar"] = kanallar
        _kanallari_depoya_yaz(is_id, kanallar)

        with simulasyon_kilidi:
            sim["durum"] = "bitti"
            sim["bitis"] = time.time()
        canli_yayin.yayinla("is-durumu", isId=is_id, isTipi="simulasyon",
                            durum="bitti", ilerleme=100, mesaj="Tatbikat tamamlandı.")
    except Exception as e:
        with simulasyon_kilidi:
            sim["durum"] = "hata"
            sim["hata"] = f"{type(e).__name__}: {e}"
        canli_yayin.yayinla("is-durumu", isId=is_id, isTipi="simulasyon",
                            durum="hata", hata=str(e))


def _gecerli_maske_oku(is_id):
    """Görüntünün BOŞ olmayan kısmı: drone ortofotosunda uçuş izi dışı siyahtır.

    Kapanma kapsaması bununla hesaplanır — modelin gerçekten baktığı kenarlar.
    """
    import numpy as np
    from PIL import Image

    yol = ck.ANALIZ_GORSEL_DIZINI / is_id / "imageOriginal.png"
    if not yol.exists():
        return None
    return (np.asarray(Image.open(yol).convert("L")) > 12).astype(np.uint8)


def _kanallari_depoya_yaz(is_id, kanallar):
    """Kamera ve metin kayitlarini ORTAK SOZLESMEYE yazar (CLAUDE.md kural 2).

    Boylece konsolun isi haritasindaki "kamera" ve "metin" kanallari tatbikat
    sirasinda da dolar; uydu kanaliyla ayni tabloya inerler. Her kayit
    `ek.tatbikat` tasir: kosu bitirilince `hasar_sil_tatbikat` bunlari siler,
    tatbikat verisi gercek olay verisiyle karismaz.
    """
    try:
        from depo import aktif_depo

        depo = aktif_depo()
    except Exception as e:
        print(f"tatbikat kanallari depoya yazilamadi: {e}", flush=True)
        return 0
    yazilan = 0
    for kanal_adi, kanal in (kanallar or {}).items():
        for k in kanal.get("kayitlar") or []:
            try:
                depo.hasar_ekle(
                    lon=k["lon"], lat=k["lat"], skor=k["skor"], guven=k["guven"],
                    kaynak=k["kaynak"], zaman=k["zaman"], etiket=k.get("etiket"),
                    ek={
                        "tatbikat": is_id,
                        "kanal": kanal_adi,
                        # Konum UYDURULMUSTUR; arayuz ve sorgular bunu gorsun.
                        "sentetikKonum": True,
                        "sentetikMetin": bool(k.get("sentetikMetin")),
                        "kokenNotu": k.get("konumNotu"),
                    },
                )
                yazilan += 1
            except Exception as e:
                print(f"tatbikat kanal kaydi yazilamadi ({kanal_adi}): {e}", flush=True)
    return yazilan


def _maske_oku(is_id):
    """Analizin diske yazdığı hasar maskesi (PNG) → ikili dizi."""
    import numpy as np
    from PIL import Image

    yol = ck.ANALIZ_GORSEL_DIZINI / is_id / "imageDamageMask.png"
    if not yol.exists():
        return None
    return (np.asarray(Image.open(yol).convert("L")) > 127).astype(np.uint8)


@yonlendirici.post("/api/simulasyon/bitir")
def simulasyon_bitir(
    istek: SimulasyonBitirIstegi,
    _kul: dict = Depends(kimlik.rol_gerektir("koordinator", "yonetici")),
):
    """Tatbikatı bitirir: konsol normal akışa döner.

    Tatbikat GERÇEK görüntüde GERÇEK model koşturur, ama sonucu canlı olay
    değildir. Koşu bitirilince o koşunun yazdığı hasar noktaları silinir; aksi
    hâlde tatbikat verisi gerçek olay verisiyle karışırdı (CLAUDE.md 1).
    Analizin kendi kaydı (görseller, sonuç) durur — geriye dönüp bakılabilsin.

    Açık bütün istemciler aynı anda çıksın diye canlı akışa `durum: "iptal"`
    gider; tek bir istemcinin ekranını temizlemek yetmez.
    """
    with simulasyon_kilidi:
        sim = simulasyon_isleri.get(istek.isId)
        if sim is None:
            raise HTTPException(status_code=404, detail="Bilinmeyen ya da süresi dolmuş iş kimliği.")
        sim["bitirildi"] = time.time()

    silinen = 0
    try:
        from depo import aktif_depo

        depo = aktif_depo()
        if hasattr(depo, "hasar_sil_tatbikat"):
            silinen = depo.hasar_sil_tatbikat(istek.isId)
    except Exception as e:
        print(f"tatbikat hasar noktalari silinemedi: {e}", flush=True)

    canli_yayin.yayinla("is-durumu", isId=istek.isId, isTipi="simulasyon",
                        durum="iptal", mesaj="Tatbikat bitirildi.")
    # Isı haritası ve genel durum ekranı tazelensin.
    canli_yayin.yayinla("yeni-analiz", kaynak="uydu", isId=istek.isId)
    return {"isId": istek.isId, "durum": "bitti", "silinenHasarNoktasi": silinen}


@yonlendirici.get("/api/simulasyon/kosu/{is_id}")
def simulasyon_kosusu(
    is_id: str,
    _kul: dict = Depends(kimlik.rol_gerektir("saha", "koordinator", "yonetici")),
):
    """Tatbikat koşusunun durumu ve bittiyse sonucu (sözleşme §4)."""
    with simulasyon_kilidi:
        sim = simulasyon_isleri.get(is_id)
        if sim is None:
            raise HTTPException(status_code=404, detail="Bilinmeyen ya da süresi dolmuş iş kimliği.")
        sim = dict(sim)
    with ck.road_damage_jobs_lock:
        analiz_isi = ck.road_damage_jobs.get(is_id) or {}
        analiz = analiz_isi.get("result") or {}
        analiz_durumu = analiz_isi.get("status", "queued")

    if sim["durum"] == "hata" or analiz_durumu == "error":
        return {"isId": is_id, "durum": "hata",
                "hata": sim.get("hata") or analiz_isi.get("error")}

    katman = sim["katman"]
    bitti = sim["durum"] == "bitti"
    # Kısmi sonuç (J-62/3): bölümler hazır oldukça döner, hazır olmayan bölüm
    # `null` gelir. Arayüz eldekini çizer, sonucun tamamını beklemez.
    return {
        "isId": is_id,
        # İlerleme başladıysa iş KOŞUYOR demektir: analiz iş deposu durumu işin
        # sonuna kadar "queued" kalıyor, ilerleme ise ayrı bir kanaldan geliyor
        # (ölçüldü: %47'de durum hâlâ "kuyrukta" görünüyordu).
        "durum": ("bitti" if bitti
                  else "calisiyor" if (analiz_durumu != "queued" or (analiz_isi.get("progress") or 0) > 0)
                  else "kuyrukta"),
        # Ölçek YÜZDE (0-100), SSE `is-durumu.ilerleme` ile aynı (J-62/1).
        "ilerleme": 100 if bitti else (analiz_isi.get("progress") or 0),
        "mesaj": analiz_isi.get("progressMessage"),
        "parmakIzi": sim["parmakIzi"],
        "alan": {"id": sim["alan"]["id"], "ad": sim["alan"]["ad"], "bbox": analiz.get("bounds")},
        "kaynak": {
            "katmanId": katman["id"], "saglayici": katman["saglayici"],
            "cekimTarihi": katman["cekimTarihi"],
            "gsdM": (analiz.get("model") or {}).get("kullanilanGsdM"),
            "gercek": True,
            "not": katman.get("not"),
            "gsdUyarisi": (analiz.get("model") or {}).get("gsdUyarisi"),
        },
        "model": sim["model"],
        "hasar": {
            "maskeUrl": f"/api/road_damage/gorsel/{is_id}/imageDamageMask",
            "bbox": analiz.get("bounds"),
            # Kare üzerinden oran (eski alan) ve görüntünün BOŞ olmayan kısmına
            # göre oran. Drone ortofotosunda kare %61 siyah; arayüz ikincisini
            # göstermeli, kaynak panelinde `gecerliAlanOrani` ile birlikte.
            "hasarliPikselOrani": analiz.get("damageRate"),
            "hasarliPikselOraniGecerli": analiz.get("damageRateValid"),
            "gecerliAlanOrani": analiz.get("validPixelRatio"),
            # Aynı model, deprem ÖNCESİ görüntü: yanlış alarm tabanı. Kontrol
            # koşusu bitmediyse `null`.
            "oncesiKontrol": sim.get("oncesiKontrol"),
        },
        "kapanma": {
            "yaricapM": analiz.get("blockageRadiusM"),
            "kural": analiz.get("closureRule"),
            # Tatbikatın KENDİ kapanmaları (rota grafiği üzerinde, §5'teki kural).
            # Analizin kendi sayısı ayrı tutulur: o, görüntü kutusuyla sınırlı
            # küçük grafikte ve kendi kuralıyla hesaplanır; ikisi karışmasın.
            "kapaliKenarSayisi": (sim.get("grafik") or {}).get("kapaliKenar"),
            "analizKapaliKenarSayisi": analiz.get("blockedRoads"),
            "acikKenarSayisi": analiz.get("openRoads"),
            "kapaliKenarlar": sim.get("kapaliCizgiler"),
            "analizKapaliKenarlar": analiz.get("blockedRoadSegments"),
            # True ise OSM yol katmanı çekilemedi; kesişim sayıları geçersiz.
            # Arayüz bu durumda sayı göstermez, "yol katmanı alınamadı" yazar.
            "yolKatmaniYok": analiz.get("roadLayerMissing"),
        },
        "grafik": sim.get("grafik"),
        "ekipler": sim.get("ekipler"),
        "afetzedeler": sim.get("afetzedeler"),
        "gorevler": (sim["rota"] or {}).get("gorevler"),
        "olcum": (sim["rota"] or {}).get("olcum"),
        # Yalnız varyantlar (R0…bizimSistem); açıklama ve görüş mesafesi ayrı
        # alanlarda, yoksa arayüz onları da varyant sanıyor.
        "referansAjanlar": (sim.get("referansAjanlar") or {}).get("varyantlar"),
        "referansNotu": (sim.get("referansAjanlar") or {}).get("not"),
        "referansGorusMesafesiM": (sim.get("referansAjanlar") or {}).get("gorusMesafesiM"),
        # Arayüz varsayımları yazabilsin diye (her panel kaynağını söyler):
        "donusMaliyetli": (sim.get("referansAjanlar") or {}).get("donusMaliyetli"),
        # Fiilen sürülen yollar: haritada "bilmeseydik böyle sürerdik" çizilir.
        "izlenenYollar": (sim.get("referansAjanlar") or {}).get("izlenenYollar"),
        # Kıyas kutusu: aynı maske, farklı r_h. En sonda dolar; hazır değilse null.
        "yaricapKiyasi": sim.get("yaricapKiyasi"),
        # Yer seviyesi kanallar (kamera/YOLO ve metin/BERTurk). En sonda dolar;
        # hazır değilse null. Fotoğraf ve model çıktısı GERÇEK, metinler ve
        # her ikisinin KONUMU ÜRETİLMİŞ -- her kayıt bunu kendi içinde yazar.
        "kanallar": sim.get("kanallar"),
        "sureler": analiz.get("timingsMs"),
        "gunluk": analiz.get("logLines"),
    }
