import { lazy, Suspense, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Megaphone, Phone } from '@phosphor-icons/react'
import { useOturum } from '@/kimlik/oturum'
import { ROL_ADI } from '@/kimlik/roller'
import { Marka } from '@/kabuk/Marka'
import { ProfilMenusu } from '@/kimlik/ProfilMenusu'
import { useCanliAkisDurumu } from '@/canli/canliAkis'
import { enOnemli, onemi, useAktifBildirimler, type Bildirim } from '@/veri/bildirim'
import type { IhbarTuru } from '@/veri/ihbar'
import { ApiHatasi } from '@/veri/istemci'
import { sn } from '@/lib/sinif'
import { BildirDugmeleri } from './BildirDugmeleri'
import { Bildirimlerim } from './Bildirimlerim'
import { Diyalog } from './Diyalog'
import { DuyuruKarti, DuyuruListesi, SonDuyuru, YeniDuyuruUyarisi } from './Duyurular'
import type { HaritaKonumu } from './haritaKatmanlari'
import { KonumDiyalogu } from './KonumDiyalogu'
import { useCevrimici, useGpsKonumu, type EtkinKonum } from './konum'
import { NereyeKarti } from './NereyeKarti'
import { SosKarti } from './SosKarti'
import {
  useCagrilarim,
  useIhbarlarim,
  useSokakRotasi,
  useYakinYerler,
  useYurumeRotasi,
  type SokakRotasi,
  type YakinYer,
  type Yer,
  type YerTuru,
} from './veri'

/* ---------------------------------------------------------------------------
   Afetzede portalı (J-43, yeniden tasarım J-50, üçüncü tur J-51).

   Deprem sonrası giren kişi için tek ekran, kaydırmasız (≥ 1280 × 640):
     · solda "Acil yardım": kırmızı SOS (sabit boy); çağrı gidince durum
       adımları. Altında "Bildirimlerim": gönderdiklerinin canlı durumu;
       boşken deprem sonrası ilk adımlar.
     · ≥ 1600 px'te sağda üçüncü sütun: duyuruların tam metni. Yeni duyuru
       gelince ekranın üstünde uyarı çıkar (J-51).
     · sağda "Nereye gidebilirim?": en yakın yerler listesi ve küçük harita;
       altında üç "Bildir" düğmesi (hasar fotoğrafı, yazarak, ihtiyaç), her
       biri kendi renginde; pencerede açılır.
   En yeni duyuru en üstte tek satır; bütün duyurular üst çubuktan açılır.
   Sayfa en çok 1920 px genişler; geniş ekranda iki yan boş kalmaz.
   Dar ekranda sıra: SOS, Bildir, Nereye, Bildirimlerim.

   Canlı veri tek akıştan gelir (kural 4): kendi çağrının ve ihbarının durumu
   ve duyurular. Sunucu afetzedeye başkasının kaydını ve ekip konumlarını
   göndermez (J-42).
--------------------------------------------------------------------------- */

type Pencere = IhbarTuru | 'duyurular' | null

// İhbar pencereleri yalnız açılınca iner: SOS ve liste ilk açılışta onları
// beklemez (afetzede ekranının ilk yükü).
const FotografIcerigi = lazy(() => import('./FotografIcerigi').then((m) => ({ default: m.FotografIcerigi })))
const MetinIhbari = lazy(() => import('./MetinIhbari').then((m) => ({ default: m.MetinIhbari })))
const IhtiyacIhbari = lazy(() => import('./IhtiyacIhbari').then((m) => ({ default: m.IhtiyacIhbari })))

const PENCERE_BASLIGI: Record<IhbarTuru, string> = {
  fotograf: 'Hasar fotoğrafı gönder',
  metin: 'Yazarak bildir',
  ihtiyac: 'İhtiyaç bildir',
}

