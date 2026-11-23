"""Demo hesaplari -- her gelistiricinin kendi yerel veritabaninda ayni hesaplar.

Veritabani (veri/quakemind.sqlite3) depoya girmez; projeyi yeni ceken kisi bos
veritabaniyla baslar ve demo hesaplariyla giremez. Bu arac dort rol icin birer
ortak hesap acar (`ornek_hesaplar.HESAPLAR`; varsa dokunmaz), saha hesabini
bir ekibe baglar.

    python araclar_demo_hesaplari.py                    # eksikleri ac
    python araclar_demo_hesaplari.py --sifreleri-sifirla # var olanlarin sifresini de demo sifresine cek

UYARI: yerel demo sifresi depoda acik yazilidir; CANLIDA CALISTIRILMAZ.
Canlida ayni hesaplar API acilisinda `QUAKEMIND_ORNEK_HESAP_SIFRESI` ortam
degiskeniyle, depoda yazmayan bir sifreyle kurulur (J-183).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ornek_hesaplar  # noqa: E402
from depo import depo_ac  # noqa: E402

DEMO_SIFRE = ornek_hesaplar.YEREL_DEMO_SIFRESI


def main() -> int:
    sifirla = "--sifreleri-sifirla" in sys.argv[1:]
    depo = depo_ac()
    print(f"Veritabani: {depo.yol}")
    satirlar = ornek_hesaplar.kur(depo, DEMO_SIFRE, sifreyi_cek=sifirla)
    print()
    print(f"{'E-posta':32} {'Rol':12} {'Giris kapisi':14} Durum")
    for eposta, rol, kapi, durum in satirlar:
        print(f"{eposta:32} {rol:12} {kapi:14} {durum}")
    print(f"\nYeni acilan hesaplarin sifresi: {DEMO_SIFRE}")
    if not sifirla:
        print("Var olan hesaplarin sifresine dokunulmadi (--sifreleri-sifirla ile cekilir).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
