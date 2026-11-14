import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Amac, Bolum, HazirSecenekler, InceAyar, SuAn, Teknik, VeriYok } from '@/kabuk/Panel'
import { Anahtar, Chip, Kaydirici, Micro, Rozet } from '@/kabuk/parcalar'
import { sonIsSec, useIsler, type IsKunyesi } from '@/durum/islerDurumu'
import { useCanliAkisDurumu } from '@/canli/canliAkis'
import { useHarita } from '@/harita/HaritaKabugu'
import { karoAdresi } from '@/harita/goruntuKatmani'
import { useKonsol } from '@/durum/konsolDurumu'
import {
  BOLGELER,
  EN_AZ_KAPSAMA,
  KAYNAKLAR,
  analizBaslat,
  goruntuyeTasinmisAlan,
  ilkOlaySonrasi,
  kapsamaOrani,
  merkezKutusu,
  oamOnerisi,
  olaydanGun,
  sonOlayOncesi,
  surumunGoruntusu,
  useAnalizSegmentleri,
  useAnalizModelleri,
  useOamArama,
  useUyduModeli,
  useWaybackGoruntuGecmisi,
  useWaybackSurumleri,
  type AnalizSonucu,
  type BolgeId,
  type KaynakId,
  type OamGoruntu,
  type WaybackGoruntu,
  type WaybackGoruntuGecmisi,
} from '@/veri/analiz'
import { kutuCevresi, useSecim, type Kutu } from '@/durum/secimDurumu'
import { gunMetni, sayi, saat } from '@/lib/bicim'
import { sn } from '@/lib/sinif'

/* Hasar analizi modu: uydu görüntüsünden yol kapanmalarını çıkaran modelin
   koşturulduğu ekran. Model istek yolunda koşmaz; iş kuyruğa girer (kural 3). */

/* ---------------------------------------------------------------------------
   Hasar analizi — sol panel (13 Kasım 2026 yeniden düzen, J-161).

   Akış üç adım: 1 görüntü → 2 alan → 3 özet ve başlat. Görüntü önce gelir,
   çünkü model yalnız görüntünün olduğu yerde hasar arayabilir (J-160).

   Tek koşunun sınırı dürüstçe yazılır: analiz her zaman modelin eğitim
   ölçeğinde (z18 ≈ 0,48 m/piksel) koşar ve sunucu en çok 8×8 karo indirir,
   yani tek koşuda ~1 × 1 km incelenir. Eski hazır ayarlar "2,5 km",
   "4 km" diyordu ama ortadaki ~1 km² dışında hiçbir yer incelenmiyordu.
--------------------------------------------------------------------------- */

/** Sunucunun tek koşuda indirdiği en çok karo (fetcher.py, 8×8). */
const KARO_KENARI = 8
/** Varsayılan yarıçap: tek koşuya sığan alan (~1 km kenar). */
const VARSAYILAN_YARICAP_KM = 0.5
/** Görüntü araması şehrin bu yarıçapındaki bütün sahneleri listeler. */
const ARAMA_YARICAPI_KM = 8

/** Modelin eğitim ölçeğine en yakın yakınlaştırma (sunucudaki zoom_for_gsd ile aynı). */
function egitimZoomu(hedefGsdM: number, enlem: number) {
  const tam = Math.log2((156543.03392 * Math.cos((enlem * Math.PI) / 180)) / hedefGsdM)
  return Math.max(13, Math.min(20, Math.round(tam)))
}

/** Drone sahneleri birkaç yüz metredir, uydu sahneleri kilometrelerce. */
function goruntuTuru(g: OamGoruntu) {
  const enKm = (g.bbox[2] - g.bbox[0]) * 111.32 * Math.cos(((g.bbox[1] + g.bbox[3]) / 2) * (Math.PI / 180))
  return enKm < 3 ? 'Drone / hava çekimi' : 'Uydu'
}

const km = (x: number) => x.toFixed(x < 10 ? 2 : 1).replace('.', ',')

type AlanSecenegi = 'goruntu' | 'alan' | 'cokgen' | 'nokta' | 'sehir'

/** Karar ayarlarında null = modelin künyesindeki değer. */
type Ayar = {
  radiusKm: number
  esikCarpani: number
  threshold: number | null
  postProcessLevel: number | null
}

function Adim({ no, baslik, ek, children }: { no: number; baslik: string; ek?: ReactNode; children: ReactNode }) {
  return (
    <section className="mt-4 border-t border-line pt-3" aria-label={baslik}>
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-2">
          <span className="grid h-5 w-5 place-items-center rounded-full border border-accent text-micro text-accent">
            {no}
          </span>
          <span className="text-body font-semibold text-ink">{baslik}</span>
        </span>
        {ek}
      </div>
      <div className="mt-2">{children}</div>
    </section>
  )
}

function KapsamaCubugu({ oran }: { oran: number }) {
  return (
    <span className="mt-1 flex items-center gap-2">
      <span className="h-1 flex-1 overflow-hidden rounded-badge bg-sunken" aria-hidden>
        <span
          className={sn('block h-full rounded-badge', oran >= EN_AZ_KAPSAMA ? 'bg-accent' : 'bg-line-2')}
          style={{ width: `${Math.round(Math.min(1, oran) * 100)}%` }}
        />
      </span>
      <span className="w-24 shrink-0 text-right text-small text-ink-3">kapsama %{Math.round(100 * oran)}</span>
    </span>
  )
}

