"""Esitleme tablolari (OPTIMIZASYON madde 31): saha sunucusu <-> merkez.

Bu dosya `SqliteDepo`'nun bir parcasidir (karisim sinifi); butun SQL burada,
uclar ve `esitleme.py` yalniz bu yontemleri cagirir (CLAUDE.md 10).

Degisim gunlugu. `degisim_gunlugu` her satir icin EN SON degisikligi tutar
(tablo + satir kimligi tekil): satir yeniden degisince eski giris silinir,
yenisi yeni sira numarasiyla girer. Bu yuzden gunluk hic budanmadan satir
sayisini gecmez. Girisleri SQLite tetikleyicileri yazar; uygulama kodunda
"gunluge de yaz" diye unutulacak bir adim yok.

  * Saha sunucusu (rol "dugum"): kendi urettigi hasar noktasi, yol kapanmasi,
    SOS ve ihbar satirlari gunluge girer; gonderilince `gonderildi` yazilir.
    Merkezden gelen satirlar (kimliginde `~` var) gunluge GIRMEZ, geri
    gonderilmez.
  * Merkez (rol "merkez"): hasar noktasi ve yol kapanmasi (kendi ve
    dugumlerden gelen) gunluge girer; dugumler `sira`dan sonrasini ceker.

Kimlik. Baska sunucudan gelen satir `<koken>~<ozgun kimlik>` olarak saklanir:
`merkez~hsr-...`, `antakya-1~kap-...`. Kimlikler onekle ayristirilmiyor (bakildi:
kod `hsr-`/`kap-` onekine bakmiyor), `~` URL'de ayrilmis karakter degil.

Gonderilmeyenler. Tatbikat verisi (hasar `ek.tatbikat`, kapanma `analiz_id`
`sim_` ile baslar) gercek olay degildir, hicbir yone gitmez (CLAUDE.md 1).
Ihbar fotograflari gonderilmez (aralikli baglantida megabaytlarca veri);
ihbarin metni, konumu ve model sonucu gider. Ihbarin tekrar-istek anahtari ve
istek ozeti yereldir, gitmez.
"""
from __future__ import annotations

import time
from typing import Iterable, Optional

ESITLEME_SEMASI = """
CREATE TABLE IF NOT EXISTS degisim_gunlugu (
    sira        INTEGER PRIMARY KEY AUTOINCREMENT,
    tablo       TEXT NOT NULL,
    satir_id    TEXT NOT NULL,
    zaman       REAL NOT NULL,
    gonderildi  REAL
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_degisim_satir ON degisim_gunlugu(tablo, satir_id);
CREATE INDEX IF NOT EXISTS ix_degisim_bekleyen ON degisim_gunlugu(gonderildi, sira);

CREATE TABLE IF NOT EXISTS esitleme_durumu (
    anahtar  TEXT PRIMARY KEY,
    deger    TEXT
);

-- Merkez: dugumlerden gelen ham kayitlar (son hali). SOS ve ihbar yalniz
-- burada durur, merkezin kendi is akisi tablolarina karismaz: atama ve kapatma
-- saha sunucusunda yapilir, iki yerde ayni anda degisirse hangisinin dogru
-- oldugu bilinemez.
CREATE TABLE IF NOT EXISTS gelen_kayitlar (
    dugum     TEXT NOT NULL,
    tablo     TEXT NOT NULL,
    satir_id  TEXT NOT NULL,
    sira      INTEGER NOT NULL,
    veri      TEXT NOT NULL,
    alindi    REAL NOT NULL,
    PRIMARY KEY (dugum, tablo, satir_id)
);
CREATE INDEX IF NOT EXISTS ix_gelen_alindi ON gelen_kayitlar(alindi);
"""

