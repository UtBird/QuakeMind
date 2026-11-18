import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { WarningCircle } from '@phosphor-icons/react'
import { Amac, Bolum, HazirSecenekler, SuAn, Teknik, VeriYok } from '@/kabuk/Panel'
import { Micro, Rozet } from '@/kabuk/parcalar'
import { apiGet, apiPost } from '@/veri/istemci'
import { useHarita } from '@/harita/HaritaKabugu'
import { useCozumleme } from '@/durum/cozumlemeDurumu'
import { sn } from '@/lib/sinif'

/* ---------------------------------------------------------------------------
   Deprem riski (J-173). Panelin sorusu: hangi ilde risk daha yüksek, neden?
   Sol: 81 il riske göre sıralı. Harita: il merkezleri risk renginde, seçili
   ilin hesap alanı halkalarla. Sağ: skor ve üç bileşen, her biri neyi
   ölçtüğü ve dayanağıyla; zayıf olan bileşen bunu söyler.
   Hesap sunucuda (`risk_hizmeti.py`), model dosyadan yüklenir.
--------------------------------------------------------------------------- */

export type RiskYaniti = {
  city: string
  coordinates: { lat: number; lon: number }
  riskScore: number
  riskLevel: string
  lastUpdate?: string
  metrics: {
    shortRisk: number
    longHazard: number
    faultScore: number
    faultDistanceKm: number
    nearbyQuakeCount?: number
    maxMagnitude?: number
  }
  dayanak?: {
    kisaVadeKaynagi: 'yerel' | 'ulke'
    kisaVadeYerelDeprem: number
    uzunVadeAnaSok: number
    katalogBasi: string
    katalogSonu: string
    agirlik: { kisa: number; uzun: number; fay: number }
    yaricapKm: { kisa: number; uzun: number; yakinDeprem: number }
  }
  yakinFaylar?: { tur: string; kimlik: string; km: number }[]
  sonDepremler?: { time: string; magnitude: number; distanceKm: number; place: string; depth: number | null }[]
}

export type RiskSirasi = {
  il: string
  lat: number
  lon: number
  skor: number
  seviye: string
  kisa: number
  uzun: number
  fay: number
  fayKm: number
  kisaVadeKaynagi: 'yerel' | 'ulke'
}

export const RISK_TONU = (skor: number): 'crit' | 'high' | 'mid' | 'ok' =>
  skor >= 75 ? 'crit' : skor >= 50 ? 'high' : skor >= 25 ? 'mid' : 'ok'

const TON_ZEMIN = { crit: 'bg-crit', high: 'bg-high', mid: 'bg-mid', ok: 'bg-ok' } as const

const OPERASYON = [
  { id: 'Hatay', etiket: 'Antakya (Hatay)' },
  { id: 'Kahramanmaraş', etiket: 'Kahramanmaraş' },
  { id: 'Gaziantep', etiket: 'Gaziantep' },
  { id: 'Malatya', etiket: 'Malatya' },
  { id: 'Adıyaman', etiket: 'Adıyaman' },
] as const

const yuzde = (x: number) => `%${Math.round(x * 100)}`
const ondalik = (x: number, b = 1) => x.toFixed(b).replace('.', ',')

export function useRiskSiralamasi() {
  return useQuery({
    queryKey: ['risk', 'siralama'],
    staleTime: 10 * 60_000,
    queryFn: () => apiGet<{ iller: RiskSirasi[] }>('/api/risk/siralama'),
  })
}

function useRisk(il: RiskSirasi | null) {
  return useQuery({
    queryKey: ['risk', 'il', il?.il],
    enabled: !!il,
    staleTime: 10 * 60_000,
    queryFn: () =>
      apiPost<RiskYaniti>('/api/risk/predict', { city: il!.il, manualLatitude: il!.lat, manualLongitude: il!.lon }),
  })
}

