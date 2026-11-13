import { useEffect, useMemo, useRef } from 'react'
import { Navigate, useParams } from 'react-router-dom'
import { HaritaKabugu, useHarita } from '@/harita/HaritaKabugu'
import { AlanSecici } from '@/harita/AlanSecici'
import { katmanlariKur } from '@/harita/katmanlar'
import { karoAdresi } from '@/harita/goruntuKatmani'
import { useKonsol } from '@/durum/konsolDurumu'
import { useSecim, type Kutu } from '@/durum/secimDurumu'
import { useSorguAraligi } from '@/durum/zamanDurumu'
import { useEkipler, useHasarNoktalari, useIsiIzgarasi, useSosCagrilari } from '@/veri/sorgular'
import { useIhbarlar, type IhbarTuru } from '@/veri/ihbar'
import { useDepremler, useFaylar, useKapanmalar, useToplanmaAlanlari } from '@/veri/katman'
import { useSimAlanlar, useSimMaske, useSimSonuc } from '@/veri/simulasyon'
import { useSimulasyon } from '@/durum/simulasyonDurumu'
import { isiDokusuKur } from '@/harita/isiDokusu'
import { KANALLAR } from '@/durum/konsolDurumu'
import { useAnalizSegmentleri } from '@/veri/analiz'
import { operasyonBolgeleri, useAltlikKatalogu } from '@/veri/altlik'
import { gunMetni } from '@/lib/bicim'
import { Chip } from './parcalar'
import {
  ALTLIK_EN_AZ_ZOOM,
  TOPLANMA_EN_AZ_ZOOM,
  kisaAd,
  kutuMerkezi,
  useAltlikGirdisi,
  useGorunenAltlik,
} from '@/harita/altlikGorunumu'
import { sonIsSec, useIsler } from '@/durum/islerDurumu'
import { MODLAR, VARSAYILAN_MOD, modBul, type ModId } from '@/modlar/modlar'
import { UstCubuk } from './UstCubuk'
import { SolPanel } from './SolPanel'
import { SagPanel } from './SagPanel'
import { ZamanSeridi } from './ZamanSeridi'
import { KomutPaleti } from './KomutPaleti'
import { YeniOlaylar } from './YeniOlaylar'
import { KatmanDugmesi } from './KatmanDugmesi'
import { HaritaGostergesi } from './HaritaGostergesi'
import { TatbikatSeridi } from './TatbikatSeridi'

/* ---------------------------------------------------------------------------
   Konsol kabuğu: üst çubuk · sol mod paneli · harita (köşesinde katmanlar
   düğmesi) · sağ durum paneli · alt zaman şeridi (ARAYUZ §8).

   Harita bu kabukta BİR kez kurulur. Mod değişince kabuk yeniden kurulmaz;
   yalnız panellerin içeriği ve açık katmanlar değişir.
--------------------------------------------------------------------------- */

export function KonsolKabugu() {
  const { mod } = useParams()
  const tanim = modBul(mod)

  if (!tanim) return <Navigate to={`/konsol/${VARSAYILAN_MOD}`} replace />

  return (
    <div className="flex h-full flex-col">
      <UstCubuk />

      {/* Tatbikat şeridi kabukta durur: mod değişse de görünür, kapatılamaz
          (SIMULASYON_SOZLESMESI.md §5 madde 1). Koşu yoksa hiç çizilmez. */}
      <div className="px-gutter pt-gutter empty:hidden">
        <TatbikatSeridi />
      </div>

      <div className="relative flex min-h-0 flex-1 flex-col overflow-auto genis:block genis:overflow-hidden">
        <HaritaKabugu>
          <KatmanKopru />
          <AlanSecici />

          {/* Dar ekranda (<= 980 px) harita üstte, paneller altında dikey sıralanır. */}
          <div className="relative z-10 flex flex-col gap-gutter p-gutter genis:pointer-events-none genis:absolute genis:inset-0 genis:h-full genis:overflow-hidden">
            <div className="flex min-h-0 flex-1 flex-col gap-gutter genis:flex-row genis:items-stretch">
              {/* Dar ekranda katmanlar düğmesi panellerin üstünde, aşağı açılır. */}
              <div className="genis:hidden">
                <KatmanDugmesi yukari={false} />
              </div>
              {/* Sol panel içeriği kadar uzar (en çok sütun boyu), altında harita görünür. */}
              <div className="genis:pointer-events-auto genis:w-panel-l genis:shrink-0 genis:self-start genis:max-h-full flex min-h-0">
                <SolPanel mod={tanim.id} />
              </div>
              <div className="hidden flex-1 genis:flex genis:flex-col genis:items-center genis:justify-between">
                <div className="genis:pointer-events-auto">
                  <SehirDugmeleri />
                </div>
                {/* Solda katmanlar (J-56) ve tatbikat göstergesi (J-95),
                    sağda yeni SOS ve ihbar kartı (ARAYUZ §10, J-51). */}
                <div className="flex w-full items-end justify-between gap-gutter">
                  <div className="genis:pointer-events-auto flex flex-col items-start gap-2">
                    <HaritaGostergesi />
                    <KatmanDugmesi />
                  </div>
                  <div className="genis:pointer-events-auto">
                    <YeniOlaylar />
                  </div>
                </div>
              </div>
              <div className="genis:pointer-events-auto genis:w-panel-r genis:shrink-0 flex min-h-0">
                <SagPanel mod={tanim.id} />
              </div>
            </div>

            <HaritaKunyesi />

            <div className="genis:pointer-events-auto shrink-0">
              <ZamanSeridi />
            </div>
          </div>
        </HaritaKabugu>
      </div>

      <KomutPaleti />
    </div>
  )
}