export function HasarSol() {
  const [bolge, setBolge] = useState<BolgeId>('antakya')
  // Varsayılan kaynak OpenAerialMap (J-35): Wayback'in 2023 sürümleri deprem
  // bölgesinde deprem ÖNCESİ görüntüyü gösteriyor (Antakya'da 2021 çekimi);
  // OAM'daki Maxar Open Data ve drone sahneleri depremden günler sonra çekildi.
  const [kaynak, setKaynak] = useState<KaynakId>('oam')
  const [waybackId, setWaybackId] = useState<string | null>(null)
  const [waybackElle, setWaybackElle] = useState(false)
  const [ayar, setAyar] = useState<Ayar>({
    radiusKm: VARSAYILAN_YARICAP_KM,
    esikCarpani: 1,
    threshold: null,
    postProcessLevel: null,
  })
  const [gonderiliyor, setGonderiliyor] = useState(false)
  const [hata, setHata] = useState<string | null>(null)

  const [oamBaslangic, setOamBaslangic] = useState('2023-02-06')
  const [oamBitis, setOamBitis] = useState('2023-02-28')
  const [oamArandi, setOamArandi] = useState(true)
  const [tarihAcik, setTarihAcik] = useState(false)
  const [oamSecili, setOamSecili] = useState<OamGoruntu | null>(null)
  const [oamElle, setOamElle] = useState(false)
  /* Model seçimi (J-76): bütün künyeler listelenir, seçilen model koşar. */
  const modeller = useAnalizModelleri()
  const [seciliModel, setSeciliModel] = useState<string | null>(null)
  /** Alan görüntüye taşındıysa o kutu; "Görüntünün tamamı" seçeneğini işaretler. */
  const [goruntuAlani, setGoruntuAlani] = useState<Kutu | null>(null)
  /** J-161: eğitim ölçeğinden bir kademe yakın (deneysel). Varsayılan kapalı. */
  const [yakinCekim, setYakinCekim] = useState(false)

  const secimModu = useSecim((d) => d.modu)
  const moduSec = useSecim((d) => d.moduSec)
  const kutu = useSecim((d) => d.kutu)
  const cokgen = useSecim((d) => d.cokgen)
  const merkez = useSecim((d) => d.merkez)
  const secimTemizle = useSecim((d) => d.temizle)
  const kutuSec = useSecim((d) => d.kutuSec)
  const ciziyor = useSecim((d) => d.ciziyor)
  const taslakKose = useSecim((d) => d.taslak?.nokta?.length ?? 0)
  const cizimiBitir = useSecim((d) => d.cizimiBitir)
  const sonKoseyiSil = useSecim((d) => d.sonKoseyiSil)
  const cizimiIptal = useSecim((d) => d.cizimiIptal)

  const surumler = useWaybackSurumleri()
  const isBasladi = useIsler((d) => d.isBasladi)
  const akis = useCanliAkisDurumu((d) => d.durum)
  const { kutuyaUc } = useHarita()

  const bolgeBilgi = BOLGELER.find((b) => b.id === bolge)!
  const liste = useMemo(() => surumler.data ?? [], [surumler.data])
  const tarihliKaynak = kaynak === 'esri'
  const oamKaynak = kaynak === 'oam'

  // Analiz merkezi: seçilen kutunun ortası ya da nokta, yoksa şehir merkezi.
  const [merkezLon, merkezLat] = kutu
    ? [(kutu[0] + kutu[2]) / 2, (kutu[1] + kutu[3]) / 2]
    : (merkez ?? [bolgeBilgi.lon, bolgeBilgi.lat])
  const analizKutusu = useMemo<Kutu>(
    () => kutu ?? merkezKutusu(merkezLon, merkezLat, ayar.radiusKm),
    [kutu, merkezLon, merkezLat, ayar.radiusKm],
  )
  /* Sunucuya giden yarıçap ANALİZ KUTUSUNDAN hesaplanır (J-76). */
  const { etkinYaricapKm, enKm, boyKm } = useMemo(() => {
    const [b, g, d, k] = analizKutusu
    const en = (d - b) * 111.32 * Math.cos(((g + k) / 2) * (Math.PI / 180))
    const boy = (k - g) * 111.32
    return { etkinYaricapKm: Math.max(0.05, Math.max(en, boy) / 2), enKm: en, boyKm: boy }
  }, [analizKutusu])

  // Wayback: bu konumda hangi sürüm hangi tarihte çekilmiş görüntüyü gösteriyor.
  const gecmis = useWaybackGoruntuGecmisi({
    lat: merkezLat,
    lon: merkezLon,
    radiusKm: etkinYaricapKm,
    aktif: tarihliKaynak,
  })
  const ilkSonrasi = ilkOlaySonrasi(gecmis.data)
  const sonOncesi = sonOlayOncesi(gecmis.data)
  useEffect(() => {
    if (waybackElle || !gecmis.data) return
    const hedef = ilkSonrasi?.surumId ?? liste[0]?.id ?? null
    if (hedef !== null && hedef !== waybackId) setWaybackId(hedef)
  }, [waybackElle, gecmis.data, ilkSonrasi, liste, waybackId])
  const seciliSurum = liste.find((v) => v.id === waybackId)
  const seciliGoruntu = seciliSurum ? surumunGoruntusu(seciliSurum.date, gecmis.data) : undefined

  /* Seçilen görüntü haritada görünür (J-75): modelin NE GÖRDÜĞÜ ekranda olsun. */
  const karo = karoAdresi({
    kaynak,
    waybackId,
    waybackTarihi: seciliSurum?.date ?? null,
    oamTmsUrl: oamSecili?.tms_url ?? null,
    oamBasligi: oamSecili?.title ?? null,
    oamTarihi: oamSecili?.date ?? null,
  })
  const analizKarosuYaz = useKonsol((d) => d.analizKarosuYaz)
  useEffect(() => {
    analizKarosuYaz(karo)
    return () => analizKarosuYaz(null)
  }, [karo?.url, karo?.kunye, analizKarosuYaz])

  /* Görüntü araması ŞEHİR çevresinde yapılır, analiz alanında değil (13 Kasım).
     Alan görüntüye taşınınca (J-160) arama da o 0,5 km'lik kutuya daralıyor ve
     öbür mahalle sahneleri listeden kayboluyordu. Çizilen alan şehir kutusunun
     dışına taşarsa ikisinin birleşimi aranır. */
  const aramaKutusu = useMemo<Kutu>(() => {
    const s = merkezKutusu(bolgeBilgi.lon, bolgeBilgi.lat, ARAMA_YARICAPI_KM)
    return kutu
      ? [Math.min(s[0], kutu[0]), Math.min(s[1], kutu[1]), Math.max(s[2], kutu[2]), Math.max(s[3], kutu[3])]
      : s
  }, [bolgeBilgi.lon, bolgeBilgi.lat, kutu])
  const oam = useOamArama({
    lat: bolgeBilgi.lat,
    lon: bolgeBilgi.lon,
    baslangic: oamBaslangic,
    bitis: oamBitis,
    kutu: aramaKutusu,
    aktif: oamKaynak && oamArandi,
  })
  const oneri = useMemo(
    () => (oam.data ? oamOnerisi(oam.data, analizKutusu) : undefined),
    [oam.data, analizKutusu],
  )
  useEffect(() => {
    if (!oamElle) setOamSecili(oneri?.goruntu ?? null)
  }, [oamElle, oneri])
  const oamOrani = oamSecili ? kapsamaOrani(oamSecili.bbox, analizKutusu) : null
  /* J-160: görüntü alanın yarısından azını kapsıyorsa analiz başlamaz. */
  const kapsamaYetersiz = oamKaynak && !!oamSecili && (oamOrani ?? 0) < EN_AZ_KAPSAMA

  function alaniGoruntuyeTasi(g: OamGoruntu) {
    const yeni = goruntuyeTasinmisAlan(g.bbox, analizKutusu)
    moduSec('alan')
    kutuSec(yeni)
    setGoruntuAlani(yeni)
    kutuyaUc(yeni)
  }

  function goruntuSec(g: OamGoruntu) {
    setOamSecili(g)
    setOamElle(true)
    // Görüntü seçmek alanı da görüntüye taşır (J-160); tamamen kapsıyorsa dokunulmaz.
    if (kapsamaOrani(g.bbox, analizKutusu) < 0.95) alaniGoruntuyeTasi(g)
  }

  // Etkin modelin künyesi: karar ayarlarının ve çözünürlüğün kaynağı (J-36).
  const model = useUyduModeli()
  const m = model.data
  const etkinEsik =
    ayar.threshold ?? (m ? Math.round(m.esik * ayar.esikCarpani * 100) / 100 : null)
  const etkinSonIsleme = ayar.postProcessLevel ?? m?.sonIsleme ?? null
  const esikNeden =
    ayar.threshold !== null ? 'elle' : ayar.esikCarpani !== 1 ? 'hassas' : 'modelin'

  // Tek koşunun sınırı: eğitim ölçeğindeki 8×8 karo.
  const hedefGsd = m ? (m.egitimGsdM[0] + m.egitimGsdM[1]) / 2 : 0.4
  const egitimZ = egitimZoomu(hedefGsd, merkezLat)
  const zoom = yakinCekim ? Math.min(20, egitimZ + 1) : egitimZ
  const mPiksel = (156543.03392 * Math.cos((merkezLat * Math.PI) / 180)) / 2 ** zoom
  const tekKosuKenarKm = (KARO_KENARI * 256 * mPiksel) / 1000
  const sigmiyor = enKm > tekKosuKenarKm * 1.05 || boyKm > tekKosuKenarKm * 1.05

  const alanSecimi: AlanSecenegi = cokgen
    ? 'cokgen'
    : kutu && goruntuAlani && kutu === goruntuAlani
      ? 'goruntu'
      : kutu || secimModu === 'alan'
        ? 'alan'
        : secimModu === 'cokgen'
          ? 'cokgen'
          : secimModu === 'nokta'
            ? 'nokta'
            : 'sehir'

  function alanSec(id: AlanSecenegi) {
    setHata(null)
    if (id === 'goruntu') {
      if (oamSecili) alaniGoruntuyeTasi(oamSecili)
      else setHata('Önce yukarıdan bir görüntü seç.')
      return
    }
    setGoruntuAlani(null)
    if (id === 'sehir') {
      secimTemizle()
      moduSec('sehir')
      kutuyaUc(merkezKutusu(bolgeBilgi.lon, bolgeBilgi.lat, ayar.radiusKm))
      return
    }
    secimTemizle()
    moduSec(id === 'alan' ? 'alan' : id === 'cokgen' ? 'cokgen' : 'nokta')
  }

  function ayarDegistir(yama: Partial<Ayar>) {
    setAyar((a) => ({ ...a, ...yama }))
  }

  const olcu = kutu ? kutuCevresi(kutu) : null
  const baslatilamaz = gonderiliyor || (oamKaynak && !oamSecili) || !m || kapsamaYetersiz
  const baslatNedeni = !m
    ? model.isError
      ? 'Model künyesi okunamadı; analiz başlatılamaz.'
      : 'Model bilgisi alınıyor…'
    : oamKaynak && !oamSecili
      ? oam.isFetching
        ? 'Görüntüler aranıyor…'
        : 'Başlamak için yukarıdan bir görüntü seç.'
      : kapsamaYetersiz
        ? 'Görüntü alanın yarısından azını kapsıyor; alanı görüntüye taşı.'
        : null

  async function baslat() {
    if (!m || etkinEsik === null || etkinSonIsleme === null) return
    setHata(null)
    setGonderiliyor(true)
    try {
      const { analysisId } = await analizBaslat({
        city: bolgeBilgi.ad,
        latitude: merkezLat,
        longitude: merkezLon,
        source: kaynak,
        threshold: esikNeden === 'modelin' ? undefined : etkinEsik,
        postProcessLevel: ayar.postProcessLevel ?? undefined,
        radiusKm: etkinYaricapKm,
        modelAdi: seciliModel ?? undefined,
        waybackId: tarihliKaynak ? (waybackId ?? undefined) : undefined,
        oamTileUrl: oamKaynak ? (oamSecili?.tms_url ?? undefined) : undefined,
        yakinCekim: yakinCekim || undefined,
        bboxWest: kutu?.[0],
        bboxSouth: kutu?.[1],
        bboxEast: kutu?.[2],
        bboxNorth: kutu?.[3],
      })
      isBasladi(analysisId, 'hasar-analizi', 'Sıraya alındı.', {
        bolge: bolgeBilgi.ad,
        kaynak:
          oamKaynak && oamSecili
            ? `OpenAerialMap · ${oamSecili.provider}`
            : (KAYNAKLAR.find((k) => k.id === kaynak)?.ad ?? kaynak),
        goruntuTarihi: tarihliKaynak
          ? (seciliGoruntu?.cekimTarihi ?? undefined)
          : oamKaynak && oamSecili
            ? oamSecili.date.slice(0, 10)
            : undefined,
        surumTarihi: tarihliKaynak ? seciliSurum?.date : undefined,
        esik: etkinEsik,
        sonIsleme: etkinSonIsleme,
        // Künye gerçekte incelenen alanı yazar, hazır ayarın yarıçapını değil.
        yaricapKm: etkinYaricapKm,
      })
      kutuyaUc(analizKutusu)
    } catch (e) {
      setHata(e instanceof Error ? e.message : 'Analiz başlatılamadı.')
    } finally {
      setGonderiliyor(false)
    }
  }

  const alanSecenekleri = [
    ...(oamKaynak ? [{ id: 'goruntu' as const, etiket: 'Görüntünün tamamı' }] : []),
    { id: 'alan' as const, etiket: 'Alan çiz' },
    { id: 'cokgen' as const, etiket: 'Çokgen çiz' },
    { id: 'nokta' as const, etiket: 'Nokta çevresi' },
    { id: 'sehir' as const, etiket: 'Şehir merkezi' },
  ]
  const chipSinifi = (secili: boolean) =>
    sn(
      'rounded-full border px-2.5 py-1.5 text-small transition-colors duration-150 ease-out-qm',
      secili ? 'border-accent bg-accent-soft text-ink' : 'border-line-2 text-ink-2 hover:bg-hover hover:text-ink',
    )

  return (
    <Bolum baslik="Uydudan hasar analizi" ek={<Micro>{bolgeBilgi.ad}</Micro>}>
      <Amac>
        Bu bölgede hangi yollar kapandı? Seçtiğin görüntü modelden geçer; hasar yolun üstüne
        düşüyorsa yol kapalı sayılır ve rota bundan sonra o ağda hesaplanır.
      </Amac>

      {/* ---------------------------------------------------- 1 GÖRÜNTÜ */}
      <Adim
        no={1}
        baslik="Görüntü"
        ek={<Micro>{oamKaynak ? 'drone ve uydu' : tarihliKaynak ? 'tarihli arşiv' : 'güncel'}</Micro>}
      >
        <div role="group" aria-label="Görüntü kaynağı" className="flex flex-wrap gap-1.5">
          {(
            [
              ['oam', 'Deprem sonrası (OpenAerialMap)'],
              ['esri', 'Tarihli arşiv (Wayback)'],
              ['google', 'Güncel uydu'],
            ] as Array<[KaynakId, string]>
          ).map(([id, etiket]) => (
            <button
              key={id}
              type="button"
              aria-pressed={kaynak === id}
              onClick={() => setKaynak(id)}
              className={chipSinifi(kaynak === id)}
            >
              {etiket}
            </button>
          ))}
        </div>

        <label className="mt-2.5 block" htmlFor="sehir">
          <Micro>Şehir</Micro>
        </label>
        <select
          id="sehir"
          value={bolge}
          onChange={(e) => {
            const yeni = e.target.value as BolgeId
            const b = BOLGELER.find((x) => x.id === yeni)!
            setBolge(yeni)
            // Şehir değişince eski alan ve seçili görüntü o şehre ait değildir.
            secimTemizle()
            moduSec('sehir')
            setGoruntuAlani(null)
            setOamElle(false)
            kutuyaUc(merkezKutusu(b.lon, b.lat, ARAMA_YARICAPI_KM / 2))
          }}
          className="mt-1.5 w-full rounded-control border border-line-2 bg-sunken px-2.5 py-2 text-body text-ink"
        >
          {BOLGELER.map((b) => (
            <option key={b.id} value={b.id}>
              {b.ad}
            </option>
          ))}
        </select>

        {kaynak === 'google' && (
          <p className="mt-2 text-small text-ink-2">
            Güncel uydu görüntüsü bugünün hâlidir; depremden sonraki hasarı göstermeyebilir ve çekim
            tarihi bilinmez. Hasar için deprem sonrası görüntüyü kullan.
          </p>
        )}

        {oamKaynak && (
          <>
            <div className="mt-2 flex items-center justify-between gap-2 text-small text-ink-3">
              <span>
                Çekim aralığı: {gunMetni(oamBaslangic)} – {gunMetni(oamBitis)}
              </span>
              <button type="button" onClick={() => setTarihAcik((a) => !a)} className="text-accent">
                {tarihAcik ? 'Kapat' : 'Değiştir'}
              </button>
            </div>
            {tarihAcik && (
              <div className="mt-1.5">
                <div className="grid grid-cols-2 gap-1.5">
                  <input
                    type="date"
                    aria-label="Başlangıç tarihi"
                    value={oamBaslangic}
                    onChange={(e) => {
                      setOamBaslangic(e.target.value)
                      setOamArandi(false)
                    }}
                    className="rounded-control border border-line-2 bg-sunken px-2.5 py-2 text-body text-ink"
                  />
                  <input
                    type="date"
                    aria-label="Bitiş tarihi"
                    value={oamBitis}
                    onChange={(e) => {
                      setOamBitis(e.target.value)
                      setOamArandi(false)
                    }}
                    className="rounded-control border border-line-2 bg-sunken px-2.5 py-2 text-body text-ink"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setOamArandi(true)
                    void oam.refetch()
                  }}
                  className="mt-1.5 w-full rounded-control border border-line-2 px-3 py-1.5 text-small text-ink-2 hover:bg-hover hover:text-ink"
                >
                  Bu aralıkta ara
                </button>
              </div>
            )}

            {oamArandi && oam.isFetching && !oam.data && (
              <p className="mt-2 text-small text-ink-3">Görüntüler aranıyor…</p>
            )}
            {oamArandi && oam.isError && (
              <p className="mt-2 text-small text-ink-3">Arama yapılamadı — OpenAerialMap ucu yanıt vermedi.</p>
            )}
            {oamArandi && oam.data?.length === 0 && (
              <p className="mt-2 text-small text-ink-3">
                Bu aralıkta ve bu çevrede görüntü yok. Aralığı genişlet ya da alanı taşı.
              </p>
            )}

            {!!oam.data?.length && (
              <ul className="mt-2 max-h-72 overflow-auto rounded-control border border-line-2">
                {oam.data.map((g) => {
                  const secili = oamSecili?.id === g.id
                  const oran = kapsamaOrani(g.bbox, analizKutusu)
                  const gun = olaydanGun(g.date.slice(0, 10))
                  return (
                    <li key={g.id} className="border-b border-line last:border-b-0">
                      <button
                        type="button"
                        aria-pressed={secili}
                        onClick={() => goruntuSec(g)}
                        className={sn(
                          'block w-full px-2.5 py-2 text-left',
                          secili ? 'bg-accent-soft' : 'hover:bg-hover',
                        )}
                      >
                        <span className="flex items-baseline justify-between gap-2">
                          <span className="min-w-0 truncate text-small text-ink">{g.title}</span>
                          {secili && <Rozet ton="accent">Seçili</Rozet>}
                        </span>
                        <span className="mt-0.5 block text-small text-ink-3">
                          {goruntuTuru(g)} · {g.provider} · {gunMetni(g.date.slice(0, 10))}
                          {gun >= 0 ? ` · depremden ${gun} gün sonra` : ' · deprem ÖNCESİ'}
                        </span>
                        <KapsamaCubugu oran={oran} />
                      </button>
                    </li>
                  )
                })}
              </ul>
            )}
            {oamSecili && !oamElle && (
              <p className="mt-1.5 text-small text-ink-3">
                Önerilen: alanı en çok kapsayan en erken uydu çekimi. Başka birini seçmek için listeye
                tıkla; seçince alan görüntünün üstüne taşınır.
              </p>
            )}
          </>
        )}

        {tarihliKaynak && (
          <div className="mt-2">
            {surumler.isLoading && <p className="text-small text-ink-3">Arşiv sürümleri alınıyor…</p>}
            {surumler.isError && (
              <p className="text-small text-ink-3">Arşiv sürümleri alınamadı — tarih seçilemiyor.</p>
            )}
            {liste.length > 0 && (
              <>
                <div className="flex flex-wrap gap-1.5">
                  {[
                    { id: ilkSonrasi?.surumId, etiket: 'Deprem sonrası ilk çekim' },
                    { id: sonOncesi?.surumId, etiket: 'Deprem öncesi' },
                    { id: liste[0]?.id, etiket: 'En güncel' },
                  ].map(
                    ({ id, etiket }) =>
                      id && (
                        <Chip
                          key={etiket}
                          secili={waybackId === id}
                          onClick={() => {
                            setWaybackId(id)
                            setWaybackElle(true)
                          }}
                        >
                          {etiket}
                        </Chip>
                      ),
                  )}
                </div>
                <select
                  aria-label="Arşiv sürümü"
                  value={waybackId ?? ''}
                  onChange={(e) => {
                    setWaybackId(e.target.value)
                    setWaybackElle(true)
                  }}
                  className="mt-1.5 w-full rounded-control border border-line-2 bg-sunken px-2.5 py-2 text-body text-ink"
                >
                  {liste.map((v) => {
                    const g = surumunGoruntusu(v.date, gecmis.data)
                    return (
                      <option key={v.id} value={v.id}>
                        {gunMetni(v.date)} sürümü
                        {g?.cekimTarihi ? ` · çekim ${gunMetni(g.cekimTarihi)}` : ''}
                      </option>
                    )
                  })}
                </select>
                <WaybackBilgisi
                  yukleniyor={gecmis.isLoading}
                  hataVar={gecmis.isError}
                  gecmis={gecmis.data}
                  surumTarihi={seciliSurum?.date}
                  goruntu={seciliGoruntu}
                  ilkSonrasi={ilkSonrasi}
                />
              </>
            )}
          </div>
        )}
      </Adim>

      {/* ------------------------------------------------------- 2 ALAN */}
      <Adim
        no={2}
        baslik="Alan"
        ek={<Micro>{`${km(enKm)} × ${km(boyKm)} km`}</Micro>}
      >
        <HazirSecenekler
          etiket="Analiz alanı"
          secenekler={alanSecenekleri}
          secili={alanSecimi}
          onSec={alanSec}
        />

        <p className="mt-1.5 text-small text-ink-3">
          {alanSecimi === 'goruntu' && 'Seçili görüntünün kapladığı alan analiz edilir.'}
          {alanSecimi === 'alan' && !kutu && 'Haritada basılı tutup sürükle: dikdörtgen alan çizilir.'}
          {alanSecimi === 'alan' && kutu && 'Haritada çizdiğin alan analiz edilir.'}
          {alanSecimi === 'cokgen' &&
            (cokgen
              ? 'Çokgenin sınır kutusu analiz edilir; köşelerdeki fazlalık da hesaba girer.'
              : 'Her tıklama bir köşe. Bitir, çift tıklama ya da Enter kapatır; Esc vazgeçer.')}
          {alanSecimi === 'nokta' && 'Haritaya tıkla: analiz o noktanın çevresinde yapılır.'}
          {alanSecimi === 'sehir' && `${bolgeBilgi.ad} merkezinin çevresi analiz edilir.`}
        </p>


        {secimModu === 'cokgen' && ciziyor && (
          <div className="mt-2 rounded-control border border-accent bg-accent-soft px-2.5 py-2">
            <p className="text-small text-ink">
              Çizim sürüyor · {taslakKose} köşe{taslakKose < 3 ? ' (en az 3 köşe gerekir)' : ''}
            </p>
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={cizimiBitir}
                disabled={taslakKose < 3}
                className="rounded-control bg-accent px-2.5 py-1.5 text-small font-semibold text-accent-ink disabled:opacity-40"
              >
                Bitir
              </button>
              <button
                type="button"
                onClick={sonKoseyiSil}
                className="rounded-control border border-line-2 px-2.5 py-1.5 text-small text-ink-2 hover:bg-hover hover:text-ink"
              >
                Son noktayı sil
              </button>
              <button
                type="button"
                onClick={cizimiIptal}
                className="rounded-control border border-line-2 px-2.5 py-1.5 text-small text-ink-2 hover:bg-hover hover:text-ink"
              >
                Vazgeç
              </button>
            </div>
          </div>
        )}

        {olcu && alanSecimi !== 'goruntu' && (
          <div className="mt-2 flex items-center justify-between gap-2 text-small text-ink-2">
            <span>
              {cokgen ? 'Çokgen' : 'Dikdörtgen'} · {km(olcu.genislikKm)} × {km(olcu.yukseklikKm)} km
            </span>
            <button
              type="button"
              onClick={() => {
                secimTemizle()
                setGoruntuAlani(null)
              }}
              className="text-accent"
            >
              Temizle
            </button>
          </div>
        )}

        {oamSecili && (oamOrani ?? 0) < 0.95 && alanSecimi !== 'goruntu' && (
          <div className="mt-2 rounded-control border border-accent bg-accent-soft px-2.5 py-2">
            <p className="text-small text-ink">
              {kapsamaYetersiz
                ? `Seçili görüntü bu alanın yalnız ~%${Math.round(100 * (oamOrani ?? 0))} kadarını kapsıyor. Böyle başlatılırsa model çoğunlukla boşluk tarar ve sonuç "hasar yok" gibi görünür.`
                : `Seçili görüntü bu alanın ~%${Math.round(100 * (oamOrani ?? 0))} kadarını kapsıyor; kalan kısımda görüntü yok.`}
            </p>
            <button
              type="button"
              onClick={() => alaniGoruntuyeTasi(oamSecili)}
              className="mt-1.5 rounded-control border border-line-2 bg-panel px-2.5 py-1.5 text-small text-ink hover:bg-hover"
            >
              Alanı görüntüye taşı
            </button>
          </div>
        )}
      </Adim>

      {/* -------------------------------------------- 3 ÖZET VE BAŞLAT */}
      <Adim no={3} baslik="Başlat">
        <dl className="kilav-kv gap-x-2.5 gap-y-1 text-small">
          <dt className="text-ink-3">Alan</dt>
          <dd className="text-ink">
            {km(enKm)} × {km(boyKm)} km
          </dd>
          <dt className="text-ink-3">Görüntü</dt>
          <dd className="text-ink">
            {oamKaynak
              ? oamSecili
                ? `${goruntuTuru(oamSecili)} · ${gunMetni(oamSecili.date.slice(0, 10))} · kapsama %${Math.round(100 * (oamOrani ?? 0))}`
                : 'seçilmedi'
              : tarihliKaynak
                ? seciliSurum
                  ? `Wayback ${gunMetni(seciliSurum.date)}${seciliGoruntu?.cekimTarihi ? ` · çekim ${gunMetni(seciliGoruntu.cekimTarihi)}` : ''}`
                  : 'sürüm seçilmedi'
                : 'güncel uydu (tarih bilinmiyor)'}
          </dd>
          <dt className="text-ink-3">Çözünürlük</dt>
          <dd className="text-ink">
            z{zoom} · ~{mPiksel.toFixed(2).replace('.', ',')} m/piksel
            {yakinCekim ? ' (yakın çekim, deneysel)' : ' (modelin eğitim ölçeği)'}
          </dd>
        </dl>

        {sigmiyor && (
          <p className="mt-2 rounded-control border border-line-2 px-2.5 py-2 text-small text-ink">
            Alan tek koşuya sığmıyor: bu çözünürlükte bir koşu en çok ~{km(tekKosuKenarKm)} ×{' '}
            {km(tekKosuKenarKm)} km inceler. Ortadaki o kısım analiz edilir; geri kalanı için alanı
            kaydırıp yeniden başlat.
          </p>
        )}

        <button
          type="button"
          onClick={baslat}
          disabled={baslatilamaz}
          className="mt-3 w-full rounded-control bg-accent px-3 py-2.5 text-body font-semibold text-accent-ink disabled:opacity-50"
        >
          {gonderiliyor ? 'İş kuyruğa veriliyor…' : 'Analizi başlat'}
        </button>
        {baslatNedeni && <p className="mt-1.5 text-small text-ink-3">{baslatNedeni}</p>}
        {hata && (
          <p role="alert" className="mt-1.5 text-small text-crit">
            {hata}
          </p>
        )}
        {akis !== 'bagli' && (
          <p className="mt-1.5 text-small text-ink-3">
            Canlı akış bağlı değil: analiz başlasa bile ilerleme buraya düşmez.
          </p>
        )}
      </Adim>

      {/* --------------------------------------------------- ince ayar */}
      <InceAyar baslik="İnce ayar">
        <Anahtar
          acik={ayar.esikCarpani !== 1}
          etiket="Hassas tarama"
          onDegis={() => ayarDegistir({ esikCarpani: ayar.esikCarpani !== 1 ? 1 : 0.7, threshold: null })}
          ek={<span className="text-small text-ink-3">eşik %70</span>}
        />
        <p className="text-small text-ink-3">
          Daha çok yeri hasarlı işaretler: gözden kaçan azalır, yanlış alarm artar.
        </p>
        <Anahtar
          acik={yakinCekim}
          etiket="Yakın çekim (deneysel)"
          onDegis={() => setYakinCekim((y) => !y)}
          ek={<span className="text-small text-ink-3">z{egitimZ + 1}</span>}
        />
        <p className="text-small text-ink-3">
          Görüntüye bir kademe yakından bakar (~{(mPiksel * (yakinCekim ? 1 : 0.5)).toFixed(2).replace('.', ',')}{' '}
          m/piksel). Defne/Elektrik'te 8 yerine 19 kapalı yol buldu, ama model bu ölçekte
          eğitilmedi ve doğruluğu yer gerçeğiyle ölçülmedi; yanlış alarm da artabilir. Tek koşunun
          alanı dörtte bire iner.
        </p>
        {!kutu && (
          <Satir
            etiket="Yarıçap"
            deger={`${ayar.radiusKm.toFixed(1).replace('.', ',')} km`}
            kaydirici={
              <Kaydirici
                etiket="Yarıçap (km)"
                deger={ayar.radiusKm * 10}
                enAz={1}
                enCok={20}
                adim={1}
                degerEtiketi={ayar.radiusKm.toFixed(1).replace('.', ',')}
                onDegis={(v) => ayarDegistir({ radiusKm: v / 10 })}
              />
            }
            not={`Nokta ya da şehir merkezi çevresi. ~${km(tekKosuKenarKm / 2)} km'den büyüğü tek koşuya sığmaz.`}
          />
        )}
        <Satir
          etiket="Hasar eşiği"
          deger={etkinEsik === null ? '—' : etkinEsik.toFixed(2).replace('.', ',')}
          kaydirici={
            <Kaydirici
              etiket="Hasar eşiği"
              deger={(etkinEsik ?? 0.5) * 100}
              enAz={5}
              enCok={90}
              adim={1}
              degerEtiketi={etkinEsik === null ? '—' : etkinEsik.toFixed(2).replace('.', ',')}
              onDegis={(v) => ayarDegistir({ threshold: v / 100 })}
            />
          }
          not={`${m ? `Modelin ölçüldüğü eşik ${m.esik.toFixed(2).replace('.', ',')}. ` : ''}Düşük eşik daha çok yeri hasarlı işaretler.`}
        />
        <Satir
          etiket="Son işleme"
          deger={etkinSonIsleme === null ? '—' : etkinSonIsleme === 0 ? 'kapalı' : `seviye ${etkinSonIsleme}`}
          kaydirici={
            <Kaydirici
              etiket="Son işleme seviyesi"
              deger={etkinSonIsleme ?? 0}
              enAz={0}
              enCok={2}
              adim={1}
              degerEtiketi={String(etkinSonIsleme ?? '—')}
              onDegis={(v) => ayarDegistir({ postProcessLevel: v })}
            />
          }
          not="Maskedeki küçük lekeleri temizler; yükseldikçe ufak hasar kaybolabilir."
        />
        <label className="mt-2 block text-micro ls-micro text-ink-3 uppercase" htmlFor="model">
          Model
        </label>
        {modeller.isError && <VeriYok ne="Model listesi" neden="uç yanıt vermedi" />}
        <select
          id="model"
          value={seciliModel ?? ''}
          onChange={(e) => setSeciliModel(e.target.value || null)}
          className="mt-1.5 w-full rounded-control border border-line-2 bg-sunken px-2.5 py-2 text-body text-ink"
        >
          <option value="">Sunucunun etkin modeli{m ? ` (${m.etiket})` : ''}</option>
          {(modeller.data ?? [])
            .filter((x) => x.hazir)
            .map((x) => (
              <option key={x.ad} value={x.ad}>
                {x.mimari}
                {x.sinamaIoU != null ? ` · IoU ${x.sinamaIoU.toFixed(3).replace('.', ',')}` : ''}
              </option>
            ))}
        </select>
      </InceAyar>

      <SuAn>
        {`${km(enKm)} × ${km(boyKm)} km alan, `}
        {oamKaynak && oamSecili
          ? `${gunMetni(oamSecili.date.slice(0, 10))} tarihli ${oamSecili.provider} görüntüsü`
          : tarihliKaynak && seciliSurum
            ? `Wayback'in ${gunMetni(seciliSurum.date)} sürümü`
            : KAYNAKLAR.find((k) => k.id === kaynak)?.ad.toLocaleLowerCase('tr')}
        {m
          ? ` ile, eşik ${etkinEsik?.toFixed(2).replace('.', ',')} (${
              esikNeden === 'modelin' ? 'modelin kendi eşiği' : esikNeden === 'hassas' ? 'hassas tarama' : 'elle'
            }) ve son işleme ${etkinSonIsleme === 0 ? 'kapalı' : `seviye ${etkinSonIsleme}`} ile analiz edilecek.`
          : '.'}
      </SuAn>

      <Teknik>
        Model bu istekte koşmaz: iş kuyruğa girer (HTTP 202), ayrı işçi süreçte işlenir; ilerleme
        canlı akıştan gelir, ekran hiçbir ucu yoklamaz. Çözünürlük alan büyüklüğünden değil modelin
        eğitim ölçeğinden seçilir (J-76); bir koşu en çok {KARO_KENARI}×{KARO_KENARI} karo indirir.
      </Teknik>
    </Bolum>
  )
}

