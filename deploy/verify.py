"""Public deployment smoke checks; --models runs inside the API container.

The optional full check creates one temporary account, exercises real models
without a location (so no incident is created), and removes the account.
"""

import argparse
import base64
import json
import os
import secrets
import sqlite3
import uuid

import httpx


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://quakemind-api.dehaozcan.online")
    parser.add_argument("--revision")
    parser.add_argument("--models", action="store_true")
    args = parser.parse_args()
    summary: dict[str, object] = {}
    with httpx.Client(base_url=args.url, timeout=240) as client:
        root = client.get("/")
        root.raise_for_status()
        assert root.json()["status"] == "ok"
        if args.revision:
            assert root.headers["x-quakemind-revision"] == args.revision
        summary["revision"] = root.headers.get("x-quakemind-revision")
        status = client.get("/api/status")
        status.raise_for_status()
        summary["modules"] = status.json()["modules"]
        assert status.json()["modules"]["risk"]
        assert status.json()["modules"]["camera"]
        schema = client.get("/openapi.json")
        schema.raise_for_status()
        assert "/api/oturum/giris" in schema.json()["paths"]
        assert client.get("/api/oturum/ben").status_code == 401
        assert client.post("/api/nlp/analyze", json={"text": "test"}).status_code == 401
        summary["unauthenticated_access"] = "rejected"
        catalog = client.get("/api/risk/all_quakes", params={"limit": 2})
        catalog.raise_for_status()
        assert catalog.json()["returned"] == 2
        summary["earthquake_catalog"] = "ok"
        if not args.models:
            print(json.dumps(summary, ensure_ascii=False))
            return

        email = f"deploy-check-{uuid.uuid4().hex}@example.invalid"
        password = secrets.token_urlsafe(24)
        user_id = None
        database = os.environ["QUAKEMIND_SQLITE"]
        try:
            signup = client.post("/api/oturum/kayit", json={
                "eposta": email, "adSoyad": "Deployment verification", "sifre": password,
            })
            signup.raise_for_status()
            user_id = signup.json()["kullanici"]["id"]
            assert signup.json()["kullanici"]["rol"] == "afetzede"
            cookie = signup.headers["set-cookie"].lower()
            assert "secure" in cookie and "httponly" in cookie
            with sqlite3.connect(database) as connection:
                connection.execute("UPDATE kullanicilar SET rol='saha' WHERE id=?", (user_id,))
            login = client.post("/api/oturum/giris", json={"eposta": email, "sifre": password})
            login.raise_for_status()
            token = login.json()["erisimJetonu"]
            client.headers["Authorization"] = f"Bearer {token}"
            profile = client.get("/api/oturum/ben")
            profile.raise_for_status()
            assert profile.json()["kullanici"]["id"] == user_id
            refresh = client.post("/api/oturum/yenile")
            refresh.raise_for_status()
            summary["auth_registration_login_refresh"] = "ok"
            prediction = client.post("/api/risk/predict", json={
                "city": "Amasya", "manualLatitude": 40.653, "manualLongitude": 35.833,
            })
            prediction.raise_for_status()
            summary["risk_prediction"] = "ok"
            nlp = client.post("/api/nlp/analyze", json={"text": "Bugün kahve içiyorum ve kitap okuyorum."})
            nlp.raise_for_status()
            assert nlp.json().get("status") == "ignored", nlp.json()
            summary["nlp_inference"] = "ok"

            import cv2
            import numpy as np

            ok, image = cv2.imencode(".jpg", np.zeros((640, 640, 3), dtype=np.uint8))
            assert ok
            camera = client.post("/api/camera/analyze", json={
                "imageBase64": base64.b64encode(image).decode("ascii"), "modelType": "both",
            })
            camera.raise_for_status()
            assert camera.json()["status"] == "NO_DETECTION", camera.json()
            summary["camera_inference"] = "ok"
            client.post("/api/oturum/cikis").raise_for_status()
            assert client.post("/api/oturum/yenile").status_code == 401
            summary["logout"] = "ok"
        finally:
            if user_id:
                with sqlite3.connect(database) as connection:
                    connection.execute("DELETE FROM oturumlar WHERE kullanici_id=?", (user_id,))
                    connection.execute("DELETE FROM kullanicilar WHERE id=? AND eposta=?", (user_id, email))
        print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
