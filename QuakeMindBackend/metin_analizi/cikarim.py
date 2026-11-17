"""Metinden yapılandırılmış bilgi (J-170): kişi sayısı, ihtiyaçlar, sinyaller.

Kural tabanlı ve belirlenimci: aynı metin her zaman aynı sonucu verir, model
koşmaz. Her bulgu metindeki yeriyle (bas/son) döner; ekran o parçayı vurgular.
Bulgular sınıflandırmayı ya da aciliyeti DEĞİŞTİRMEZ (o karar ölçülmeden
verilmez, CLAUDE.md §8); koordinatöre "metinde ne yazıyor"u gösterir.
"""
from __future__ import annotations

import re

from .normal import katla

SAYI = {
    "bir": 1, "iki": 2, "uc": 3, "dort": 4, "bes": 5, "alti": 6, "yedi": 7, "sekiz": 8,
    "dokuz": 9, "on": 10, "onbir": 11, "oniki": 12, "yirmi": 20, "otuz": 30, "elli": 50, "yuz": 100,
}
# Sayıdan sonra gelen ve kişi/hane bildiren sözcükler (katlanmış kök -> ad).
KISI_SOZCUGU = {
    "kisi": "kişi", "insan": "kişi", "nufus": "kişi", "kisilik": "kişi",
    "cocuk": "çocuk", "bebek": "bebek", "yasli": "yaşlı", "hasta": "hasta", "yarali": "yaralı",
    "aile": "aile", "hane": "hane", "kadin": "kadın", "erkek": "erkek", "ogrenci": "öğrenci",
    "cift": "çift", "olu": "ölü", "ceset": "ölü",
}
# Sayının adın ARDINDAN geldiği kalıp: "ölüler var 2 tane", "yaralı üç tane".
# Yalnız "tane"/"adet" ile: "çocuk 5 yaşında" gibi cümleler sayılmasın.
SAYAC_SOZCUGU = ("tane", "adet")

# İhtiyaç kimlikleri sözleşmedeki IHTIYACLAR ile aynı (uclar/sozlesme.py).
IHTIYAC = {
    "su": ["su", "suyu", "susuz", "icme suyu"],
    "gida": ["gida", "yemek", "ekmek", "erzak", "mama", "bebek mamasi", "yiyecek", "acliktan", "ac kaldik"],
    "barinma": ["cadir", "barinma", "barinak", "konteyner", "kalacak yer", "sokakta kaldik"],
    "isinma": ["battaniye", "soba", "yakacak", "odun", "komur", "isinma", "isinamiyoruz", "uyku tulumu", "mont"],
    "ilac": ["ilac", "insulin", "tansiyon ilaci", "kalp ilaci", "recete"],
    "tuvalet": ["tuvalet", "hijyen", "ped", "bez", "cocuk bezi"],
}

SINYAL = {
    # "öldü"/"ölmüş" katlanınca "oldu"/"olmus" (olmak) olur; bu yüzden yalnız ad biçimleri.
    "olu": ("Ölü var", ["olu", "oluler", "olumuz", "ceset", "cesetler", "cenaze", "vefat", "hayatini kaybet",
                         "can kaybi"]),
    "enkaz_altinda": ("Enkaz altında kişi", ["enkaz altinda", "enkaz altindan", "enkazin altinda", "altinda kaldi",
                                              "altinda kalan", "goçuk altinda", "gocuk altinda"]),
    "ses_geliyor": ("Ses geliyor", ["ses geliyor", "sesi geliyor", "ses duyuluyor", "ses var", "sesler geliyor",
                                    "ses veriyor"]),
    "yarali": ("Yaralı / tıbbi acil", ["yarali", "yaralanan", "kanama", "kaniyor", "bilinci kapali", "nefes alamiyor",
                                       "kalp krizi"]),
    # "ambulans" sinyal değil: "ambulans giremiyor" yol kapanmasını anlatır.
    "mahsur": ("Mahsur / çıkamıyor", ["mahsur", "sikisti", "sikismis", "cikamiyor", "cikamiyoruz", "kapali kaldi"]),
    "cokme": ("Bina çöktü", ["coktu", "cokmus", "yikildi", "yikilmis", "gocto", "goctu", "yan yatti", "yan yatmis"]),
    "riskli_bina": ("Bina riskli", ["catlak", "catlaklar", "cokebilir", "cokecek", "yikilacak", "riskli"]),
    "yol_kapali": ("Yol kapalı / ulaşılamıyor", ["yol kapali", "yolu kapali", "kapandi", "giremiyor", "gecemiyor",
                                                 "gecis yok", "ulasilamiyor", "ulasamiyor"]),
    "savunmasiz": ("Savunmasız kişi (çocuk, yaşlı, hasta, hamile)", ["bebek", "cocuk", "yasli", "hamile", "engelli", "hasta"]),
}