/** Modun gösterdiği ihbar türleri; listede olmayan mod hepsini gösterir. */
const MOD_IHBARLARI: Partial<Record<ModId, readonly IhbarTuru[]>> = {
  kamera: ['fotograf'],
  metin: ['metin'],
  ihtiyac: ['ihtiyac'],
}

// Isı ızgarası şimdilik sabit bir bölge için isteniyor; harita kaydırınca
// yeni istek atılmaz (kural 4). Bölge seçimi ilerleyen adımda panelden gelecek.
const ISI_MERKEZI = { lon: 36.161, lat: 36.202 }
const ISI_YARICAP_KM = 10

/** Şehre git (J-41): prototipteki görünüm düğmeleri gibi; tek tıkla şehir
    merkezine, "Tüm bölge" ile bütün şehirleri kapsayan görünüme uçar. Yalnız
    operasyon bölgeleri: 81 il altlığı risk ekranının il seçicisinden açılır. */
function SehirDugmeleri() {
  const { ucus, kutuyaUc, gorunum } = useHarita()
  const katalog = useAltlikKatalogu()
  const bolgeler = operasyonBolgeleri(katalog.data ?? [])
  if (bolgeler.length === 0) return null

  const merkez = gorunum ? kutuMerkezi(gorunum.kutu) : null
  const aktif =
    gorunum && merkez && gorunum.zoom >= 11
      ? bolgeler.find(
          (b) =>
            merkez[0] >= b.kutu[0] &&
            merkez[0] <= b.kutu[2] &&
            merkez[1] >= b.kutu[1] &&
            merkez[1] <= b.kutu[3],
        )?.id
      : undefined
  const tumu: Kutu = [
    Math.min(...bolgeler.map((b) => b.kutu[0])),
    Math.min(...bolgeler.map((b) => b.kutu[1])),
    Math.max(...bolgeler.map((b) => b.kutu[2])),
    Math.max(...bolgeler.map((b) => b.kutu[3])),
  ]

  return (
    <nav
      aria-label="Şehre git"
      className="flex flex-wrap justify-center gap-1.5 rounded-control border border-line bg-panel p-1.5"
    >
      {bolgeler.map((b) => (
        <Chip
          key={b.id}
          secili={aktif === b.id}
          onClick={() => ucus(...kutuMerkezi(b.kutu), 13)}
        >
          {kisaAd(b.ad)}
        </Chip>
      ))}
      <Chip secili={!!gorunum && gorunum.zoom < ALTLIK_EN_AZ_ZOOM} onClick={() => kutuyaUc(tumu)}>
        Tüm bölge
      </Chip>
    </nav>
  )
}

/** Kaynak künyesi her zaman ekranda durur (ARAYUZ §11): altlık nereden, hangi
    tarihli; görünen alanda altlık yoksa bu da yazar. */
