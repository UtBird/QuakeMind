"""Kullanici olusturma araci -- kayit ucu rol kabul etmedigi icin saha/
koordinator/yonetici hesaplari buradan acilir.

    python araclar_kullanici.py ekle eposta@ornek.com "Ad Soyad" koordinator
    python araclar_kullanici.py listele
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import kimlik  # noqa: E402
from depo import depo_ac  # noqa: E402


def main() -> int:
    depo = depo_ac()
    if len(sys.argv) < 2 or sys.argv[1] == "listele":
        for k in depo._oku("SELECT id, eposta, ad_soyad, rol FROM kullanicilar ORDER BY eposta"):
            print(f"{k['rol']:12} {k['eposta']:32} {k['ad_soyad']}")
        return 0

    if sys.argv[1] == "ekle":
        if len(sys.argv) < 5:
            print("kullanim: ekle <eposta> <ad soyad> <rol> [sifre]")
            return 2
        eposta, ad, rol = sys.argv[2], sys.argv[3], sys.argv[4]
        sifre = sys.argv[5] if len(sys.argv) > 5 else "degistir1234"
        if rol not in kimlik.ROLLER:
            print(f"bilinmeyen rol: {rol} (secenekler: {', '.join(kimlik.ROLLER)})")
            return 2
        mevcut = depo.kullanici_eposta(eposta)
        if mevcut:
            depo.rol_ata(mevcut["id"], rol)
            print(f"var olan kullanicinin rolu guncellendi: {eposta} -> {rol}")
            return 0
        kayit = depo.kullanici_olustur(
            eposta=eposta, ad_soyad=ad, sifre_ozeti=kimlik.sifre_ozetle(sifre), rol=rol
        )
        print(f"olusturuldu: {kayit['eposta']} ({rol}) sifre: {sifre}")
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
