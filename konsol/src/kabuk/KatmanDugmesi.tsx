import { useEffect, useId, useRef, useState, type ReactNode } from 'react'
import { useParams } from 'react-router-dom'
import { CaretDown, Stack } from '@phosphor-icons/react'
import { Micro } from './parcalar'
import {
  KATMANLAR,
  KATMAN_ADI,
  KATMAN_BILGI,
  KATMAN_GRUBU,
  useKonsol,
  type KatmanId,
} from '@/durum/konsolDurumu'
import { MODLAR, modBul } from '@/modlar/modlar'
import { useSorguAraligi } from '@/durum/zamanDurumu'
import { useEkipler, useOzet, useSosCagrilari } from '@/veri/sorgular'
import { useIhbarlar } from '@/veri/ihbar'
import {
  DEPREM_EN_AZ,
  useDepremler,
  useFaylar,
  useKapanmalar,
  useSaglik,
  useToplanmaAlanlari,
} from '@/veri/katman'
import { TOPLANMA_EN_AZ_ZOOM, YAPI_EN_AZ_ZOOM, useGorunenAltlik } from '@/harita/altlikGorunumu'
import { simgeAdresi, type SimgeTuru } from '@/harita/simgeler'
import { sayi } from '@/lib/bicim'
import { sn } from '@/lib/sinif'

/* ---------------------------------------------------------------------------
   Harita katmanları (J-56, J-172). Her satır haritadakiyle AYNI işareti
   taşır: panel aynı zamanda lejanttır. Satırda yalnız ad, sayı ve anahtar;
   kaynaklar en altta toplu. Yalnız o modda anlamı olan katmanlar görünür
   (tatbikat katmanları tatbikatta, analiz katmanları hasar analizinde).
   Yakınlaşınca çizilen katman, eşiğin altındayken bunu satırında yazar.
--------------------------------------------------------------------------- */

const MODA_OZEL: Partial<Record<KatmanId, string>> = {
  analizGoruntusu: 'hasar',
  analizSonucu: 'hasar',
  simHasar: 'simulasyon',
  simKapanma: 'simulasyon',
  simRota: 'simulasyon',
  simGorev: 'simulasyon',
  simKamera: 'simulasyon',
  simMetin: 'simulasyon',
}

const ESIK: Partial<Record<KatmanId, number>> = {
  // Sağlık ve toplanma uzakta küme olarak görünür (J-191); toplanma verisi
  // bölge altlığı görününce iner.
  toplanma: TOPLANMA_EN_AZ_ZOOM,
  yapilar: YAPI_EN_AZ_ZOOM,
}

function Simge({ tur }: { tur: SimgeTuru }) {
  return <img alt="" src={simgeAdresi(tur)} className="h-4 w-4 shrink-0" />
}

/** Katmanın haritadaki işareti (lejant). */
export function KatmanIsareti({ k }: { k: KatmanId | 'sos' }) {
  const kutu = (c: ReactNode) => (
    <span aria-hidden className="flex w-12 shrink-0 items-center gap-0.5">
      {c}
    </span>
  )
  switch (k) {
    case 'sos':
      return kutu(
        <>
          <Simge tur="sos-kritik" />
          <Simge tur="sos-yuksek" />
          <Simge tur="sos-orta" />
        </>,
      )
    case 'ihbarlar':
      return kutu(
        <>
          <Simge tur="ihbar-fotograf" />
          <Simge tur="ihbar-metin" />
          <Simge tur="ihbar-ihtiyac" />
        </>,
      )
    case 'ekipler':
      return kutu(
        <>
          <Simge tur="ekip-musait" />
          <Simge tur="ekip-gorevde" />
        </>,
      )
    case 'toplanma':
      return kutu(<Simge tur="toplanma" />)
    case 'saglik':
      return kutu(<Simge tur="hastane" />)
    case 'hasarliYollar':
      return kutu(
        <>
          <span className="h-1 w-4 rounded-full bg-crit" />
          <Simge tur="kapanma" />
        </>,
      )
    case 'analizSonucu':
      return kutu(<span className="h-1 w-6 rounded-full bg-crit" />)
    case 'isi':
      return kutu(
        <span
          className="h-2 w-10 rounded-badge"
          style={{ background: 'linear-gradient(90deg, var(--heat-1), var(--heat-3), var(--heat-5))' }}
        />,
      )
    case 'depremler':
      return kutu(<span className="h-3 w-3 rounded-full border-2 border-deprem" />)
    case 'faylar':
      return kutu(<span className="w-6 border-t-2 border-dashed border-fay" />)
    case 'yollar':
      return kutu(<span className="h-1 w-6 rounded-full bg-map-motorway" />)
    case 'yapilar':
      return kutu(<span className="h-3 w-3 rounded-badge border border-line-2 bg-map-building" />)
    default:
      return kutu(<span className="h-3 w-3 rounded-badge border border-line-2 bg-raised" />)
  }
}

