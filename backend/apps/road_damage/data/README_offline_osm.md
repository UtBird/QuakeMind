# Offline OSM Dataset

This app can run the safety-area layer and road-mask generation from local files.

Expected files:

```text
apps/road_damage/data/osm/safety_areas.geojson
apps/road_damage/data/osm/roads.gpkg
```

Download Turkey OSM PBF:

```bash
mkdir -p apps/road_damage/data/osm
wget -O apps/road_damage/data/osm/turkey-latest.osm.pbf \
  https://download.geofabrik.de/asia/turkey-latest.osm.pbf
```

Install the build dependency if needed:

```bash
pip install pyrosm
```

Build local datasets:

```bash
python apps/road_damage/scripts/build_local_osm_dataset.py \
  apps/road_damage/data/osm/turkey-latest.osm.pbf
```

Generated files:

- `safety_areas.geojson`: `emergency=assembly_point`, parks, gardens, and candidate open areas.
- `roads.gpkg`: walking road network used for road masks and offline route attempts.

The `data/osm/` directory is ignored by git because Turkey-wide OSM files can be large.
