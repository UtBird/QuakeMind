import { lazy, Suspense, useState } from 'react'
import type { Icon } from '@phosphor-icons/react'
import {
  ArrowBendUpLeft,
  ArrowBendUpRight,
  ArrowUp,
  ArrowUpLeft,
  ArrowUpRight,
  CaretDown,
  CheckCircle,
  FlagCheckered,
  Info,
  MapTrifold,
  NavigationArrow,
  PersonSimpleWalk,
  Warning,
} from '@phosphor-icons/react'
import { Micro } from '@/kabuk/parcalar'
import { ApiHatasi } from '@/veri/istemci'
import { gunMetni } from '@/lib/bicim'
import { sn } from '@/lib/sinif'
import type { SosCagrisi } from '@/veri/sorgular'
import type { HaritaKonumu } from './haritaKatmanlari'
import { mesafeMetni, yon, type EtkinKonum } from './konum'
import { YER_SIRASI, YER_TURLERI, yerAdi } from './yerTurleri'
import {
  YAKIN_YARICAP_KM,
  type SokakRotasi,
  type YakinYer,
  type YakinYerlerYaniti,
  type YerTuru,
  type Manevra,
  type YurumeRotasi,
} from './veri'

/* ---------------------------------------------------------------------------
   "Nereye gidebilirim?" (J-50). Toplanma alanı, hastane, sağlık merkezi,
   eczane, itfaiye ve polis; en yakından başlayarak. Liste önde, harita yanında
   ve küçük: harita yön ve yakınlık için yardımcıdır, ekranı kaplamaz.
   Harita tembel yüklenir; liste harita inmeden çalışır.

   Mesafe ve rota kendi yol ağımızdan gelir (J-44): liste yürüme mesafesine
   göre sıralı; yer seçilince yollar üzerinden rota çizilir (Dijkstra, bilinen
   kapanma ve hasar noktalarından kaçınan maliyetle). Yol ağı üretilmemiş
   bölgede kuş uçuşu uzaklık kalır ve dış servis rotası istenebilir.
--------------------------------------------------------------------------- */

const AfetzedeHaritasi = lazy(() => import('./AfetzedeHaritasi'))
const LISTE_BOYU = 10

type Props = {
  konum: EtkinKonum | null
  haritaKonumu: HaritaKonumu | null
  veri: YakinYerlerYaniti | undefined
  yukleniyor: boolean
  hata: boolean
  tur: YerTuru
  turSec: (t: YerTuru) => void
  secili: YakinYer | null
  sec: (y: YakinYer | null) => void
  cagrilar: SosCagrisi[]
  /** Kendi yol ağımızdan yürüme rotası (seçili yer için). */
  yurume: { veri: YurumeRotasi | null; bekliyor: boolean; hata: unknown; agYok: boolean }
  /** Yedek: dış servis rotası (yalnız yol ağı olmayan bölgede, istenirse). */
  rota: { yerId: string; sonuc: SokakRotasi } | null
  rotaIste: (y: YakinYer) => void
  rotaBekliyor: boolean
  rotaHatasi: unknown
  /** Haritada çizilecek rota: önce kendi ağımız, yoksa dış servis. */
  haritaRotasi: [number, number][] | null
  konumAc: () => void
}

function YonOku({ derece }: { derece: number }) {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 14 14"
      aria-hidden="true"
      style={{ transform: `rotate(${Math.round(derece)}deg)` }}
      className="shrink-0"
    >
      <path d="M7 1.5 11 12 7 9.5 3 12Z" fill="currentColor" />
    </svg>
  )
}

