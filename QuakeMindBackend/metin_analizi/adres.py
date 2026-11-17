"""Metindeki adresi yerel dizinde çözer (J-170). Ağa çıkmaz.

Eskiden adres önce il/ilçe sözlüğünde, bulunamazsa OpenStreetMap Nominatim'de
aranıyordu. Üç sorun vardı:
  * afetzedenin yazdığı adres üçüncü tarafa gidiyordu (J-167 S-5);
  * istek 1,2 sn gecikmeli, internet yoksa hiç çözülmüyordu (P-2);
  * "Antakya Armutlu mahallesinde" yazısı ekrana mahalle gibi çıkıyor, koordinat
    ise ilçe merkezi oluyordu (yanıltıcı).

Şimdi: il/ilçe merkezi, mahalle/köy ve adlı sokaklar yerel dizinden
(`veri/adres_dizini.json.gz`, OSM). Sonuç hangi DÜZEYDE bulunduğunu ve ne kadar
belirsiz olduğunu açıkça söyler; çözülen adın kendisi dizinden yazılır,
metindeki ham parça değil.

Karar sırası: en özgül tutarlı eşleşme. Sokak, ancak aynı metinde geçen mahalle
ya da ilçeyle tutarlıysa (ya da adı dizinde tekse) seçilir; yoksa mahalle
düzeyinde kalınır ve not düşülür. Aynı adlı birden çok mahalle varsa ve metin
ayırt etmiyorsa konum seçilmez, adaylar döner (uydurma yok).
"""
from __future__ import annotations

import gzip
import json
import math
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional

from .normal import ek_adaylari, katla, levenshtein

DIZIN = Path(__file__).resolve().parent / "veri" / "adres_dizini.json.gz"

# Tür sözcükleri (katlanmış, eklerden arındırılmış kök -> tür).
TUR_SOZCUGU = {
    "mahalle": "mahalle", "mahallesi": "mahalle", "mah": "mahalle", "mh": "mahalle",
    "sokak": "sokak", "sokagi": "sokak", "sok": "sokak", "sk": "sokak",
    "cadde": "cadde", "caddesi": "cadde", "cad": "cadde", "cd": "cadde",
    "bulvar": "bulvar", "bulvari": "bulvar",
    "meydan": "meydan", "meydani": "meydan",
    "koy": "koy", "koyu": "koy",
}
# Tür sözcüğünün çekimli biçimleri: "mahallesinde", "sokakta", "caddesinde", "köyünde".
# Tür sözcüğünün çekimli biçimleri: "mahallesinde", "sokakta", "caddesindeyiz",
# "köyünde". Kökten sonra en çok 7 harflik ek kabul edilir.
_TUR_EK = re.compile(r"^(mahallesi|mahalle|sokag|sokak|caddesi|cadde|bulvari|bulvar|meydani|meydan|koyu|koy)([a-z]{0,7})$")
_TUR_KOK = {"sokag": "sokak", "mahallesi": "mahalle", "caddesi": "cadde", "bulvari": "bulvar", "meydani": "meydan",
            "koyu": "koy"}

# Yalın (türsüz) geçtiğinde yer adı sayılmayacak yaygın sözcükler: "merkez",
# "yeni" gibi adlar onlarca mahallede var ve cümlede başka anlamda geçer.
YALIN_YASAK = {
    "merkez", "yeni", "yeni mahalle", "cumhuriyet", "bahce", "carsi", "istasyon", "ova",
    "pazar", "bina", "okul", "cami", "hastane", "koy", "sehir", "ilce", "mahalle", "sokak",
    "yol", "kopru", "park", "saray", "kale", "tepe", "dere", "baglar", "bag", "ciftlik",
    "acil", "ekip", "yardim", "su", "ev", "kat", "aile", "cocuk",
}