function Satir({
  etiket,
  deger,
  kaydirici,
  not,
}: {
  etiket: string
  deger: string
  kaydirici: React.ReactNode
  not: string
}) {
  return (
    <div className="border-t border-line py-2 first:border-t-0">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-small text-ink">{etiket}</span>
        <span className="font-mono text-small text-ink-2">{deger}</span>
      </div>
      {kaydirici}
      <p className="mt-1 text-small text-ink-3">{not}</p>
    </div>
  )
}

/** Seçili Wayback sürümünün bu konumda GERÇEKTE gösterdiği görüntü (J-35).
    Sürüm tarihi çekim tarihi değildir; bu blok aradaki farkı açıkça yazar. */
function WaybackBilgisi({
  yukleniyor,
  hataVar,
  gecmis,
  surumTarihi,
  goruntu,
  ilkSonrasi,
}: {
  yukleniyor: boolean
  hataVar: boolean
  gecmis: WaybackGoruntuGecmisi | undefined
  surumTarihi: string | undefined
  goruntu: WaybackGoruntu | undefined
  ilkSonrasi: WaybackGoruntu | undefined
}) {
  let durum: React.ReactNode
  if (yukleniyor) {
    durum = 'Bu konumun arşiv geçmişi çıkarılıyor (ilk seferde birkaç saniye)…'
  } else if (hataVar || !gecmis) {
    durum = 'Çekim tarihi okunamadı; bu görüntünün depremden sonra çekildiği doğrulanamıyor.'
  } else if (goruntu?.cekimTarihi) {
    const gun = olaydanGun(goruntu.cekimTarihi)
    durum = (
      <>
        Seçili sürüm bu konumda{' '}
        <span className="text-ink">{gunMetni(goruntu.cekimTarihi)}</span> tarihinde çekilmiş{' '}
        {goruntu.kaynak ?? 'kaynağı bilinmeyen'} görüntüsünü gösteriyor
        {goruntu.cozunurlukM ? ` (${String(goruntu.cozunurlukM).replace('.', ',')} m)` : ''}.{' '}
        {gun < 0 ? (
          <span className="text-ink">
            Deprem öncesi: görüntüde depremin hasarı yok, bulunan her hasar yanlış alarmdır.
          </span>
        ) : (
          `Depremden ${gun} gün sonra${gun > 60 ? '; enkazın bir kısmı kaldırılmış olabilir' : ''}.`
        )}
      </>
    )
  } else if (surumTarihi && surumTarihi < gecmis.olayTarihi) {
    durum = 'Bu sürüm depremden önce yayımlandı; gösterdiği görüntü de deprem öncesine ait.'
  } else if (gecmis.bitis === 'karo-yok') {
    durum = `Bu sürümde z${gecmis.zoom} yakınlaştırmasında karo yok; analiz daha kaba bir yakınlaştırmaya iner.`
  } else {
    durum = 'Bu sürümün gösterdiği görüntünün çekim tarihi bilinmiyor.'
  }

  return (
    <div className="mt-1.5 text-small text-ink-3">
      <p>{durum}</p>
      {!yukleniyor && gecmis && !ilkSonrasi && (
        <p className="mt-1.5 rounded-control border border-line-2 px-2.5 py-2 text-ink">
          Wayback bu konumda depremden sonra çekilmiş görüntü göstermiyor. Hasar aramak için
          OpenAerialMap'i kullan.
        </p>
      )}
      <p className="mt-1.5">
        Wayback'te sürüm tarihi görüntünün çekim tarihi değildir: güncellenmeyen karo eski
        sürümden gelir. Çekim tarihi Esri'nin metadata katmanından, analizin kullanacağı
        yakınlaştırmada (z{gecmis?.zoom ?? '—'}) okunur.
      </p>
    </div>
  )
}

