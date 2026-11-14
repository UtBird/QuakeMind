"""Demo hesaplari -- her gelistiricinin kendi yerel veritabaninda ayni hesaplar.

Veritabani (veri/quakemind.sqlite3) depoya girmez; projeyi yeni ceken kisi bos
veritabaniyla baslar ve demo hesaplariyla giremez. Bu arac dort rol icin birer
demo hesabi acar (varsa dokunmaz), saha hesabini bir ekibe baglar.

    python araclar_demo_hesaplari.py                    # eksikleri ac
    python araclar_demo_hesaplari.py --sifreleri-sifirla # var olanlarin sifresini de demo sifresine cek

UYARI: demo sifresi bu dosyada acik yazilidir. Yalniz yerel gelistirme ve
tanitim icindir; gercek kullanimda bu hesaplar acilmaz ya da sifreleri degistirilir.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import kimlik  # noqa: E402
from depo import depo_ac  # noqa: E402

DEMO_SIFRE = "degistir1234"  # araclar_kullanici.py varsayilaniyla ayni

# (e-posta, ad soyad, rol, giris kapisi)
HESAPLAR = [
    ("yonetici-demo@quakemind.local", "Demo Yönetici", "yonetici", "Koordinasyon"),
    ("demo@quakemind.local", "Demo Sunum", "koordinator", "Koordinasyon"),
    ("saha-demo@quakemind.local", "Demo Saha Ekibi", "saha", "Saha ekibi"),
    ("afetzede-demo@quakemind.local", "Demo Afetzede", "afetzede", "Afetzede"),
]
DEMO_EKIP_ADI = "Demo Ekip"


def main() -> int:
    sifirla = "--sifreleri-sifirla" in sys.argv[1:]
    depo = depo_ac()
    print(f"Veritabani: {depo.yol}")
    satirlar = []
    for eposta, ad, rol, kapi in HESAPLAR:
        var = depo.kullanici_eposta(eposta)
        if var is None:
            k = depo.kullanici_olustur(
                eposta=eposta, ad_soyad=ad, sifre_ozeti=kimlik.sifre_ozetle(DEMO_SIFRE), rol=rol
            )
            depo.hesap_kaydi_ekle(None, k, "hesap-acildi", {"rol": rol, "kaynak": "araclar_demo_hesaplari"})
            durum = "acildi"
        else:
            k = var
            durum = "zaten var"
            if var["rol"] != rol:
                durum += f" (rolu {var['rol']}; degistirilmedi)"
            if sifirla:
                depo.sifre_ata(var["id"], kimlik.sifre_ozetle(DEMO_SIFRE), degismeli=False)
                depo.hesap_kaydi_ekle(None, var, "sifre-yenilendi", {"kaynak": "araclar_demo_hesaplari"})
                durum += ", sifre demo sifresine cekildi"
            if var.get("askida"):
                durum += ", ASKIDA (giremez; Hesaplar sayfasindan etkinlestir)"

        # Saha hesabi gorev gorsun diye bir ekibe bagli olmali (J-155).
        if rol == "saha" and not depo.kullanici_id(k["id"]).get("ekip_id") and depo.kullanici_id(k["id"])["rol"] == "saha":
            ekipler = depo.ekip_listele()
            ekip = next((e for e in ekipler if e["ad"] == DEMO_EKIP_ADI), None) or (ekipler[0] if ekipler else None)
            if ekip is None:
                # Konum: Antakya merkezi (konsolun varsayilan bolgesi).
                ekip = depo.ekip_olustur(DEMO_EKIP_ADI, kurum=None, tur=None, kisi_sayisi=4, lon=36.161, lat=36.202)
                durum += f", '{DEMO_EKIP_ADI}' ekibi acildi"
            depo.ekibe_bagla(k["id"], ekip["id"])
            durum += f", ekibe baglandi: {ekip['ad']}"
        satirlar.append((eposta, rol, kapi, durum))

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
