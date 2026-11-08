"""Hoca sunumu icin TEK KOMUTLA hazirlik: backend'i ayaga kaldirir (zaten
ayaktaysa dokunmaz), 8 bolgenin graf cache'ini kontrol eder, senaryoyu
kosturur, sonucu dogrular ve ACIK NET bir "HAZIR" raporu basar.

ALTIN KURAL (bu script bunu degistiremez, sadece hatirlatir):
  Butun veri (ihbarlar, ekipler, rotalar) sadece backend surecinin BELLEGINDE
  tutulur -- hicbir yere yazilmaz. Bu script bittikten SONRA backend sureci
  KAPANIRSA/YENIDEN BASLARSA (terminali kapatmak, bilgisayari uyutmak, cokme
  vs.) TUM VERI SILINIR ve /command bombos gorunur. Hazirlik ile sunum
  arasinda backend'e HICBIR SEKILDE dokunulmamali.

Kullanim (tek satir, sunumdan ~10 dk once):
  cd backend
  venv\\Scripts\\python.exe benchmark\\prepare_demo.py hatay
  venv\\Scripts\\python.exe benchmark\\prepare_demo.py kahramanmaras
  venv\\Scripts\\python.exe benchmark\\prepare_demo.py hatay --check   (sadece durumu goster, hicbir sey degistirme)
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

import requests

BACKEND_DIR = Path(__file__).resolve().parents[1]
VENV_PYTHON = BACKEND_DIR / "venv" / "Scripts" / "python.exe"
API_BASE = "http://127.0.0.1:8000"
BACKEND_LOG = BACKEND_DIR / "benchmark" / "runs" / "_backend_demo.log"


def _safe_print(text: str) -> None:
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"), flush=True)


def backend_alive() -> bool:
    try:
        r = requests.get(f"{API_BASE}/api/status", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def start_backend() -> None:
    _safe_print("[1/4] Backend ayakta degil -- baslatiliyor (bu pencereyi KAPATMA)...")
    BACKEND_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(BACKEND_LOG, "w", encoding="utf-8") as log:
        subprocess.Popen(
            [str(VENV_PYTHON), "-m", "uvicorn", "fastapi_app:app",
             "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(BACKEND_DIR), stdout=log, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
        )
    for _ in range(120):
        if backend_alive():
            _safe_print("      Backend hazir.")
            return
        time.sleep(2)
    raise RuntimeError(f"Backend 4 dakikada ayaga kalkmadi -- {BACKEND_LOG} dosyasina bak.")


def check_graph_cache(city: str) -> bool:
    result = subprocess.run(
        [str(VENV_PYTHON), "benchmark/warm_scenario_v2_cache.py", "--check"],
        cwd=str(BACKEND_DIR), capture_output=True, text=True,
    )
    ok = result.returncode == 0
    if not ok:
        _safe_print("[2/4] UYARI: bazi bolge graflari cache'te yok, PBF'ten cikarilacak (dakikalar surebilir):")
        _safe_print(result.stdout)
        subprocess.run([str(VENV_PYTHON), "benchmark/warm_scenario_v2_cache.py"],
                       cwd=str(BACKEND_DIR), check=True)
    else:
        _safe_print("[2/4] Graf cache'leri hazir.")
    return True


def run_scenario(city: str, run_id: str) -> None:
    _safe_print(f"[3/4] Senaryo kosturuluyor ({city})... ~4-5 dk surer.")
    subprocess.run(
        [str(VENV_PYTHON), "benchmark/full_scenario.py", city, "--run-id", run_id, "--speed", "3"],
        cwd=str(BACKEND_DIR), check=True,
    )


def verify_live_state(city_label_hint: str) -> None:
    _safe_print("[4/4] Canli durum dogrulaniyor...")
    alerts = requests.get(f"{API_BASE}/api/sos/alerts", timeout=10).json()
    claims = requests.get(f"{API_BASE}/api/team/claims", timeout=10).json()
    analyses = requests.get(f"{API_BASE}/api/road_damage/recent?minutes=30", timeout=15).json()

    n_alerts = alerts["totalAlerts"]
    n_claims = len(claims["claims"])
    n_zones = len(analyses["analyses"])

    _safe_print("")
    _safe_print("=" * 60)
    if n_alerts == 0 or n_claims == 0:
        _safe_print("HAZIR DEGIL -- ihbar/ekip verisi bos gorunuyor. Tekrar calistir.")
        _safe_print("=" * 60)
        sys.exit(1)

    _safe_print(f"HAZIR -- {n_alerts} ihbar, {n_claims} ekip, {n_zones} bolge haritada.")
    _safe_print("=" * 60)
    _safe_print("")
    _safe_print("SIMDI YAPILACAKLAR:")
    _safe_print("  1. Tarayicida http://localhost:3100/login ac")
    _safe_print("  2. Demo giris -> 'Saha Ekibi & Komuta' -> herhangi bir hesap")
    _safe_print("  3. /command sayfasinda sag ustten 'Simulasyon Modu'nu AC")
    _safe_print("")
    _safe_print("BUNDAN SONRA BACKEND TERMINALINE (yeni acilan pencere) DOKUNMA.")
    _safe_print("Ekipler ~4-25 dk icinde hedeflerine ulasir, sonrasinda hareket durur")
    _safe_print("ama pinler/rotalar haritada KALICI kalir (hoca gec gelse bile gorunur).")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("city", choices=["hatay", "kahramanmaras"])
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--check", action="store_true", help="Hicbir sey baslatma, sadece mevcut durumu goster.")
    args = parser.parse_args()

    if args.check:
        if not backend_alive():
            _safe_print("Backend AYAKTA DEGIL.")
            return 1
        verify_live_state(args.city)
        return 0

    if backend_alive():
        _safe_print("[1/4] Backend zaten ayakta -- dokunulmuyor.")
    else:
        start_backend()

    check_graph_cache(args.city)
    run_scenario(args.city, args.run_id or f"hoca-sunumu-{args.city}")
    verify_live_state(args.city)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