BELIRSIZLIK_M = {"sokak": 400, "mahalle": 800, "koy": 1500, "kasaba": 2500, "sehir": 5000, "ilce": 5000, "il": 30000}
TUTARLILIK_M = {"ilce": 12000, "il": 80000, "mahalle": 2500}


def mesafe_m(a, b) -> float:
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    h = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2)
    return 6371000 * 2 * math.asin(math.sqrt(h))


@dataclass
class Sozcuk:
    ham: str
    katli: str
    bas: int
    son: int
    buyuk: bool


@dataclass
class Eslesme:
    tur: str                 # il | ilce | mahalle | koy | kasaba | sehir | sokak
    kayitlar: list           # dizin kayitlari (ayni ad birden cok yerde olabilir)
    bas: int                 # metindeki karakter araligi
    son: int
    metin: str
    acik: bool = False       # tur sozcuguyle mi gecti ("X Mahallesi")
    bulanik: bool = False


@dataclass
class Sonuc:
    konum: Optional[list] = None
    duzey: Optional[str] = None
    belirsizlik_m: Optional[int] = None
    adres: dict = field(default_factory=dict)
    konum_metin: Optional[str] = None
    eslesmeler: list = field(default_factory=list)
    adaylar: list = field(default_factory=list)
    notlar: list = field(default_factory=list)

    def sozluk(self) -> dict:
        return {
            "konum": self.konum,
            "konumDuzeyi": self.duzey,
            "belirsizlikM": self.belirsizlik_m,
            "adres": self.adres,
            "konumMetin": self.konum_metin,
            "adresEslesmeleri": self.eslesmeler,
            "adresAdaylari": self.adaylar,
            "adresNotlari": self.notlar,
            "adresKaynagi": "yerel adres dizini (OpenStreetMap, ağ yok)",
        }


class AdresDizini:
    def __init__(self, yol: Path = DIZIN):
        with gzip.open(yol, "rt", encoding="utf-8") as f:
            d = json.load(f)
        self.kunye = d["_kunye"]
        self.iller = d["iller"]
        self.ilceler = d["ilceler"]
        self.yerler = d["yerler"]
        self.sokaklar = d["sokaklar"]
        self.ad_indeksi: dict[str, list[tuple[str, dict]]] = {}
        for il in self.iller:
            self._ekle(il["ad"], "il", il)
        for x in self.ilceler:
            self._ekle(x["ad"], "ilce", x)
        for x in self.yerler:
            tur = {"mahalle": "mahalle", "köy": "koy", "kasaba": "kasaba", "şehir": "sehir"}.get(x["tur"], "mahalle")
            self._ekle(x["ad"], tur, x)
        # Sokaklar: tam ad ("ataturk cadde") ile; tür sözcüğü köke indirilir.
        self.sokak_indeksi: dict[str, list[dict]] = {}
        for s in self.sokaklar:
            self.sokak_indeksi.setdefault(self.sokak_anahtari(s["ad"]), []).append(s)
        self._ilk_harf: dict[str, list[str]] = {}
        for k in self.ad_indeksi:
            self._ilk_harf.setdefault(k[:1], []).append(k)
        self.en_uzun_ad = max(len(k.split()) for k in self.ad_indeksi)

    def _ekle(self, ad, tur, kayit):
        self.ad_indeksi.setdefault(katla(ad), []).append((tur, kayit))

    @staticmethod
    def sokak_anahtari(ad: str) -> str:
        parca = katla(ad).split()
        return " ".join(_TUR_KOK.get(p, TUR_SOZCUGU.get(p, p)) for p in parca)

    def bul(self, anahtar: str, bulanik: bool) -> list[tuple[str, dict]]:
        if anahtar in self.ad_indeksi:
            return self.ad_indeksi[anahtar]
        if not bulanik or len(anahtar) < 5:
            return []
        sinir = 1 if len(anahtar) < 8 else 2
        en_iyi, en_iyi_d = [], sinir + 1
        for k in self._ilk_harf.get(anahtar[:1], []):
            d = levenshtein(anahtar, k, sinir)
            if d < en_iyi_d:
                en_iyi, en_iyi_d = self.ad_indeksi[k], d
        return en_iyi