/** Sonucun görüntü künyesi: koşumun GERÇEKTE kullandığı kaynak sonuçtan okunur. */
function goruntuKunyesi(sonuc: AnalizSonucu, kunye: IsKunyesi | undefined, surumTarihi?: string) {
  const cekimler = (sonuc.imageryCaptures ?? []).filter((c) => c.cekimTarihi)
  if (sonuc.imagerySource === 'esri') {
    const surum = surumTarihi ?? kunye?.surumTarihi
    const cekim = cekimler.length
      ? `çekim ${cekimler
          .map((c) => `${gunMetni(c.cekimTarihi!)}${c.kaynak ? ` (${c.kaynak})` : ''}`)
          .join(', ')}`
      : 'çekim tarihi okunamadı'
    return `Esri Wayback${surum ? ` · ${gunMetni(surum)} sürümü` : ''} · ${cekim}`
  }
  if (sonuc.imagerySource === 'custom') {
    return `${kunye?.kaynak ?? sonuc.imageryLabel ?? 'OpenAerialMap'}${
      kunye?.goruntuTarihi ? ` · çekim ${gunMetni(kunye.goruntuTarihi)}` : ''
    }`
  }
  return `${sonuc.imageryLabel ?? 'Güncel uydu görüntüsü'} · çekim tarihi bilinmiyor`
}

