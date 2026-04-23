#!/usr/bin/env python3
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from risk_bridge import build_payload


HOST = "0.0.0.0"
PORT = 8765


class RiskBridgeHandler(BaseHTTPRequestHandler):
    server_version = "QuakeMindRiskBridge/1.0"

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"ok": True})
            return
        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/risk":
            self._send_json(404, {"error": "Not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length) if content_length else b"{}"
            payload = json.loads(raw_body.decode("utf-8") or "{}")
            city = str(payload.get("city") or "Hatay")
            manual_lat = payload.get("manualLatitude")
            manual_lon = payload.get("manualLongitude")
            refresh_data = bool(payload.get("refreshData"))
            manual_coords = None
            if manual_lat is not None or manual_lon is not None:
                if manual_lat is None or manual_lon is None:
                    raise ValueError("Manuel koordinat icin hem enlem hem boylam gerekli.")
                manual_coords = (float(manual_lat), float(manual_lon))

            result = build_payload(
                city=city,
                manual_coords=manual_coords,
                refresh_data=refresh_data,
            )
            self._send_json(200, result)
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})

    def log_message(self, format, *args):
        return

    def _send_json(self, status_code: int, payload):
        data = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)


def main():
    server = ThreadingHTTPServer((HOST, PORT), RiskBridgeHandler)
    print(f"Risk bridge server listening on http://{HOST}:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