@lru_cache(maxsize=1)
def dizin() -> AdresDizini:
    return AdresDizini()


def _sozcukler(metin: str) -> list[Sozcuk]:
    out = []
    for m in re.finditer(r"\w+(?:['’]\w+)?\.?", metin):
        ham = m.group(0)
        katli = katla(ham)
        if not katli:
            continue
        out.append(Sozcuk(ham=ham, katli=katli, bas=m.start(), son=m.end(), buyuk=ham[:1].isupper()))
    return out


def _tur_sozcugu(s: Sozcuk) -> Optional[str]:
    k = s.katli.replace(" ", "")
    if k in TUR_SOZCUGU:
        return TUR_SOZCUGU[k]
    m = _TUR_EK.match(k)
    if m:
        kok = _TUR_KOK.get(m.group(1), m.group(1))
        return TUR_SOZCUGU.get(kok, kok)
    return None


def eslesmeleri_bul(metin: str, d: AdresDizini) -> list[Eslesme]:
    sz = _sozcukler(metin)
    bulunan: list[Eslesme] = []
    kullanilan: set[int] = set()

    # 1) Türlü açık anma: "<ad> Mahallesi", "<ad> Sokak", "<ad> Caddesi".
    for i, s in enumerate(sz):
        tur = _tur_sozcugu(s)
        if tur is None or i == 0:
            continue
        for n in (3, 2, 1):
            j = i - n
            if j < 0 or any(k in kullanilan for k in range(j, i)):
                continue
            ad_parca = [x.katli for x in sz[j:i]]
            # Meydan da sokak dizininde ("Cumhuriyet Meydanı", OSM yol adı).
            if tur in ("sokak", "cadde", "bulvar", "meydan"):
                anahtar = " ".join(ad_parca + [tur])
                kayitlar = d.sokak_indeksi.get(anahtar)
                if kayitlar:
                    bulunan.append(Eslesme("sokak", kayitlar, sz[j].bas, s.son, metin[sz[j].bas:s.son], acik=True))
                    kullanilan.update(range(j, i + 1))
                    break
            else:
                hedef = {"mahalle": ("mahalle", "kasaba", "sehir"), "koy": ("koy",)}[tur]
                ad = " ".join(ad_parca)
                for bul_ad in [ad] + ek_adaylari(ad)[1:]:
                    kayitlar = [(t, k) for t, k in d.bul(bul_ad, bulanik=True) if t in hedef]
                    if kayitlar:
                        bulunan.append(Eslesme(kayitlar[0][0], [k for _, k in kayitlar], sz[j].bas, s.son,
                                               metin[sz[j].bas:s.son], acik=True,
                                               bulanik=bul_ad not in d.ad_indeksi))
                        kullanilan.update(range(j, i + 1))
                        break
                if kullanilan.issuperset(range(j, i + 1)):
                    break
        else:
            # Türlü anma var ama dizinde yok: not düşülür (uydurma yok).
            onceki = sz[i - 1] if i >= 1 else None
            ozel_ad = onceki is not None and (onceki.buyuk or onceki.katli.isdigit())
            if (tur in ("mahalle", "koy", "sokak", "cadde", "meydan") and ozel_ad and (i - 1) not in kullanilan
                    and onceki.katli not in YALIN_YASAK):
                bulunan.append(Eslesme("bilinmeyen_" + tur, [], onceki.bas, s.son, metin[onceki.bas:s.son], acik=True))

    # 2) Yalın anma: il, ilçe, mahalle adları (ek atılarak: "Nurdağı'nda", "antakyada").
    i = 0
    while i < len(sz):
        if i in kullanilan or _tur_sozcugu(sz[i]):
            i += 1
            continue
        eslesti = False
        for n in range(min(d.en_uzun_ad, 3), 0, -1):
            if i + n > len(sz) or any(k in kullanilan for k in range(i, i + n)):
                continue
            parca = [x.katli for x in sz[i:i + n]]
            son_adaylar = ek_adaylari(parca[-1])
            for son in son_adaylar:
                anahtar = " ".join(parca[:-1] + [son])
                if anahtar in YALIN_YASAK:
                    continue
                # Bulanık (yazım hatası toleranslı) eşleşme yalnız büyük harfle
                # başlayan sözcükte: "altından" -> Altındağ, "bitmiş" -> Bitlis
                # gibi sıradan sözcükler yer adına çekilmesin.
                kayitlar = d.bul(anahtar, bulanik=len(anahtar) >= 6 and sz[i].buyuk)
                il_ilce = [(t, k) for t, k in kayitlar if t in ("il", "ilce")]
                yer = [(t, k) for t, k in kayitlar if t not in ("il", "ilce")]
                # Yalın mahalle adı yalnız TAM eşleşmeyse (bulanık eşleşme cümle
                # başındaki büyük harfli sözcüğü benzer adlı bir mahalleye çekerdi).
                secilen = il_ilce or (yer if anahtar in d.ad_indeksi else [])
                if secilen:
                    turler = {t for t, _ in secilen}
                    tur = "il" if "il" in turler else "ilce" if "ilce" in turler else secilen[0][0]
                    bulunan.append(Eslesme(tur, [k for t, k in secilen if t == tur], sz[i].bas, sz[i + n - 1].son,
                                           metin[sz[i].bas:sz[i + n - 1].son],
                                           bulanik=anahtar not in d.ad_indeksi))
                    kullanilan.update(range(i, i + n))
                    i += n
                    eslesti = True
                    break
            if eslesti:
                break
        if not eslesti:
            i += 1
    return sorted(bulunan, key=lambda e: e.bas)