export function NereyeKarti(p: Props) {
  const tumu = p.veri?.yerler[p.tur] ?? []
  const liste = tumu.slice(0, LISTE_BOYU)
  const kapsam = p.veri?.hizmetKapsami
  const bilinmiyor = p.tur !== 'toplanma' && !!kapsam && (!kapsam.uretildi || !kapsam.icinde)
  const kaynak = p.veri?.kaynaklar.hizmet

  return (
    <section
      aria-label="Nereye gidebilirim"
      className="flex shrink-0 flex-col rounded-panel border border-line bg-panel genis:min-h-0 genis:flex-1"
    >
      <header className="shrink-0 border-b border-line px-3.5 pt-2.5 pb-2">
        <div className="flex items-baseline justify-between gap-2">
          <h2 className="flex items-center gap-2 text-subtitle text-ink">
            <MapTrifold size={20} className="text-yer-toplanma" aria-hidden />
            Nereye gidebilirim?
          </h2>
          <Micro>
            {YAKIN_YARICAP_KM} km içinde · {p.veri?.yurume ? 'yürüme mesafesi' : 'kuş uçuşu'}
          </Micro>
        </div>
        <div role="tablist" aria-label="Yer türü" className="mt-2 flex flex-wrap gap-1.5">
          {YER_SIRASI.map((t) => {
            const n = p.veri?.yerler[t].length
            return (
              <button
                key={t}
                type="button"
                role="tab"
                aria-selected={p.tur === t}
                onClick={() => p.turSec(t)}
                className={sn(
                  'flex h-9 items-center gap-1.5 rounded-full border px-3 text-body transition-colors duration-150 ease-out-qm',
                  p.tur === t
                    ? sn(YER_TURLERI[t].kenar, YER_TURLERI[t].soluk, 'text-ink')
                    : 'border-line-2 text-ink-2 hover:bg-hover hover:text-ink',
                )}
              >
                <span
                  aria-hidden
                  className={sn('grid h-5 w-5 place-items-center rounded-full text-micro text-ground', YER_TURLERI[t].nokta)}
                >
                  {YER_TURLERI[t].harf}
                </span>
                {YER_TURLERI[t].cogul}
                {/* 0 yerine "—": kayıt yokluğu yer yokluğu değildir (J-167 F-5). */}
                {n != null && <span className="text-ink-3">{n === 0 ? '—' : n}</span>}
              </button>
            )
          })}
        </div>
      </header>

      <div className="grid grid-cols-1 genis:min-h-0 genis:flex-1 genis:grid-cols-5">
        <div className="genis:col-span-2 genis:min-h-0 genis:overflow-auto genis:border-r genis:border-line">
          {!p.konum ? (
            <div className="px-3.5 py-3">
              <p className="text-body text-ink">Konumun olmadan en yakın yerler hesaplanamaz.</p>
              <button
                type="button"
                onClick={p.konumAc}
                className="mt-2 h-10 rounded-control border border-crit px-3 text-body text-ink hover:bg-hover"
              >
                Konumunu seç
              </button>
            </div>
          ) : p.yukleniyor ? (
            <p className="px-3.5 py-3 text-small text-ink-3">Yakındaki yerler aranıyor…</p>
          ) : p.hata ? (
            <p role="alert" className="px-3.5 py-3 text-small text-crit">
              Yakındaki yerler alınamadı. Bağlantın dönünce sayfayı yenile.
            </p>
          ) : bilinmiyor ? (
            <p className="px-3.5 py-3 text-small text-ink-2">
              Bu konum için {YER_TURLERI[p.tur].ad.toLocaleLowerCase('tr-TR')} verisi üretilmedi; bu,
              yakında olmadığı anlamına gelmez. Veri şu bölgelerde var: {kapsam?.bolgeler.join(', ') || '—'}.
            </p>
          ) : liste.length === 0 ? (
            <p className="px-3.5 py-3 text-small text-ink-2">
              {YAKIN_YARICAP_KM} km içinde haritada (OpenStreetMap) kayıtlı{' '}
              {YER_TURLERI[p.tur].ad.toLocaleLowerCase('tr-TR')} yok. Bu, yakında olmadığı anlamına
              gelmez; harita verisi eksik olabilir. Acil durumda 112'yi ara.
            </p>
          ) : (
            <ol>
              {liste.map((y) => (
                <YerSatiri key={y.id} y={y} {...p} />
              ))}
            </ol>
          )}
        </div>

        <div className="relative h-64 min-h-0 border-t border-line genis:col-span-3 genis:h-auto genis:border-t-0">
          <Suspense
            fallback={
              <div className="grid h-full place-items-center bg-sunken text-small text-ink-3">
                Harita yükleniyor…
              </div>
            }
          >
            <AfetzedeHaritasi
              konum={p.haritaKonumu}
              yerler={tumu}
              secili={p.secili}
              sec={p.sec}
              cagrilar={p.cagrilar}
              rota={p.haritaRotasi}
            />
          </Suspense>
        </div>
      </div>

      <p className="flex shrink-0 items-start gap-2 border-t border-line px-3.5 py-1.5 text-small text-ink-3">
        <Info size={16} className="mt-0.5 shrink-0 text-ink-2" aria-hidden />
        <span>
          <span className="text-ink-2">Kayıttır; yerin şu an açık ya da güvenli olduğunu göstermez.</span>{' '}
          Toplanma: AFAD listesi. Hastane, sağlık, eczane, itfaiye, polis: OpenStreetMap
          {kaynak ? ` (yerel kopya ${gunMetni(kaynak.dosyaTarihi)})` : ''}.
        </span>
      </p>
    </section>
  )
}