export function AfetzedeEkrani() {
  const { oturum } = useOturum()
  const cevrimici = useCevrimici()
  const { gps, iste } = useGpsKonumu()
  const [mahalle, setMahalle] = useState<Yer | null>(null)
  const [pencere, setPencere] = useState<Pencere>(null)
  // Konum penceresi ayrı durur: ihbar penceresinin üstünde açılır, altındaki
  // fotoğraf ve yazılanlar kaybolmaz.
  const [konumAcik, setKonumAcik] = useState(false)
  const cagrilar = useCagrilarim()
  const ihbarlar = useIhbarlarim()
  const duyurular = useAktifBildirimler()

  // Koordinatör ve yönetici bu ekranı önizleyebilir; sunucu onlara bütün
  // kayıtları verdiği için açık çağrı izlenmez, haritada çağrı gösterilmez.
  const onizleme = oturum?.rol !== 'afetzede'

  const gpsKonumu = gps.durum === 'hata' ? null : gps.konum
  const konum: EtkinKonum | null = mahalle
    ? { kaynak: 'mahalle', lon: mahalle.lon, lat: mahalle.lat, yer: mahalle }
    : gpsKonumu
      ? { kaynak: 'gps', lon: gpsKonumu.lon, lat: gpsKonumu.lat, dogrulukM: gpsKonumu.dogrulukM }
      : null

  // Yakındaki yerler: liste ve harita aynı seçimi paylaşır.
  const yakin = useYakinYerler(konum)
  const [tur, setTur] = useState<YerTuru>('toplanma')
  const [secili, setSecili] = useState<YakinYer | null>(null)
  const [rota, setRota] = useState<{ yerId: string; sonuc: SokakRotasi } | null>(null)
  const sokakRotasi = useSokakRotasi()
  // Yürüme rotası kendi yol ağımızdan, yer seçilince kendiliğinden (J-44).
  // Bölgenin yol ağı yoksa (404) dış servis rotası istenebilir.
  const yurume = useYurumeRotasi(konum, secili)
  const agYok = yurume.error instanceof ApiHatasi && yurume.error.durum === 404
  const disRota = rota && secili && rota.yerId === secili.id ? rota.sonuc : null

  // Konum değişince (yeni liste) eski seçim ve rota geçersizleşir.
  useEffect(() => {
    setSecili(null)
    setRota(null)
  }, [yakin.data])

  function sec(y: YakinYer | null) {
    setSecili(y)
    sokakRotasi.reset()
    if (y) setTur(y.tur)
  }

  function rotaIste(y: YakinYer) {
    if (!konum) return
    sokakRotasi.mutate(
      { baslangicLat: konum.lat, baslangicLon: konum.lon, hedefLat: y.lat, hedefLon: y.lon },
      { onSuccess: (sonuc) => setRota({ yerId: y.id, sonuc }) },
    )
  }

  const haritaKonumu: HaritaKonumu | null = useMemo(
    () =>
      konum
        ? konum.kaynak === 'gps'
          ? { lon: konum.lon, lat: konum.lat, kaynak: 'gps', dogrulukM: konum.dogrulukM }
          : { lon: konum.lon, lat: konum.lat, kaynak: 'mahalle', ad: konum.yer.ad }
        : null,
    // Nesne her çizimde yeniden kurulur; yalnız değerler değişince yenilensin.
    [konum?.lon, konum?.lat, konum?.kaynak, konum?.kaynak === 'gps' ? konum.dogrulukM : null],
  )
  const haritaCagrilari = useMemo(
    () => (onizleme ? [] : (cagrilar.data ?? []).filter((c) => c.durum !== 'kapandi')),
    [onizleme, cagrilar.data],
  )

  const kapat = () => setPencere(null)
  const konumAc = () => setKonumAcik(true)
  const duyuruListesi = duyurular.data ?? []

  return (
    <div className="flex h-full flex-col bg-ground">
      <UstSerit
        onizleme={onizleme}
        rol={oturum ? ROL_ADI[oturum.rol] : null}
        duyurular={duyuruListesi}
        duyurulariAc={() => setPencere('duyurular')}
      />

      {!cevrimici && (
        <p role="alert" className="shrink-0 border-b border-crit bg-panel px-3.5 py-2 text-body text-ink">
          İnternet bağlantın yok. Çağrı şu an gönderilemez; şebeke varsa 112'yi ara.
        </p>
      )}
      <SonDuyuru duyurular={duyuruListesi} tumunuAc={() => setPencere('duyurular')} />

      <main className="flex min-h-0 flex-1 flex-col gap-gutter overflow-auto p-gutter genis:mx-auto genis:grid genis:w-full genis:max-w-afetzede genis:kilav-afetzede genis:overflow-hidden uclu:kilav-afetzede-uclu">
        {/* Geniş ekranda alan adlı ızgara (stil/token.css): iki sütunda solda SOS
            ve gönderilenler, sağda "nereye" ve bildir düğmeleri; ≥ 1600 px'te
            sağda duyurular sütunu. Dar ekranda ızgara yok, kartlar order ile
            dizilir: SOS, Bildir, Duyurular (varsa), Nereye, Gönderilenler.
            Kartlar yalnız geniş ekranda sıkışır (min-h-0); dar ekranda sayfa
            kayar, kartlar üst üste binmez. */}
        <div className="order-1 shrink-0 genis:order-none genis:alan-sos">
          <SosKarti
            konum={konum}
            gps={gps}
            konumAc={konumAc}
            cagrilar={cagrilar.data ?? []}
            onizleme={onizleme}
          />
        </div>
        <div className="order-2 shrink-0 genis:order-none genis:alan-bildir">
          <BildirDugmeleri ac={setPencere} />
        </div>
        <div
          className={sn(
            'order-3 shrink-0 flex-col genis:order-none genis:hidden genis:min-h-0 genis:shrink genis:alan-duyuru uclu:flex',
            duyuruListesi.length ? 'flex' : 'hidden',
          )}
        >
          <DuyuruKarti duyurular={duyuruListesi} tumunuAc={() => setPencere('duyurular')} />
        </div>
        <div className="order-4 flex shrink-0 flex-col genis:order-none genis:alan-nereye genis:min-h-0 genis:shrink">
          <NereyeKarti
            konum={konum}
            haritaKonumu={haritaKonumu}
            veri={yakin.data}
            yukleniyor={yakin.isPending && !!konum}
            hata={yakin.isError}
            tur={tur}
            turSec={setTur}
            secili={secili}
            sec={sec}
            cagrilar={haritaCagrilari}
            yurume={{
              veri: yurume.data ?? null,
              bekliyor: yurume.isFetching,
              hata: agYok ? null : yurume.error,
              agYok,
            }}
            rota={rota}
            rotaIste={rotaIste}
            rotaBekliyor={sokakRotasi.isPending}
            rotaHatasi={sokakRotasi.error}
            haritaRotasi={yurume.data?.koordinatlar ?? disRota?.koordinatlar ?? null}
            konumAc={konumAc}
          />
        </div>
        <div className="order-5 flex shrink-0 flex-col genis:order-none genis:alan-gonderilen genis:min-h-0 genis:shrink">
          <Bildirimlerim
            cagrilar={cagrilar.data ?? []}
            ihbarlar={ihbarlar.data ?? []}
            yukleniyor={cagrilar.isPending || ihbarlar.isPending}
            hata={cagrilar.isError || ihbarlar.isError}
            onizleme={onizleme}
          />
        </div>
      </main>
      <YeniDuyuruUyarisi oku={() => setPencere('duyurular')} />

      {(['fotograf', 'metin', 'ihtiyac'] as const).map((t) => (
        <Diyalog key={t} acik={pencere === t} kapat={kapat} baslik={PENCERE_BASLIGI[t]} genis={t !== 'ihtiyac'}>
          <Suspense fallback={<p className="text-small text-ink-3">Yükleniyor…</p>}>
            {t === 'fotograf' ? (
              <FotografIcerigi konum={konum} konumAc={konumAc} />
            ) : t === 'metin' ? (
              <MetinIhbari konum={konum} konumAc={konumAc} />
            ) : (
              <IhtiyacIhbari konum={konum} konumAc={konumAc} />
            )}
          </Suspense>
        </Diyalog>
      ))}
      <Diyalog acik={pencere === 'duyurular'} kapat={kapat} baslik="Duyurular">
        <DuyuruListesi duyurular={duyuruListesi} />
      </Diyalog>
      <KonumDiyalogu
        acik={konumAcik}
        kapat={() => setKonumAcik(false)}
        konum={konum}
        gps={gps}
        gpsIste={iste}
        mahalleSec={setMahalle}
      />
    </div>
  )
}