/** Seçili il (mağazada `il:<ad>`); sol ve sağ panel ile harita paylaşır. */
export function useSeciliRiskIli(siralama: RiskSirasi[] | undefined): RiskSirasi | null {
  const secim = useCozumleme((d) => d.riskBolge)
  return useMemo(() => {
    const ad = secim?.startsWith('il:') ? secim.slice(3) : null
    return (ad && siralama?.find((x) => x.il === ad)) || null
  }, [secim, siralama])
}

export function RiskSol() {
  const siralama = useRiskSiralamasi()
  const secili = useSeciliRiskIli(siralama.data?.iller)
  const sec = useCozumleme((d) => d.riskBolgeSec)
  const { ucus } = useHarita()
  const [ara, setAra] = useState('')

  const ilSec = (il: RiskSirasi) => {
    sec(`il:${il.il}`)
    ucus(il.lon, il.lat, 6.4) // 200 km'lik hesap alanı ekrana sığsın
  }
  // Haritadan ya da düğmeden seçilen il listede görünür olsun.
  useEffect(() => {
    if (secili) document.getElementById(`risk-il-${secili.il}`)?.scrollIntoView({ block: 'nearest' })
  }, [secili])
  const liste = useMemo(() => {
    const a = ara.trim().toLocaleLowerCase('tr')
    return (siralama.data?.iller ?? [])
      .map((x, i) => ({ ...x, sira: i + 1 }))
      .filter((x) => !a || x.il.toLocaleLowerCase('tr').includes(a))
  }, [siralama.data, ara])

  return (
    <Bolum baslik="Deprem riski" ek={<Micro>81 il</Micro>}>
      <Amac>
        Hangi ilde deprem riski daha yüksek, neden? Geçmiş depremler, fay uzaklığı ve son
        hareketlilik birlikte; her il merkezi için.
      </Amac>

      <HazirSecenekler
        etiket="Operasyon bölgeleri"
        secenekler={OPERASYON}
        secili={(secili?.il as (typeof OPERASYON)[number]['id']) ?? null}
        onSec={(id) => {
          const il = siralama.data?.iller.find((x) => x.il === id)
          if (il) ilSec(il)
        }}
      />

      <label className="mt-3 block" htmlFor="risk-ara">
        <Micro>İl ara</Micro>
      </label>
      <input
        id="risk-ara"
        type="search"
        value={ara}
        onChange={(e) => setAra(e.target.value)}
        placeholder="ör. Bolu"
        className="mt-1 w-full rounded-control border border-line-2 bg-sunken px-2.5 py-1.5 text-body text-ink"
      />

      {siralama.isError ? (
        <div className="mt-2">
          <VeriYok ne="Risk sıralaması" neden="model yüklenemedi (araclar_risk_egit.py)" />
        </div>
      ) : (
        <ol aria-label="İller, riske göre" className="mt-2 max-h-form overflow-auto rounded-control border border-line">
          {siralama.isPending && <li className="px-2.5 py-2 text-small text-ink-3">81 il hesaplanıyor…</li>}
          {liste.map((il) => (
            <li key={il.il}>
              <button
                id={`risk-il-${il.il}`}
                type="button"
                aria-pressed={secili?.il === il.il}
                onClick={() => ilSec(il)}
                className={sn(
                  'flex w-full items-center gap-2 border-b border-line px-2.5 py-1.5 text-left last:border-b-0',
                  secili?.il === il.il ? 'bg-raised' : 'hover:bg-hover',
                )}
              >
                <span className="w-6 shrink-0 font-mono text-small text-ink-3">{il.sira}</span>
                <span className="min-w-0 flex-1 truncate text-small text-ink">{il.il}</span>
                <span className="h-1.5 w-16 shrink-0 overflow-hidden rounded-full bg-line">
                  <span
                    className={sn('block h-full', TON_ZEMIN[RISK_TONU(il.skor)])}
                    style={{ width: `${Math.max(3, il.skor)}%` }}
                  />
                </span>
                <span className="w-9 shrink-0 text-right font-mono text-small text-ink">{Math.round(il.skor)}</span>
              </button>
            </li>
          ))}
        </ol>
      )}

      <SuAn>
        {secili
          ? `${secili.il}: skor ${Math.round(secili.skor)}, ${secili.seviye.toLocaleLowerCase('tr')}; ayrıntı sağda.`
          : 'Bir ile tıkla; skorun bileşenleri ve dayanağı sağda, hesap alanı haritada.'}
      </SuAn>

      <Teknik>
        Skor her il için il merkezinde hesaplanır, ilin tamamı için değil. Model istek yolunda
        eğitilmez; sonuç veri değişmedikçe sunucuda saklanır (ilk sıralama ~2 sn, sonra anında).
      </Teknik>
    </Bolum>
  )
}

