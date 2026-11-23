"""Sunucuda hesap araci (J-182). Konsola girecek kimse yokken kullanilir.

Hesaplarin olagan yolu konsoldur (Kullanicilar sayfasi, J-155–J-157):
yonetici her rolu acar, koordinator saha hesabi acar, afetzede kendi hesabini
giris ekranindan acar. Bu arac yalniz iki durum icindir:

  * Bos sunucu (yeni kurulum, canliya ilk cikis): ilk yonetici.
  * Tek yonetici sifresini unuttu ve sifreyi sifirlayacak baska yonetici yok.

    python araclar_kullanici.py ilk-yonetici eposta@kurum.gov.tr "Ad Soyad"
    python araclar_kullanici.py sifre-sifirla eposta@kurum.gov.tr
    python araclar_kullanici.py ekle eposta@kurum.gov.tr "Ad Soyad" koordinator
    python araclar_kullanici.py listele

Canli sunucuda (Docker) ayni komut konteynerin icinde calisir:

    docker exec -it "$(cat ~/opt/quakemind/active-container)" \\
        python araclar_kullanici.py ilk-yonetici eposta@kurum.gov.tr "Ad Soyad"

Sifre komut satirindan VERILMEZ (kabuk gecmisine ve surec listesine duserdi).
Arac rastgele gecici sifre uretir, yalniz bir kez ekrana yazar; kisi ilk
giriste degistirmek zorundadir. Islem hesap kayit defterine yazilir.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import kimlik  # noqa: E402
from depo import depo_ac  # noqa: E402

KAYNAK = {"kaynak": "araclar_kullanici"}


def _yoneticiler(depo) -> list[dict]:
    return depo._oku("SELECT id, eposta FROM kullanicilar WHERE rol = 'yonetici'")


def _sifre_yaz(eposta: str, sifre: str) -> None:
    print(f"  e-posta      : {eposta}")
    print(f"  gecici sifre : {sifre}")
    print("  Bu sifre bir daha gosterilmez. Ilk giriste yeni sifre istenir.")


def _hesap_ac(depo, eposta: str, ad: str, rol: str) -> int:
    eposta = eposta.strip().lower()
    if "@" not in eposta or len(ad.strip()) < 2:
        print("Ad soyad ve gecerli bir e-posta gerekli.")
        return 2
    sifre = kimlik.gecici_sifre()
    yeni = depo.kullanici_olustur(eposta=eposta, ad_soyad=ad, sifre_ozeti=kimlik.sifre_ozetle(sifre), rol=rol)
    depo.sifre_ata(yeni["id"], kimlik.sifre_ozetle(sifre), degismeli=True)
    depo.hesap_kaydi_ekle(None, yeni, "hesap-acildi", {"rol": rol, **KAYNAK})
    print(f"Olusturuldu ({rol}):")
    _sifre_yaz(eposta, sifre)
    return 0


def ilk_yonetici(depo, eposta: str, ad: str) -> int:
    var = _yoneticiler(depo)
    if var:
        print(
            f"Zaten {len(var)} yonetici var ({', '.join(y['eposta'] for y in var)}). "
            "Yeni hesaplari konsoldan (Kullanicilar) yonetici acar. Sifre unutulduysa: sifre-sifirla."
        )
        return 1
    mevcut = depo.kullanici_eposta(eposta)
    if mevcut:
        # Kendi kaydini acmis birini (afetzede) ilk yonetici yap; sifresi
        # sifirlanir ki kimin elinde oldugu belli olsun.
        depo.rol_ata(mevcut["id"], "yonetici")
        depo.oturumlari_iptal(mevcut["id"])
        depo.hesap_kaydi_ekle(None, mevcut, "rol-degisti", {"once": mevcut["rol"], "sonra": "yonetici", **KAYNAK})
        print(f"Var olan hesap yonetici yapildi ({mevcut['rol']} -> yonetici).")
        return sifre_sifirla(depo, eposta)
    return _hesap_ac(depo, eposta, ad, "yonetici")


def sifre_sifirla(depo, eposta: str) -> int:
    hedef = depo.kullanici_eposta(eposta)
    if hedef is None:
        print(f"Hesap yok: {eposta}")
        return 1
    sifre = kimlik.gecici_sifre()
    depo.sifre_ata(hedef["id"], kimlik.sifre_ozetle(sifre), degismeli=True)
    depo.oturumlari_iptal(hedef["id"])
    depo.hesap_kaydi_ekle(None, hedef, "sifre-yenilendi", KAYNAK)
    print(f"Sifre yenilendi, acik oturumlar kapatildi ({hedef['rol']}):")
    _sifre_yaz(hedef["eposta"], sifre)
    return 0


def ekle(depo, eposta: str, ad: str, rol: str) -> int:
    if rol not in kimlik.ROLLER:
        print(f"Bilinmeyen rol: {rol} (secenekler: {', '.join(kimlik.ROLLER)})")
        return 2
    mevcut = depo.kullanici_eposta(eposta)
    if mevcut:
        if mevcut["rol"] != rol:
            depo.rol_ata(mevcut["id"], rol)
            depo.oturumlari_iptal(mevcut["id"])
            depo.hesap_kaydi_ekle(None, mevcut, "rol-degisti", {"once": mevcut["rol"], "sonra": rol, **KAYNAK})
        print(f"Var olan hesap: {eposta} {mevcut['rol']} -> {rol}. Sifresi degismedi.")
        return 0
    return _hesap_ac(depo, eposta, ad, rol)


def main(argv: list[str]) -> int:
    depo = depo_ac()
    komut = argv[0] if argv else "listele"
    if komut == "listele":
        for k in depo._oku("SELECT eposta, ad_soyad, rol, sifre_degismeli FROM kullanicilar ORDER BY rol, eposta"):
            not_ = "  (gecici sifre)" if k["sifre_degismeli"] else ""
            print(f"{k['rol']:12} {k['eposta']:36} {k['ad_soyad']}{not_}")
        return 0
    if komut == "ilk-yonetici" and len(argv) == 3:
        return ilk_yonetici(depo, argv[1], argv[2])
    if komut == "sifre-sifirla" and len(argv) == 2:
        return sifre_sifirla(depo, argv[1])
    if komut == "ekle" and len(argv) == 4:
        return ekle(depo, argv[1], argv[2], argv[3])
    if komut == "ekle" and len(argv) == 5:
        print("Sifre komut satirindan verilmez; arac gecici sifre uretir.")
        return 2
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