function UstSerit({
  onizleme,
  rol,
  duyurular,
  duyurulariAc,
}: {
  onizleme: boolean
  rol: string | null
  duyurular: Bildirim[]
  duyurulariAc: () => void
}) {
  const akis = useCanliAkisDurumu((d) => d.durum)
  // Duyuru varken düğme en önemli duyurunun renginde: gözden kaçmasın (J-51).
  const onde = enOnemli(duyurular)
  const o = onde ? onemi(onde.onem) : null
  return (
    <header className="flex h-topbar shrink-0 items-center gap-2 border-b border-line bg-panel px-3.5 sm:gap-gutter">
      <Marka daraltilir="telefon" />
      <span className="hidden h-5 w-px bg-line-2 sm:block" />
      <span className="hidden text-body text-ink-2 sm:inline">Afetzede</span>
      {onizleme && rol && (
        <span className="hidden text-small text-ink-3 md:inline">önizleme · {rol.toLocaleLowerCase('tr-TR')}</span>
      )}
      <span className="flex-1" />
      <span
        className="flex items-center gap-2 text-small text-ink-2"
        title="Çağrının, ihbarlarının durumu ve duyurular canlı gelir"
      >
        <span
          aria-hidden
          className={sn('h-2 w-2 rounded-full', akis === 'bagli' ? 'bg-ok' : akis === 'kopuk' ? 'bg-ink-3' : 'bg-mid')}
        />
        <span className="hidden lg:inline">
          {akis === 'bagli' ? 'Canlı' : akis === 'kopuk' ? 'Bağlantı koptu' : 'Bağlanıyor'}
        </span>
      </span>
      {onizleme && (
        <Link
          to="/konsol"
          className="hidden h-9 items-center rounded-control border border-line-2 px-3 text-body text-ink-2 hover:bg-hover hover:text-ink md:flex"
        >
          Konsol
        </Link>
      )}
      <button
        type="button"
        onClick={duyurulariAc}
        aria-label={`Duyurular: ${duyurular.length}`}
        className={sn(
          'flex h-9 shrink-0 items-center gap-1.5 rounded-control border px-2.5 text-body text-ink hover:bg-hover',
          o ? sn(o.kenar, o.zemin) : 'border-line-2',
        )}
      >
        <Megaphone size={18} weight={o ? 'fill' : 'regular'} className={o ? o.metin : 'text-ink-2'} aria-hidden />
        <span className="hidden sm:inline">Duyurular</span>
        {duyurular.length > 0 && (
          <span className="rounded-full bg-panel px-1.5 font-mono text-small text-ink">{duyurular.length}</span>
        )}
      </button>
      <a
        href="tel:112"
        className="flex h-9 shrink-0 items-center gap-1.5 rounded-control border border-crit px-3 text-body font-semibold whitespace-nowrap text-crit hover:bg-crit/15"
      >
        <Phone size={18} weight="fill" aria-hidden />
        112'yi ara
      </a>
      <ProfilMenusu boyut="buyuk" />
    </header>
  )
}
