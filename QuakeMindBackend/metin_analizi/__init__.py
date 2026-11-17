"""Metin analizi (J-170): afetzede ve konsol ihbar metninin çözümü.

Tek giriş noktası `MetinAnalizci.coz(metin)`. Üç parça:
  * kategori ve güven  -- BERTurk sınıflandırıcı (`apps/disaster_nlp`, model
    `2kveri`); karar mantığı değişmedi (J-111). Ham skorlardan ikinci olasılık.
  * adres              -- `adres.py`, yerel dizin; ağa çıkmaz.
  * kişi/ihtiyaç/sinyal -- `cikarim.py`, kural tabanlı.

Eskiden ayrıca bir NER modeli (yhaslan/turkish-earthquake-tweets-ner) yükleniyor
ve adayları Nominatim'e soruluyordu. Adres artık dizinden çözüldüğü için NER
çıktısının koordinata dönüşecek bir yolu kalmadı; model yüklenmiyor (bellek ve
açılış süresi). Tatbikat kanalı (apps/road_damage/utils/tatbikat_kanallar.py)
kendi NER kullanımını koruyor.

Model API sürecinde değil, `isci.py`'deki tek işçi süreçte durur (CLAUDE.md §3).
"""
from __future__ import annotations

import importlib.util
import os
import time
from pathlib import Path
from typing import Optional

from . import adres as adres_modulu
from .cikarim import cikar

NLP_KOK = Path(__file__).resolve().parents[1] / "apps" / "disaster_nlp"

# Aciliyet kategoriden türetilir (eski boru hattıyla aynı). "Belirsiz"de aciliyet
# yok: 1 ("düşük") demek uydurma olurdu.
ACILIYET = {
    "Enkaz Bildirimi": 5,
    "Acil Yardım İhtiyacı": 4,
    "Yol Kapanma Bilgisi / Lojistik": 3,
    "Lojistik İhtiyaç Bildirimi": 2,
}
METIN_SINIRI = 1000

# Metindeki sinyal hangi kategoriyi düşündürüyor (J-170). Kararı DEĞİŞTİRMEZ
# (değişiklik gerçek sınama kümesinde ölçülmeden yapılmaz, J-111); model başka
# bir kategori dediğinde koordinatöre "kontrol et" uyarısı olarak gösterilir.
SINYAL_KATEGORISI = {
    "yarali": ("Acil Yardım İhtiyacı", "yaralı ya da tıbbi acil"),
    "enkaz_altinda": ("Enkaz Bildirimi", "enkaz altında kişi"),
    "ses_geliyor": ("Enkaz Bildirimi", "enkazdan ses"),
    "yol_kapali": ("Yol Kapanma Bilgisi / Lojistik", "yol kapanması"),
}


# Model "ilgisiz" dese de koordinatöre gösterilecek işaretler.
AGIR_SINYAL = ("olu", "enkaz_altinda", "ses_geliyor", "yarali", "mahsur", "cokme")