function YerSatiri({ y, ...p }: Props & { y: YakinYer }) {
  const secili = p.secili?.id === y.id
  const y2 = p.konum ? yon(p.konum, y) : null
  const disRota = p.rota?.yerId === y.id ? p.rota.sonuc : null
  const yuruyerek = y.yuruyusM != null

  return (
    <li className={sn('border-b border-line last:border-b-0', secili && 'bg-raised')}>
      <button
        type="button"
        aria-expanded={secili}
        // Ekran okuyucuya açık ad (J-167 U-6): tür, ad, uzaklık, yön tek cümlede.
        aria-label={[
          YER_TURLERI[y.tur].ad ?? null,
          yerAdi(y),
          `${yuruyerek ? 'yürüyerek' : 'kuş uçuşu'} ${mesafeMetni(yuruyerek ? (y.yuruyusM as number) : y.mesafeM)}`,
          y2 ? `yön ${y2.ad}` : null,
        ]
          .filter(Boolean)
          .join(', ')}
        onClick={() => p.sec(secili ? null : y)}
        className="flex w-full items-start gap-2.5 px-3.5 py-2 text-left hover:bg-hover"
      >
        <span
          aria-hidden
          className={sn(
            'mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full text-small text-ground',
            YER_TURLERI[y.tur].nokta,
          )}
        >
          {YER_TURLERI[y.tur].harf}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-body text-ink">{yerAdi(y)}</span>
          {y.adres && <span className="block truncate text-small text-ink-3">{y.adres}</span>}
        </span>
        <span className="shrink-0 text-right">
          <span
            className="block font-mono text-body text-ink"
            title={yuruyerek ? `Yürüyerek; kuş uçuşu ${mesafeMetni(y.mesafeM)}` : 'Kuş uçuşu'}
          >
            {mesafeMetni(yuruyerek ? (y.yuruyusM as number) : y.mesafeM)}
          </span>
          {y2 && (
            <span className="flex items-center justify-end gap-1 text-small text-ink-2">
              <YonOku derece={y2.derece} />
              {y2.ad}
            </span>
          )}
        </span>
      </button>

      {secili && (
        <div className="px-3.5 pb-2.5">
          {p.yurume.veri ? (
            <RotaOzeti r={p.yurume.veri} kusUcusuM={y.mesafeM} hedefAdi={yerAdi(y)} />
          ) : p.yurume.bekliyor ? (
            <p className="text-small text-ink-2">Yol ağında rota hesaplanıyor…</p>
          ) : p.yurume.agYok ? (
            disRota ? (
              <p className="text-small text-ink">
                Yürüyerek {mesafeMetni(disRota.uzunlukM)} · ~{disRota.yuruyusDk} dk.{' '}
                <span
                  role={disRota.kapanma.rotada > 0 ? 'alert' : undefined}
                  className={disRota.kapanma.rotada > 0 ? 'font-semibold text-crit' : 'text-ink-2'}
                >
                  {disRota.uyari}
                </span>
              </p>
            ) : (
              <>
                <p className="mb-1.5 text-small text-ink-2">
                  Bu bölge için yol ağımız üretilmedi; haritadaki kesikli çizgi yalnız yönü gösterir.
                </p>
                <button
                  type="button"
                  disabled={!p.konum || p.rotaBekliyor}
                  onClick={() => p.rotaIste(y)}
                  className="flex h-10 w-full items-center justify-center gap-2 rounded-control border border-accent bg-accent-soft px-3 text-body text-ink hover:bg-accent/20 disabled:opacity-50"
                >
                  <PersonSimpleWalk size={18} className="text-accent" aria-hidden />
                  {p.rotaBekliyor ? 'Yol tarifi isteniyor…' : 'Dış servisten yol tarifi iste'}
                </button>
                <p className="mt-1 text-small text-ink-3">
                  OpenStreetMap'in yol tarifi servisi; konumun o servise gider. Servisin önerdiği
                  rotalardan bilinen kapalı yollardan geçmeyeni seçilir; hasarı bilmez.
                </p>
                {p.rotaHatasi != null && (
                  <p role="alert" className="mt-1 text-small text-crit">
                    Yol tarifi alınamadı:{' '}
                    {p.rotaHatasi instanceof ApiHatasi ? p.rotaHatasi.message : 'servise ulaşılamadı'}.
                  </p>
                )}
              </>
            )
          ) : p.yurume.hata != null ? (
            <p role="alert" className="text-small text-crit">
              Rota hesaplanamadı:{' '}
              {p.yurume.hata instanceof ApiHatasi ? p.yurume.hata.message : 'sunucuya ulaşılamadı'}.
              Haritadaki kesikli çizgi yönü gösterir.
            </p>
          ) : null}
        </div>
      )}
    </li>
  )
}

