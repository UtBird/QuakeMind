#!/usr/bin/env python3
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from nlp_bridge import build_payload


HOST = "0.0.0.0"
PORT = 8766


class NlpBridgeHandler(BaseHTTPRequestHandler):
    server_version = "QuakeMindNlpBridge/1.0"

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"ok": True})
            return
        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/nlp":
            self._send_json(404, {"error": "Not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length) if content_length else b"{}"
            payload = json.loads(raw_body.decode("utf-8") or "{}")
            text = str(payload.get("text") or "").strip()
            if not text:
                raise ValueError("Analiz icin bos metin gonderilemez.")

            result = build_payload(text)
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
    server = ThreadingHTTPServer((HOST, PORT), NlpBridgeHandler)
    print(f"NLP bridge server listening on http://{HOST}:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