def _siniflandirma_modulu():
    """classification.py, `src` paket adı başka modüllerle çakışmasın diye
    dosyasından yüklenir."""
    spec = importlib.util.spec_from_file_location("quakemind_metin_siniflandirma", NLP_KOK / "src" / "classification.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class MetinAnalizci:
    def __init__(self):
        os.environ.setdefault("HF_HUB_OFFLINE", "1")  # model diskte; çalışırken ağa gitme
        t0 = time.perf_counter()
        self._s = _siniflandirma_modulu()
        self.siniflandirici = self._s.DisasterClassifier()
        self.dizin = adres_modulu.dizin()
        self.yukleme_sn = round(time.perf_counter() - t0, 2)
        self.model_adi = Path(str(self.siniflandirici.model_name)).name

    def isit(self) -> None:
        """İlk gerçek isteğin model ilk-koşu bedelini ödememesi için."""
        self.coz("Isınma cümlesi: Antakya'da bina çöktü.")

    def _kategori_puanlari(self, tahminler) -> list[dict]:
        """13 alt etiketin skorunu gösterilen üst kategorilere indirir (her
        kategori için en yüksek). 'Lojistik' alt etiketi iki üst kategoriye de
        yazılır; ayrımı metin yapar."""
        puan: dict[str, float] = {}
        for t in tahminler:
            ham = self._s._normalize_label(t["label"])
            hedefler = (["Yol Kapanma Bilgisi / Lojistik", "Lojistik İhtiyaç Bildirimi"] if ham == "Lojistik"
                        else [self._s.CATEGORY_MAPPING.get(ham, "Diğer")])
            for h in hedefler:
                puan[h] = max(puan.get(h, 0.0), float(t["score"]))
        return [{"kategori": k, "puan": round(v, 3)} for k, v in sorted(puan.items(), key=lambda x: -x[1])]

    def coz(self, metin: str) -> dict:
        t0 = time.perf_counter()
        metin = (metin or "").strip()[:METIN_SINIRI]
        tahminler = self.siniflandirici.classifier(metin[:512])[0] if len(metin) >= 5 else []
        detay = self.siniflandirici.classify_detay(metin, predictions=tahminler or None) if tahminler else {
            "kategori": "Alakasız", "guven": 0.0, "kaynak": "kisa_metin", "hamEtiket": None, "hamSkor": 0.0}
        kategori = detay["kategori"]
        ilgili = kategori != "Alakasız"
        puanlar = self._kategori_puanlari(tahminler) if tahminler else []
        ikinci = next((p for p in puanlar if p["kategori"] not in (kategori, "Alakasız", "Diğer")), None)

        a = adres_modulu.coz(metin, self.dizin).sozluk()
        c = cikar(metin)
        uyarilar = []
        if not ilgili:
            # Model "ilgisiz" dedi ama metinde ağır bir işaret var: karar
            # değişmez (J-111), koordinatörün gözü çekilir.
            agir = next((sy for sy in c["sinyaller"] if sy["sinyal"] in AGIR_SINYAL), None)
            if agir:
                uyarilar.append({
                    "onerilen": "ilgili",
                    "metin": f"Model metni afetle ilgisiz buldu, ama metinde “{agir['metin']}” geçiyor "
                             f"({agir['ad'].lower()}). Kontrol et.",
                })
        if ilgili:
            for sy in c["sinyaller"]:
                hedef = SINYAL_KATEGORISI.get(sy["sinyal"])
                if hedef and hedef[0] != kategori and not any(u["onerilen"] == hedef[0] for u in uyarilar):
                    uyarilar.append({
                        "onerilen": hedef[0],
                        "metin": f"Metinde {hedef[1]} var (“{sy['metin']}”); model “{kategori}” dedi. Kontrol et.",
                    })
        sure_ms = round((time.perf_counter() - t0) * 1000)
        konum = a["konum"]
        return {
            "ilgili": ilgili,
            "kategori": kategori,
            "guven": round(float(detay.get("guven") or 0.0), 3),
            # Kararı kim verdi: model | anahtar_sozcuk | belirsiz | kisa_metin
            "kategoriKaynagi": detay.get("kaynak"),
            "hamEtiket": detay.get("hamEtiket"),
            "ikinciKategori": ikinci,
            "kategoriPuanlari": puanlar[:5],
            "kategoriUyarilari": uyarilar,
            "aciliyet": ACILIYET.get(kategori) if ilgili else None,
            **a,
            **c,
            "model": {"siniflandirici": self.model_adi},
            "sureMs": sure_ms,
            # Eski istemciler (eski web, Flutter) için.
            "konum_metin": a["konumMetin"],
            "konum_adaylari": [x["konumMetin"] for x in a["adresAdaylari"]],
            "guven_skoru": round(float(detay.get("guven") or 0.0), 3),
        }


_yerel: Optional[MetinAnalizci] = None


def yerel_analizci() -> MetinAnalizci:
    """Aynı süreçte analizci (işçi süreç ve ölçüm araçları için)."""
    global _yerel
    if _yerel is None:
        _yerel = MetinAnalizci()
    return _yerel