function Satir({
  k,
  ad,
  sayiMetni,
  not,
  acik,
  onDegis,
}: {
  k: KatmanId | 'sos'
  ad: string
  sayiMetni?: string | null
  not?: string | null
  acik?: boolean
  onDegis?: () => void
}) {
  const icerik = (
    <>
      <KatmanIsareti k={k} />
      <span className="min-w-0 flex-1">
        <span className={sn('block truncate text-body', acik === false ? 'text-ink-2' : 'text-ink')}>{ad}</span>
        {(sayiMetni || not) && (
          <span className="block truncate text-small text-ink-3">{[sayiMetni, not].filter(Boolean).join(' · ')}</span>
        )}
      </span>
    </>
  )
  if (!onDegis) {
    return <div className="flex items-center gap-2.5 py-1.5">{icerik}<span className="text-small text-ink-3">hep açık</span></div>
  }
  return (
    <button
      type="button"
      aria-pressed={acik}
      onClick={onDegis}
      className="flex w-full items-center gap-2.5 rounded-control py-1.5 text-left hover:bg-hover"
    >
      {icerik}
      <span
        aria-hidden
        className={sn(
          'relative h-4 w-8 shrink-0 rounded-full transition-colors duration-150 ease-out-qm',
          acik ? 'bg-accent-deep' : 'bg-line-2',
        )}
      >
        <span
          className={sn(
            'absolute top-0.5 left-0.5 h-3 w-3 rounded-full transition-transform duration-150 ease-out-qm',
            acik ? 'translate-x-4 bg-ink' : 'bg-ink-3',
          )}
        />
      </span>
    </button>
  )
}