const ADIM_SAYISI = 4

/* Dönüşün adı ve simgesi. Keskin dönüş de aynı okla, adı ayrı. */
const MANEVRA: Record<Manevra, { ad: string; ikon: Icon }> = {
  basla: { ad: 'Yürümeye başla', ikon: NavigationArrow },
  duz: { ad: 'Düz devam et', ikon: ArrowUp },
  'hafif-sag': { ad: 'Hafif sağa', ikon: ArrowUpRight },
  sag: { ad: 'Sağa dön', ikon: ArrowBendUpRight },
  'keskin-sag': { ad: 'Keskin sağa dön', ikon: ArrowBendUpRight },
  'hafif-sol': { ad: 'Hafif sola', ikon: ArrowUpLeft },
  sol: { ad: 'Sola dön', ikon: ArrowBendUpLeft },
  'keskin-sol': { ad: 'Keskin sola dön', ikon: ArrowBendUpLeft },
}

/** "güneybatı" -> "güneybatıya" */
const YONELME: Record<string, string> = {
  kuzey: 'kuzeye',
  kuzeydoğu: 'kuzeydoğuya',
  doğu: 'doğuya',
  güneydoğu: 'güneydoğuya',
  güney: 'güneye',
  güneybatı: 'güneybatıya',
  batı: 'batıya',
  kuzeybatı: 'kuzeybatıya',
}

/** Rota özeti: büyük uzunluk ve süre, rotadaki hasar durumu, dönüş oklarıyla
    adım adım tarif ve varış. Adımlar rotanın kendisinden hesaplanır; yürürken
    hangi adımda olunduğunu izleyen bir sistem yok (J-44). */