export function RiskSag() {
  const siralama = useRiskSiralamasi()
  const secili = useSeciliRiskIli(siralama.data?.iller)
  const risk = useRisk(secili)
  if (!secili) {
    return (
      <Bolum baslik="Risk">
        <Amac>Seçilen ilin risk skoru, üç bileşeni ve her birinin dayanağı burada görünür.</Amac>
        <div className="mt-2">
          <VeriYok ne="Risk" neden="henüz il seçilmedi" />
        </div>
      </Bolum>
    )
  }
  if (!risk.data) {
    return (
      <Bolum baslik={secili.il}>
        <p className="text-small text-ink-3">{risk.isError ? 'Risk hesaplanamadı.' : 'Hesaplanıyor…'}</p>
      </Bolum>
    )
  }
  return <RiskSonucu veri={risk.data} />
}

function Bilesen({
  ad,
  soru,
  deger,
  agirlik,
  dayanak,
  uyari,
}: {
  ad: string
  soru: string
  deger: number
  agirlik: number
  dayanak: string
  uyari?: string | null
}) {
  const ton = RISK_TONU(deger * 100)
  return (
    <div className="border-t border-line py-2.5 first:border-t-0">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-body text-ink">{ad}</span>
        <span className="font-mono text-body text-ink">{yuzde(deger)}</span>
      </div>
      <p className="text-small text-ink-3">{soru}</p>
      <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-line">
        <span className={sn('block h-full', TON_ZEMIN[ton])} style={{ width: `${Math.max(2, deger * 100)}%` }} />
      </div>
      <p className="mt-1 text-small text-ink-2">
        {dayanak} <span className="text-ink-3">· skordaki payı {yuzde(agirlik)}</span>
      </p>
      {uyari && (
        <p className="mt-1 flex items-start gap-1.5 text-small text-ink-2">
          <WarningCircle size={14} weight="bold" className="mt-0.5 shrink-0 text-high" aria-hidden />
          {uyari}
        </p>
      )}
    </div>
  )
}

