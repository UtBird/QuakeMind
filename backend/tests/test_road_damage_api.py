"""Smoke tests for the road-damage risk/heatmap endpoints added in IP4.

Importing fastapi_app eagerly loads the Risk/YOLO/Segformer models (see that
module's own comments) -- slow (tens of seconds), but a one-time cost per
test session, not something these tests try to avoid. TestClient is used
WITHOUT its `with` context manager on purpose: entering it would run the
app's lifespan, which spins up the road-damage ProcessPoolExecutor and
blocks warming up a worker process -- none of the endpoints tested here
need that pool.
"""
import sys
from pathlib import Path

import networkx as nx
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import fastapi_app  # noqa: E402
from utils.postgis_manager import postgis_engine  # noqa: E402


@pytest.fixture(scope="session")
def client():
    return TestClient(fastapi_app.app)


@pytest.fixture(autouse=True)
def postgis_offline(monkeypatch):
    """Forces every test onto the offline-fallback path -- deterministic,
    with no dependency on a real PostGIS instance being reachable."""
    monkeypatch.setattr(postgis_engine, "check_connection", lambda: False)


def test_heatmap_offline_fallback_returns_200(client):
    resp = client.get(
        "/api/road_damage/heatmap",
        params={"latitude": 36.20, "longitude": 36.16, "radiusKm": 5.0},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["points"], list)
    assert body["generatedFrom"]["source"] == "offline_fallback"


def test_nearest_debris_offline_fallback_returns_200(client):
    resp = client.get(
        "/api/road_damage/nearest_debris",
        params={"latitude": 36.20, "longitude": 36.16, "limit": 5},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "offline_fallback"
    assert body["debrisSites"] == []


def _fake_routable_graph(*args, **kwargs):
    """A minimal 2-node routable graph standing in for a real OSMnx fetch,
    centered far from the demo LIVE_ROAD_BLOCKAGES data so the offline
    hard-block fallback never removes its only edge."""
    graph = nx.MultiDiGraph(crs="epsg:4326")
    graph.add_node(1, x=10.000, y=10.000)
    graph.add_node(2, x=10.002, y=10.002)
    graph.add_edge(1, 2, key=0, length=250.0)
    graph.add_edge(2, 1, key=0, length=250.0)
    return graph


def test_safe_route_offline_fallback_returns_200(client, monkeypatch):
    monkeypatch.setattr("osmnx.graph_from_bbox", _fake_routable_graph)

    resp = client.post(
        "/api/road_damage/safe_route",
        json={
            "startLat": 10.000,
            "startLon": 10.000,
            "destLat": 10.002,
            "destLon": 10.002,
            "radiusKm": 3.0,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["algorithm"] in ("dijkstra", "astar")
    assert len(body["routeCoords"]) >= 2
    assert body["distanceMeters"] > 0


def test_safe_route_no_path_returns_422(client, monkeypatch):
    """Two disconnected nodes -- no edge between them -- must surface as a
    client error, not a 500 or a fabricated route."""

    def _disconnected_graph(*args, **kwargs):
        graph = nx.MultiDiGraph(crs="epsg:4326")
        graph.add_node(1, x=10.000, y=10.000)
        graph.add_node(2, x=10.002, y=10.002)
        return graph

    monkeypatch.setattr("osmnx.graph_from_bbox", _disconnected_graph)

    resp = client.post(
        "/api/road_damage/safe_route",
        json={
            "startLat": 10.000,
            "startLon": 10.000,
            "destLat": 10.002,
            "destLon": 10.002,
        },
    )
    assert resp.status_code == 422
