"""Install the published OSM basemap into the API's persistent data directory."""

import json
import os
import re
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from huggingface_hub import snapshot_download


DATASET = "Utbird/quakemind-altlik"
REVISION = "17410bd87069b24a726100f6b00b623498fb2134"


def install_basemap(data_dir: Path) -> None:
    target = data_dir / "altlik"
    catalog = target / "katalog.json"
    if catalog.is_file():
        print("Existing basemap catalog retained")
        return

    with TemporaryDirectory(prefix=".altlik-", dir=data_dir) as staging_dir:
        staging = Path(staging_dir)
        snapshot_download(
            repo_id=DATASET,
            repo_type="dataset",
            revision=REVISION,
            local_dir=staging,
            allow_patterns=["katalog.json", "yerler.json", "*.json.gz"],
            token=False,
        )
        regions = json.loads((staging / "katalog.json").read_text(encoding="utf-8"))
        places = json.loads((staging / "yerler.json").read_text(encoding="utf-8"))
        if not regions or not places or not any(region["tur"] == "ulke" for region in regions):
            raise ValueError("Basemap snapshot is missing the catalog, place names or national coverage")

        packages = []
        for region in regions:
            region_id = region["id"]
            if not re.fullmatch(r"[a-z0-9]+", region_id):
                raise ValueError(f"Invalid basemap region ID: {region_id!r}")
            package = staging / f"{region_id}.json.gz"
            if package.stat().st_size != region["boyutBayt"]:
                raise ValueError(f"Basemap package size does not match the catalog: {package.name}")
            packages.append(package)

        target.mkdir(exist_ok=True)
        # Publish the catalog last so a request cannot discover half-installed data.
        for source in (*packages, staging / "yerler.json", staging / catalog.name):
            destination = target / source.name
            try:
                os.link(source, destination)
            except FileExistsError:
                if destination.stat().st_size != source.stat().st_size:
                    raise ValueError(f"Existing basemap file differs from the snapshot: {destination.name}")

    print(f"Installed {len(packages)} basemap regions from {DATASET}@{REVISION}")


if __name__ == "__main__":
    install_basemap(Path(sys.argv[1]))
