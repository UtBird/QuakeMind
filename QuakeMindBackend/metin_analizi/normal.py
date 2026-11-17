"""Türkçe metin normalleştirme (J-170): eşleme için tek biçim.

Kurallar:
  * Türkçe büyük/küçük harf: "I" -> "ı", "İ" -> "i" (str.lower() "I"yı "i" yapar).
  * Aksanlar katlanır (ç->c, ğ->g, ı->i, ö->o, ş->s, ü->u): afetzede çoğu zaman
    Türkçe klavyesiz yazar ("Nurdagi", "sekeroba").
  * Kesme işaretinden sonrası ek sayılır: "Nurdağı'nda" -> "nurdagi".
"""
from __future__ import annotations

import re
import unicodedata

_KATLA = str.maketrans({"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u", "â": "a", "î": "i", "û": "u"})
_KESME = re.compile(r"['’`´](\w+)")


def kucuk(metin: str) -> str:
    return str(metin).replace("I", "ı").replace("İ", "i").lower()


def katla(metin: str) -> str:
    """Eşleme anahtarı: küçük harf, aksansız, noktalama boşluk."""
    s = kucuk(metin)
    s = _KESME.sub("", s)  # kesmeden sonraki ek atılır
    s = s.translate(_KATLA)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def sozcukler(metin: str) -> list[str]:
    return katla(metin).split()


# Yer adına eklenen çekim ekleri (katlanmış, uzundan kısaya). Kesme işareti
# olmadan yazılanlar için: "antakyada", "defnede", "nurdaginda", "islahiyede".
_EKLER = (
    "ndaki", "ndeki", "ndan", "nden", "nda", "nde", "nin", "nun", "nın", "nün",
    "daki", "deki", "taki", "teki",
    "dan", "den", "tan", "ten", "da", "de", "ta", "te",
    "ya", "ye", "yi", "yu", "na", "ne", "in", "un", "a", "e",
)


def ek_adaylari(sozcuk: str) -> list[str]:
    """Sözcüğün kendisi ve ekleri atılmış biçimleri (en az 3 harf kalır)."""
    out = [sozcuk]
    for ek in _EKLER:
        if sozcuk.endswith(ek) and len(sozcuk) - len(ek) >= 3:
            out.append(sozcuk[: -len(ek)])
    return out


def levenshtein(a: str, b: str, sinir: int = 2) -> int:
    """Küçük düzenleme uzaklığı; `sinir`i aşınca sinir+1 döner (hızlı kesme)."""
    if abs(len(a) - len(b)) > sinir:
        return sinir + 1
    onceki = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        simdi = [i] + [0] * len(b)
        en_az = simdi[0]
        for j, cb in enumerate(b, 1):
            simdi[j] = min(onceki[j] + 1, simdi[j - 1] + 1, onceki[j - 1] + (ca != cb))
            en_az = min(en_az, simdi[j])
        if en_az > sinir:
            return sinir + 1
        onceki = simdi
    return onceki[-1]
