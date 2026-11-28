"""Karo vekilinin disk onbellegi (`uclar/goruntu.py`).

Neden. Saha sunucusu internet varken acilan uydu/drone karolarini saklarsa,
baglanti kopunca ayni bolge haritada gorunmeye devam eder (OPTIMIZASYON
madde 33, "internetsiz calisir mi"). Eskiden karo her istekte kaynagindan
yeniden iniyordu; internet yokken 20 sn zaman asimindan sonra 502 donuyordu.

Hangi kaynak. Analiz goruntusunun onbellegiyle ayni kural (J-172,
`apps/road_damage/utils/fetcher.py`): OpenAerialMap ve Esri Wayback saklanir,
Google karolari lisansi geregi SAKLANMAZ.

Bicim. `veri/karo_onbellek/<kaynak>/<ilk iki hane>/<sha256>.<uzanti>`;
anahtar karonun tam adresi (OAM sablonu ya da Wayback surumu dahil), yani ayni
yerin farkli goruntusu ayri dosyadir. Yazma gecici dosyaya, sonra yeniden
adlandirma: yarim dosya okunmaz.

Sinir. `QUAKEMIND_KARO_ONBELLEK_MB` (varsayilan 2048). Her BUDAMA_ARALIGI
yazmada bir toplam boyut olculur; asilmissa en eski erisilen dosyalar sinirin
%90'ina inene kadar silinir. Okunan dosyanin degisim zamani tazelenir (en son
kullanilan kalir).
"""
from __future__ import annotations

import hashlib
import os
import threading
from pathlib import Path

DIZIN = Path(__file__).resolve().parent / "veri" / "karo_onbellek"
SAKLANAN_KAYNAKLAR = ("oam", "esri")
BUDAMA_ARALIGI = 200
_UZANTI = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
_TUR = {v: k for k, v in _UZANTI.items()}

_kilit = threading.Lock()
_yazma_sayaci = [0]


def sinir_bayt() -> int:
    try:
        return max(0, int(os.environ.get("QUAKEMIND_KARO_ONBELLEK_MB", "2048"))) * 1024 * 1024
    except ValueError:
        return 2048 * 1024 * 1024


def _dizin() -> Path:
    # Testler QUAKEMIND_KARO_ONBELLEK ile gecici dizin verir.
    return Path(os.environ.get("QUAKEMIND_KARO_ONBELLEK") or DIZIN)


def _anahtar(adres: str) -> str:
    return hashlib.sha256(adres.encode("utf-8")).hexdigest()


def oku(kaynak: str, adres: str) -> tuple[bytes, str] | None:
    """Onbellekteki karo ve icerik turu; yoksa None."""
    if kaynak not in SAKLANAN_KAYNAKLAR:
        return None
    a = _anahtar(adres)
    klasor = _dizin() / kaynak / a[:2]
    for uzanti, tur in _TUR.items():
        yol = klasor / f"{a}.{uzanti}"
        try:
            veri = yol.read_bytes()
        except OSError:
            continue
        try:
            os.utime(yol)
        except OSError:
            pass
        return veri, tur
    return None


def yaz(kaynak: str, adres: str, veri: bytes, tur: str) -> bool:
    """Karoyu saklar. Saklanmayan kaynak, bilinmeyen tur ya da bos icerik:
    False. Disk hatasi istegi bozmaz (False)."""
    if kaynak not in SAKLANAN_KAYNAKLAR or not veri or sinir_bayt() == 0:
        return False
    uzanti = _UZANTI.get((tur or "").split(";")[0].strip().lower())
    if uzanti is None:
        return False
    a = _anahtar(adres)
    klasor = _dizin() / kaynak / a[:2]
    try:
        klasor.mkdir(parents=True, exist_ok=True)
        gecici = klasor / f".{a}.{threading.get_ident()}.yaziliyor"
        gecici.write_bytes(veri)
        gecici.replace(klasor / f"{a}.{uzanti}")
    except OSError:
        return False
    with _kilit:
        _yazma_sayaci[0] += 1
        budanacak = _yazma_sayaci[0] % BUDAMA_ARALIGI == 0
    if budanacak:
        buda()
    return True


def buda() -> dict:
    """Sinir asilmissa en eski erisilen dosyalari siler. Donus: sayilar."""
    dosyalar = []
    toplam = 0
    for kok, _, adlar in os.walk(_dizin()):
        for ad in adlar:
            if ad.startswith("."):
                continue
            yol = os.path.join(kok, ad)
            try:
                st = os.stat(yol)
            except OSError:
                continue
            dosyalar.append((st.st_mtime, st.st_size, yol))
            toplam += st.st_size
    sinir = sinir_bayt()
    silinen = 0
    if toplam > sinir:
        hedef = int(sinir * 0.9)
        for _, boyut, yol in sorted(dosyalar):
            if toplam <= hedef:
                break
            try:
                os.unlink(yol)
            except OSError:
                continue
            toplam -= boyut
            silinen += 1
    return {"dosya": len(dosyalar) - silinen, "bayt": toplam, "silinen": silinen}
