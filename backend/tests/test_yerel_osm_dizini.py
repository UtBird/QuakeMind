"""Yerel OSM yol dosyasinin aranacagi dizin (J-184)."""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from apps.road_damage.utils import yerel_yol  # noqa: E402


def test_ortam_degiskeni_once_gelir(tmp_path, monkeypatch):
    (tmp_path / "roads.gpkg").write_bytes(b"x")
    monkeypatch.setenv("QUAKEMIND_OSM_DIZINI", str(tmp_path))
    assert yerel_yol.osm_dizini() == tmp_path


def test_dosya_olmayan_aday_atlanir(tmp_path, monkeypatch):
    # Degisken dosyasiz bir dizini gosteriyorsa secilmez; kalici veri dizini
    # ya da eski yer secilir (ikisi de yoksa eski yer, veri_var() False).
    monkeypatch.setenv("QUAKEMIND_OSM_DIZINI", str(tmp_path))
    secilen = yerel_yol.osm_dizini()
    assert secilen != tmp_path
    assert secilen.name == "osm"
