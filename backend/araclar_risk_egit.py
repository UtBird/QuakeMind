"""Risk modeli egitim komutu.

CLAUDE.md kural 3: egitim istek yolunda yapilmaz. Bu komut modeli egitir ve
`apps/earthquake_risk/models/risk_catboost.cbm` dosyasina yazar; API yalnizca
bu dosyayi yukler.

    python araclar_risk_egit.py            # egit ve kaydet
    python araclar_risk_egit.py --durum    # mevcut modelin kunyesini yaz
"""

import json
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parent
sys.path.insert(0, str(KOK))
sys.path.insert(0, str(KOK / "apps" / "earthquake_risk"))

from apps.earthquake_risk.risk_engine import (  # noqa: E402
    MODEL_DOSYASI,
    MODEL_KUNYESI,
    EarthquakeRiskEngine,
)


def durum() -> int:
    if not MODEL_DOSYASI.exists():
        print("Model yok. Egitmek icin: python araclar_risk_egit.py")
        return 1
    boyut = MODEL_DOSYASI.stat().st_size / 1024
    print(f"Model: {MODEL_DOSYASI} ({boyut:.0f} KB)")
    if MODEL_KUNYESI.exists():
        kunye = json.loads(MODEL_KUNYESI.read_text(encoding="utf-8"))
        zaman = time.strftime("%d.%m.%Y %H:%M", time.localtime(kunye.get("egitimZamani", 0)))
        print(f"Egitim: {zaman} · {kunye.get('kayitSayisi')} kayit · "
              f"{kunye.get('egitimSuresiSn')} sn · parmak izi {kunye.get('veriParmakIzi')}")
    return 0


def main() -> int:
    if "--durum" in sys.argv:
        return durum()

    motor = EarthquakeRiskEngine()
    print("Risk modeli egitiliyor (istek yolunda degil, burada)...")
    baslangic = time.time()
    sonuc = motor.modeli_egit(kaydet=True)
    print(
        f"Bitti: {sonuc['kayitSayisi']} kayit, {sonuc['sureSn']} sn egitim, "
        f"toplam {time.time() - baslangic:.1f} sn"
    )
    return durum()


if __name__ == "__main__":
    raise SystemExit(main())