export function RiskSonucu({ veri }: { veri: RiskYaniti }) {
  const d = veri.dayanak
  const ag = d?.agirlik ?? { kisa: 0.4, uzun: 0.3, fay: 0.3 }
  const katalogYil = d ? `${d.katalogBasi.slice(0, 4)}–${d.katalogSonu.slice(0, 4)}` : null
  return (
    <>
      <Bolum baslik="Risk skoru" ek={<Micro>{veri.city}</Micro>}>
        <div className="flex items-end justify-between gap-2">
          <p className="font-cond text-metric text-ink">{Math.round(veri.riskScore)}</p>
          <Rozet ton={RISK_TONU(veri.riskScore)}>{veri.riskLevel}</Rozet>
        </div>
        <p className="mt-1 text-small text-ink-3">100 üzerinden; üç bileşenin ağırlıklı toplamı.</p>

        <div className="mt-2">
          <Bilesen
            ad="Kısa vadeli"
            soru={`30 gün içinde ${d?.yaricapKm.kisa ?? 150} km'de M ≥ 4 olasılığı (model)`}
            deger={veri.metrics.shortRisk}
            agirlik={ag.kisa}
            dayanak={
              d?.kisaVadeKaynagi === 'yerel'
                ? `Son bir yılda yakında ${d.kisaVadeYerelDeprem} deprem.`
                : 'Yakında son bir yılda yeterli deprem yok.'
            }
            uyari={
              d?.kisaVadeKaynagi === 'ulke'
                ? 'Bu il için ülke genelinin son depremleri kullanıldı; bu bileşen burada anlamlı değil.'
                : 'Zayıf model: ROC-AUC 0,61 (yedi model kıyası). Tek başına karar verdirmez.'
            }
          />
          <Bilesen
            ad="Uzun vadeli"
            soru={`10 yılda ${d?.yaricapKm.uzun ?? 200} km'de en az bir M ≥ 6 olasılığı`}
            deger={veri.metrics.longHazard}
            agirlik={ag.uzun}
            dayanak={
              d ? `${katalogYil} kataloğunda ${d.uzunVadeAnaSok} ana şok (artçılar sayılmadı).` : 'Katalogdan.'
            }
          />
          <Bilesen
            ad="Fay etkisi"
            soru="En yakın etkin faya uzaklık"
            deger={veri.metrics.faultScore}
            agirlik={ag.fay}
            dayanak={`En yakın fay ${ondalik(veri.metrics.faultDistanceKm)} km (30 km altı tam puan, 150 km üstü %10).`}
          />
        </div>
      </Bolum>

      {!!veri.yakinFaylar?.length && (
        <Bolum baslik="Yakın faylar">
          <ul>
            {veri.yakinFaylar.map((f) => (
              <li key={f.kimlik} className="flex justify-between gap-2 border-b border-line py-1.5 text-small last:border-b-0">
                <span className="text-ink-2">{`${f.tur.charAt(0).toLocaleUpperCase('tr')}${f.tur.slice(1)} fay`}</span>
                <span className="font-mono text-ink">{ondalik(f.km)} km</span>
              </li>
            ))}
          </ul>
          <p className="mt-1 text-small text-ink-3">GEM Global Active Faults; veri setinde fay adı yok.</p>
        </Bolum>
      )}

      {!!veri.sonDepremler?.length && (
        <Bolum
          baslik="Yakındaki son depremler"
          ek={<Micro>{`${d?.yaricapKm.yakinDeprem ?? 150} km içinde`}</Micro>}
        >
          <ul>
            {veri.sonDepremler.map((o, i) => (
              <li key={`${o.time}-${i}`} className="flex items-baseline justify-between gap-2 border-b border-line py-1.5 last:border-b-0">
                <span className="font-mono text-small text-ink">{`M ${ondalik(o.magnitude)}`}</span>
                <span className="min-w-0 flex-1 truncate text-small text-ink-2">{o.place}</span>
                <span className="shrink-0 font-mono text-small text-ink-3">
                  {`${Math.round(o.distanceKm)} km · ${o.time.slice(0, 10)}`}
                </span>
              </li>
            ))}
          </ul>
        </Bolum>
      )}

      <Bolum baslik="Yöntem">
        <Teknik>
          Ağırlıklar (kısa %40, uzun %30, fay %30) uzman tanımlıdır, ölçülmüş değildir. Uzun vadeli
          bileşende artçılar Gardner–Knopoff pencereleriyle ayıklanır ve oran kataloğun bütün süresine
          bölünür. Katalog: Kandilli ve USGS{d ? `, ${d.katalogBasi} – ${d.katalogSonu}` : ''}. Fay
          mesafesi GEM Global Active Faults (CC BY-SA 4.0). Bu bir tehlike göstergesidir, deprem
          tahmini değildir.
        </Teknik>
      </Bolum>
    </>
  )
}
