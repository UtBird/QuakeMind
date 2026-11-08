"""Afetzede ihbarlari (J-51): hasar fotografi, yazili ihbar, ihtiyac talebi.

Akis iki adimdir:

1. INCELETME. Afetzede fotografini ya da metnini modele verir:
   `POST /api/afetzede/fotograf-analiz`, `POST /api/afetzede/metin-analiz`.
   Fotografta modeli afetzede secer: catlak, bina hasari ya da ikisi. Bu adim
   kayit acmaz ve haritaya bir sey yazmaz. Sonuc yalniz afetzedeye doner ve
   30 dakika sunucu belleginde durur (analiz kimligi).
2. IHBAR. Afetzede sonucu gorup isterse ihbari olusturur: `POST /api/ihbarlar`.
   Modelin ciktisi istemciden ALINMAZ; sunucu kendi bellegindeki sonucu
   kullanir, istemci tespit uyduramaz.

Ihbar depoya yazilir (`ihbarlar`). Model hasar ya da aciliyet cikardiysa ihbar
ortak sozlesmeye bir nokta olarak da duser (kaynak 'kamera' ya da 'metin';
kural 2). Canli akisla konsola 'ihbar' mesaji gider (kural 4).

Ihtiyac talebi (su, gida, barinma...) hasar degildir. Isi haritasina yazilmaz,
konsolda kendi modunda durur.

Bilinen sinir (kural 3): model cikarimi hala istek yolunda. YOLO ~1,4 sn
suruyor; metin modeli adres aramasi (Nominatim) yuzunden birkac saniye
surebilir. Is kuyruguna tasinmasi J-51'de acik madde.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import sqlite3
import threading
import time
import uuid
from collections import OrderedDict
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field

import canli_yayin
import cekirdek as ck
import kimlik
from depo import aktif_depo
from depo.sqlite_surucu import yeni_ihbar_kimligi
from uclar.gorev_bicim import gorev_yayinla, gorevleri_ekle
from uclar.kamera import goruntu_coz, yolo_tespit
from uclar.sozlesme import IHTIYACLAR, SAHA_VE_USTU

yonlendirici = APIRouter(tags=["ihbar"])

TURLER = ("fotograf", "metin", "ihtiyac")
DURUMLAR = ("yeni", "goruldu", "kapandi")
KONUM_KAYNAKLARI = ("gps", "manuel", "mahalle", "metin")

# Afetzedenin secebildigi model -> kamera kodundaki ad.
MODELLER = {"catlak": "catlak", "bina": "bina", "ikisi": "hybrid"}
MODEL_DOSYASI = {"catlak": ("catlak",), "bina": ("bina",), "ikisi": ("catlak", "bina")}

IHTIYAC_ADI = {
    "su": "Su",
    "gida": "Gıda",
    "barinma": "Barınma",
    "isinma": "Isınma",
    "ilac": "İlaç, ilk yardım",
    "tuvalet": "Tuvalet, hijyen",
}

# Sinif -> (afetzedenin dilinde ad, hasar mi, hasar skoru). Skor sinifin
# agirligidir, guven modelin kendi olasiligi; sozlesmede ikisi ayri alan.
# Agirliklar tasarim karari [T]. Eski kamera ucu ikisine de guveni yaziyordu.
SINIF = {
    "crack": ("Çatlak", True, 0.5),
    "0_NoDamage": ("Hasarsız sınıfı", False, 0.0),
    "1_ModerateDamage": ("Orta yapı hasarı", True, 0.6),
    "2_VeryHeavyDamage": ("Ağır yapı hasarı", True, 1.0),
}

EN_UZUN_KENAR = 1600
ANALIZ_OMRU_SN = 30 * 60
ANALIZ_SINIRI = 200
# Kotuye kullanim siniri: bir kisi 10 dakikada en cok 20 ihbar acar.
PENCERE_SN = 10 * 60
KISI_BASI_SINIR = 20


# --- inceleme sonuclari (bellekte, kisa omurlu) ----------------------------

_analizler: "OrderedDict[str, dict]" = OrderedDict()
_kilit = threading.Lock()


def _sakla(kayit: dict) -> str:
    kimlik_ = f"anl-{uuid.uuid4().hex[:12]}"
    simdi = time.time()
    with _kilit:
        for eski in [k for k, v in _analizler.items() if simdi - v["zaman"] > ANALIZ_OMRU_SN]:
            del _analizler[eski]
        while len(_analizler) >= ANALIZ_SINIRI:
            _analizler.popitem(last=False)
        _analizler[kimlik_] = {**kayit, "zaman": simdi, "ihbarId": None}
    return kimlik_


def _analizi_kullan(analiz_id: str, kul: dict, tur: str) -> dict:
    """Incelemeyi ihbar icin ayirir. Ayni inceleme iki ihbar acamaz (cift
    tiklama); ihbar yazilamazsa `_analizi_birak` ayirmayi geri alir."""
    with _kilit:
        kayit = _analizler.get(analiz_id)
        if kayit is None or time.time() - kayit["zaman"] > ANALIZ_OMRU_SN:
            raise HTTPException(
                status_code=410,
                detail="İnceleme sonucu artık yok (30 dakika geçti ya da sunucu yeniden başladı). "
                "Yeniden inceletip gönder.",
            )
        if kayit["kullanici_id"] != kul["id"] or kayit["tur"] != tur:
            raise HTTPException(status_code=404, detail="İnceleme bulunamadı.")
        if kayit["ihbarId"] is not None:
            raise HTTPException(status_code=409, detail="Bu inceleme için ihbar zaten gönderildi.")
        kayit["ihbarId"] = "isleniyor"
        return kayit


def _analizi_birak(analiz_id: str, ihbar_id: Optional[str]) -> None:
    with _kilit:
        kayit = _analizler.get(analiz_id)
        if kayit is not None:
            kayit["ihbarId"] = ihbar_id


# --- yardimcilar -------------------------------------------------------------

def _sn(ms: Optional[float]) -> Optional[float]:
    return None if ms is None else float(ms) / 1000.0


def _ms(sn: Optional[float]) -> Optional[float]:
    return None if sn is None else round(float(sn) * 1000.0)


def _kucult(img):
    import cv2

    boy, en = img.shape[:2]
    oran = EN_UZUN_KENAR / max(boy, en)
    if oran >= 1:
        return img
    return cv2.resize(img, (round(en * oran), round(boy * oran)), interpolation=cv2.INTER_AREA)


def _tespit(d: dict) -> dict:
    ad, hasar, skor = SINIF.get(d.get("sinif", ""), (d.get("label", "?"), True, 0.5))
    return {
        "model": "catlak" if d["model"].startswith("catlak") else "bina",
        "sinif": d.get("sinif"),
        "ad": ad,
        "hasar": hasar,
        "skor": skor,
        "guven": round(d["confidence"] / 100.0, 3),
        "kutu": d["box"],
    }


def _ek(k: dict) -> dict:
    try:
        return json.loads(k["ek"]) if k.get("ek") else {}
    except (TypeError, ValueError):
        return {}


def _cikti(k: dict, afetzede: bool = False) -> dict:
    ek = _ek(k)
    c = {
        "id": k["id"],
        "tur": k["tur"],
        "lon": k["lon"],
        "lat": k["lat"],
        "zaman": _ms(k["zaman"]),
        "durum": k["durum"],
        "metin": k.get("metin"),
        "mahalle": k.get("mahalle"),
        "etiket": k.get("etiket"),
        "skor": k.get("skor"),
        "guven": k.get("guven"),
        "fotografVar": bool(k.get("fotograf_var")),
        "konumKaynagi": ek.get("konumKaynagi"),
        "konumDogrulukM": ek.get("konumDogrulukM"),
        "guncellendi": _ms(k.get("guncellendi")),
    }
    if k["tur"] == "fotograf":
        c["model"] = ek.get("model")
        c["tespitler"] = ek.get("tespitler", [])
        c["en"] = ek.get("en")
        c["boy"] = ek.get("boy")
    elif k["tur"] == "metin":
        c["analiz"] = ek.get("analiz")
    else:
        c["ihtiyaclar"] = ek.get("ihtiyaclar", [])
        c["kisiSayisi"] = ek.get("kisiSayisi")
    # Kimin isledigi konsol icindir; afetzedeye gitmez.
    if not afetzede:
        c["isleyenAd"] = k.get("isleyen_ad")
    return c


def _yayinla(k: dict, hasar_kaynagi: Optional[str] = None) -> None:
    canli_yayin.yayinla(
        "ihbar",
        id=k["id"],
        tur=k["tur"],
        durum=k["durum"],
        lon=k["lon"],
        lat=k["lat"],
        etiket=k.get("etiket"),
        # Konsol yalniz bu kanalin isi izgarasini tazeler.
        hasarKaynagi=hasar_kaynagi,
    )


# --- 1. inceletme --------------------------------------------------------------

class FotografAnalizIstegi(BaseModel):
    imageBase64: str = Field(..., min_length=100, max_length=8_000_000)
    model: str


@yonlendirici.post("/api/afetzede/fotograf-analiz")
def fotograf_analiz(istek: FotografAnalizIstegi, kul: dict = Depends(kimlik.kullanici)):
    """Secilen modeli fotografta kosar. Kayit acmaz, haritaya yazmaz."""
    import cv2

    if istek.model not in MODELLER:
        raise HTTPException(status_code=422, detail="Model: catlak | bina | ikisi")
    img = goruntu_coz(istek.imageBase64)
    if img is None:
        raise HTTPException(status_code=422, detail="Fotoğraf okunamadı; JPEG ya da PNG gönder.")
    img = _kucult(img)

    # Secilen model yuklenemezse sessizce atlanmaz (eski kamera ucu atliyordu
    # ve "tespit yok" diyordu).
    eksik = [m for m in MODEL_DOSYASI[istek.model] if ck.get_yolo(m) is None]
    if eksik:
        raise HTTPException(
            status_code=503,
            detail=f"Model sunucuda yüklü değil: {', '.join(eksik)}. Başka model seç ya da SOS notuna yaz.",
        )

    t0 = time.perf_counter()
    ham, _, _ = yolo_tespit(img, MODELLER[istek.model])
    sure_ms = round((time.perf_counter() - t0) * 1000)
    tespitler = [_tespit(d) for d in ham]

    # Yeniden kodlama fotograftaki EXIF'i (konum, cihaz) de siler.
    ok, jpeg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not ok:
        raise HTTPException(status_code=500, detail="Fotoğraf saklanamadı.")
    boy, en = img.shape[:2]
    analiz_id = _sakla(
        {
            "tur": "fotograf",
            "kullanici_id": kul["id"],
            "model": istek.model,
            "tespitler": tespitler,
            "jpeg": jpeg.tobytes(),
            "en": int(en),
            "boy": int(boy),
        }
    )
    return {
        "analizId": analiz_id,
        "model": istek.model,
        "tespitler": tespitler,
        "hasarVar": any(t["hasar"] for t in tespitler),
        "en": int(en),
        "boy": int(boy),
        "sureMs": sure_ms,
    }


class MetinAnalizIstegi(BaseModel):
    metin: str = Field(..., min_length=5, max_length=1000)


@yonlendirici.post("/api/afetzede/metin-analiz")
def metin_analiz(istek: MetinAnalizIstegi, kul: dict = Depends(kimlik.kullanici)):
    """Metin modelini (BERTurk + adres cozumleme) kosar. Kayit acmaz.

    Eski `/api/nlp/analyze` her cagrida sonucu bellekteki konum listesine ve
    isi haritasina yaziyordu; burada yazma yalniz ihbar olusturulunca olur."""
    metin = istek.metin.strip()
    if len(metin) < 5:
        raise HTTPException(status_code=422, detail="Metin çok kısa.")
    pipeline = ck._get_nlp_pipeline()
    if not pipeline:
        raise HTTPException(status_code=503, detail="Metin modeli sunucuda yüklü değil.")

    t0 = time.perf_counter()
    try:
        with ck.temporary_sys_path(ck.NLP_ROOT), ck.temporary_cwd(ck.NLP_ROOT):
            sonuc = pipeline.process_tweet(metin)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metin modeli çalışmadı: {e}")
    sure_ms = round((time.perf_counter() - t0) * 1000)

    if not sonuc:
        # Model metni afetle ilgisiz buldu; ihbar yine gonderilebilir ama
        # modelin kategorisi, aciliyeti ve adresi yok.
        analiz = {"ilgisiz": True, "kategori": None, "aciliyet": None, "guven": None,
                  "konum": None, "konumMetin": None, "adaylar": []}
    else:
        k = sonuc.get("konum")
        analiz = {
            "ilgisiz": False,
            "kategori": sonuc.get("kategori"),
            "aciliyet": sonuc.get("aciliyet"),
            "guven": sonuc.get("guven_skoru"),
            # Boru hatti [enlem, boylam] doner.
            "konum": {"lat": float(k[0]), "lon": float(k[1])} if k and len(k) == 2 else None,
            "konumMetin": sonuc.get("konum_metin"),
            "adaylar": list(sonuc.get("konum_adaylari") or [])[:6],
        }
    analiz_id = _sakla({"tur": "metin", "kullanici_id": kul["id"], "metin": metin, "analiz": analiz})
    return {"analizId": analiz_id, **analiz, "sureMs": sure_ms}


# --- 2. ihbar --------------------------------------------------------------------

class IhbarIstegi(BaseModel):
    tur: str
    analizId: Optional[str] = None
    # Fotograf ve ihtiyacta afetzedenin notu; yazili ihbarda ihbarin kendisi.
    metin: Optional[str] = Field(None, max_length=1000)
    lon: Optional[float] = None
    lat: Optional[float] = None
    konumKaynagi: str
    konumDogrulukM: Optional[float] = Field(None, ge=0, le=100000)
    mahalle: Optional[str] = Field(None, max_length=120)
    ihtiyaclar: Optional[list[str]] = None
    kisiSayisi: Optional[int] = Field(None, ge=1, le=500)


def _tekrar_ihbar(depo, kul: dict, anahtar: str, ozet: str) -> Optional[dict]:
    kayit = depo.ihbar_istemci_anahtari(kul["id"], anahtar)
    if kayit is None:
        return None
    if kayit["istek_ozeti"] != ozet:
        raise HTTPException(status_code=409, detail="Bu Idempotency-Key baska bir ihbar icin kullanildi.")
    return {**_cikti(kayit, afetzede=kul["rol"] == "afetzede"), "gorevler": []}


@yonlendirici.post("/api/ihbarlar", status_code=201)
def ihbar_ac(
    istek: IhbarIstegi,
    kul: dict = Depends(kimlik.kullanici),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    if istek.tur not in TURLER:
        raise HTTPException(status_code=422, detail="Tür: fotograf | metin | ihtiyac")
    if istek.konumKaynagi not in KONUM_KAYNAKLARI:
        raise HTTPException(status_code=422, detail="konumKaynagi: gps | manuel | mahalle | metin")
    if istek.konumKaynagi == "metin" and istek.tur != "metin":
        raise HTTPException(status_code=422, detail="Metindeki adres yalnız yazılı ihbarda kullanılır.")

    depo = aktif_depo()
    ozet = None
    if idempotency_key is not None:
        if not re.fullmatch(r"[A-Za-z0-9._:-]{8,128}", idempotency_key):
            raise HTTPException(status_code=422, detail="Idempotency-Key 8-128 karakter, harf/rakam/._:- olmali.")
        # JSON anahtar sirasindan bagimsiz, kullaniciya ozel tekrar kontrolu.
        icerik = json.dumps(istek.model_dump(exclude_none=True), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        ozet = hashlib.sha256(icerik.encode("utf-8")).hexdigest()
        onceki = _tekrar_ihbar(depo, kul, idempotency_key, ozet)
        if onceki is not None:
            return onceki

    son = depo.ihbar_listele(baslangic=time.time() - PENCERE_SN, kullanici_id=kul["id"], sinir=KISI_BASI_SINIR)
    if len(son) >= KISI_BASI_SINIR:
        raise HTTPException(
            status_code=429,
            detail="Son 10 dakikada çok sayıda ihbar gönderdin; biraz sonra yeniden dene. "
            "Hayati tehlike varsa SOS gönder ya da 112'yi ara.",
        )

    metin = (istek.metin or "").strip() or None

    # Tur kurallari (analiz ayirmadan once; hatali istek incelemeyi harcamasin).
    if istek.tur == "fotograf" and not istek.analizId:
        raise HTTPException(status_code=422, detail="Önce fotoğrafı inceletmelisin (analizId).")
    if istek.tur == "metin" and not metin:
        raise HTTPException(status_code=422, detail="İhbar metni boş.")
    if istek.tur == "ihtiyac":
        if istek.analizId:
            raise HTTPException(status_code=422, detail="İhtiyaç talebinde inceleme olmaz.")
        if not istek.ihtiyaclar or any(i not in IHTIYACLAR for i in istek.ihtiyaclar):
            raise HTTPException(status_code=422, detail=f"İhtiyaç: {' | '.join(IHTIYACLAR)} (en az biri)")

    if istek.konumKaynagi != "metin":
        if istek.lon is None or istek.lat is None:
            raise HTTPException(status_code=422, detail="Konum gerekli.")
        if not (-90.0 <= istek.lat <= 90.0) or not (-180.0 <= istek.lon <= 180.0):
            raise HTTPException(status_code=422, detail="Geçersiz koordinat.")

    analiz = _analizi_kullan(istek.analizId, kul, istek.tur) if istek.analizId else None
    try:
        if istek.tur == "metin" and analiz is not None and analiz["metin"] != metin:
            raise HTTPException(status_code=409, detail="Metin incelendikten sonra değişti; yeniden inceletin.")

        if istek.konumKaynagi == "metin":
            k = analiz["analiz"].get("konum") if analiz else None
            if not k:
                raise HTTPException(status_code=422, detail="Metinde konum bulunamadı; kendi konumunu seç.")
            lon, lat = k["lon"], k["lat"]
        else:
            lon, lat = float(istek.lon), float(istek.lat)

        ek: dict = {"konumKaynagi": istek.konumKaynagi}
        if istek.konumKaynagi == "gps" and istek.konumDogrulukM is not None:
            ek["konumDogrulukM"] = round(istek.konumDogrulukM)
        zaman = time.time()
        ihbar_id = yeni_ihbar_kimligi()
        etiket, skor, guven, fotograf = None, None, None, None
        hasar_kaynagi = None

        if istek.tur == "fotograf":
            tespitler = analiz["tespitler"]
            ek.update(model=analiz["model"], tespitler=tespitler, en=analiz["en"], boy=analiz["boy"])
            fotograf = (analiz["jpeg"], analiz["en"], analiz["boy"])
            hasarlar = [t for t in tespitler if t["hasar"]]
            if hasarlar:
                # En agir sinif, esitse en guvenli tespit ihbari temsil eder.
                en_iyi = max(hasarlar, key=lambda t: (t["skor"], t["guven"]))
                etiket, skor, guven = en_iyi["ad"], en_iyi["skor"], en_iyi["guven"]
                hasar_kaynagi = "kamera"
            else:
                etiket = "Model hasar işaretlemedi"
        elif istek.tur == "metin":
            a = analiz["analiz"] if analiz else None
            ek["analiz"] = a
            if a is None:
                etiket = "Model incelemedi"
            elif a["ilgisiz"]:
                etiket = "Model: afetle ilgisiz"
            else:
                etiket = a["kategori"]
                skor = round(float(a["aciliyet"]) / 5.0, 2) if a.get("aciliyet") else None
                guven = a.get("guven")
                if skor is not None and guven is not None:
                    hasar_kaynagi = "metin"
        else:
            ihtiyaclar = [i for i in IHTIYACLAR if i in set(istek.ihtiyaclar or [])]
            ek.update(ihtiyaclar=ihtiyaclar, kisiSayisi=istek.kisiSayisi)
            etiket = ", ".join(IHTIYAC_ADI[i] for i in ihtiyaclar)

        try:
            kayit = depo.ihbar_ekle(
                ihbar_id=ihbar_id,
                tur=istek.tur,
                lon=lon,
                lat=lat,
                kullanici_id=kul["id"],
                metin=metin,
                mahalle=istek.mahalle if istek.konumKaynagi == "mahalle" else None,
                etiket=etiket,
                skor=skor,
                guven=guven,
                ek=ek,
                fotograf=fotograf,
                zaman=zaman,
                istemci_anahtari=idempotency_key,
                istek_ozeti=ozet,
                hasar_noktasi={"kaynak": hasar_kaynagi, "skor": skor, "guven": guven, "etiket": etiket}
                if hasar_kaynagi else None,
            )
        except sqlite3.IntegrityError:
            # Baska worker/process ayni anahtari ilk kontrolumuzden sonra
            # kaydetmis olabilir. Veritabani UNIQUE indeksi son savunmadir.
            if idempotency_key:
                tekrar = _tekrar_ihbar(depo, kul, idempotency_key, ozet)
                if tekrar is not None:
                    if istek.analizId:
                        _analizi_birak(istek.analizId, tekrar["id"])
                    return tekrar
            raise
    except BaseException:
        if istek.analizId:
            _analizi_birak(istek.analizId, None)
        raise
    if istek.analizId:
        _analizi_birak(istek.analizId, kayit["id"])

    _yayinla(kayit, hasar_kaynagi)
    return {**_cikti(kayit, afetzede=kul["rol"] == "afetzede"), "gorevler": []}


@yonlendirici.get("/api/ihbarlar")
def ihbar_listesi(
    baslangic: Optional[float] = None,
    bitis: Optional[float] = None,
    tur: Optional[str] = None,
    durum: Optional[str] = None,
    sinir: int = Query(default=2000, ge=1, le=5000),
    kul: dict = Depends(kimlik.kullanici),
):
    """Afetzede yalniz kendi ihbarini gorur; sahada ve ustunde herkes hepsini."""
    if tur and tur not in TURLER:
        raise HTTPException(status_code=422, detail="Tür: fotograf | metin | ihtiyac")
    if durum and durum not in DURUMLAR:
        raise HTTPException(status_code=422, detail="Durum: yeni | goruldu | kapandi")
    afetzede = kul["rol"] == "afetzede"
    kayitlar = aktif_depo().ihbar_listele(
        baslangic=_sn(baslangic),
        bitis=_sn(bitis),
        tur=tur,
        durum=durum,
        kullanici_id=kul["id"] if afetzede else None,
        sinir=sinir,
    )
    # Ihbara giden ekip (J-54); afetzede kendi ihbarininkini gorur.
    return gorevleri_ekle("ihbar", kayitlar, [_cikti(k, afetzede) for k in kayitlar], afetzede)


@yonlendirici.get("/api/ihbarlar/{ihbar_id}/fotograf")
def ihbar_fotografi(ihbar_id: str, kul: dict = Depends(kimlik.kullanici)):
    """Fotograf JSON icinde doner: istek jetonla gider, <img> adresine jeton
    yazilmaz (kural 5)."""
    depo = aktif_depo()
    kayit = depo.ihbar_bul(ihbar_id)
    # Afetzede baskasinin ihbarinin var olup olmadigini da ogrenmez.
    if kayit is None or (kul["rol"] == "afetzede" and kayit.get("kullanici_id") != kul["id"]):
        raise HTTPException(status_code=404, detail="İhbar bulunamadı.")
    if kul["rol"] != "afetzede" and kul["rol"] not in SAHA_VE_USTU:
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok.")
    foto = depo.ihbar_fotografi(ihbar_id)
    if foto is None:
        raise HTTPException(status_code=404, detail="Bu ihbarın fotoğrafı yok.")
    return {
        "veri": "data:image/jpeg;base64," + base64.b64encode(foto["veri"]).decode("ascii"),
        "en": foto["en"],
        "boy": foto["boy"],
    }


class DurumIstegi(BaseModel):
    durum: str


@yonlendirici.post("/api/ihbarlar/{ihbar_id}/durum")
def ihbar_durumu(
    ihbar_id: str,
    istek: DurumIstegi,
    kul: dict = Depends(kimlik.rol_gerektir(*SAHA_VE_USTU)),
):
    """Konsol ihbari isler: 'goruldu' ya da 'kapandi'. Geri gidilmez.
    Kapaninca ihbara giden ekiplerin gorevi de biter (J-54)."""
    if istek.durum not in ("goruldu", "kapandi"):
        raise HTTPException(status_code=422, detail="Durum: goruldu | kapandi")
    depo = aktif_depo()
    if depo.ihbar_bul(ihbar_id) is None:
        raise HTTPException(status_code=404, detail="İhbar bulunamadı.")
    degisti, biten = depo.ihbar_durum(ihbar_id, istek.durum, kul["id"], kul.get("ad_soyad"))
    if not degisti:
        raise HTTPException(status_code=409, detail="İhbar zaten bu durumda ya da kapanmış.")
    kayit = depo.ihbar_bul(ihbar_id)
    _yayinla(kayit)
    for gorev_id in biten:
        gorev_yayinla(depo.gorev_bul(gorev_id), "kapandi")
    return gorevleri_ekle("ihbar", [kayit], [_cikti(kayit)])[0]