export function KatmanDugmesi({ yukari = true }: { yukari?: boolean }) {
  const [acik, setAcik] = useState(false)
  const kutu = useRef<HTMLDivElement>(null)
  const kimlik = useId()
  const { mod } = useParams()
  const tanim = modBul(mod) ?? MODLAR[0]
  const katmanlar = useKonsol((d) => d.katmanlar)
  const katmanDegistir = useKonsol((d) => d.katmanDegistir)
  const katmanlariAyarla = useKonsol((d) => d.katmanlariAyarla)
  const aralik = useSorguAraligi()
  const ozet = useOzet(aralik)
  const sos = useSosCagrilari(aralik)
  const ihbar = useIhbarlar(aralik)
  const ekipler = useEkipler()
  // Aynı sorgu anahtarları kabuktakilerle paylaşılır: katman kapalıyken istek
  // atılmaz, açıkken sayı önbellekten gelir.
  const { gorunen: gorunenBolgeler, gorunum } = useGorunenAltlik()
  const kapanmalar = useKapanmalar(katmanlar.hasarliYollar)
  const depremler = useDepremler(katmanlar.depremler)
  const faylar = useFaylar(katmanlar.faylar)
  const toplanma = useToplanmaAlanlari(katmanlar.toplanma, gorunenBolgeler)
  const saglik = useSaglik(katmanlar.saglik)
  const zoom = gorunum?.zoom ?? 0

  const gorunur = (k: KatmanId) => KATMAN_BILGI[k].bagli && (!MODA_OZEL[k] || MODA_OZEL[k] === tanim.id)
  const acikSayisi = KATMANLAR.filter((k) => katmanlar[k] && gorunur(k)).length
  const oneri = new Set<KatmanId>(tanim.katmanlar)
  const onerilenden = KATMANLAR.some((k) => gorunur(k) && katmanlar[k] !== oneri.has(k))

  useEffect(() => {
    if (!acik) return
    const disari = (e: MouseEvent) => {
      if (!kutu.current?.contains(e.target as Node)) setAcik(false)
    }
    const tus = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setAcik(false)
    }
    document.addEventListener('mousedown', disari)
    document.addEventListener('keydown', tus)
    return () => {
      document.removeEventListener('mousedown', disari)
      document.removeEventListener('keydown', tus)
    }
  }, [acik])

  const noktalar = ozet.data ? Object.values(ozet.data.kaynakSayilari).reduce((t, n) => t + (n ?? 0), 0) : null
  const sayilar: Partial<Record<KatmanId, string | null>> = {
    ihbarlar: ihbar.data ? `${sayi(ihbar.data.length)} ihbar` : null,
    ekipler: ekipler.data ? `${sayi(ekipler.data.length)} ekip` : null,
    isi: noktalar != null ? `${sayi(noktalar)} nokta` : null,
    hasarliYollar: kapanmalar.data ? `${sayi(kapanmalar.data.sayi)} kapanma` : null,
    depremler: depremler.data ? `${sayi(depremler.data.sayi)} deprem, M ≥ ${DEPREM_EN_AZ}` : null,
    faylar: faylar.data ? `${sayi(faylar.data.sayi)} hat` : null,
    toplanma: toplanma.data ? `${sayi(toplanma.data.sayi)} alan` : null,
    saglik: saglik.data ? `${sayi(saglik.data.sayi)} tesis` : null,
  }

  return (
    <div ref={kutu} className="relative">
      <button
        type="button"
        aria-expanded={acik}
        aria-controls={kimlik}
        onClick={() => setAcik((v) => !v)}
        className="flex h-9 items-center gap-2 rounded-control border border-line-2 bg-panel px-3 text-body text-ink shadow-float hover:bg-hover"
      >
        <Stack size={16} weight="bold" aria-hidden />
        Katmanlar
        <span className="rounded-badge bg-raised px-1.5 font-mono text-small text-ink-2">{acikSayisi}</span>
        <CaretDown size={12} className={sn((acik ? !yukari : yukari) && 'rotate-180')} aria-hidden />
      </button>

      {acik && (
        <div
          id={kimlik}
          role="dialog"
          aria-label="Harita katmanları"
          className={sn(
            'absolute left-0 z-30 max-h-form w-80 overflow-auto rounded-panel border border-line-2 bg-panel p-3 shadow-float',
            yukari ? 'bottom-full mb-1.5' : 'top-full mt-1.5',
          )}
        >
          <div className="flex items-baseline justify-between gap-2">
            <p className="text-small text-ink-2">
              <span className="text-ink">{tanim.ad}</span> için önerilen katmanlar
            </p>
            {onerilenden && (
              <button
                type="button"
                onClick={() => katmanlariAyarla([...tanim.katmanlar])}
                className="shrink-0 text-small text-accent hover:underline"
              >
                Önerilene dön
              </button>
            )}
          </div>

          {(Object.keys(KATMAN_GRUBU) as (keyof typeof KATMAN_GRUBU)[]).map((grup) => {
            const satirlar = KATMANLAR.filter((k) => KATMAN_BILGI[k].grup === grup && gorunur(k))
            if (!satirlar.length && grup !== 'olay') return null
            return (
              <section key={grup} className="mt-2.5 border-t border-line pt-2">
                <Micro>{KATMAN_GRUBU[grup]}</Micro>
                {grup === 'olay' && (
                  <Satir k="sos" ad="SOS çağrıları" sayiMetni={sos.data ? `${sayi(sos.data.length)} çağrı` : null} />
                )}
                {satirlar.map((k) => (
                  <Satir
                    key={k}
                    k={k}
                    ad={KATMAN_ADI[k]}
                    acik={katmanlar[k]}
                    onDegis={() => katmanDegistir(k)}
                    sayiMetni={sayilar[k]}
                    not={katmanlar[k] && ESIK[k] && zoom < ESIK[k]! ? 'yakınlaşınca görünür' : null}
                  />
                ))}
              </section>
            )
          })}

          <details className="mt-2.5 border-t border-line pt-2">
            <summary className="cursor-pointer text-small text-ink-2 hover:text-ink">Veri kaynakları</summary>
            <dl className="mt-1.5 grid gap-1.5">
              <div>
                <dt className="text-small text-ink">SOS çağrıları</dt>
                <dd className="text-small text-ink-3">Afetzede ekranından gelen acil çağrılar</dd>
              </div>
              {KATMANLAR.filter(gorunur).map((k) => (
                <div key={k}>
                  <dt className="text-small text-ink">{KATMAN_ADI[k]}</dt>
                  <dd className="text-small text-ink-3">{KATMAN_BILGI[k].kaynak}</dd>
                </div>
              ))}
            </dl>
          </details>
        </div>
      )}
    </div>
  )
}