def _ad(k: dict) -> str:
    return k["ad"]


def coz(metin: str, d: Optional[AdresDizini] = None) -> Sonuc:
    d = d or dizin()
    es = eslesmeleri_bul(metin, d)
    s = Sonuc()
    s.eslesmeler = [{"tur": e.tur, "metin": e.metin, "bas": e.bas, "son": e.son, "bulanik": e.bulanik} for e in es]
    for e in es:
        if e.tur.startswith("bilinmeyen_"):
            s.notlar.append(f"“{e.metin}” yerel adres dizininde yok; bu ad konuma çevrilemedi.")

    iller = [k for e in es if e.tur == "il" for k in e.kayitlar]
    ilceler = [k for e in es if e.tur == "ilce" for k in e.kayitlar]
    if iller:
        ilceler = [x for x in ilceler if any(x["il"] == il["ad"] for il in iller)] or ilceler
    # Bağlam noktaları: tutarlılık için (il > ilçe).
    baglam = [(x, "ilce") for x in ilceler] + [(x, "il") for x in iller]

    def tutarli(k, sinir_m=None):
        if not baglam:
            return True
        return any(mesafe_m((k["lat"], k["lon"]), (b["lat"], b["lon"])) <= (sinir_m or TUTARLILIK_M[t])
                   for b, t in baglam)

    yer_es = [e for e in es if e.tur in ("mahalle", "koy", "kasaba", "sehir")]
    yerler = []
    for e in yer_es:
        uygun = [k for k in e.kayitlar if tutarli(k)]
        if uygun:
            yerler.append((e, uygun))
    if not yerler and baglam:
        # Açıkça yazılmış mahalle ("X Mahallesi") uzaktaki yalın bir il/ilçe adı
        # yüzünden elenmez: açık anma daha özgül ve daha güvenilir kanıttır.
        acik = [(e, e.kayitlar) for e in yer_es if e.acik and len(e.kayitlar) == 1]
        if acik:
            yerler = acik
            s.notlar.append("Metindeki il/ilçe adı mahalleyle aynı yerde değil; mahalle esas alındı.")
            ilceler, iller = [], []

    sokak_es = [e for e in es if e.tur == "sokak"]
    secim = None  # (duzey, kayit, eslesme)

    # Sokak: metindeki mahalleye bağlı kayıt (dizinde o mahalleye atanmış ya da
    # merkezine 800 m'den yakın); mahalle yoksa ilçede tek sokaksa; o da yoksa
    # adı bütün dizinde tekse. "5. Sokak" gibi sık adlar böylece başka
    # mahalledeki aynı adlı sokağa gitmez.
    for e in sokak_es:
        adaylar = e.kayitlar
        if yerler:
            mah = [(m, d.yerler.index(m)) for _, ms in yerler for m in ms]
            bagli = [k for k in adaylar if any(k.get("yer") == mi for _, mi in mah)]
            yakin = [k for k in adaylar
                     if any(mesafe_m((k["lat"], k["lon"]), (m["lat"], m["lon"])) <= 800 for m, _ in mah)]
            birlesik = _tek_sokak(bagli or yakin)
            if birlesik is not None:
                secim = ("sokak", birlesik, e)
                break
            if bagli or yakin:
                s.notlar.append(f"“{e.metin}” mahallede birden çok yerde geçiyor; sokak seçilmedi.")
            else:
                s.notlar.append(f"“{e.metin}” bu mahallede bulunamadı; mahalle düzeyinde kalındı.")
        elif ilceler:
            uygun = [k for k in adaylar
                     if any(mesafe_m((k["lat"], k["lon"]), (x["lat"], x["lon"])) <= TUTARLILIK_M["ilce"] for x in ilceler)]
            birlesik = _tek_sokak(uygun)
            if birlesik is not None:
                secim = ("sokak", birlesik, e)
                break
            if uygun:
                s.notlar.append(f"“{e.metin}” bu ilçede birden çok yerde var; mahalle yazılmadığı için sokak seçilmedi.")
        elif _tek_sokak(adaylar) is not None:
            secim = ("sokak", _tek_sokak(adaylar), e)
            break
        else:
            s.notlar.append(f"“{e.metin}” {len(adaylar)} ayrı yerde var; mahalle ya da ilçe yazılmadığı için sokak seçilmedi.")

    if secim is None and yerler:
        # En özgül yer: mahalle/köy > kasaba > şehir; aynı ad birden çok yerdeyse belirsiz.
        sira = {"mahalle": 0, "koy": 1, "kasaba": 2, "sehir": 3}
        e, ks = min(yerler, key=lambda x: sira[x[0].tur])
        if len(ks) == 1:
            secim = ({"koy": "koy"}.get(e.tur, "mahalle" if e.tur == "mahalle" else e.tur), ks[0], e)
        else:
            s.notlar.append(f"“{e.metin}” {len(ks)} ayrı yerde var; ilçe yazılmadığı için hangisi olduğu seçilmedi.")
            s.adaylar = [{"konumMetin": _yer_metni(k), "konum": [k["lat"], k["lon"]], "duzey": e.tur} for k in ks[:6]]

    if secim is None and ilceler:
        if len(ilceler) == 1:
            e = next(e for e in es if e.tur == "ilce")
            secim = ("ilce", ilceler[0], e)
        else:
            s.adaylar = [{"konumMetin": f"{k['ad']}, {k['il']}", "konum": [k["lat"], k["lon"]], "duzey": "ilce"}
                         for k in ilceler[:6]]
            s.notlar.append("Aynı adlı birden çok ilçe var; il yazılmadığı için seçilmedi.")
    if secim is None and len(iller) == 1:
        e = next(e for e in es if e.tur == "il")
        secim = ("il", iller[0], e)

    if secim is None:
        return s

    duzey, k, e = secim
    s.konum = [k["lat"], k["lon"]]
    s.duzey = duzey
    # İlçe yalnız METİNDE yazıldıysa gösterilir: dizinde mahalle sınırı yok, ilçe
    # en yakın ilçe merkezinden tahmin edilirdi (Elektrik Mah. Defne'de ama
    # Antakya merkezine daha yakın). Tahmini ilçe yazılmaz.
    metindeki_ilce = ilceler[0]["ad"] if len(ilceler) == 1 else None
    il = (iller[0]["ad"] if len(iller) == 1 else None) or (ilceler[0]["il"] if len(ilceler) == 1 else None) or k.get("il")
    if duzey == "sokak":
        s.belirsizlik_m = max(BELIRSIZLIK_M["sokak"], min(int(k.get("yayilimM") or 0), 2000))
        mah = next((m["ad"] for _, ms in yerler for m in ms), None)
        s.adres = {"sokak": k["ad"], "mahalle": mah, "ilce": metindeki_ilce, "il": il}
    elif duzey == "il":
        s.belirsizlik_m = BELIRSIZLIK_M["il"]
        s.adres = {"il": k["ad"]}
        s.notlar.append("Yalnız il bulundu: konum il merkezidir, olay yeri değildir.")
    elif duzey == "ilce":
        s.belirsizlik_m = BELIRSIZLIK_M["ilce"]
        s.adres = {"ilce": k["ad"], "il": k["il"]}
        s.notlar.append("Yalnız ilçe bulundu: konum ilçe merkezidir, olay yeri değildir.")
    else:
        s.belirsizlik_m = BELIRSIZLIK_M.get(duzey, 1000)
        anahtar = "mahalle" if duzey == "mahalle" else "yer"
        s.adres = {anahtar: k["ad"], "ilce": metindeki_ilce, "il": il}
        if duzey == "mahalle":
            s.notlar.append("Konum mahallenin merkezidir; sokak ya da bina bilinmiyor.")
    s.adres = {a: b for a, b in s.adres.items() if b}
    s.konum_metin = _adres_metni(s.adres, duzey)
    return s