/** Web Mercator'da bir yakınlaştırmanın bu enlemdeki piksel boyu (m). */
function metrePiksel(z: number, enlem: number) {
  return (156543.03 * Math.cos((enlem * Math.PI) / 180)) / 2 ** z
}

/* Sağ panel (J-161): ilerleme aşama aşama, sonuç büyük sayılarla; künye katlanır.
   Aşamalar işçinin bildirdiği yüzdelerden okunur (worker.py `_report`). */
const ASAMALAR = [
  { ad: 'Görüntü indiriliyor', bas: 0 },
  { ad: 'Yol ağı çıkarılıyor', bas: 20 },
  { ad: 'Model hasar arıyor', bas: 25 },
  { ad: 'Kapanan yollar ve rota', bas: 90 },
  { ad: 'Sonuç hazırlanıyor', bas: 97 },
] as const

function Sayac({ etiket, deger, alt, vurgu }: { etiket: string; deger: string; alt?: string; vurgu?: boolean }) {
  return (
    <div className="rounded-control border border-line bg-sunken px-2.5 py-2">
      <Micro>{etiket}</Micro>
      <p className={sn('mt-0.5 text-title font-semibold', vurgu ? 'text-crit' : 'text-ink')}>{deger}</p>
      {alt && <p className="text-small text-ink-3">{alt}</p>}
    </div>
  )
}

