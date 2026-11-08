"""Görüntü karosu vekili: uydu/drone karoları kendi API'mizden geçer.

Neden gerekli. Konsolun haritası karoları `fetch` ile indiriyor (deck.gl
TileLayer). OpenAerialMap ve benzeri karo sunucuları `Access-Control-Allow-Origin`
başlığı göndermiyor, bu yüzden tarayıcı indirmeyi CORS kuralıyla engelliyordu:
karo istekleri gidiyor, hiçbiri çizilmiyordu (ölçüldü, 26 Eylül). Sunucu
tarafından çekip kendi kaynağımızdan sunmak bunu çözer.

Güvenlik. Bu bir **açık vekil değildir**: yalnızca aşağıdaki bilinen karo
sunucularına gidilir. Adres istemciden gelse bile konak adı listede yoksa istek
reddedilir (SSRF). Yol ve sorgu dizisi de karo deseninin dışına çıkamaz.
"""
import re

import httpx
import kimlik
from fastapi import APIRouter, Depends, HTTPException, Query, Response

yonlendirici = APIRouter(prefix="/api/goruntu", tags=["goruntu"])

# Yalnız bu konaklar. Listeye ekleme yapılırken kaynağın lisansı ve künyesi
# ARAYUZ §11'e göre ekranda yazılmalı.
IZINLI_KONAKLAR = {
    "tiles.openaerialmap.org",
    "titiler.hotosm.org",
    "wayback.maptiles.arcgis.com",
    "mt1.google.com",
}
ZAMAN_ASIMI = httpx.Timeout(20.0, connect=10.0)
# Karo içeriği değişmez; tarayıcı ve ara katman uzun süre saklayabilir.
ONBELLEK = "public, max-age=86400"

_istemci: httpx.Client | None = None


def _http() -> httpx.Client:
    """Tek bağlantı havuzu: karo başına yeni TCP el sıkışması açılmasın."""
    global _istemci
    if _istemci is None:
        _istemci = httpx.Client(
            timeout=ZAMAN_ASIMI,
            follow_redirects=True,  # OAM karoları titiler'a yönlendiriyor
            headers={"User-Agent": "QuakeMind/1.0 (TUBITAK 2209-A)"},
            limits=httpx.Limits(max_connections=32, max_keepalive_connections=16),
        )
    return _istemci


def _adres_dogrula(adres: str) -> str:
    if not re.match(r"^https://[A-Za-z0-9.\-]+/", adres):
        raise HTTPException(status_code=422, detail="Karo adresi https olmalı.")
    konak = adres.split("/", 3)[2]
    if konak not in IZINLI_KONAKLAR:
        raise HTTPException(status_code=403, detail=f"İzin verilmeyen karo sunucusu: {konak}")
    return adres


@yonlendirici.get("/karo/{z}/{x}/{y}")
def karo(
    z: int,
    x: int,
    y: int,
    kaynak: str = Query(..., pattern="^(oam|esri|google)$"),
    adres: str | None = Query(None, description="OAM için karo şablonu (tms)"),
    surum: str | None = Query(None, description="Esri Wayback sürüm kimliği"),
    _kul: dict = Depends(kimlik.rol_gerektir("saha", "koordinator", "yonetici")),
):
    """Tek bir karoyu kaynağından çekip döndürür (CORS'suz kaynaklar için)."""
    if kaynak == "google":
        hedef = f"https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
    elif kaynak == "esri":
        if not surum or not surum.isdigit():
            raise HTTPException(status_code=422, detail="Esri karosu için sürüm kimliği gerekli.")
        hedef = (
            "https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/"
            f"MapServer/tile/{surum}/{z}/{y}/{x}"
        )
    else:
        if not adres:
            raise HTTPException(status_code=422, detail="OAM karosu için adres şablonu gerekli.")
        # YER TUTUCU ÇİFTLENMESİ. Adres şablonunda `{z}` birden çok kez geçiyorsa
        # adres bozuktur: çağıran, zaten `{z}/{x}/{y}` ile biten bir OAM adresine
        # bir kez daha eklemiştir ve `.../{z}/{x}/{y}/{z}/{x}/{y}.png` çıkar.
        # Bunu 404 olarak geçirmek TEŞHİSİ İMKÂNSIZ kılıyordu: uç "kapsama dışı
        # karo" ile "yanlış adres"i aynı kodla döndürüyor, harita sessizce boş
        # kalıyordu (ölçüldü, 26 Eylül: 180 isteğin 180'i 404, sebep görünmüyor;
        # aynı hata J-75'te bir kez düzeltilip J-90'da geri gelmişti).
        if adres.count("{z}") > 1 or adres.count("{x}") > 1 or adres.count("{y}") > 1:
            raise HTTPException(
                status_code=422,
                detail="Karo adresinde yer tutucu çiftlenmiş "
                       "(`{z}/{x}/{y}` birden çok kez geçiyor). Adres şablonuna "
                       "yer tutucu eklemeden önce zaten taşıyıp taşımadığına bakın.",
            )
        hedef = (
            adres.replace("{z}", str(z)).replace("{x}", str(x)).replace("{y}", str(y))
        )
    _adres_dogrula(hedef)

    try:
        yanit = _http().get(hedef)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Karo alınamadı: {type(e).__name__}")

    if yanit.status_code == 404:
        # Kapsama dışındaki karo: harita boş bırakır, hata göstermez. Adres
        # bozukluğu buraya DÜŞMEZ; yukarıdaki yer tutucu kontrolü onu 422 ile
        # ayırır, yoksa iki ayrı durum aynı 404'te birleşip teşhisi engelliyor.
        raise HTTPException(status_code=404, detail="Karo yok (kapsama dışı).")
    if yanit.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Karo sunucusu {yanit.status_code} döndü.")

    return Response(
        content=yanit.content,
        media_type=yanit.headers.get("content-type", "image/png"),
        headers={"Cache-Control": ONBELLEK},
    )