function RotaOzeti({ r, kusUcusuM, hedefAdi }: { r: YurumeRotasi; kusUcusuM: number; hedefAdi: string }) {
  const [tumu, setTumu] = useState(false)
  const uzun = r.adimlar.length > ADIM_SAYISI
  const gosterilen = tumu || !uzun ? r.adimlar : r.adimlar.slice(0, ADIM_SAYISI)

  return (
    <div className="overflow-hidden rounded-panel border border-accent bg-sunken">
      <div className="flex items-center gap-3 border-b border-line-2 bg-accent-soft px-3 py-2.5">
        <span aria-hidden className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-accent text-accent-ink">
          <PersonSimpleWalk size={22} weight="bold" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-title font-semibold text-ink">
            {mesafeMetni(r.uzunlukM)}
            <span className="text-subtitle font-normal text-ink-2"> · ~{r.yuruyusDk} dk yürüyüş</span>
          </p>
          <p className="text-small text-ink-2">
            Kuş uçuşu {mesafeMetni(kusUcusuM)} · {r.adimlar.length} adım
          </p>
        </div>
      </div>

      <div className="px-3 pt-2.5">
        {r.hasar.rotadaKapanma > 0 ? (
          <p role="alert" className="flex gap-2 rounded-control border border-crit bg-crit/15 px-2.5 py-1.5 text-small text-ink">
            <Warning size={16} weight="fill" className="mt-0.5 shrink-0 text-crit" aria-hidden />
            Başka yol olmadığı için rota bilinen bir kapanmadan geçiyor; oraya yaklaşınca dikkat et.
          </p>
        ) : r.hasar.rotadaRiskliM > 0 ? (
          <p className="flex gap-2 rounded-control border border-high bg-high/15 px-2.5 py-1.5 text-small text-ink">
            <Warning size={16} weight="fill" className="mt-0.5 shrink-0 text-high" aria-hidden />
            Rotanın {mesafeMetni(r.hasar.rotadaRiskliM)} kadarı bilinen bir hasar noktasına 400 m'den yakın.
          </p>
        ) : (
          <p className="flex gap-2 rounded-control border border-ok bg-ok/15 px-2.5 py-1.5 text-small text-ink">
            <CheckCircle size={16} weight="fill" className="mt-0.5 shrink-0 text-ok" aria-hidden />
            Rotada bilinen kapanma ya da hasar noktası yok.
          </p>
        )}
      </div>

      <ol aria-label="Adım adım yol tarifi" className="px-3 pt-3">
        {gosterilen.map((a, i) => {
          const m = MANEVRA[a.manevra] ?? MANEVRA.duz
          const Ikon = m.ikon
          return (
            <li key={i} className="flex gap-2.5">
              <div className="flex flex-col items-center">
                <span aria-hidden className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-accent-soft text-accent">
                  <Ikon size={18} weight="bold" />
                </span>
                <span aria-hidden className="w-px flex-1 bg-line-2" />
              </div>
              <div className="min-w-0 flex-1 pb-3">
                <p className="text-small text-accent">
                  {m.ad}
                  {a.manevra === 'basla' && a.yon ? ` · ${YONELME[a.yon] ?? a.yon} doğru` : ''}
                </p>
                <p className="flex items-baseline justify-between gap-2">
                  <span className="truncate text-body text-ink">{a.ad}</span>
                  <span className="shrink-0 font-mono text-small text-ink-2">{mesafeMetni(a.uzunlukM)}</span>
                </p>
              </div>
            </li>
          )
        })}
        {(tumu || !uzun) && (
          <li className="flex gap-2.5 pb-3">
            <span aria-hidden className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-accent text-accent-ink">
              <FlagCheckered size={18} weight="bold" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-small text-accent">Varış</p>
              <p className="truncate text-body font-semibold text-ink">{hedefAdi}</p>
            </div>
          </li>
        )}
      </ol>

      {uzun && (
        <button
          type="button"
          aria-expanded={tumu}
          onClick={() => setTumu((v) => !v)}
          className="flex h-10 w-full items-center justify-center gap-1.5 border-t border-line-2 text-body text-accent hover:bg-hover"
        >
          {tumu ? 'Daha az göster' : `Tüm adımlar ve varış (${r.adimlar.length - ADIM_SAYISI} adım daha)`}
          <CaretDown size={14} className={sn(tumu && 'rotate-180')} aria-hidden />
        </button>
      )}

      <details className="border-t border-line-2 px-3 py-2 text-small text-ink-3">
        <summary className="flex cursor-pointer items-center gap-1.5 text-ink-2 hover:text-ink">
          <Info size={14} aria-hidden /> Nasıl hesaplandı?
        </summary>
        <p className="mt-1.5">
          {r.uyari} Rota kendi yol ağımızda (OpenStreetMap, {gunMetni(r.kaynak.osm)} kopyası) Dijkstra
          ile bulunur; hasar noktalarından ve kapanmalardan kaçınan bir maliyet kullanılır. Sokak adları
          OpenStreetMap'ten, dönüş yönü sokak geçişindeki açıdan gelir. Yürürken hangi adımda olduğunu
          izleyen bir sistem yok.
        </p>
      </details>
    </div>
  )
}
