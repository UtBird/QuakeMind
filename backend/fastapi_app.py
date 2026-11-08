"""QuakeMind API -- uygulama girisi.

TASIMA_PLANI.md Faz 5: bu dosya eskiden 2.859 satirlik tek parcaydi. Artik
yalnizca uygulamayi kurar ve router'lari baglar:

  cekirdek.py        paylasilan durum, yardimcilar, veri modelleri, lifespan
  uclar/*.py         uclar, konuya gore (her biri 400 satirin altinda)

Yerel mobil istemci icin: python fastapi_app.py
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

import cekirdek as ck
from uclar import (
    altlik,
    bildirim,
    canli,
    ekip,
    eski_kimlik,
    eski_sos,
    genel,
    gorev,
    goruntu,
    guvenlik,
    hasar_analiz,
    ihbar,
    kamera,
    kapanma,
    katmanlar,
    metin,
    oturum,
    risk,
    rota,
    simulasyon,
    sozlesme,
    yerler,
)

app = FastAPI(title="QuakeMind API", version="1.0.0", lifespan=ck.lifespan)

# Siralama korunur: yeni oturum ve sozlesme uclari eskiden de ilk sirada
# kaydediliyordu; ardindan eski dosyadaki sirayla digerleri.
for modul in (
    oturum,
    sozlesme,
    genel,
    metin,
    risk,
    hasar_analiz,
    canli,
    rota,
    kapanma,
    eski_sos,
    kamera,
    ekip,
    eski_kimlik,
    bildirim,
    altlik,
    yerler,
    ihbar,
    guvenlik,
    gorev,
    katmanlar,
    simulasyon,
    goruntu,
):
    app.include_router(modul.yonlendirici)


class SecmeliGzip:
    """Gzip, canli akis disindaki yanitlara uygulanir (25 Eylul 2026).

    Starlette 0.38.6'nin GZipMiddleware'i AKISLI yaniti parca parca tamponda
    biriktirir ve yalniz akis kapaninca bosaltir (`gzip.py`; parca basina flush
    yok). SSE boyle sikistirilsaydi olaylar tarayiciya akis bitene kadar
    ulasmazdi -- kural 4'un tam tersi. Bu yuzden `/api/live` gzip'e hic girmez.

    Sunucu tarafi Server-Sent Events disinda akisli yanit uretmiyor; yeni bir
    akis ucu eklenirse yolu HARIC listesine yazilmali.
    """

    HARIC = ("/api/live",)

    # Seviye 9 degil 6: 462 KB'lik toplanma yanitinda ikisi de 4,9x sikistiriyor
    # ama seviye 9 sikistirma 55,9 ms, seviye 6 13,5 ms suruyor (olculdu,
    # 25 Eylul 2026). 1 KB icin 4 kat CPU.
    def __init__(self, app: ASGIApp, en_az_bayt: int = 500, seviye: int = 6) -> None:
        self.app = app
        self.gzipli = GZipMiddleware(app, minimum_size=en_az_bayt, compresslevel=seviye)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and not scope["path"].startswith(self.HARIC):
            await self.gzipli(scope, receive, send)
            return
        await self.app(scope, receive, send)


# Gelistirmedeki istemciler; uretimde QUAKEMIND_CORS ile alan adi eklenir.
# Konsol Vite vekili uzerinden ayni origin'den konustugu icin bu liste asil
# dogrudan baglanan istemciler icindir (eski web, mobil, dis arac).
KOKENLER = [
    f"http://{makine}:{port}"
    for makine in ("127.0.0.1", "localhost")
    for port in (3200, 3201, 3100, 4173, 5173)
]
KOKENLER += [k.strip() for k in os.environ.get("QUAKEMIND_CORS", "").split(",") if k.strip()]

# Onemli: middleware'de SON eklenen en distadir. CORS en distaki olsun ki hata
# yanitlarina da basligi eklensin; gzip onun icinde calissin.
app.add_middleware(SecmeliGzip)
app.add_middleware(
    CORSMiddleware,
    # Eskiden `allow_origins=["*"]` + `allow_credentials=True` idi (J-60):
    # bu ikili istegi atan origin'i oldugu gibi yansitir, yani HER site kimlik
    # bilgisiyle bu API'ye istek atabilirdi. Yenileme cerezinin SameSite=lax
    # olmasi zarari sinirliyordu ama dogrusu adres listesi.
    allow_origins=KOKENLER,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["authorization", "content-type", "idempotency-key"],
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.environ.get("QUAKEMIND_HOST", "0.0.0.0"),
        port=int(os.environ.get("QUAKEMIND_PORT", "8000")),
    )
