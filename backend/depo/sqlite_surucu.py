"""SQLite surucusu -- yerel gelistirme ve tek makinede calisan kurulum icin.

Tablolar MIMARI.md 3'teki mekansal depoyla ayni isleri gorur; mekansal indeks
yerine basit sinir kutusu suzmesi ve haversine mesafesi kullanilir. Sehir
olceginde (on binlerce kayit) bu yeterlidir; il olcegine cikildiginda PostGIS
surucusu devreye girecek, arayuz ayni kalacak.

Es zamanlilik: SQLite tek yazar kabul eder. WAL kipi acik, `check_same_thread`
kapali ve butun yazmalar tek kilit altinda; FastAPI'nin is parcaciklari boylece
guvenle paylasir.
"""

from __future__ import annotations

import json
import math
import sqlite3
import time
import uuid
from threading import Lock
from typing import Any, Iterable, Optional

SEMA = """
CREATE TABLE IF NOT EXISTS kullanicilar (
    id            TEXT PRIMARY KEY,
    eposta        TEXT NOT NULL UNIQUE,
    ad_soyad      TEXT NOT NULL,
    sifre_ozeti   TEXT NOT NULL,
    rol           TEXT NOT NULL,
    birim         TEXT,
    sehir         TEXT,
    olusturuldu   REAL NOT NULL,
    son_giris     REAL,
    ekip_id       TEXT
);

CREATE TABLE IF NOT EXISTS oturumlar (
    jeton_ozeti   TEXT PRIMARY KEY,
    kullanici_id  TEXT NOT NULL REFERENCES kullanicilar(id) ON DELETE CASCADE,
    olusturuldu   REAL NOT NULL,
    biter         REAL NOT NULL,
    iptal         INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_oturum_kullanici ON oturumlar(kullanici_id);

-- Mobil "güvendeyim" bildirimi: yalnız hesap sahibinin son seçimi.
-- SOS değildir, otomatik yardım çağrısı oluşturmaz.
CREATE TABLE IF NOT EXISTS kullanici_guvenlik_durumlari (
    kullanici_id TEXT PRIMARY KEY REFERENCES kullanicilar(id) ON DELETE CASCADE,
    durum TEXT NOT NULL CHECK (durum IN ('SAFE','NEED_HELP','UNKNOWN')),
    lat REAL,
    lon REAL,
    not_metni TEXT,
    guncellendi REAL NOT NULL
);

-- Ortak cikti sozlesmesi (CLAUDE.md kural 2):
-- (konum, hasar/aciliyet skoru, guven, zaman damgasi, kaynak tipi)
CREATE TABLE IF NOT EXISTS hasar_noktalari (
    id          TEXT PRIMARY KEY,
    lon         REAL NOT NULL,
    lat         REAL NOT NULL,
    skor        REAL NOT NULL,
    guven       REAL NOT NULL,
    zaman       REAL NOT NULL,
    kaynak      TEXT NOT NULL,
    etiket      TEXT,
    bolge       TEXT,
    ek          TEXT
);
CREATE INDEX IF NOT EXISTS ix_hasar_zaman ON hasar_noktalari(zaman);
CREATE INDEX IF NOT EXISTS ix_hasar_kaynak ON hasar_noktalari(kaynak);
CREATE INDEX IF NOT EXISTS ix_hasar_konum ON hasar_noktalari(lon, lat);

CREATE TABLE IF NOT EXISTS sos_cagrilari (
    id            TEXT PRIMARY KEY,
    lon           REAL NOT NULL,
    lat           REAL NOT NULL,
    oncelik       TEXT NOT NULL,
    durum         TEXT NOT NULL DEFAULT 'bekliyor',
    zaman         REAL NOT NULL,
    mahalle       TEXT,
    metin         TEXT,
    kullanici_id  TEXT,
    ekip_id       TEXT,
    atama_zamani  REAL,
    kapanma_zamani REAL,
    kanal         TEXT,
    ek            TEXT
);
CREATE INDEX IF NOT EXISTS ix_sos_zaman ON sos_cagrilari(zaman);
CREATE INDEX IF NOT EXISTS ix_sos_durum ON sos_cagrilari(durum);
CREATE INDEX IF NOT EXISTS ix_sos_kullanici ON sos_cagrilari(kullanici_id);

-- Ekip (J-54): kurum, tur ve kisi sayisi sevkte "kac kisi gidiyor" sorusunun
-- cevabidir. `durum` yalniz elle verilen durumdur (musait | hizmet-disi);
-- ekibin gorevde olup olmadigi `gorevler` tablosundan okunur, burada tutulmaz.
-- `gorev_id` eski surumden kaldi, kullanilmiyor (hic yazilmiyordu, J-54).
CREATE TABLE IF NOT EXISTS ekipler (
    id           TEXT PRIMARY KEY,
    ad           TEXT NOT NULL,
    lon          REAL,
    lat          REAL,
    durum        TEXT NOT NULL DEFAULT 'musait',
    gorev_id     TEXT,
    guncellendi  REAL NOT NULL,
    ek           TEXT,
    kurum        TEXT,
    tur          TEXT,
    kisi_sayisi  INTEGER,
    konum_zamani REAL
);

-- Sevk gorevi (J-54): bir olaya (SOS cagrisi ya da ihbar) giden ekip. Gorev
-- silinmez; biter ('tamamlandi') ya da iptal edilir. Bir ekibin ayni anda tek
-- acik gorevi olur ve bunu veritabani saglar (ux_gorev_ekip_acik): ayni ekip
-- iki yere birden gonderilemez. Bir olaya birden cok ekip gidebilir (ek destek).
CREATE TABLE IF NOT EXISTS gorevler (
    id           TEXT PRIMARY KEY,
    hedef_tur    TEXT NOT NULL CHECK (hedef_tur IN ('sos','ihbar')),
    hedef_id     TEXT NOT NULL,
    ekip_id      TEXT NOT NULL REFERENCES ekipler(id),
    kisi_sayisi  INTEGER NOT NULL CHECK (kisi_sayisi BETWEEN 1 AND 500),
    durum        TEXT NOT NULL DEFAULT 'atandi'
                 CHECK (durum IN ('atandi','yolda','olay-yerinde','tamamlandi','iptal')),
    ek_destek    INTEGER NOT NULL DEFAULT 0,
    not_metni    TEXT,
    cikis_lon    REAL,
    cikis_lat    REAL,
    atandi       REAL NOT NULL,
    yola_cikti   REAL,
    vardi        REAL,
    bitti        REAL,
    sonuc        TEXT,
    -- Ekip isini bitirdi ama olay suruyor (baska ekip ya da ekipman gerek).
    olay_suruyor INTEGER NOT NULL DEFAULT 0,
    atayan_id    TEXT,
    atayan_ad    TEXT
);
CREATE INDEX IF NOT EXISTS ix_gorev_hedef ON gorevler(hedef_tur, hedef_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_gorev_ekip_acik ON gorevler(ekip_id)
    WHERE durum IN ('atandi','yolda','olay-yerinde');

-- Gorevin her adimi, kimden geldigiyle: ekibin kendi telefonu ya da
-- koordinasyon (telsizle gelen bilgi).
CREATE TABLE IF NOT EXISTS gorev_adimlari (
    gorev_id   TEXT NOT NULL REFERENCES gorevler(id) ON DELETE CASCADE,
    durum      TEXT NOT NULL,
    zaman      REAL NOT NULL,
    kisi_id    TEXT,
    kisi_ad    TEXT,
    kaynak     TEXT NOT NULL CHECK (kaynak IN ('ekip','koordinasyon')),
    not_metni  TEXT
);
CREATE INDEX IF NOT EXISTS ix_gorev_adim ON gorev_adimlari(gorev_id, zaman);

CREATE TABLE IF NOT EXISTS yol_kapanmalari (
    id          TEXT PRIMARY KEY,
    lon         REAL NOT NULL,
    lat         REAL NOT NULL,
    derece      INTEGER NOT NULL,
    zaman       REAL NOT NULL,
    kaynak      TEXT NOT NULL,
    analiz_id   TEXT,
    ek          TEXT
);
CREATE INDEX IF NOT EXISTS ix_kapanma_zaman ON yol_kapanmalari(zaman);

-- Acil durum bildirimleri (J-45). Eskiden yalniz bellekteydi: sunucu yeniden
-- baslayinca yayindaki bildirim kayboluyordu ve kimin gonderdigi tutulmuyordu.
-- Geri cekilen bildirim silinmez; `kaldirildi` zamani ve geri ceken yazilir.
CREATE TABLE IF NOT EXISTS bildirimler (
    id            TEXT PRIMARY KEY,
    baslik        TEXT NOT NULL,
    metin         TEXT NOT NULL,
    onem          TEXT NOT NULL CHECK (onem IN ('acil','uyari','bilgi')),
    konum         TEXT,
    buyukluk      REAL,
    zaman         REAL NOT NULL,
    kaynak        TEXT NOT NULL,
    gonderen_id   TEXT,
    gonderen_ad   TEXT,
    kaldirildi    REAL,
    kaldiran_id   TEXT,
    kaldiran_ad   TEXT
);
CREATE INDEX IF NOT EXISTS ix_bildirim_zaman ON bildirimler(zaman);

-- Afetzede ihbarlari (J-51): hasar fotografi, yazili ihbar ve ihtiyac talebi.
-- SOS kendi tablosunda kalir (sos_cagrilari). Modelin ciktisi `ek` icinde
-- (secilen model, tespitler ya da metin modelinin sonucu); ihbari yapanin kendi
-- yazdigi `metin`. Isleme alinan ihbar silinmez, durumu degisir.
CREATE TABLE IF NOT EXISTS ihbarlar (
    id            TEXT PRIMARY KEY,
    tur           TEXT NOT NULL CHECK (tur IN ('fotograf','metin','ihtiyac')),
    lon           REAL NOT NULL,
    lat           REAL NOT NULL,
    zaman         REAL NOT NULL,
    durum         TEXT NOT NULL DEFAULT 'yeni' CHECK (durum IN ('yeni','goruldu','kapandi')),
    kullanici_id  TEXT,
    metin         TEXT,
    mahalle       TEXT,
    etiket        TEXT,
    skor          REAL,
    guven         REAL,
    hasar_id      TEXT,
    ek            TEXT,
    isleyen_id    TEXT,
    isleyen_ad    TEXT,
    guncellendi   REAL,
    istemci_anahtari TEXT,
    istek_ozeti     TEXT
);
CREATE INDEX IF NOT EXISTS ix_ihbar_zaman ON ihbarlar(zaman);
CREATE INDEX IF NOT EXISTS ix_ihbar_kullanici ON ihbarlar(kullanici_id);

-- Fotograf ayri tabloda: ihbar listesi okunurken goruntu bellege alinmasin.
CREATE TABLE IF NOT EXISTS ihbar_fotograflari (
    ihbar_id  TEXT PRIMARY KEY REFERENCES ihbarlar(id) ON DELETE CASCADE,
    veri      BLOB NOT NULL,
    en        INTEGER NOT NULL,
    boy       INTEGER NOT NULL
);
"""