export function HasarSag() {
  const is = useIsler(sonIsSec)
  const sonuc = is?.sonuc as AnalizSonucu | undefined
  const surumler = useWaybackSurumleri()
  const { kutuyaUc } = useHarita()
  const segmentler = useAnalizSegmentleri(
    is?.durum === 'bitti' && is.isTipi === 'hasar-analizi' ? is.id : null,
  )

  const surumTarihi =
    sonuc?.waybackId != null
      ? surumler.data?.find((v) => v.id === String(sonuc.waybackId))?.date
      : undefined
  const zamanlama = sonuc?.imageryEventTiming
  // J-160: görüntü kutunun yarısından azını dolduruyorsa sayılar yalnız o kısmı anlatır.
  const goruntuAz = sonuc?.validPixelRatio != null && sonuc.validPixelRatio < EN_AZ_KAPSAMA
  const cekimMetni = (sonuc?.imageryCaptures ?? [])
    .flatMap((c) => (c.cekimTarihi ? [gunMetni(c.cekimTarihi)] : []))
    .join(', ')
  const enlem = sonuc?.bounds ? (sonuc.bounds.south + sonuc.bounds.north) / 2 : 37

  if (!is) {
    return (
      <Bolum baslik="Analiz">
        <Amac>Başlattığın analizin ilerlemesi ve sonucu burada görünür.</Amac>
        <ol className="mt-2.5 space-y-1.5 text-small text-ink-2">
          <li>1 · Soldan deprem sonrası bir görüntü seç; alan görüntünün üstüne taşınır.</li>
          <li>2 · Gerekirse alanı daralt ya da haritada çiz.</li>
          <li>3 · Analizi başlat; ilerleme ve kapanan yollar burada çıkar.</li>
        </ol>
      </Bolum>
    )
  }

  const ton = is.durum === 'hata' ? 'crit' : is.durum === 'bitti' ? 'ok' : 'mid'
  const etiket =
    is.durum === 'kuyrukta' ? 'Sırada' : is.durum === 'calisiyor' ? 'Çalışıyor' : is.durum === 'bitti' ? 'Bitti' : 'Hata'
  const parca = is.mesaj?.match(/\((\d+)\/(\d+) parca\)/)
  const etkinAsama =
    is.durum === 'bitti' ? ASAMALAR.length : ASAMALAR.filter((a) => is.ilerleme >= a.bas).length - 1
  const sinir = sonuc?.bounds
  const kapali = sonuc?.blockedRoads ?? 0

  return (
    <>
      <Bolum baslik="Analiz" ek={<span className="font-mono text-small text-ink-3">{saat(is.baslangic)}</span>}>
        <div className="flex items-center justify-between gap-2">
          <Rozet ton={ton}>{etiket}</Rozet>
          <span className="font-mono text-small text-ink-2">{is.ilerleme}%</span>
        </div>
        <div className="mt-2 h-1.5 w-full overflow-hidden rounded-badge bg-sunken">
          <div
            className={sn(
              'h-full rounded-badge transition-all duration-200 ease-out-qm',
              is.durum === 'hata' ? 'bg-crit' : 'bg-accent',
            )}
            style={{ width: `${Math.max(2, Math.min(100, is.ilerleme))}%` }}
          />
        </div>

        {is.durum === 'hata' ? (
          <p role="alert" className="mt-2.5 rounded-control border border-line-2 px-2.5 py-2 text-small text-ink">
            {is.hata ?? 'Analiz tamamlanamadı.'}
          </p>
        ) : (
          <ol className="mt-2.5 space-y-1" aria-label="Aşamalar">
            {ASAMALAR.map((a, i) => {
              const bitti = i < etkinAsama
              const simdi = i === etkinAsama
              return (
                <li key={a.ad} className="flex items-center gap-2 text-small">
                  <span
                    aria-hidden
                    className={sn(
                      'grid h-4 w-4 shrink-0 place-items-center rounded-full border text-micro',
                      bitti
                        ? 'border-accent bg-accent text-accent-ink'
                        : simdi
                          ? 'border-accent text-accent'
                          : 'border-line-2 text-ink-3',
                    )}
                  >
                    {bitti ? '✓' : i + 1}
                  </span>
                  <span className={bitti ? 'text-ink-2' : simdi ? 'text-ink' : 'text-ink-3'}>
                    {a.ad}
                    {simdi && a.bas === 25 && parca ? ` · ${parca[1]}/${parca[2]} parça` : ''}
                  </span>
                </li>
              )
            })}
          </ol>
        )}
        <p className="mt-2 font-mono text-small text-ink-3">iş: {is.id.slice(0, 8)}</p>
      </Bolum>

      {sonuc && sonuc.status === 'done' && (
        <Bolum baslik="Sonuç">
          {(zamanlama === 'pre' || zamanlama === 'mixed') && (
            <p role="alert" className="mb-3 rounded-control border border-line-2 px-2.5 py-2 text-small text-ink">
              {zamanlama === 'pre'
                ? `Bu analiz deprem ÖNCESİ çekilmiş görüntüyle yapıldı (çekim ${cekimMetni}). Görüntüde depremin hasarı yok; aşağıdaki hasar ve kapanmalar yanlış alarmdır, karar için kullanılamaz.`
                : `Alandaki görüntüler karışık (çekim ${cekimMetni || 'bir kısmı bilinmiyor'}); bir kısmı deprem öncesine ait. O kısımlarda sonuç depremi göstermez.`}
            </p>
          )}

          <div className="grid grid-cols-3 gap-1.5">
            <Sayac
              etiket="Kapalı yol"
              deger={sayi(kapali)}
              alt={sonuc.blockedRoadPct != null ? `%${(sonuc.blockedRoadPct * 100).toFixed(1).replace('.', ',')}` : undefined}
              vurgu={kapali > 0}
            />
            <Sayac etiket="Açık yol" deger={sayi(sonuc.openRoads ?? 0)} alt="segment" />
            <Sayac
              etiket="Hasar"
              deger={sonuc.damageRate != null ? `%${(sonuc.damageRate * 100).toFixed(1).replace('.', ',')}` : '—'}
              alt="piksel oranı"
            />
          </div>

          {goruntuAz && (
            <p role="note" className="mt-2.5 text-small text-ink-2">
              Görüntü incelenen kutunun ~%{Math.round(100 * (sonuc.validPixelRatio ?? 0))} kadarını dolduruyor;
              kalan kısım boş (drone görüntülerinin kenarları düzensizdir). Sayılar yalnız görüntülü kısmı anlatır
              {kapali === 0 ? '; "0 kapalı yol" boş kısımda hasar olmadığı anlamına gelmez.' : '.'}
            </p>
          )}

          {sonuc.recommendedAction && zamanlama !== 'pre' && !(goruntuAz && kapali === 0) && (
            <p className="mt-2.5 text-body text-ink">{sonuc.recommendedAction}</p>
          )}

          <p className="mt-2.5 flex items-center gap-2 text-small text-ink-2">
            <span aria-hidden className="h-0.5 w-4 shrink-0 rounded-badge bg-crit" />
            {segmentler.isLoading
              ? 'Yol geometrisi indiriliyor…'
              : segmentler.data
                ? `Haritada ${sayi(segmentler.data.kapali.length)} kapalı segment kırmızı, ${sayi(segmentler.data.acik.length)} açık segment sönük.`
                : 'Yol geometrisi alınamadı; harita yalnız sayıları gösteriyor.'}
          </p>

          <div className="mt-2.5 flex flex-wrap gap-1.5">
            {sinir && (
              <button
                type="button"
                onClick={() => kutuyaUc([sinir.west, sinir.south, sinir.east, sinir.north])}
                className="rounded-control border border-line-2 px-2.5 py-1.5 text-small text-ink hover:bg-hover"
              >
                Sonuca yaklaş
              </button>
            )}
            {kapali > 0 && (
              <Link
                to="/konsol/yol"
                className="rounded-control border border-accent px-2.5 py-1.5 text-small text-ink hover:bg-hover"
              >
                Bu ağda rota planla
              </Link>
            )}
          </div>

          <details className="mt-3 border-t border-line pt-2">
            <summary className="cursor-pointer text-small text-ink-2">Görüntü ve model künyesi</summary>
            <p className="mt-2 text-small text-ink-2">
              <span className="text-ink">Görüntü:</span> {goruntuKunyesi(sonuc, is.kunye, surumTarihi)}
              {is.kunye
                ? ` · ${
                    is.kunye.yaricapKm < 1
                      ? `${sayi(Math.round(is.kunye.yaricapKm * 1000))} m`
                      : `${is.kunye.yaricapKm.toFixed(1).replace('.', ',')} km`
                  } yarıçap`
                : ''}
            </p>
            {sonuc.imageryZoom != null && (
              <p className="mt-1 text-small text-ink-2">
                <span className="text-ink">Çözünürlük:</span> z{sonuc.imageryZoom} · ~
                {metrePiksel(sonuc.imageryZoom, enlem).toFixed(2).replace('.', ',')} m/piksel
                {sonuc.yakinCekim ? ' · yakın çekim (deneysel, eğitim ölçeğinin dışında)' : ''}
                {sonuc.imageryRequestedZoom != null && sonuc.imageryRequestedZoom !== sonuc.imageryZoom
                  ? ` (istenen z${sonuc.imageryRequestedZoom}'de karo yoktu, bir alta inildi)`
                  : ''}
              </p>
            )}
            {sonuc.model?.gsdUyarisi && (
              <p className="mt-1.5 text-small text-ink">
                Model {sonuc.model.egitimGsdM.map((g) => String(g).replace('.', ',')).join('–')} m/piksel
                görüntüyle eğitildi; bu analiz ~{sonuc.model.kullanilanGsdM.toFixed(2).replace('.', ',')}{' '}
                m/pikselle yapıldı. Eğitim ölçeğinin dışında sonuç güvenilmez (J-20).
              </p>
            )}
            <Teknik>
              Model:{' '}
              {sonuc.model
                ? `${sonuc.model.etiket} (${sonuc.model.mimari} / ${sonuc.model.kodlayici}, ağırlık ${
                    sonuc.model.sha256Kisa
                  }) · sınama IoU ${
                    sonuc.model.olcum?.sinamaIoU != null
                      ? sonuc.model.olcum.sinamaIoU.toFixed(3).replace('.', ',')
                      : 'ölçülmedi'
                  }`
                : 'bilgi yok'}
              . Bölge: {sonuc.city ?? '—'} · eşik {sonuc.threshold?.toFixed(2).replace('.', ',') ?? '—'} · hasar
              çarpanı {sonuc.damageBooster?.toFixed(1).replace('.', ',') ?? '—'} · son işleme{' '}
              {sonuc.postProcessLevel == null ? '—' : sonuc.postProcessLevel === 0 ? 'kapalı' : `seviye ${sonuc.postProcessLevel}`}{' '}
              · kapanma kuralı{' '}
              {sonuc.closureRule === 'radius' ? `yarıçap ${sonuc.blockageRadiusM} m` : 'yol pikseli üzerinde hasar'}.
            </Teknik>
          </details>
        </Bolum>
      )}
    </>
  )
}