def _sozcukler(metin: str):
    for m in re.finditer(r"\w+", metin):
        yield katla(m.group(0)), m.start(), m.end()


def _ara(metin: str, kalip: str):
    """Kalıbı (katlanmış, çok sözcüklü olabilir) metinde sözcük başlarından arar;
    son sözcük ek alabilir ("enkazda", "kapandı"). (bas, son) döndürür."""
    hedef = kalip.split()
    sz = list(_sozcukler(metin))
    for i in range(len(sz) - len(hedef) + 1):
        pencere = sz[i:i + len(hedef)]
        if all(p[0] == h for p, h in zip(pencere[:-1], hedef[:-1])):
            son, h = pencere[-1][0], hedef[-1]
            if son == h or (len(h) >= 4 and son.startswith(h)):
                return pencere[0][1], pencere[-1][2]
    return None


def kisiler(metin: str) -> list[dict]:
    out = []
    sz = list(_sozcukler(metin))
    for i in range(len(sz) - 1):
        k, bas, _ = sz[i]
        sayi = int(k) if k.isdigit() and 0 < int(k) < 10000 else SAYI.get(k)
        if sayi is None:
            continue
        # "iki kişi", "3 çocuk", "dört aile", "yaşlı bir çift"; araya bir sıfat girebilir.
        for j in (i + 1, i + 2):
            if j >= len(sz):
                break
            kok = next((v for s, v in KISI_SOZCUGU.items() if sz[j][0].startswith(s)), None)
            if kok:
                if kok == "çift":
                    sayi, kok = sayi * 2, "kişi"
                out.append({"sayi": sayi, "ne": kok, "metin": metin[bas:sz[j][2]], "bas": bas, "son": sz[j][2]})
                break
    # Ardından gelen sayı: "<ad> (var) N tane".
    for j in range(len(sz)):
        kok = next((v for s, v in KISI_SOZCUGU.items() if sz[j][0].startswith(s)), None)
        if not kok or kok == "çift" or any(o["bas"] <= sz[j][1] < o["son"] for o in out):
            continue
        for i in (j + 1, j + 2):
            if i + 1 >= len(sz):
                break
            k = sz[i][0]
            sayi = int(k) if k.isdigit() and 0 < int(k) < 10000 else SAYI.get(k)
            if sayi is not None and sz[i + 1][0] in SAYAC_SOZCUGU:
                out.append({"sayi": sayi, "ne": kok, "metin": metin[sz[j][1]:sz[i + 1][2]],
                            "bas": sz[j][1], "son": sz[i + 1][2]})
                break
    return sorted(out, key=lambda o: o["bas"])


def ihtiyaclar(metin: str) -> list[dict]:
    out = []
    for kimlik, kaliplar in IHTIYAC.items():
        for kalip in sorted(kaliplar, key=len, reverse=True):
            yer = _ara(metin, kalip)
            if yer:
                # "su" kısa: "susuz" ayrı kalıp; "suyu" gibi ekleri kalıp listesi taşır.
                if kalip == "su" and katla(metin[yer[0]:yer[1]]) != "su":
                    continue
                out.append({"ihtiyac": kimlik, "metin": metin[yer[0]:yer[1]], "bas": yer[0], "son": yer[1]})
                break
    return out


# "öldü", "ölmüş", "öldüler": katlanmış metinde "oldu" (olmak) ile karışır;
# özgün metinde ö harfiyle aranır. "ö" yazılmamışsa ("oldu") yakalanmaz.
OLUM_FIILI = re.compile(r"\b[öÖ]l(?:dü|mü[şs]|ecek|üyor)\w*", re.IGNORECASE)


def sinyaller(metin: str) -> list[dict]:
    out = []
    for kimlik, (ad, kaliplar) in SINYAL.items():
        for kalip in sorted(kaliplar, key=len, reverse=True):
            yer = _ara(metin, kalip)
            if yer:
                out.append({"sinyal": kimlik, "ad": ad, "metin": metin[yer[0]:yer[1]], "bas": yer[0], "son": yer[1]})
                break
        if kimlik == "olu" and not any(o["sinyal"] == "olu" for o in out):
            m = OLUM_FIILI.search(metin)
            if m:
                out.append({"sinyal": "olu", "ad": ad, "metin": m.group(0), "bas": m.start(), "son": m.end()})
    return out


def cikar(metin: str) -> dict:
    return {"kisiler": kisiler(metin), "ihtiyaclar": ihtiyaclar(metin), "sinyaller": sinyaller(metin)}
