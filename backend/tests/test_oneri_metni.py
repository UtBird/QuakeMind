"""Analiz sonucunun öneri metni (J-38): yol ağı yoksa "kapanma yok" denmez."""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from apps.road_damage.worker import oneri_metni  # noqa: E402

ORTAK = dict(yol_katmani_yok=False, blocked_count=0, damage_rate=0.01, yerel_yol_var=True)


def test_yol_agi_zaman_asiminda_erisilebilir_denmez():
    m = oneri_metni(yol_agi_durumu="zaman_asimi", blocked_road_pct=0.0019, **ORTAK)
    assert "hesaplanamadı" in m and "45 sn" in m
    assert "erişilebilir olduğunu göstermez" in m
    assert "bulunmadı" not in m and "0 sokak kapalı" not in m


def test_yol_agi_hatasinda_ve_yoklugunda_da_soyler():
    for durum in ("hata", "yok"):
        m = oneri_metni(yol_agi_durumu=durum, blocked_road_pct=0.0, **ORTAK)
        assert "hesaplanamadı" in m and "bulunmadı" not in m


def test_yol_katmani_yoksa_neden_yazar():
    ortak = {**ORTAK, "yol_katmani_yok": True}
    assert "kurulu değil" in oneri_metni(yol_agi_durumu="yok", blocked_road_pct=0.0, **{**ortak, "yerel_yol_var": False})
    assert "kapsamıyor" in oneri_metni(yol_agi_durumu="yok", blocked_road_pct=0.0, **ortak)


def test_olagan_durumlar_degismedi():
    assert oneri_metni(yol_agi_durumu="tamam", blocked_road_pct=0.6, **{**ORTAK, "blocked_count": 12}).startswith("Kritik: 12 sokak")
    assert oneri_metni(yol_agi_durumu="tamam", blocked_road_pct=0.3, **ORTAK).startswith("Dikkat:")
    assert "bulunmadı" in oneri_metni(yol_agi_durumu="tamam", blocked_road_pct=0.0, **ORTAK)