# Sevk gorevi (J-54). Acik gorev: ekip yolda ya da olay yerinde, is bitmedi.
ACIK_GOREV = ("atandi", "yolda", "olay-yerinde")
ACIK_GOREV_SQL = "('atandi','yolda','olay-yerinde')"
GOREV_SIRASI = {"atandi": 0, "yolda": 1, "olay-yerinde": 2, "tamamlandi": 3}


class GorevHatasi(Exception):
    """Sevk kurali ihlali. `kod` uca HTTP durumunu sectirir; `mesaj` kullaniciya
    gosterilecek Turkce aciklamadir."""

    def __init__(self, kod: str, mesaj: str):
        super().__init__(mesaj)
        self.kod = kod
        self.mesaj = mesaj


def yeni_ihbar_kimligi() -> str:
    return f"ihb-{uuid.uuid4().hex[:8]}"


def _satir(row: Optional[sqlite3.Row]) -> Optional[dict]:
    return dict(row) if row is not None else None


def _satirlar(rows: Iterable[sqlite3.Row]) -> list[dict]:
    return [dict(r) for r in rows]


class SqliteDepo:
    def __init__(self, yol: str):
        self.yol = yol
        self._kilit = Lock()
        self._baglanti = sqlite3.connect(yol, check_same_thread=False)
        self._baglanti.row_factory = sqlite3.Row
        self._baglanti.execute("PRAGMA journal_mode=WAL")
        self._baglanti.execute("PRAGMA synchronous=NORMAL")
        self._baglanti.execute("PRAGMA foreign_keys=ON")
        with self._kilit:
            self._baglanti.executescript(SEMA)
            self._sutunlari_tamamla()
            # Eski SQLite dosyalarinda yeni sutunlar _sutunlari_tamamla'dan
            # sonra var olur. Her kullanicinin tekrar-istek anahtari benzersizdir.
            self._baglanti.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_ihbar_istemci_anahtari "
                "ON ihbarlar(kullanici_id, istemci_anahtari) "
                "WHERE istemci_anahtari IS NOT NULL"
            )
            self._baglanti.commit()

    # Sonradan eklenen sutunlar. `CREATE TABLE IF NOT EXISTS` var olan tabloya
    # sutun eklemez; eski veritabani burada tamamlanir, veri kaybolmaz.
    _SONRADAN_EKLENEN = {
        "kullanicilar": (("ekip_id", "TEXT"),),
        "ihbarlar": (("istemci_anahtari", "TEXT"), ("istek_ozeti", "TEXT")),
        "ekipler": (
            ("kurum", "TEXT"),
            ("tur", "TEXT"),
            ("kisi_sayisi", "INTEGER"),
            ("konum_zamani", "REAL"),
        ),
    }

    def _sutunlari_tamamla(self) -> None:
        for tablo, sutunlar in self._SONRADAN_EKLENEN.items():
            var = {r[1] for r in self._baglanti.execute(f"PRAGMA table_info({tablo})")}
            for ad, tip in sutunlar:
                if ad not in var:
                    self._baglanti.execute(f"ALTER TABLE {tablo} ADD COLUMN {ad} {tip}")

    # ---- genel yardimcilar ------------------------------------------------

    def _yaz(self, sql: str, parametreler: tuple = ()) -> None:
        with self._kilit:
            self._baglanti.execute(sql, parametreler)
            self._baglanti.commit()

    def _oku(self, sql: str, parametreler: tuple = ()) -> list[dict]:
        with self._kilit:
            return _satirlar(self._baglanti.execute(sql, parametreler).fetchall())

    def _tek(self, sql: str, parametreler: tuple = ()) -> Optional[dict]:
        with self._kilit:
            return _satir(self._baglanti.execute(sql, parametreler).fetchone())

    def kapat(self) -> None:
        with self._kilit:
            self._baglanti.close()

    # ---- kullanicilar -----------------------------------------------------

    def kullanici_olustur(
        self,
        eposta: str,
        ad_soyad: str,
        sifre_ozeti: str,
        rol: str,
        birim: str | None = None,
        sehir: str | None = None,
    ) -> dict:
        kayit = {
            "id": f"kul-{uuid.uuid4().hex[:10]}",
            "eposta": eposta.strip().lower(),
            "ad_soyad": ad_soyad.strip(),
            "sifre_ozeti": sifre_ozeti,
            "rol": rol,
            "birim": birim,
            "sehir": sehir,
            "olusturuldu": time.time(),
            "son_giris": None,
        }
        self._yaz(
            """INSERT INTO kullanicilar
               (id, eposta, ad_soyad, sifre_ozeti, rol, birim, sehir, olusturuldu, son_giris)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            tuple(kayit.values()),
        )
        return kayit

    def kullanici_eposta(self, eposta: str) -> Optional[dict]:
        return self._tek(
            "SELECT * FROM kullanicilar WHERE eposta = ?", (eposta.strip().lower(),)
        )

    def kullanici_id(self, kullanici_id: str) -> Optional[dict]:
        return self._tek("SELECT * FROM kullanicilar WHERE id = ?", (kullanici_id,))

    def giris_isle(self, kullanici_id: str) -> None:
        self._yaz(
            "UPDATE kullanicilar SET son_giris = ? WHERE id = ?", (time.time(), kullanici_id)
        )

    def rol_ata(self, kullanici_id: str, rol: str) -> None:
        """Rol YALNIZCA buradan degisir; istemci gonderdigi rolle rol alamaz."""
        self._yaz("UPDATE kullanicilar SET rol = ? WHERE id = ?", (rol, kullanici_id))

    def kullanici_sayisi(self) -> int:
        satir = self._tek("SELECT COUNT(*) AS n FROM kullanicilar")
        return int(satir["n"]) if satir else 0

    def guvenlik_durumu_yaz(
        self, kullanici_id: str, durum: str, lat: float | None = None,
        lon: float | None = None, not_metni: str | None = None,
    ) -> dict:
        """Kullaniciya ozel son beyan; yardim cagrisina donusturmez."""
        zaman = time.time()
        self._yaz(
            """INSERT INTO kullanici_guvenlik_durumlari
               (kullanici_id, durum, lat, lon, not_metni, guncellendi)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(kullanici_id) DO UPDATE SET
               durum=excluded.durum, lat=excluded.lat, lon=excluded.lon,
               not_metni=excluded.not_metni, guncellendi=excluded.guncellendi""",
            (kullanici_id, durum, lat, lon, not_metni, zaman),
        )
        return self.guvenlik_durumu_oku(kullanici_id)

    def guvenlik_durumu_oku(self, kullanici_id: str) -> Optional[dict]:
        return self._tek(
            "SELECT * FROM kullanici_guvenlik_durumlari WHERE kullanici_id = ?",
            (kullanici_id,),
        )

    # ---- oturumlar (yenileme jetonlari) -----------------------------------

    def oturum_ac(self, kullanici_id: str, jeton_ozeti: str, omur_sn: float) -> None:
        simdi = time.time()
        self._yaz(
            """INSERT OR REPLACE INTO oturumlar
               (jeton_ozeti, kullanici_id, olusturuldu, biter, iptal)
               VALUES (?,?,?,?,0)""",
            (jeton_ozeti, kullanici_id, simdi, simdi + omur_sn),
        )

    def oturum_bul(self, jeton_ozeti: str) -> Optional[dict]:
        kayit = self._tek(
            "SELECT * FROM oturumlar WHERE jeton_ozeti = ? AND iptal = 0", (jeton_ozeti,)
        )
        if kayit and kayit["biter"] < time.time():
            return None
        return kayit

    def oturum_iptal(self, jeton_ozeti: str) -> None:
        self._yaz("UPDATE oturumlar SET iptal = 1 WHERE jeton_ozeti = ?", (jeton_ozeti,))

    def oturumlari_iptal(self, kullanici_id: str) -> None:
        self._yaz("UPDATE oturumlar SET iptal = 1 WHERE kullanici_id = ?", (kullanici_id,))

    # ---- hasar noktalari (ortak sozlesme) ---------------------------------

    def hasar_ekle(
        self,
        lon: float,
        lat: float,
        skor: float,
        guven: float,
        kaynak: str,
        zaman: float | None = None,
        etiket: str | None = None,
        bolge: str | None = None,
        ek: dict | None = None,
    ) -> dict:
        kayit = {
            "id": f"hsr-{uuid.uuid4().hex[:10]}",
            "lon": float(lon),
            "lat": float(lat),
            "skor": float(skor),
            "guven": float(guven),
            "zaman": float(zaman if zaman is not None else time.time()),
            "kaynak": kaynak,
            "etiket": etiket,
            "bolge": bolge,
            "ek": json.dumps(ek, ensure_ascii=False) if ek else None,
        }
        self._yaz(
            """INSERT INTO hasar_noktalari
               (id, lon, lat, skor, guven, zaman, kaynak, etiket, bolge, ek)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            tuple(kayit.values()),
        )
        return kayit

    def hasar_sil_tatbikat(self, is_id: str) -> int:
        """Bir tatbikat kosusunun yazdigi hasar noktalarini siler.

        Tatbikat gercek goruntude gercek model kosturur, ama sonucu CANLI OLAY
        degildir: kosu bitirilince bu noktalar gercek veriyle karismamali
        (CLAUDE.md 1). Noktalar `ek.tatbikat` alaninda kosunun kimligini tasir.
        Donus: silinen kayit sayisi.
        """
        satirlar = self._oku(
            # Onek eslemesi: kontrol kosusu `<isId>_kontrol` kimligiyle yaziyordu,
            # tam esleme onu birakiyordu.
            "SELECT id FROM hasar_noktalari WHERE ek LIKE ?", (f'%"tatbikat": "{is_id}%',)
        )
        for satir in satirlar:
            self._yaz("DELETE FROM hasar_noktalari WHERE id = ?", (satir["id"],))
        return len(satirlar)

    def hasar_listele(
        self,
        baslangic: float | None = None,
        bitis: float | None = None,
        kutu: tuple[float, float, float, float] | None = None,
        kaynak: str | None = None,
        sinir: int = 20000,
    ) -> list[dict]:
        kosullar, parametreler = self._zaman_kutu_kosullari(baslangic, bitis, kutu)
        if kaynak:
            kosullar.append("kaynak = ?")
            parametreler.append(kaynak)
        nerede = f"WHERE {' AND '.join(kosullar)}" if kosullar else ""
        return self._oku(
            f"SELECT * FROM hasar_noktalari {nerede} ORDER BY zaman DESC LIMIT ?",
            (*parametreler, sinir),
        )

    # ---- SOS cagrilari ----------------------------------------------------

    def sos_ekle(
        self,
        lon: float,
        lat: float,
        oncelik: str,
        metin: str | None = None,
        mahalle: str | None = None,
        kullanici_id: str | None = None,
        kanal: str | None = None,
        zaman: float | None = None,
        ek: dict | None = None,
    ) -> dict:
        """`ek`: yapilandirilmis ek bilgi (kisi sayisi, ihtiyaclar, konumun
        kaynagi) -- tablodaki `ek` sutununa JSON olarak yazilir."""
        kayit = {
            "id": f"sos-{uuid.uuid4().hex[:8]}",
            "lon": float(lon),
            "lat": float(lat),
            "oncelik": oncelik,
            "durum": "bekliyor",
            "zaman": float(zaman if zaman is not None else time.time()),
            "mahalle": mahalle,
            "metin": metin,
            "kullanici_id": kullanici_id,
            "ekip_id": None,
            "atama_zamani": None,
            "kapanma_zamani": None,
            "kanal": kanal,
            "ek": json.dumps(ek, ensure_ascii=False) if ek else None,
        }
        self._yaz(
            """INSERT INTO sos_cagrilari
               (id, lon, lat, oncelik, durum, zaman, mahalle, metin, kullanici_id,
                ekip_id, atama_zamani, kapanma_zamani, kanal, ek)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            tuple(kayit.values()),
        )
        return kayit

    def sos_listele(
        self,
        baslangic: float | None = None,
        bitis: float | None = None,
        kutu: tuple[float, float, float, float] | None = None,
        durum: str | None = None,
        kullanici_id: str | None = None,
        sinir: int = 5000,
    ) -> list[dict]:
        kosullar, parametreler = self._zaman_kutu_kosullari(baslangic, bitis, kutu)
        if durum:
            kosullar.append("durum = ?")
            parametreler.append(durum)
        if kullanici_id:
            # Afetzede yalniz kendi cagrisini gorur (MIMARI 9).
            kosullar.append("kullanici_id = ?")
            parametreler.append(kullanici_id)
        nerede = f"WHERE {' AND '.join(kosullar)}" if kosullar else ""
        return self._oku(
            f"SELECT * FROM sos_cagrilari {nerede} ORDER BY zaman DESC LIMIT ?",
            (*parametreler, sinir),
        )

    def sos_bul(self, sos_id: str) -> Optional[dict]:
        return self._tek("SELECT * FROM sos_cagrilari WHERE id = ?", (sos_id,))

    def sos_kapat(
        self, sos_id: str, kisi_id: str | None = None, kisi_ad: str | None = None
    ) -> tuple[bool, list[str]]:
        """Cagriyi kapatir; acik gorevleri de bitirir ki ekip "gorevde" asili
        kalmasin (J-54). Doner: (kapandi mi, biten gorevlerin kimlikleri)."""
        simdi = time.time()
        with self._kilit:
            imlec = self._baglanti.execute(
                """UPDATE sos_cagrilari
                   SET durum = 'kapandi', kapanma_zamani = ?
                   WHERE id = ? AND durum != 'kapandi'""",
                (simdi, sos_id),
            )
            if imlec.rowcount == 0:
                self._baglanti.rollback()
                return False, []
            biten = self._acik_gorevleri_bitir("sos", sos_id, kisi_id, kisi_ad, simdi)
            self._baglanti.commit()
            return True, biten

    def sos_sayilari(
        self, baslangic: float | None = None, bitis: float | None = None
    ) -> dict[str, int]:
        kosullar, parametreler = self._zaman_kutu_kosullari(baslangic, bitis, None)
        nerede = f"WHERE {' AND '.join(kosullar)}" if kosullar else ""
        satirlar = self._oku(
            f"SELECT durum, COUNT(*) AS n FROM sos_cagrilari {nerede} GROUP BY durum",
            tuple(parametreler),
        )
        return {s["durum"]: int(s["n"]) for s in satirlar}

    # ---- ekipler ----------------------------------------------------------

    def ekip_olustur(
        self,
        ad: str,
        kurum: str | None,
        tur: str | None,
        kisi_sayisi: int | None,
        lon: float | None = None,
        lat: float | None = None,
    ) -> dict:
        simdi = time.time()
        ekip_id = f"ekp-{uuid.uuid4().hex[:6]}"
        self._yaz(
            """INSERT INTO ekipler
               (id, ad, lon, lat, durum, gorev_id, guncellendi, ek, kurum, tur, kisi_sayisi, konum_zamani)
               VALUES (?,?,?,?,'musait',NULL,?,NULL,?,?,?,?)""",
            (ekip_id, ad, lon, lat, simdi, kurum, tur, kisi_sayisi,
             simdi if lon is not None and lat is not None else None),
        )
        return self.ekip_bul(ekip_id)

    def ekip_kaydet(
        self,
        ekip_id: str,
        ad: str,
        lon: float | None = None,
        lat: float | None = None,
        durum: str = "musait",
        kurum: str | None = None,
        tur: str | None = None,
        kisi_sayisi: int | None = None,
    ) -> dict:
        """Kimligi verilen ekibi acar ya da gunceller. Konum verilmezse eski
        konum korunur (eskiden siliniyordu)."""
        simdi = time.time()
        konum_zamani = simdi if lon is not None and lat is not None else None
        self._yaz(
            """INSERT INTO ekipler
               (id, ad, lon, lat, durum, gorev_id, guncellendi, ek, kurum, tur, kisi_sayisi, konum_zamani)
               VALUES (?,?,?,?,?,NULL,?,NULL,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET
                 ad = excluded.ad,
                 lon = COALESCE(excluded.lon, ekipler.lon),
                 lat = COALESCE(excluded.lat, ekipler.lat),
                 konum_zamani = COALESCE(excluded.konum_zamani, ekipler.konum_zamani),
                 durum = excluded.durum,
                 kurum = COALESCE(excluded.kurum, ekipler.kurum),
                 tur = COALESCE(excluded.tur, ekipler.tur),
                 kisi_sayisi = COALESCE(excluded.kisi_sayisi, ekipler.kisi_sayisi),
                 guncellendi = excluded.guncellendi""",
            (ekip_id, ad, lon, lat, durum, simdi, kurum, tur, kisi_sayisi, konum_zamani),
        )
        return self.ekip_bul(ekip_id)

    def ekip_guncelle(self, ekip_id: str, alanlar: dict) -> Optional[dict]:
        """Yalniz verilen alanlari degistirir: ad, kurum, tur, kisi_sayisi, durum."""
        izinli = ("ad", "kurum", "tur", "kisi_sayisi", "durum")
        degisen = {k: v for k, v in alanlar.items() if k in izinli}
        if degisen:
            atama = ", ".join(f"{k} = ?" for k in degisen)
            self._yaz(
                f"UPDATE ekipler SET {atama}, guncellendi = ? WHERE id = ?",
                (*degisen.values(), time.time(), ekip_id),
            )
        return self.ekip_bul(ekip_id)

    def ekip_konum(self, ekip_id: str, lon: float, lat: float) -> None:
        simdi = time.time()
        self._yaz(
            "UPDATE ekipler SET lon = ?, lat = ?, konum_zamani = ?, guncellendi = ? WHERE id = ?",
            (lon, lat, simdi, simdi, ekip_id),
        )

    def ekip_listele(self) -> list[dict]:
        return self._oku("SELECT * FROM ekipler ORDER BY ad")

    def ekip_bul(self, ekip_id: str) -> Optional[dict]:
        return self._tek("SELECT * FROM ekipler WHERE id = ?", (ekip_id,))

    def saha_kullanicilari(self) -> list[dict]:
        """Ekibe baglanabilecek hesaplar: saha rolundekiler."""
        return self._oku(
            """SELECT id, eposta, ad_soyad, ekip_id FROM kullanicilar
               WHERE rol = 'saha' ORDER BY ad_soyad"""
        )

    def ekip_uyelerini_ayarla(self, ekip_id: str, kullanici_idler: list[str]) -> None:
        """Ekibin uyelerini verilen listeyle degistirir. Bir kisi tek ekipte
        olur: baska ekipteyse oradan cikar."""
        with self._kilit:
            self._baglanti.execute(
                "UPDATE kullanicilar SET ekip_id = NULL WHERE ekip_id = ?", (ekip_id,)
            )
            for kid in kullanici_idler:
                self._baglanti.execute(
                    "UPDATE kullanicilar SET ekip_id = ? WHERE id = ? AND rol = 'saha'",
                    (ekip_id, kid),
                )
            self._baglanti.commit()

    def musait_ekipler(self) -> list[dict]:
        """Elle hizmet disi yapilmamis ve acik gorevi olmayan ekipler."""
        return self._oku(
            f"""SELECT e.* FROM ekipler e
                WHERE e.durum = 'musait' AND NOT EXISTS (
                  SELECT 1 FROM gorevler g
                  WHERE g.ekip_id = e.id AND g.durum IN {ACIK_GOREV_SQL})
                ORDER BY e.ad"""
        )

    def en_yakin_ekip(self, lon: float, lat: float) -> Optional[dict]:
        """Musait ekiplerin en yakini. Musait ekip yoksa None: gorevdeki bir
        ekip onerilmez (J-54'ten once gorevdeki ekip yeniden oneriliyordu)."""
        ekipler = [e for e in self.musait_ekipler() if e["lon"] is not None]
        if not ekipler:
            return None
        return min(ekipler, key=lambda e: mesafe_m(lon, lat, e["lon"], e["lat"]))

    # ---- sevk gorevleri (J-54) ---------------------------------------------

    _GOREV_SUTUNLARI = (
        "g.*, e.ad AS ekip_ad, e.kurum AS ekip_kurum, e.tur AS ekip_tur, "
        "e.kisi_sayisi AS ekip_kisi_sayisi, e.lon AS ekip_lon, e.lat AS ekip_lat, "
        "e.konum_zamani AS ekip_konum_zamani"
    )

    def _kilitsiz_tek(self, sql: str, parametreler: tuple = ()) -> Optional[dict]:
        """Kilit ALINMIS iken okuma (kilit yeniden girilemez)."""
        return _satir(self._baglanti.execute(sql, parametreler).fetchone())

    def _kilitsiz_hepsi(self, sql: str, parametreler: tuple = ()) -> list[dict]:
        return _satirlar(self._baglanti.execute(sql, parametreler).fetchall())

    def _hedef_oku(self, hedef_tur: str, hedef_id: str) -> Optional[dict]:
        tablo = {"sos": "sos_cagrilari", "ihbar": "ihbarlar"}[hedef_tur]
        return self._kilitsiz_tek(f"SELECT * FROM {tablo} WHERE id = ?", (hedef_id,))

    def _adim_yaz(
        self, gorev_id: str, durum: str, zaman: float, kisi_id: str | None,
        kisi_ad: str | None, kaynak: str, not_metni: str | None = None,
    ) -> None:
        self._baglanti.execute(
            """INSERT INTO gorev_adimlari (gorev_id, durum, zaman, kisi_id, kisi_ad, kaynak, not_metni)
               VALUES (?,?,?,?,?,?,?)""",
            (gorev_id, durum, zaman, kisi_id, kisi_ad, kaynak, not_metni),
        )

    def gorev_ac(
        self,
        hedef_tur: str,
        hedef_id: str,
        ekip_id: str,
        kisi_sayisi: int | None,
        kisi_id: str | None,
        kisi_ad: str | None,
        kaynak: str,
        not_metni: str | None = None,
        ek_destek: bool = False,
    ) -> dict:
        """Olaya ekip gonderir. Kurallar tek kilit altinda, tek islemde:
          - kapanmis olaya ekip gitmez;
          - hizmet disi ya da baska gorevdeki ekip gonderilmez (veritabani da
            engeller: ux_gorev_ekip_acik);
          - olaya zaten ekip gidiyorsa ikincisi ancak `ek_destek` ile gider;
          - giden kisi sayisi ekibin kayitli sayisini gecemez.
        Olay 'bekliyor' ise 'atandi' olur (ihbar 'yeni' ise 'goruldu')."""
        simdi = time.time()
        with self._kilit:
            try:
                hedef = self._hedef_oku(hedef_tur, hedef_id)
                if hedef is None:
                    raise GorevHatasi("hedef-yok", "Olay bulunamadı.")
                if hedef["durum"] == "kapandi":
                    raise GorevHatasi("hedef-kapali", "Olay kapanmış; ekip gönderilemez.")
                ekip = self._kilitsiz_tek("SELECT * FROM ekipler WHERE id = ?", (ekip_id,))
                if ekip is None:
                    raise GorevHatasi("ekip-yok", "Ekip bulunamadı.")
                if ekip["durum"] != "musait":
                    raise GorevHatasi("ekip-hizmet-disi", f"{ekip['ad']} hizmet dışı işaretli.")
                mesgul = self._kilitsiz_tek(
                    f"SELECT hedef_tur, hedef_id FROM gorevler WHERE ekip_id = ? AND durum IN {ACIK_GOREV_SQL}",
                    (ekip_id,),
                )
                if mesgul is not None:
                    orasi = self._hedef_oku(mesgul["hedef_tur"], mesgul["hedef_id"]) or {}
                    yer = orasi.get("mahalle") or mesgul["hedef_id"]
                    raise GorevHatasi(
                        "ekip-mesgul",
                        f"{ekip['ad']} şu an başka görevde ({yer}). "
                        "Önce o görev bitmeli ya da iptal edilmeli.",
                    )
                gidenler = self._kilitsiz_hepsi(
                    f"""SELECT e.ad FROM gorevler g JOIN ekipler e ON e.id = g.ekip_id
                        WHERE g.hedef_tur = ? AND g.hedef_id = ? AND g.durum IN {ACIK_GOREV_SQL}""",
                    (hedef_tur, hedef_id),
                )
                if gidenler and not ek_destek:
                    adlar = ", ".join(g["ad"] for g in gidenler)
                    raise GorevHatasi(
                        "zaten-ekip-var",
                        f"Bu olaya zaten {adlar} gidiyor. İkinci ekip ancak ek destek olarak gönderilir.",
                    )
                kayitli = ekip.get("kisi_sayisi")
                kisi = int(kisi_sayisi) if kisi_sayisi is not None else (kayitli or None)
                if kisi is None:
                    raise GorevHatasi(
                        "kisi-yok", f"{ekip['ad']} için kişi sayısı kayıtlı değil; kaç kişi gittiğini yaz."
                    )
                if not 1 <= kisi <= 500:
                    raise GorevHatasi("kisi-gecersiz", "Kişi sayısı 1 ile 500 arasında olmalı.")
                if kayitli and kisi > kayitli:
                    raise GorevHatasi(
                        "kisi-fazla",
                        f"{ekip['ad']} {kayitli} kişi kayıtlı; en çok {kayitli} kişi gönderilebilir. "
                        "Ekip büyüdüyse önce ekip kaydını güncelle.",
                    )

                gorev_id = f"grv-{uuid.uuid4().hex[:8]}"
                try:
                    self._baglanti.execute(
                        """INSERT INTO gorevler
                           (id, hedef_tur, hedef_id, ekip_id, kisi_sayisi, durum, ek_destek, not_metni,
                            cikis_lon, cikis_lat, atandi, atayan_id, atayan_ad)
                           VALUES (?,?,?,?,?,'atandi',?,?,?,?,?,?,?)""",
                        (gorev_id, hedef_tur, hedef_id, ekip_id, kisi, int(bool(gidenler)), not_metni,
                         ekip.get("lon"), ekip.get("lat"), simdi, kisi_id, kisi_ad),
                    )
                except sqlite3.IntegrityError as e:
                    raise GorevHatasi("ekip-mesgul", f"{ekip['ad']} şu an başka görevde.") from e
                self._adim_yaz(gorev_id, "atandi", simdi, kisi_id, kisi_ad, kaynak, not_metni)

                if hedef_tur == "sos":
                    self._baglanti.execute(
                        """UPDATE sos_cagrilari
                           SET durum = 'atandi', ekip_id = ?, atama_zamani = COALESCE(atama_zamani, ?)
                           WHERE id = ? AND durum != 'kapandi'""",
                        (ekip_id, simdi, hedef_id),
                    )
                else:
                    self._baglanti.execute(
                        """UPDATE ihbarlar SET durum = 'goruldu', isleyen_id = ?, isleyen_ad = ?, guncellendi = ?
                           WHERE id = ? AND durum = 'yeni'""",
                        (kisi_id, kisi_ad, simdi, hedef_id),
                    )
                self._baglanti.commit()
            except Exception:
                self._baglanti.rollback()
                raise
        return self.gorev_bul(gorev_id)

    def gorev_durum(
        self,
        gorev_id: str,
        durum: str,
        kisi_id: str | None,
        kisi_ad: str | None,
        kaynak: str,
        not_metni: str | None = None,
        olay_suruyor: bool = False,
    ) -> tuple[dict, Optional[str]]:
        """Gorev yalniz ileri gider: atandi -> yolda -> olay-yerinde -> tamamlandi.
        Adim atlanabilir (yola cikisi bildirmeden "vardik" denebilir; o zaman
        cikis zamani bos kalir, uydurulmaz). Acik gorev her an iptal edilir.

        Olaydaki son acik gorev bitince olayin durumu da degisir:
          - tamamlandi: olay kapanir; `olay_suruyor` ise SOS kuyruga doner.
          - iptal: olayda daha once isini bitiren ekip varsa ve "olay suruyor"
            dememisse olay kapanir (ek destek artik gerekmedi); yoksa SOS
            kuyruga doner (baska ekip gerekir), ihbar 'goruldu' kalir.
        Doner: (gorev, olayin yeni durumu ya da None)."""
        if durum not in GOREV_SIRASI and durum != "iptal":
            raise GorevHatasi("gecersiz-durum", f"Bilinmeyen görev durumu: {durum}")
        simdi = time.time()
        hedef_durumu: Optional[str] = None
        with self._kilit:
            try:
                g = self._kilitsiz_tek("SELECT * FROM gorevler WHERE id = ?", (gorev_id,))
                if g is None:
                    raise GorevHatasi("gorev-yok", "Görev bulunamadı.")
                if g["durum"] not in ACIK_GOREV:
                    raise GorevHatasi("gorev-bitti", "Görev bitmiş; durumu değişmez.")
                if durum != "iptal" and GOREV_SIRASI[durum] <= GOREV_SIRASI[g["durum"]]:
                    raise GorevHatasi(
                        "gecersiz-gecis", "Görev bu adımı geçmiş; geri alınamaz."
                    )
                zaman_sutunu = {"yolda": "yola_cikti", "olay-yerinde": "vardi"}.get(durum, "bitti")
                sonuc = not_metni if durum in ("tamamlandi", "iptal") else g.get("sonuc")
                suruyor = int(durum == "tamamlandi" and olay_suruyor)
                self._baglanti.execute(
                    f"UPDATE gorevler SET durum = ?, {zaman_sutunu} = ?, sonuc = ?, olay_suruyor = ? WHERE id = ?",
                    (durum, simdi, sonuc, suruyor, gorev_id),
                )
                self._adim_yaz(gorev_id, durum, simdi, kisi_id, kisi_ad, kaynak, not_metni)

                if durum in ("tamamlandi", "iptal"):
                    if durum == "tamamlandi":
                        kapansin = not olay_suruyor
                    else:
                        # En son isini bitiren ekip olayi bitmis saydiysa iptal
                        # edilen ek destek olayi yeniden kuyruga sokmaz.
                        son = self._kilitsiz_tek(
                            """SELECT olay_suruyor FROM gorevler
                               WHERE hedef_tur = ? AND hedef_id = ? AND durum = 'tamamlandi'
                               ORDER BY bitti DESC LIMIT 1""",
                            (g["hedef_tur"], g["hedef_id"]),
                        )
                        kapansin = son is not None and not son["olay_suruyor"]
                    hedef_durumu = self._olay_durumunu_esitle(
                        g["hedef_tur"], g["hedef_id"], kapansin, kisi_id, kisi_ad, simdi,
                    )
                self._baglanti.commit()
            except Exception:
                self._baglanti.rollback()
                raise
        return self.gorev_bul(gorev_id), hedef_durumu

    def _olay_durumunu_esitle(
        self, hedef_tur: str, hedef_id: str, kapansin: bool,
        kisi_id: str | None, kisi_ad: str | None, simdi: float,
    ) -> Optional[str]:
        """Kilit altinda cagrilir. Olayda hala acik gorev varsa bir sey
        degismez (yalniz SOS'un gosterdigi ekip guncellenir)."""
        kalan = self._kilitsiz_hepsi(
            f"""SELECT ekip_id FROM gorevler
                WHERE hedef_tur = ? AND hedef_id = ? AND durum IN {ACIK_GOREV_SQL}
                ORDER BY atandi DESC""",
            (hedef_tur, hedef_id),
        )
        if hedef_tur == "sos":
            if kalan:
                self._baglanti.execute(
                    "UPDATE sos_cagrilari SET ekip_id = ? WHERE id = ?", (kalan[0]["ekip_id"], hedef_id)
                )
                return None
            if kapansin:
                imlec = self._baglanti.execute(
                    """UPDATE sos_cagrilari SET durum = 'kapandi', kapanma_zamani = ?
                       WHERE id = ? AND durum != 'kapandi'""",
                    (simdi, hedef_id),
                )
                return "kapandi" if imlec.rowcount else None
            imlec = self._baglanti.execute(
                """UPDATE sos_cagrilari SET durum = 'bekliyor', ekip_id = NULL, atama_zamani = NULL
                   WHERE id = ? AND durum = 'atandi'""",
                (hedef_id,),
            )
            return "bekliyor" if imlec.rowcount else None
        if kalan or not kapansin:
            return None
        imlec = self._baglanti.execute(
            """UPDATE ihbarlar SET durum = 'kapandi', isleyen_id = ?, isleyen_ad = ?, guncellendi = ?
               WHERE id = ? AND durum != 'kapandi'""",
            (kisi_id, kisi_ad, simdi, hedef_id),
        )
        return "kapandi" if imlec.rowcount else None

    def _acik_gorevleri_bitir(
        self, hedef_tur: str, hedef_id: str, kisi_id: str | None, kisi_ad: str | None, simdi: float,
    ) -> list[str]:
        """Kilit altinda: olay kapatilinca acik gorevler biter. Olay yerindeki
        ekip 'tamamlandi', yoldaki ya da henuz cikmamis ekip 'iptal' olur."""
        acik = self._kilitsiz_hepsi(
            f"SELECT id, durum FROM gorevler WHERE hedef_tur = ? AND hedef_id = ? AND durum IN {ACIK_GOREV_SQL}",
            (hedef_tur, hedef_id),
        )
        sonuc = "Olay koordinasyonca kapatıldı."
        for g in acik:
            yeni = "tamamlandi" if g["durum"] == "olay-yerinde" else "iptal"
            self._baglanti.execute(
                "UPDATE gorevler SET durum = ?, bitti = ?, sonuc = ? WHERE id = ?",
                (yeni, simdi, sonuc, g["id"]),
            )
            self._adim_yaz(g["id"], yeni, simdi, kisi_id, kisi_ad, "koordinasyon", sonuc)
        return [g["id"] for g in acik]

    def gorev_bul(self, gorev_id: str) -> Optional[dict]:
        return self._tek(
            f"SELECT {self._GOREV_SUTUNLARI} FROM gorevler g JOIN ekipler e ON e.id = g.ekip_id WHERE g.id = ?",
            (gorev_id,),
        )

    def gorev_listele(
        self,
        hedef_tur: str | None = None,
        hedef_idler: list[str] | None = None,
        ekip_id: str | None = None,
        yalniz_acik: bool = False,
        sinir: int = 5000,
    ) -> list[dict]:
        """`hedef_idler` verilirse yalniz o olaylarin gorevleri (500'luk
        parcalarla sorulur; SQLite'in degisken siniri asilmasin)."""
        kosullar, parametreler = [], []
        if hedef_tur:
            kosullar.append("g.hedef_tur = ?")
            parametreler.append(hedef_tur)
        if ekip_id:
            kosullar.append("g.ekip_id = ?")
            parametreler.append(ekip_id)
        if yalniz_acik:
            kosullar.append(f"g.durum IN {ACIK_GOREV_SQL}")
        temel = f"SELECT {self._GOREV_SUTUNLARI} FROM gorevler g JOIN ekipler e ON e.id = g.ekip_id"
        if hedef_idler is None:
            nerede = f"WHERE {' AND '.join(kosullar)}" if kosullar else ""
            return self._oku(f"{temel} {nerede} ORDER BY g.atandi DESC LIMIT ?", (*parametreler, sinir))
        sonuc: list[dict] = []
        for i in range(0, len(hedef_idler), 500):
            parca = hedef_idler[i : i + 500]
            k = [*kosullar, f"g.hedef_id IN ({','.join('?' * len(parca))})"]
            sonuc += self._oku(
                f"{temel} WHERE {' AND '.join(k)} ORDER BY g.atandi DESC", (*parametreler, *parca)
            )
        return sonuc

    def gorev_adimlari(self, gorev_idler: list[str]) -> dict[str, list[dict]]:
        adimlar: dict[str, list[dict]] = {}
        for i in range(0, len(gorev_idler), 500):
            parca = gorev_idler[i : i + 500]
            for a in self._oku(
                f"""SELECT * FROM gorev_adimlari WHERE gorev_id IN ({','.join('?' * len(parca))})
                    ORDER BY zaman""",
                tuple(parca),
            ):
                adimlar.setdefault(a["gorev_id"], []).append(a)
        return adimlar

    def ekibin_acik_gorevi(self, ekip_id: str) -> Optional[dict]:
        satir = self._tek(
            f"""SELECT {self._GOREV_SUTUNLARI} FROM gorevler g JOIN ekipler e ON e.id = g.ekip_id
                WHERE g.ekip_id = ? AND g.durum IN {ACIK_GOREV_SQL}""",
            (ekip_id,),
        )
        return satir

    # ---- yol kapanmalari --------------------------------------------------

    def kapanma_ekle(
        self,
        lon: float,
        lat: float,
        derece: int,
        kaynak: str,
        analiz_id: str | None = None,
        zaman: float | None = None,
        cizgi: list | None = None,
    ) -> dict:
        """Kapali yol parcasi. `cizgi` verilirse [[enlem, boylam], ...] olarak
        `ek` alaninda saklanir (J-58): arayuz kapanmayi KIRMIZI CIZGI olarak
        cizebilsin. Onceden yalnizca parcanin orta noktasi tutuluyordu ve
        harita her kapanmayi tek bir nokta olarak gosteriyordu."""
        kayit = {
            "id": f"kap-{uuid.uuid4().hex[:10]}",
            "lon": float(lon),
            "lat": float(lat),
            "derece": int(derece),
            "zaman": float(zaman if zaman is not None else time.time()),
            "kaynak": kaynak,
            "analiz_id": analiz_id,
            "ek": json.dumps({"cizgi": cizgi}, ensure_ascii=False) if cizgi else None,
        }
        self._yaz(
            """INSERT INTO yol_kapanmalari (id, lon, lat, derece, zaman, kaynak, analiz_id, ek)
               VALUES (?,?,?,?,?,?,?,?)""",
            tuple(kayit.values()),
        )
        return kayit

    def kapanma_listele(
        self,
        baslangic: float | None = None,
        bitis: float | None = None,
        kutu: tuple[float, float, float, float] | None = None,
        sinir: int = 20000,
    ) -> list[dict]:
        kosullar, parametreler = self._zaman_kutu_kosullari(baslangic, bitis, kutu)
        nerede = f"WHERE {' AND '.join(kosullar)}" if kosullar else ""
        return self._oku(
            f"SELECT * FROM yol_kapanmalari {nerede} ORDER BY zaman DESC LIMIT ?",
            (*parametreler, sinir),
        )

    # ---- acil durum bildirimleri (J-45) ------------------------------------

    def bildirim_ekle(
        self,
        baslik: str,
        metin: str,
        onem: str,
        kaynak: str,
        konum: str | None = None,
        buyukluk: float | None = None,
        gonderen_id: str | None = None,
        gonderen_ad: str | None = None,
    ) -> dict:
        """`kaynak`: 'konsol' (yeni kimlik) ya da 'eski' (eski web ucu)."""
        kayit = {
            "id": f"bil-{uuid.uuid4().hex[:8]}",
            "baslik": baslik,
            "metin": metin,
            "onem": onem,
            "konum": konum,
            "buyukluk": buyukluk,
            "zaman": time.time(),
            "kaynak": kaynak,
            "gonderen_id": gonderen_id,
            "gonderen_ad": gonderen_ad,
            "kaldirildi": None,
            "kaldiran_id": None,
            "kaldiran_ad": None,
        }
        self._yaz(
            """INSERT INTO bildirimler
               (id, baslik, metin, onem, konum, buyukluk, zaman, kaynak,
                gonderen_id, gonderen_ad, kaldirildi, kaldiran_id, kaldiran_ad)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            tuple(kayit.values()),
        )
        return kayit

    def bildirim_listele(self, yalniz_yayinda: bool = True, sinir: int = 20) -> list[dict]:
        """En yeni once. `yalniz_yayinda`: geri cekilenler haric."""
        nerede = "WHERE kaldirildi IS NULL" if yalniz_yayinda else ""
        return self._oku(
            f"SELECT * FROM bildirimler {nerede} ORDER BY zaman DESC LIMIT ?", (sinir,)
        )

    def bildirim_bul(self, bildirim_id: str) -> Optional[dict]:
        return self._tek("SELECT * FROM bildirimler WHERE id = ?", (bildirim_id,))

    def bildirim_kaldir(self, bildirim_id: str, kaldiran_id: str, kaldiran_ad: str) -> bool:
        """Yayindaki bildirimi geri ceker; zaten cekilmisse False."""
        with self._kilit:
            imlec = self._baglanti.execute(
                """UPDATE bildirimler
                   SET kaldirildi = ?, kaldiran_id = ?, kaldiran_ad = ?
                   WHERE id = ? AND kaldirildi IS NULL""",
                (time.time(), kaldiran_id, kaldiran_ad, bildirim_id),
            )
            self._baglanti.commit()
            return imlec.rowcount > 0

    # ---- afetzede ihbarlari (J-51) ------------------------------------------

    _IHBAR_SUTUNLARI = (
        "i.id, i.tur, i.lon, i.lat, i.zaman, i.durum, i.kullanici_id, i.metin, i.mahalle, "
        "i.etiket, i.skor, i.guven, i.hasar_id, i.ek, i.isleyen_id, i.isleyen_ad, "
        "i.guncellendi, i.istemci_anahtari, i.istek_ozeti, "
        "(f.ihbar_id IS NOT NULL) AS fotograf_var"
    )

    def ihbar_ekle(
        self,
        tur: str,
        lon: float,
        lat: float,
        kullanici_id: str | None = None,
        metin: str | None = None,
        mahalle: str | None = None,
        etiket: str | None = None,
        skor: float | None = None,
        guven: float | None = None,
        hasar_id: str | None = None,
        ek: dict | None = None,
        fotograf: tuple[bytes, int, int] | None = None,
        zaman: float | None = None,
        ihbar_id: str | None = None,
        istemci_anahtari: str | None = None,
        istek_ozeti: str | None = None,
        hasar_noktasi: dict | None = None,
    ) -> dict:
        """`fotograf`: (JPEG baytlari, en, boy). Ihbar ve fotografi tek
        islemde yazilir: fotografsiz yarim kayit kalmaz. Varsa hasar noktasi
        da ayni transaction'a dahil edilir (idempotency yarismasinda artik
        bir hasar kaydi kalmasin)."""
        if istemci_anahtari and (not kullanici_id or not istek_ozeti):
            raise ValueError("Idempotent ihbar icin kullanici ve istek ozeti gerekli.")
        nokta_id = f"hsr-{uuid.uuid4().hex[:10]}" if hasar_noktasi else hasar_id
        kayit = {
            "id": ihbar_id or yeni_ihbar_kimligi(),
            "tur": tur,
            "lon": float(lon),
            "lat": float(lat),
            "zaman": float(zaman if zaman is not None else time.time()),
            "durum": "yeni",
            "kullanici_id": kullanici_id,
            "metin": metin,
            "mahalle": mahalle,
            "etiket": etiket,
            "skor": skor,
            "guven": guven,
            "hasar_id": nokta_id,
            "ek": json.dumps(ek, ensure_ascii=False) if ek else None,
            "isleyen_id": None,
            "isleyen_ad": None,
            "guncellendi": None,
            "istemci_anahtari": istemci_anahtari,
            "istek_ozeti": istek_ozeti,
        }
        with self._kilit:
            try:
                self._baglanti.execute(
                    """INSERT INTO ihbarlar
                       (id, tur, lon, lat, zaman, durum, kullanici_id, metin, mahalle,
                        etiket, skor, guven, hasar_id, ek, isleyen_id, isleyen_ad, guncellendi,
                        istemci_anahtari, istek_ozeti)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    tuple(kayit.values()),
                )
                if hasar_noktasi:
                    self._baglanti.execute(
                        """INSERT INTO hasar_noktalari
                           (id, lon, lat, skor, guven, zaman, kaynak, etiket, bolge, ek)
                           VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        (nokta_id, kayit["lon"], kayit["lat"], hasar_noktasi["skor"],
                         hasar_noktasi["guven"], kayit["zaman"], hasar_noktasi["kaynak"],
                         hasar_noktasi.get("etiket"), None,
                         json.dumps({"ihbarId": kayit["id"]}, ensure_ascii=False)),
                    )
                if fotograf is not None:
                    veri, en, boy = fotograf
                    self._baglanti.execute(
                        "INSERT INTO ihbar_fotograflari (ihbar_id, veri, en, boy) VALUES (?,?,?,?)",
                        (kayit["id"], sqlite3.Binary(veri), int(en), int(boy)),
                    )
                self._baglanti.commit()
            except Exception:
                self._baglanti.rollback()
                raise
        kayit["fotograf_var"] = fotograf is not None
        return kayit

    def ihbar_istemci_anahtari(self, kullanici_id: str, anahtar: str) -> Optional[dict]:
        """Ayni kullanicinin tamamlanmis istegini, tam kayitla birlikte bulur."""
        return self._tek(
            f"""SELECT {self._IHBAR_SUTUNLARI} FROM ihbarlar i
                LEFT JOIN ihbar_fotograflari f ON f.ihbar_id = i.id
                WHERE i.kullanici_id = ? AND i.istemci_anahtari = ?""",
            (kullanici_id, anahtar),
        )

    def ihbar_listele(
        self,
        baslangic: float | None = None,
        bitis: float | None = None,
        tur: str | None = None,
        durum: str | None = None,
        kullanici_id: str | None = None,
        sinir: int = 2000,
    ) -> list[dict]:
        kosullar, parametreler = self._zaman_kutu_kosullari(baslangic, bitis, None)
        if tur:
            kosullar.append("i.tur = ?")
            parametreler.append(tur)
        if durum:
            kosullar.append("i.durum = ?")
            parametreler.append(durum)
        if kullanici_id:
            # Afetzede yalniz kendi ihbarini gorur (MIMARI 9).
            kosullar.append("i.kullanici_id = ?")
            parametreler.append(kullanici_id)
        nerede = f"WHERE {' AND '.join(kosullar)}" if kosullar else ""
        return self._oku(
            f"""SELECT {self._IHBAR_SUTUNLARI} FROM ihbarlar i
                LEFT JOIN ihbar_fotograflari f ON f.ihbar_id = i.id
                {nerede} ORDER BY i.zaman DESC LIMIT ?""",
            (*parametreler, sinir),
        )

    def ihbar_bul(self, ihbar_id: str) -> Optional[dict]:
        return self._tek(
            f"""SELECT {self._IHBAR_SUTUNLARI} FROM ihbarlar i
                LEFT JOIN ihbar_fotograflari f ON f.ihbar_id = i.id
                WHERE i.id = ?""",
            (ihbar_id,),
        )

    def ihbar_fotografi(self, ihbar_id: str) -> Optional[dict]:
        return self._tek(
            "SELECT veri, en, boy FROM ihbar_fotograflari WHERE ihbar_id = ?", (ihbar_id,)
        )

    def ihbar_durum(
        self, ihbar_id: str, durum: str, isleyen_id: str, isleyen_ad: str | None
    ) -> tuple[bool, list[str]]:
        """Yalniz ileri gider: yeni -> goruldu -> kapandi (yeni -> kapandi da
        olur). Kapanmis ihbar yeniden acilmaz; geri gidis False doner.
        Kapaninca acik gorevler de biter (J-54). Doner: (degisti mi, biten gorevler)."""
        if durum not in ("goruldu", "kapandi"):
            raise ValueError(f"Gecersiz ihbar durumu: {durum}")
        simdi = time.time()
        with self._kilit:
            imlec = self._baglanti.execute(
                """UPDATE ihbarlar
                   SET durum = ?, isleyen_id = ?, isleyen_ad = ?, guncellendi = ?
                   WHERE id = ? AND durum != 'kapandi' AND (? = 'kapandi' OR durum = 'yeni')""",
                (durum, isleyen_id, isleyen_ad, simdi, ihbar_id, durum),
            )
            if imlec.rowcount == 0:
                self._baglanti.rollback()
                return False, []
            biten = (
                self._acik_gorevleri_bitir("ihbar", ihbar_id, isleyen_id, isleyen_ad, simdi)
                if durum == "kapandi"
                else []
            )
            self._baglanti.commit()
            return True, biten

    # ---- ortak suzme ------------------------------------------------------

    @staticmethod
    def _zaman_kutu_kosullari(
        baslangic: float | None,
        bitis: float | None,
        kutu: tuple[float, float, float, float] | None,
    ) -> tuple[list[str], list[Any]]:
        kosullar: list[str] = []
        parametreler: list[Any] = []
        if baslangic is not None:
            kosullar.append("zaman >= ?")
            parametreler.append(float(baslangic))
        if bitis is not None:
            kosullar.append("zaman <= ?")
            parametreler.append(float(bitis))
        if kutu is not None:
            bati, guney, dogu, kuzey = kutu
            kosullar.append("lon BETWEEN ? AND ? AND lat BETWEEN ? AND ?")
            parametreler.extend([bati, dogu, guney, kuzey])
        return kosullar, parametreler


def mesafe_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Iki nokta arasi haversine mesafesi (metre)."""
    r = 6371000.0
    f1, f2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lat2 - lat1)
    dg = math.radians(lon2 - lon1)
    a = math.sin(dl / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dg / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))