function HaritaKunyesi() {
  const { katalog, gorunum, gorunen } = useGorunenAltlik()
  const tumu = katalog.data ?? []
  const operasyon = operasyonBolgeleri(tumu)
  const ilSayisi = tumu.length - operasyon.length
  const uretilen = `${operasyon.map((b) => b.ad).join(', ')}${
    ilSayisi ? ` ve ${ilSayisi} il merkezi` : ''
  }`
  let metin: string
  if (katalog.isLoading) {
    metin = 'altlık kataloğu alınıyor…'
  } else if (katalog.isError || tumu.length === 0) {
    metin = 'üretilmedi — sunucuda `python araclar_altlik_uret.py` çalıştırılmalı.'
  } else if (gorunum && gorunum.zoom < ALTLIK_EN_AZ_ZOOM) {
    metin = `bölge ölçeğinde çizilir; yakınlaş (üretilen bölgeler: ${uretilen}).`
  } else if (gorunen.length === 0) {
    metin = `bu alan için üretilmedi (üretilen bölgeler: ${uretilen}).`
  } else {
    const k = gorunen[0].kaynak
    metin = `${k.atif} (${k.lisans}) · yerel kopya ${gunMetni(k.dosyaTarihi)} · ${gorunen
      .map((b) => b.ad)
      .join(', ')}`
  }
  return (
    <div className="genis:pointer-events-auto flex shrink-0 justify-center">
      <p className="rounded-control border border-line bg-panel px-2.5 py-1.5 text-small text-ink-3">
        <span className="text-ink-2">Harita altlığı:</span> {metin}
      </p>
    </div>
  )
}