def _tek_sokak(kayitlar: list) -> Optional[dict]:
    """Kayıtlar tek bir sokağın parçalarıysa (mahalle sınırını aşan uzun cadde;
    birbirine 2 km'den yakın) tek kayda birleştirir; ayrı yerlerdeyse None."""
    if not kayitlar:
        return None
    if len(kayitlar) == 1:
        return kayitlar[0]
    for a in kayitlar:
        for b in kayitlar:
            if mesafe_m((a["lat"], a["lon"]), (b["lat"], b["lon"])) > 2000:
                return None
    toplam = sum(k["parca"] for k in kayitlar)
    lat = sum(k["lat"] * k["parca"] for k in kayitlar) / toplam
    lon = sum(k["lon"] * k["parca"] for k in kayitlar) / toplam
    yayilim = max(mesafe_m((lat, lon), (k["lat"], k["lon"])) + k["yayilimM"] for k in kayitlar)
    en_buyuk = max(kayitlar, key=lambda k: k["parca"])
    return {**en_buyuk, "lat": round(lat, 5), "lon": round(lon, 5), "yayilimM": round(yayilim), "parca": toplam}


def _yer_metni(k: dict) -> str:
    return ", ".join(x for x in (k["ad"], k.get("ilce"), k.get("il")) if x)


def _adres_metni(adres: dict, duzey: str) -> str:
    parca = []
    if adres.get("sokak"):
        parca.append(adres["sokak"])
    if adres.get("mahalle"):
        parca.append(f"{adres['mahalle']} Mah.")
    if adres.get("yer"):
        parca.append(adres["yer"])
    for a in ("ilce", "il"):
        if adres.get(a) and adres[a] not in parca:
            parca.append(adres[a])
    return ", ".join(parca)
