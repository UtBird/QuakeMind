#!/usr/bin/env python3
import argparse
import json
import os
import site
import sys
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "QuakeMindBackend"
NLP_ROOT = BACKEND_ROOT / "apps" / "disaster_nlp"
NLP_REQUIREMENTS = NLP_ROOT / "requirements.txt"


def add_site_packages(project_root: Path) -> None:
    for env_name in [".venv", "venv"]:
        env_path = project_root / env_name
        if not env_path.exists():
            continue
        for site_path in env_path.glob("lib/python*/site-packages"):
            site.addsitedir(str(site_path))


@contextmanager
def temporary_sys_path(*paths: Path):
    old_sys_path = list(sys.path)
    normalized_paths = [str(path) for path in paths if path]
    for path in reversed(normalized_paths):
        if path in sys.path:
            sys.path.remove(path)
        sys.path.insert(0, path)
    try:
        yield
    finally:
        sys.path[:] = old_sys_path


@contextmanager
def temporary_cwd(path: Path):
    old_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_cwd)


@lru_cache(maxsize=1)
def load_pipeline():
    add_site_packages(NLP_ROOT)
    with temporary_sys_path(NLP_ROOT), temporary_cwd(NLP_ROOT):
        try:
            from src.pipeline import DisasterPipeline
        except ModuleNotFoundError as exc:
            missing_name = exc.name or "bilinmeyen paket"
            raise RuntimeError(
                "NLP bridge bagimliliklari eksik. "
                f"Eksik paket: {missing_name}. "
                f"`pip install -r {NLP_REQUIREMENTS}` komutunu calistir."
            ) from exc

        return DisasterPipeline()


def build_payload(text: str) -> dict[str, object]:
    pipeline = load_pipeline()
    result = pipeline.process_tweet(text)
    if result is None:
        return {
            "kategori": "Alakasiz",
            "konum": None,
            "konum_metin": "",
            "konum_adaylari": [],
            "aciliyet": 0,
            "guven_skoru": 0.0,
            "isRelevant": False,
            "mesaj": "Bu girdi afet yonetimi akisina uygun bulunmadi.",
        }

    payload = dict(result)
    payload["isRelevant"] = True
    return payload


def main():
    parser = argparse.ArgumentParser(
        description="Run QuakeMind disaster NLP bridge and print JSON output.",
    )
    parser.add_argument("text", help="Free-form disaster text")
    args = parser.parse_args()

    try:
        payload = build_payload(args.text)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    print(json.dumps(payload, ensure_ascii=True))


if __name__ == "__main__":
    main()
