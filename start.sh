#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
WEB_DIR="$ROOT_DIR/quakemind-web"
LOG_DIR="$ROOT_DIR/.logs"
mkdir -p "$LOG_DIR"

# Windows (Git Bash/MSYS) needs taskkill to kill the whole process tree,
# otherwise child processes (e.g. node spawned by npm) survive Ctrl+C.
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) IS_WINDOWS=1 ;;
  *) IS_WINDOWS=0 ;;
esac

kill_tree() {
  local pid="$1"
  [ -z "$pid" ] && return 0
  if [ "$IS_WINDOWS" = "1" ]; then
    # $! is an MSYS-internal PID, not the real Windows PID taskkill needs.
    local winpid="$pid"
    if [ -r "/proc/$pid/winpid" ]; then
      winpid="$(cat "/proc/$pid/winpid" 2>/dev/null)"
    fi
    taskkill //PID "$winpid" //T //F >/dev/null 2>&1
  else
    kill "$pid" 2>/dev/null
  fi
}

get_lan_ip() {
  # Backend dinliyor 0.0.0.0:8000, yani telefonun gorebilecegi adres
  # 127.0.0.1 degil, bu makinenin LAN/hotspot IP'si. Gercek bir paket
  # gondermeden hangi arayuzun kullanilacagini ogrenmek icin soket
  # trigi kullaniyoruz -- ipconfig/ifconfig parse etmekten daha guvenilir.
  if command -v python3 >/dev/null 2>&1; then
    python3 -c '
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    print(s.getsockname()[0])
    s.close()
except Exception:
    pass
' 2>/dev/null
  fi
}

CLEANED_UP=0
cleanup() {
  [ "$CLEANED_UP" = "1" ] && return 0
  CLEANED_UP=1
  echo ""
  echo "Sistem kapatiliyor..."
  kill_tree "$BACKEND_PID"
  kill_tree "$WEB_PID"
  wait 2>/dev/null
}
trap cleanup EXIT INT TERM

echo "==> Backend (FastAPI) baslatiliyor... (NLP/risk modelleri yuklenecek, bu 1-2 dakika surebilir, lutfen bekleyin)"
cd "$BACKEND_DIR"
if [ -x "./venv/Scripts/python.exe" ]; then
  PYTHON_BIN="./venv/Scripts/python.exe"
elif [ -x "./venv/bin/python" ]; then
  PYTHON_BIN="./venv/bin/python"
elif [ -x "$ROOT_DIR/.venv/Scripts/python.exe" ]; then
  PYTHON_BIN="$ROOT_DIR/.venv/Scripts/python.exe"
elif [ -x "$ROOT_DIR/.venv/bin/python" ]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
else
  echo "HATA: Backend Python sanal ortami bulunamadi. Once kurulum yapin:"
  echo "  python -m venv .venv && .venv/Scripts/python -m pip install -r backend/requirements.txt"
  exit 1
fi
"$PYTHON_BIN" fastapi_app.py > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

WEB_PID=""
WEB_STATUS="yuklenmedi (konsol klasoru bu sparse checkout'ta yok)"
if [ -d "$WEB_DIR" ]; then
  echo "==> Frontend (Next.js) baslatiliyor..."
  cd "$WEB_DIR"
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
  if command -v nvm >/dev/null 2>&1; then
    nvm use 24.18.0 >/dev/null 2>&1 || true
  fi
  if [ ! -d "$WEB_DIR/node_modules" ]; then
    echo "==> node_modules bulunamadi, npm install calistiriliyor..."
    npm install
  fi
  npm run dev > "$LOG_DIR/web.log" 2>&1 &
  WEB_PID=$!
  WEB_STATUS="http://localhost:3000 (log: $LOG_DIR/web.log)"
fi

MOBILE_STATUS="Android projesi: cd mobile; ./gradlew :app:installDebug"

LAN_IP="$(get_lan_ip)"

echo ""
echo "============================================================"
echo " Backend : http://127.0.0.1:8000   (log: $LOG_DIR/backend.log)"
echo " Frontend: $WEB_STATUS"
echo " Mobil   : $MOBILE_STATUS"
if [ -n "$LAN_IP" ]; then
  echo " Mobil API IP: $LAN_IP:8000"
  echo "   (Android build backend URL ayarina"
  echo "    bu IP:port degerini yazin. Telefon ve bilgisayar ayni"
  echo "    ag/hotspot'ta olmali.)"
else
  echo " Mobil API IP: tespit edilemedi -- 'ipconfig' / 'ifconfig' ile"
  echo "   bu bilgisayarin LAN IP'sini bulup Android backend URL'sine yazin."
fi
echo " Durdurmak icin: Ctrl+C"
echo "============================================================"

wait