YUKARI = ("hasar_noktalari", "yol_kapanmalari", "sos_cagrilari", "ihbarlar")
ASAGI = ("hasar_noktalari", "yol_kapanmalari")
GONDERILMEYEN = {"ihbarlar": ("istemci_anahtari", "istek_ozeti")}
_TATBIKAT_DEGIL = {
    "hasar_noktalari": "({s}.ek IS NULL OR {s}.ek NOT LIKE '%\"tatbikat\"%')",
    "yol_kapanmalari": "({s}.analiz_id IS NULL OR {s}.analiz_id NOT LIKE 'sim\\_%' ESCAPE '\\')",
}
_SIMDI = "((julianday('now') - 2440587.5) * 86400.0)"


def _kosul(tablo: str, rol: str, satir: str) -> str:
    parcalar = []
    if tablo in _TATBIKAT_DEGIL:
        parcalar.append(_TATBIKAT_DEGIL[tablo].format(s=satir))
    if rol == "dugum":
        parcalar.append(f"instr({satir}.id, '~') = 0")
    return " AND ".join(parcalar) or "1"


class EsitlemeKarisimi:
    """SqliteDepo'ya eklenen esitleme yontemleri (self._yazma, _oku, _tek)."""

    def _esitleme_semasi(self) -> None:
        """Acilista, yazma kilidi icinde cagrilir."""
        self._baglanti.executescript(ESITLEME_SEMASI)

    # ---- rol ve tetikleyiciler ---------------------------------------------

    def esitleme_kur(self, rol: Optional[str]) -> dict:
        """Role gore tetikleyicileri kurar (yoksa hepsini kaldirir).

        Rol ilk kez acildiginda (ya da degistiginde) var olan satirlar gunluge
        bir kez doldurulur: esitleme sonradan acilan sunucunun eski kayitlari
        da gider. Donus: {"rol", "doldurulan"}."""
        if rol not in (None, "dugum", "merkez"):
            raise ValueError(rol)
        tablolar = YUKARI if rol == "dugum" else ASAGI if rol == "merkez" else ()
        doldurulan = 0
        with self._yazma():
            b = self._baglanti
            for (ad,) in b.execute(
                "SELECT name FROM sqlite_master WHERE type = 'trigger' AND name LIKE 'esitleme\\_%' ESCAPE '\\'"
            ).fetchall():
                b.execute(f'DROP TRIGGER IF EXISTS "{ad}"')
            for t in tablolar:
                kosul = _kosul(t, rol, "NEW")
                for olay in ("INSERT", "UPDATE"):
                    b.execute(
                        f"""CREATE TRIGGER esitleme_{t}_{olay.lower()} AFTER {olay} ON {t}
                            WHEN {kosul}
                            BEGIN
                                DELETE FROM degisim_gunlugu WHERE tablo = '{t}' AND satir_id = NEW.id;
                                INSERT INTO degisim_gunlugu (tablo, satir_id, zaman) VALUES ('{t}', NEW.id, {_SIMDI});
                            END"""
                    )
            onceki = b.execute("SELECT deger FROM esitleme_durumu WHERE anahtar = 'rol'").fetchone()
            onceki = onceki[0] if onceki else None
            if rol and onceki != rol:
                for t in tablolar:
                    imlec = b.execute(
                        f"""INSERT OR IGNORE INTO degisim_gunlugu (tablo, satir_id, zaman)
                            SELECT '{t}', id, {_SIMDI} FROM {t} AS s WHERE {_kosul(t, rol, 's')}
                            ORDER BY zaman"""
                    )
                    doldurulan += imlec.rowcount
            b.execute(
                "INSERT INTO esitleme_durumu (anahtar, deger) VALUES ('rol', ?) "
                "ON CONFLICT(anahtar) DO UPDATE SET deger = excluded.deger",
                (rol,),
            )
            b.commit()
        return {"rol": rol, "doldurulan": doldurulan}

    def esitleme_deger(self, anahtar: str) -> Optional[str]:
        s = self._tek("SELECT deger FROM esitleme_durumu WHERE anahtar = ?", (anahtar,))
        return s["deger"] if s else None

    def esitleme_deger_yaz(self, anahtar: str, deger: Optional[str]) -> None:
        self._yaz(
            "INSERT INTO esitleme_durumu (anahtar, deger) VALUES (?, ?) "
            "ON CONFLICT(anahtar) DO UPDATE SET deger = excluded.deger",
            (anahtar, deger),
        )

    # ---- ortak: satiri oku / yaz ------------------------------------------

    def _sutunlar(self, tablo: str) -> tuple[str, ...]:
        onbellek = self.__dict__.setdefault("_sutun_onbellegi", {})
        if tablo not in onbellek:
            onbellek[tablo] = tuple(r["name"] for r in self._oku(f"PRAGMA table_info({tablo})"))
        return onbellek[tablo]

    def _satir_verisi(self, tablo: str, satir_id: str) -> Optional[dict]:
        s = self._tek(f"SELECT * FROM {tablo} WHERE id = ?", (satir_id,))
        if s is None:
            return None
        for ad in GONDERILMEYEN.get(tablo, ()):
            s.pop(ad, None)
        return s

    def _upsert(self, tablo: str, veri: dict) -> bool:
        """Yazma kilidi ICINDE cagrilir. Bilinmeyen sutun atilir. Donus: yazildi mi."""
        sutunlar = [c for c in self._sutunlar(tablo) if c in veri]
        if "id" not in sutunlar:
            return False
        yer = ",".join("?" * len(sutunlar))
        guncelle = ",".join(f"{c} = excluded.{c}" for c in sutunlar if c != "id")
        self._baglanti.execute(
            f"INSERT INTO {tablo} ({','.join(sutunlar)}) VALUES ({yer}) "
            f"ON CONFLICT(id) DO UPDATE SET {guncelle}",
            tuple(veri[c] for c in sutunlar),
        )
        return True

    # ---- dugum: gonderilecekler ---------------------------------------------

    def degisim_bekleyenler(self, sinir: int = 200) -> list[dict]:
        """Gonderilmemis girisler, eskiden yeniye; her biri satirin SIMDIKI hali.
        Satir silinmisse `veri` None (gonderilecek bir sey yok)."""
        girisler = self._oku(
            "SELECT sira, tablo, satir_id FROM degisim_gunlugu WHERE gonderildi IS NULL "
            "ORDER BY sira LIMIT ?",
            (int(sinir),),
        )
        return [
            {"sira": g["sira"], "tablo": g["tablo"],
             "veri": self._satir_verisi(g["tablo"], g["satir_id"]) if g["tablo"] in YUKARI else None}
            for g in girisler
        ]

    def degisim_gonderildi(self, siralar: Iterable[int]) -> int:
        siralar = [int(s) for s in siralar]
        n = 0
        simdi = time.time()
        with self._yazma():
            for i in range(0, len(siralar), 500):
                parca = siralar[i:i + 500]
                n += self._baglanti.execute(
                    f"UPDATE degisim_gunlugu SET gonderildi = ? WHERE sira IN ({','.join('?' * len(parca))})",
                    (simdi, *parca),
                ).rowcount
            self._baglanti.commit()
        return n

    def degisim_bekleyen_sayisi(self) -> int:
        return int(self._tek("SELECT COUNT(*) AS n FROM degisim_gunlugu WHERE gonderildi IS NULL")["n"])

    def uzak_kayit_yaz(self, kayitlar: list[dict]) -> int:
        """Merkezden gelen satirlar (kimlik `~` icerir). Donus: yazilan."""
        n = 0
        with self._yazma():
            for k in kayitlar:
                veri = k.get("veri") or {}
                if k.get("tablo") in ASAGI and "~" in str(veri.get("id", "")):
                    n += self._upsert(k["tablo"], veri)
            self._baglanti.commit()
        return n

    # ---- merkez: alma ve verme ----------------------------------------------

    def gelen_kaydet(self, dugum: str, kayitlar: list[dict]) -> dict:
        """Dugumun gonderdigi kayitlar. Ayni satirin eski surumu yenisini ezmez
        (sira kucukse atlanir). Hasar ve kapanma merkezin kendi tablosuna da
        `<dugum>~<kimlik>` ile yazilir: merkez haritasi ve oteki dugumler gorsun.
        Donus: {"alinan": [sira...], "reddedilen": n}."""
        import json

        alinan, reddedilen = [], 0
        simdi = time.time()
        with self._yazma():
            b = self._baglanti
            for k in kayitlar:
                tablo, veri, sira = k.get("tablo"), k.get("veri"), k.get("sira")
                sid = str((veri or {}).get("id", ""))
                if tablo not in YUKARI or not isinstance(veri, dict) or not sid or "~" in sid or not isinstance(sira, int):
                    reddedilen += 1
                    continue
                degisti = b.execute(
                    """INSERT INTO gelen_kayitlar (dugum, tablo, satir_id, sira, veri, alindi)
                       VALUES (?,?,?,?,?,?)
                       ON CONFLICT(dugum, tablo, satir_id) DO UPDATE SET
                         sira = excluded.sira, veri = excluded.veri, alindi = excluded.alindi
                       WHERE excluded.sira > gelen_kayitlar.sira""",
                    (dugum, tablo, sid, sira, json.dumps(veri, ensure_ascii=False), simdi),
                ).rowcount
                if degisti and tablo in ASAGI:
                    self._upsert(tablo, {**veri, "id": f"{dugum}~{sid}"})
                alinan.append(sira)
            b.commit()
        return {"alinan": alinan, "reddedilen": reddedilen}

    def degisimler_sonra(self, sonra: int, sinir: int, haric_dugum: str, merkez_adi: str) -> dict:
        """Dugume gidecek hasar/kapanma degisiklikleri. Dugumun kendi gonderdigi
        satirlar (`<dugum>~...`) geri gitmez; merkezin kendi satirlari
        `<merkez_adi>~<kimlik>` olarak gider. `sonSira` atlananlar dahil
        taranan son giristir: dugum bir sonraki istekte oradan devam eder."""
        girisler = self._oku(
            f"SELECT sira, tablo, satir_id FROM degisim_gunlugu WHERE sira > ? "
            f"AND tablo IN ({','.join('?' * len(ASAGI))}) ORDER BY sira LIMIT ?",
            (int(sonra), *ASAGI, int(sinir)),
        )
        kayitlar = []
        for g in girisler:
            if g["satir_id"].startswith(f"{haric_dugum}~"):
                continue
            veri = self._satir_verisi(g["tablo"], g["satir_id"])
            if veri is None:
                continue
            if "~" not in veri["id"]:
                veri["id"] = f"{merkez_adi}~{veri['id']}"
            kayitlar.append({"sira": g["sira"], "tablo": g["tablo"], "veri": veri})
        son = girisler[-1]["sira"] if girisler else int(sonra)
        return {"kayitlar": kayitlar, "sonSira": son, "devamVar": len(girisler) == int(sinir)}

    def gelen_listele(self, dugum: Optional[str], tablo: Optional[str], sinir: int = 100) -> list[dict]:
        import json

        kosul, p = [], []
        if dugum:
            kosul.append("dugum = ?")
            p.append(dugum)
        if tablo:
            kosul.append("tablo = ?")
            p.append(tablo)
        nerede = f"WHERE {' AND '.join(kosul)}" if kosul else ""
        satirlar = self._oku(
            f"SELECT dugum, tablo, satir_id, sira, veri, alindi FROM gelen_kayitlar {nerede} "
            "ORDER BY alindi DESC LIMIT ?",
            (*p, int(sinir)),
        )
        for s in satirlar:
            s["veri"] = json.loads(s["veri"])
        return satirlar

    def gelen_ozeti(self) -> list[dict]:
        return self._oku(
            "SELECT dugum, tablo, COUNT(*) AS sayi, MAX(alindi) AS sonAlinan "
            "FROM gelen_kayitlar GROUP BY dugum, tablo ORDER BY dugum, tablo"
        )
