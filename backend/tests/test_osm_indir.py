"""Yerel OSM kesitini indiren arac (J-187). Hugging Face'e baglanmaz."""
import hashlib
import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import araclar_osm_indir as arac  # noqa: E402


@pytest.fixture()
def sahte(monkeypatch):
    icerik = {"roads.gpkg": b"yollar", "tesisler.gpkg": b"tesisler"}
    monkeypatch.setattr(arac, "DOSYALAR", {ad: hashlib.sha256(v).hexdigest() for ad, v in icerik.items()})
    cagri = []
    bozuk = {}

    def indir(repo_id, filename, repo_type, revision, local_dir):
        cagri.append((repo_id, filename, repo_type, revision))
        yol = Path(local_dir) / filename
        yol.parent.mkdir(parents=True, exist_ok=True)
        yol.write_bytes(bozuk.get(filename, icerik[filename]))
        return str(yol)

    import huggingface_hub

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", indir)
    return cagri, bozuk


def test_indirir_ve_ikinci_kez_indirmez(tmp_path, sahte):
    sahte, _ = sahte
    assert arac.indir(tmp_path) == ["roads.gpkg: indirildi", "tesisler.gpkg: indirildi"]
    assert (tmp_path / "roads.gpkg").read_bytes() == b"yollar"
    assert not (tmp_path / ".indiriliyor").exists()
    assert all(c[0] == arac.DEPO and c[2] == "dataset" and c[3] == arac.SURUM for c in sahte)
    assert arac.indir(tmp_path) == ["roads.gpkg: zaten var", "tesisler.gpkg: zaten var"]
    assert len(sahte) == 2


def test_parmak_izi_tutmazsa_kurmaz(tmp_path, sahte):
    _, bozuk = sahte
    bozuk["roads.gpkg"] = b"baska bir dosya"
    with pytest.raises(RuntimeError, match="parmak izi"):
        arac.indir(tmp_path)
    assert not (tmp_path / "roads.gpkg").exists()
    assert not (tmp_path / ".indiriliyor").exists()