/** Mod → açık katmanlar; sorgu sonuçları → deck.gl katmanları. */
function KatmanKopru() {
  const { mod } = useParams()
  const tanim = modBul(mod) ?? MODLAR[0]
  const { hazir, katmanlariYaz, ucus, kutuyaUc, tiklamaYaz, haritaAl } = useHarita()
  const katmanlar = useKonsol((d) => d.katmanlar)
  const analizKarosu = useKonsol((d) => d.analizKarosu)
  const seciliKayit = useKonsol((d) => d.seciliKayit)
  const katmanlariAyarla = useKonsol((d) => d.katmanlariAyarla)
  const kayitSec = useKonsol((d) => d.kayitSec)
  const aralik = useSorguAraligi()
  const secimKutusu = useSecim((d) => d.kutu)
  const secimCokgeni = useSecim((d) => d.cokgen)
  const secimTaslagi = useSecim((d) => d.taslak)

  const hasar = useHasarNoktalari(aralik)
  const sos = useSosCagrilari(aralik)
  const ihbar = useIhbarlar(aralik)
  const ekipler = useEkipler()

  // Başvuru katmanları (J-56): yalnız katman açıkken istenir, sonra önbellekte
  // kalır. Zaman penceresine bağlı değiller; toplanma görünen bölgeye bağlı.
  const { gorunen: gorunenBolgeler } = useGorunenAltlik()
  const kapanmalar = useKapanmalar(katmanlar.hasarliYollar)
  const depremler = useDepremler(katmanlar.depremler)
  const faylar = useFaylar(katmanlar.faylar)
  const toplanma = useToplanmaAlanlari(katmanlar.toplanma, gorunenBolgeler)

  // Tatbikat koşusu (SIMULASYON_SOZLESMESI.md): sonuç canlı akış mesajıyla
  // tazelenir, maske jetonla indirilip ImageBitmap'e çevrilir.
  const simIsId = useSimulasyon((d) => d.isId)
  const simVaryantlar = useSimulasyon((d) => d.varyantlar)
  const simSonuc = useSimSonuc(simIsId)
  const simMaske = useSimMaske(katmanlar.simHasar ? simSonuc.data?.hasar?.maskeUrl : undefined)
  // Tatbikat zemini: MODELİN BAKTIĞI görüntü. Bu alanların çoğunda üretilmiş
  // altlık paketi yok (Nurdağı'nda zemin bomboş siyahtı) ve doğru zemin zaten
  // enkazın kendisidir. Yalnız koşu varken serilir.
  const simSecim = useSimulasyon((d) => d.secim)
  const simAlanlar = useSimAlanlar()
  const simGoruntu = useMemo(() => {
    if (!simIsId) return null
    // Alan KOŞUNUN kendisinden okunur, panel seçiminden değil: sayfa
    // yenilenince koşu kimliği sessionStorage'dan geri geliyor (J-74) ama
    // panel seçimi boş kalıyordu ve zemin görüntüsü kayboluyordu.
    const alanId = simSonuc.data?.alan?.id ?? simSecim.alanId
    const alan = simAlanlar.data?.find((a) => a.id === alanId)
    const kat = alan?.katmanlar.find((k) => k.id === simSecim.katmanId) ?? alan?.katmanlar[0]
    if (!kat) return null
    const kaynak = kat.kaynak === 'esri' || kat.kaynak === 'google' ? kat.kaynak : 'oam'
    const adres = karoAdresi({
      kaynak,
      oamTmsUrl: kat.oamTmsUrl ?? null,
      oamBasligi: kat.oamBasligi ?? null,
      oamTarihi: kat.cekimTarihi ?? null,
      waybackId: kat.waybackId ?? null,
      waybackTarihi: kat.cekimTarihi ?? null,
    })
    // Kapsam: alanın kendi kutusu. Dışında karo istenmez (bkz. goruntuKatmani).
    return adres ? { ...adres, kapsam: kat.bbox ?? null } : null
  }, [simIsId, simAlanlar.data, simSecim, simSonuc.data?.alan?.id])
  const simGirdi = useMemo(
    () => ({
      katmanlar,
      sonuc: simSonuc.data ?? null,
      maske: simMaske.data ?? null,
      varyantlar: simVaryantlar,
      goruntu: simGoruntu,
      izlenenYollar: simSonuc.data?.izlenenYollar ?? null,
    }),
    [katmanlar, simSonuc.data, simMaske.data, simVaryantlar, simGoruntu],
  )

  // TATBİKAT BAŞLAYINCA HARİTA ORAYA UÇAR. Önce uçmuyordu: koşu Nurdağı'nda
  // biterken harita Antakya'da kalıyor, kullanıcı hiçbir katmanı göremiyordu
  // (ölçüldü, 26 Eylül — şehir sekmesi de merkeze götürdüğü için yetmiyor,
  // tatbikat alanı merkeze 15 km uzakta). Koşu başına BİR KEZ uçulur; sonra
  // kullanıcının kendi kaydırması bozulmaz.
  const ucurulanKosu = useRef<string | null>(null)
  const oncekiGorunum = useRef<{ lon: number; lat: number; zoom: number } | null>(null)
  const simKutu = simSonuc.data?.alan?.bbox ?? simSonuc.data?.hasar?.bbox ?? null
  useEffect(() => {
    if (!hazir || !simIsId || !simKutu) return
    if (ucurulanKosu.current === simIsId) return
    const h = haritaAl()
    if (h) {
      const c = h.getCenter()
      oncekiGorunum.current = { lon: c.lng, lat: c.lat, zoom: h.getZoom() }
    }
    ucurulanKosu.current = simIsId
    kutuyaUc(simKutu)
  }, [hazir, simIsId, simKutu, kutuyaUc, haritaAl])
  // Tatbikat bitince görünüm geri alınır: tatbikat alanlarının çoğunda üretilmiş
  // altlık paketi yok, bitirince kullanıcı kapkara bir haritayla kalıyordu.
  useEffect(() => {
    if (simIsId) return
    ucurulanKosu.current = null
    const g = oncekiGorunum.current
    oncekiGorunum.current = null
    if (hazir && g) ucus(g.lon, g.lat, g.zoom)
  }, [simIsId, hazir, ucus])

  // Altlık: yalnız görünen bölgelerin paketleri iner (harita durunca), bir kez.
  const { altlik, altlikYapiGorunur, bolgeAdlari, adSeviyesi, gorunum } = useAltlikGirdisi()
  // Isı yakınlaştıkça saydamlaşır: sokak ölçeğinde zemini, yapıları ve adları
  // örtmesin (z13'e kadar 0,72, z16 ve üstü 0,30). 0,05 adımlı: her kaydırmada
  // katmanlar yeniden kurulmasın.
  const isiOrtuculugu = useMemo(() => {
    const z = gorunum?.zoom ?? 0
    const o = z <= 13 ? 0.72 : z >= 16 ? 0.3 : 0.72 - ((z - 13) / 3) * 0.42
    return Math.round(o * 20) / 20
  }, [gorunum?.zoom])
  // Haritada bir ihbara ya da ekibe tıklayınca oraya yakınlaşılır; SOS seçilir.
  useEffect(() => {
    if (!hazir) return
    tiklamaYaz((bilgi) => {
      const nesne = bilgi.object as { id?: string; lon?: number; lat?: number } | undefined
      const katman = bilgi.layer?.id
      if (!nesne || nesne.lon == null || nesne.lat == null) return
      if (katman === 'sos' && nesne.id) kayitSec({ tip: 'sos', id: nesne.id })
      if (katman === 'ihbarlar' && nesne.id) kayitSec({ tip: 'ihbar', id: nesne.id })
      if (katman === 'sos' || katman === 'ihbarlar' || katman === 'hasar-noktalari' || katman === 'ekipler') {
        ucus(nesne.lon, nesne.lat, Math.max(15.5, haritaAl()?.getZoom() ?? 0))
      }
    })
  }, [hazir, tiklamaYaz, kayitSec, ucus, haritaAl])

  // Isı: her kanalın ızgarası ayrı gelir, karışım istemcide (MIMARI §5).
  const agirliklar = useKonsol((d) => d.agirliklar)
  const isiAcik = katmanlar.isi
  const isiUydu = useIsiIzgarasi(ISI_MERKEZI, ISI_YARICAP_KM, aralik, 'uydu', isiAcik)
  const isiSos = useIsiIzgarasi(ISI_MERKEZI, ISI_YARICAP_KM, aralik, 'sos', isiAcik)
  const isiKamera = useIsiIzgarasi(ISI_MERKEZI, ISI_YARICAP_KM, aralik, 'kamera', isiAcik)
  const isiMetin = useIsiIzgarasi(ISI_MERKEZI, ISI_YARICAP_KM, aralik, 'metin', isiAcik)

  const isiDokusu = useMemo(() => {
    if (!isiAcik) return null
    const kanalVerisi = {
      sat: isiUydu.data,
      sos: isiSos.data,
      cam: isiKamera.data,
      nlp: isiMetin.data,
    }
    return isiDokusuKur(
      KANALLAR.map((k) => ({ kanal: k, veri: kanalVerisi[k], agirlik: agirliklar[k] })),
    )
  }, [isiAcik, isiUydu.data, isiSos.data, isiKamera.data, isiMetin.data, agirliklar])

  // Biten analizin geometrisi: ağır veri ayrı ve önbelleklenebilir uçtan gelir,
  // yalnız iş "bitti" durumuna geçince istenir.
  const is = useIsler(sonIsSec)
  const analizId = is?.durum === 'bitti' && is.isTipi === 'hasar-analizi' ? is.id : null
  const segmentler = useAnalizSegmentleri(analizId)

  // Mod değişince açık katmanlar değişir; harita yerinde kalır.
  useEffect(() => {
    katmanlariAyarla([...tanim.katmanlar])
  }, [tanim, katmanlariAyarla])

  const deckKatmanlari = useMemo(
    () =>
      katmanlariKur({
        katmanlar,
        altlik,
        altlikYapiGorunur,
        bolgeAdlari,
        etiketSeviyesi: adSeviyesi,
        isiOrtuculugu,
        hasar: hasar.data ?? [],
        sos: sos.data ?? [],
        ekipler: ekipler.data ?? [],
        seciliSos: seciliKayit?.tip === 'sos' ? seciliKayit.id : null,
        ihbarlar: ihbar.data ?? [],
        ihbarTurleri: MOD_IHBARLARI[tanim.id],
        seciliIhbar: seciliKayit?.tip === 'ihbar' ? seciliKayit.id : null,
        secim: { kutu: secimKutusu, cokgen: secimCokgeni, taslak: secimTaslagi },
        goruntu: analizKarosu,
        analiz: segmentler.data ?? null,
        isi: isiDokusu,
        toplanmaGorunur: (gorunum?.zoom ?? 0) >= TOPLANMA_EN_AZ_ZOOM,
        simulasyon: simGirdi,
        kapanmalar: kapanmalar.data?.kayitlar,
        depremler: depremler.data?.kayitlar,
        faylar: faylar.data?.kayitlar,
        toplanma: toplanma.data?.kayitlar,
      }),
    [
      katmanlar,
      altlik,
      altlikYapiGorunur,
      bolgeAdlari,
      adSeviyesi,
      isiOrtuculugu,
      hasar.data,
      sos.data,
      ihbar.data,
      tanim.id,
      ekipler.data,
      seciliKayit,
      secimKutusu,
      secimCokgeni,
      secimTaslagi,
      segmentler.data,
      analizKarosu,
      isiDokusu,
      gorunum?.zoom,
      kapanmalar.data,
      depremler.data,
      faylar.data,
      toplanma.data,
      simGirdi,
    ],
  )

  useEffect(() => {
    if (hazir) katmanlariYaz(deckKatmanlari)
  }, [hazir, deckKatmanlari, katmanlariYaz])

  // Analiz sonucu haritaya bindiğinde o alana bir kez git; sonra kullanıcının
  // yakınlaştırması ve kaydırması bozulmaz (veri yenilense de geri uçulmaz).
  const sinirlar = segmentler.data?.bounds
  const ucurulanAnaliz = useRef<string | null>(null)
  useEffect(() => {
    if (!hazir || !sinirlar) return
    const anahtar = `${sinirlar.west},${sinirlar.south},${sinirlar.east},${sinirlar.north}`
    if (ucurulanAnaliz.current === anahtar) return
    ucurulanAnaliz.current = anahtar
    ucus((sinirlar.west + sinirlar.east) / 2, (sinirlar.south + sinirlar.north) / 2, 14.5)
  }, [hazir, sinirlar, ucus])

  return null
}
