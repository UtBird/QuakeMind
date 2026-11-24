import { useEffect, useMemo, useRef, useState } from 'react'
import { WarningCircle } from '@phosphor-icons/react'
import { Amac, Bolum, HazirSecenekler, SuAn, Teknik, VeriYok } from '@/kabuk/Panel'
import { Chip, Micro, Rozet } from '@/kabuk/parcalar'
import { useHarita } from '@/harita/HaritaKabugu'
import { useCozumleme } from '@/durum/cozumlemeDurumu'
import {
  DUZEY_ADI,
  RISK_TONU,
  alanKutusu,
  buyukluk,
  depremKimligi,
  depremYili,
  useRisk,
  useRiskSecimi,
  useRiskSiralamasi,
  useUlkeAnaSoklari,
  type RiskDeprem,
  type RiskDuzeyi,
  type RiskSirasi,
  type RiskYaniti,
} from '@/veri/risk'
import { sn } from '@/lib/sinif'

export { useRiskSiralamasi }

/* ---------------------------------------------------------------------------
   Deprem riski (J-173; baştan düzen J-191).

   Sorusu: hangi ilde büyük deprem tehlikesi yüksek, NEDEN?
   · Sol: 81 il riske göre sıralı, düzeye göre süzülür.
   · Harita, il seçilmemişken: il merkezleri skor renginde (sayı içinde) ve
     Türkiye'nin 1933'ten beri M≥6 ana şokları (halka, çap = büyüklük).
   · İl seçilince: yalnız o ilin skoruna giren depremler. 200 km içindeki M≥6
     ana şoklar (yılıyla) ve 150 km içinde son bir yılın depremleri; hesap alanı
     ince kesik çizgi. Eskiden ülke kataloğunun binlerce dairesi ve iki dev
     dolu daire birlikte çiziliyordu; neyin skora girdiği okunmuyordu.
   · Sağ: olasılıklar düz cümleyle, sonra dayanakları (deprem listesi tıklanır).
   Hesap sunucuda (`risk_hizmeti.py`), model dosyadan yüklenir.
--------------------------------------------------------------------------- */

const TON_ZEMIN = { crit: 'bg-crit', high: 'bg-high', mid: 'bg-mid', ok: 'bg-ok' } as const
const DUZEYLER: RiskDuzeyi[] = ['crit', 'high', 'mid', 'ok']

const OPERASYON = [
  { id: 'Hatay', etiket: 'Antakya (Hatay)' },
  { id: 'Kahramanmaraş', etiket: 'Kahramanmaraş' },
  { id: 'Gaziantep', etiket: 'Gaziantep' },
  { id: 'Malatya', etiket: 'Malatya' },
  { id: 'Adıyaman', etiket: 'Adıyaman' },
] as const

/** Türkiye kutusu [batı, güney, doğu, kuzey]. */
const TURKIYE: [number, number, number, number] = [25.6, 35.8, 44.8, 42.1]

const yuzde = (x: number) => `%${Math.round(x * 100)}`
const ondalik = (x: number, b = 1) => x.toFixed(b).replace('.', ',')

/** Seçili il (mağazada `il:<ad>`); sol ve sağ panel ile harita paylaşır. */
export function useSeciliRiskIli(siralama: RiskSirasi[] | undefined): RiskSirasi | null {
  const secim = useCozumleme((d) => d.riskBolge)
  return useMemo(() => {
    const ad = secim?.startsWith('il:') ? secim.slice(3) : null
    return (ad && siralama?.find((x) => x.il === ad)) || null
  }, [secim, siralama])
}

/** İl seçimi: harita ilin 200 km'lik hesap alanına sığar. */
export function useIlSec() {
  const sec = useCozumleme((d) => d.riskBolgeSec)
  const depremSec = useRiskSecimi((d) => d.depremSec)
  const { kutuyaUc } = useHarita()
  return (il: RiskSirasi) => {
    sec(`il:${il.il}`)
    depremSec(null)
    kutuyaUc(alanKutusu(il.lon, il.lat, 210))
  }
}

export function RiskSol() {
  const siralama = useRiskSiralamasi()
  const secili = useSeciliRiskIli(siralama.data?.iller)
  const ilSec = useIlSec()
  const { duzey, duzeySec } = useRiskSecimi()
  const [ara, setAra] = useState('')
  const { kutuyaUc, hazir } = useHarita()

  // Moda girince harita sorunun ölçeğine gelir: il seçili değilse Türkiye,
  // seçiliyse ilin hesap alanı. Yalnız açılışta, harita hazır olunca (sonra
  // kullanıcı gezer).
  const ilkSecili = useState(secili)[0]
  const uculdu = useRef(false)
  useEffect(() => {
    if (!hazir || uculdu.current) return
    uculdu.current = true
    kutuyaUc(ilkSecili ? alanKutusu(ilkSecili.lon, ilkSecili.lat, 210) : TURKIYE)
  }, [hazir, ilkSecili, kutuyaUc])

  useEffect(() => {
    if (secili) document.getElementById(`risk-il-${secili.il}`)?.scrollIntoView({ block: 'nearest' })
  }, [secili])

  const sayilar = useMemo(() => {
    const s: Record<RiskDuzeyi, number> = { crit: 0, high: 0, mid: 0, ok: 0 }
    for (const x of siralama.data?.iller ?? []) s[RISK_TONU(x.skor)] += 1
    return s
  }, [siralama.data])

  const liste = useMemo(() => {
    const a = ara.trim().toLocaleLowerCase('tr')
    return (siralama.data?.iller ?? [])
      .map((x, i) => ({ ...x, sira: i + 1 }))
      .filter((x) => !duzey || RISK_TONU(x.skor) === duzey)
      .filter((x) => !a || x.il.toLocaleLowerCase('tr').includes(a))
  }, [siralama.data, ara, duzey])

  return (
    <Bolum baslik="Deprem riski" ek={<Micro>81 il</Micro>}>
      <Amac>
        Hangi ilde büyük deprem tehlikesi yüksek, neden? Bir il seç: skoru belirleyen geçmiş
        depremler haritada, olasılıklar ve dayanakları sağda.
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

      <div className="mt-3">
        <Micro>Düzeye göre</Micro>
        <div role="group" aria-label="Düzeye göre süz" className="mt-1.5 flex flex-wrap gap-1.5">
          {DUZEYLER.map((d) => (
            <Chip key={d} secili={duzey === d} onClick={() => duzeySec(duzey === d ? null : d)}>
              <span className="flex items-center gap-1.5">
                <span aria-hidden className={sn('h-2 w-2 rounded-full', TON_ZEMIN[d])} />
                {`${DUZEY_ADI[d]} · ${sayilar[d]}`}
              </span>
            </Chip>
          ))}
        </div>
      </div>

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
          {!siralama.isPending && liste.length === 0 && (
            <li className="px-2.5 py-2 text-small text-ink-3">Bu süzgeçte il yok.</li>
          )}
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
          ? `${secili.il}: skor ${Math.round(secili.skor)}, ${secili.seviye.toLocaleLowerCase('tr')}. Haritada yalnız bu ilin hesabına giren depremler var.`
          : 'Listeden ya da haritadan bir il seç. Haritadaki halkalar Türkiye’nin geçmişteki M≥6 depremleri.'}
      </SuAn>

      <Teknik>
        Skor il merkezinde hesaplanır, ilin tamamı için değil. Model istek yolunda eğitilmez; sonuç
        veri değişmedikçe sunucuda saklanır (ilk sıralama ~2 sn, sonra anında).
      </Teknik>
    </Bolum>
  )
}

/* ---- sağ panel -------------------------------------------------------------- */

export function RiskSag() {
  const siralama = useRiskSiralamasi()
  const secili = useSeciliRiskIli(siralama.data?.iller)
  const risk = useRisk(secili)
  if (!secili) return <UlkeGorunumu />
  if (!risk.data) {
    return (
      <Bolum baslik={secili.il}>
        <p className="text-small text-ink-3">{risk.isError ? 'Risk hesaplanamadı.' : 'Hesaplanıyor…'}</p>
      </Bolum>
    )
  }
  return <RiskSonucu veri={risk.data} />
}

/** Harita lejantı: neyi nasıl okuyacağız. */
function Okuma({ ilSecili }: { ilSecili: boolean }) {
  return (
    <ul className="space-y-1.5 text-small text-ink-2">
      <li className="flex items-center gap-2">
        <span aria-hidden className="grid h-4 w-4 shrink-0 place-items-center rounded-full bg-high" />
        İl merkezi; içindeki sayı risk skoru, renk düzeyi
      </li>
      <li className="flex items-center gap-2">
        <span aria-hidden className="h-4 w-4 shrink-0 rounded-full border-2 border-deprem" />
        {ilSecili ? '200 km içindeki M≥6 ana şok; çap büyüklük' : 'M≥6 ana şok (1933’ten beri); çap büyüklük'}
      </li>
      {ilSecili && (
        <li className="flex items-center gap-2">
          <span aria-hidden className="mx-1 h-2 w-2 shrink-0 rounded-full bg-deprem" />
          Son bir yılın depremi (150 km içinde)
        </li>
      )}
      {ilSecili && (
        <li className="flex items-center gap-2">
          <span aria-hidden className="w-4 shrink-0 border-t-2 border-dashed border-ink-3" />
          İlin hesap alanı (200 km)
        </li>
      )}
      <li className="flex items-center gap-2">
        <span aria-hidden className="w-4 shrink-0 border-t-2 border-dashed border-fay" />
        Etkin fay (GEM)
      </li>
    </ul>
  )
}

function DepremSatiri({ d, uzaklik }: { d: RiskDeprem; uzaklik: boolean }) {
  const { deprem, depremSec } = useRiskSecimi()
  const { ucus } = useHarita()
  const id = depremKimligi(d)
  const secili = deprem === id
  return (
    <li>
      <button
        type="button"
        aria-pressed={secili}
        onClick={() => {
          depremSec(secili ? null : id)
          if (!secili) ucus(d.longitude, d.latitude, 8)
        }}
        className={sn(
          'flex w-full items-baseline gap-2 border-b border-line px-1 py-1.5 text-left last:border-b-0',
          secili ? 'bg-raised' : 'hover:bg-hover',
        )}
      >
        <span className="w-10 shrink-0 font-mono text-small text-ink-3">{depremYili(d)}</span>
        <span className="w-12 shrink-0 font-mono text-small text-ink">{`M ${buyukluk(d.magnitude)}`}</span>
        <span className="min-w-0 flex-1 truncate text-small text-ink-2" title={d.place}>
          {d.place}
        </span>
        {uzaklik && d.distanceKm != null && (
          <span className="shrink-0 font-mono text-small text-ink-3">{`${Math.round(d.distanceKm)} km`}</span>
        )}
      </button>
    </li>
  )
}

function UlkeGorunumu() {
  const ana = useUlkeAnaSoklari(true)
  const [hepsi, setHepsi] = useState(false)
  const liste = ana.data?.depremler ?? []
  return (
    <>
      <Bolum baslik="Türkiye’nin büyük depremleri">
        <Amac>
          Haritadaki halkalar 1933’ten bu yana M≥6 ana şoklar; artçılar ayıklandı, çap büyüklüğü
          gösterir. Uzun vadeli tehlike bunlardan hesaplanır. Bir il seçince yalnız o ilin hesabına
          giren depremler kalır.
        </Amac>
        {ana.isError ? (
          <div className="mt-2">
            <VeriYok ne="Deprem kataloğu" neden="sunucu kataloğu yükleyemedi" />
          </div>
        ) : ana.isPending ? (
          <p className="mt-2 text-small text-ink-3">Yükleniyor…</p>
        ) : (
          <>
            <p className="mt-2 text-small text-ink-2">
              {`${liste.length} ana şok · katalog ${ana.data.katalogBasi.slice(0, 4)}–${ana.data.katalogSonu.slice(0, 4)} (Kandilli, USGS)`}
            </p>
            <ul className="mt-1.5 border-t border-line">
              {(hepsi ? liste : liste.slice(0, 10)).map((d) => (
                <DepremSatiri key={depremKimligi(d)} d={d} uzaklik={false} />
              ))}
            </ul>
            {liste.length > 10 && (
              <button
                type="button"
                onClick={() => setHepsi(!hepsi)}
                className="mt-1.5 text-small text-ink-3 hover:text-ink"
              >
                {hepsi ? 'En büyük 10' : `Hepsini göster (${liste.length})`}
              </button>
            )}
          </>
        )}
      </Bolum>
      <Bolum baslik="Haritayı okuma">
        <Okuma ilSecili={false} />
      </Bolum>
    </>
  )
}

function Olasilik({
  soru,
  deger,
  dayanak,
  uyari,
  agirlik,
}: {
  soru: string
  deger: string
  dayanak: string
  uyari?: string | null
  agirlik: number
}) {
  return (
    <div className="border-t border-line py-2.5 first:border-t-0">
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-body text-ink">{soru}</span>
        <span className="shrink-0 font-mono text-subtitle text-ink">{deger}</span>
      </div>
      <p className="mt-0.5 text-small text-ink-2">
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
  const yaricap = d?.yaricapKm ?? { kisa: 150, uzun: 200, yakinDeprem: 150 }
  const katalogYil = d ? `${d.katalogBasi.slice(0, 4)}–${d.katalogSonu.slice(0, 4)}` : null
  const yilSayisi = d ? Number(d.katalogSonu.slice(0, 4)) - Number(d.katalogBasi.slice(0, 4)) : null
  const ana = veri.anaSoklar ?? []
  const sonYil = veri.sonYilDepremler ?? []
  const [anaHepsi, setAnaHepsi] = useState(false)
  return (
    <>
      <Bolum baslik={veri.city} ek={<Rozet ton={RISK_TONU(veri.riskScore)}>{veri.riskLevel}</Rozet>}>
        <div className="flex items-baseline gap-2">
          <p className="font-cond text-metric text-ink">{Math.round(veri.riskScore)}</p>
          <p className="text-small text-ink-3">/ 100 · üç bileşenin ağırlıklı toplamı</p>
        </div>

        <div className="mt-2">
          <Olasilik
            soru={`10 yılda, ${yaricap.uzun} km içinde M≥6 deprem`}
            deger={yuzde(veri.metrics.longHazard)}
            agirlik={ag.uzun}
            dayanak={
              d
                ? `${katalogYil} arasında (${yilSayisi} yıl) bu alanda ${d.uzunVadeAnaSok} ana şok oldu; olasılık bu sıklıktan (Poisson).`
                : 'Katalogdaki sıklıktan.'
            }
          />
          <Olasilik
            soru={`30 günde, ${yaricap.kisa} km içinde M≥4 deprem`}
            deger={yuzde(veri.metrics.shortRisk)}
            agirlik={ag.kisa}
            dayanak={
              d?.kisaVadeKaynagi === 'yerel'
                ? `Model, son bir yılın ${d.kisaVadeYerelDeprem} depreminden tahmin ediyor.`
                : 'Yakında son bir yılda yeterli deprem yok.'
            }
            uyari={
              d?.kisaVadeKaynagi === 'ulke'
                ? 'Bu il için ülke genelinin son depremleri kullanıldı; bu bileşen burada anlamlı değil.'
                : 'Zayıf model: ROC-AUC 0,61 (yedi model kıyası). Tek başına karar verdirmez.'
            }
          />
          <Olasilik
            soru="En yakın etkin fay"
            deger={`${ondalik(veri.metrics.faultDistanceKm)} km`}
            agirlik={ag.fay}
            dayanak={`Fay puanı ${yuzde(veri.metrics.faultScore)}: 30 km altı tam puan, 150 km üstü %10.`}
          />
        </div>
      </Bolum>

      <Bolum
        baslik="Geçmişteki büyük depremler"
        ek={<Micro>{`${yaricap.uzun} km · M≥6 · ${ana.length}`}</Micro>}
      >
        {ana.length === 0 ? (
          <p className="text-small text-ink-3">
            {`${katalogYil ?? 'Katalogda'} bu alanda M≥6 ana şok yok; uzun vadeli olasılık en düşük değerde.`}
          </p>
        ) : (
          <>
            <p className="text-small text-ink-2">Uzun vadeli olasılığın dayanağı. Satıra tıkla: haritada göster.</p>
            <ul className="mt-1.5 border-t border-line">
              {(anaHepsi ? ana : ana.slice(0, 8)).map((x) => (
                <DepremSatiri key={depremKimligi(x)} d={x} uzaklik />
              ))}
            </ul>
            {ana.length > 8 && (
              <button
                type="button"
                onClick={() => setAnaHepsi(!anaHepsi)}
                className="mt-1.5 text-small text-ink-3 hover:text-ink"
              >
                {anaHepsi ? 'En büyük 8' : `Hepsini göster (${ana.length})`}
              </button>
            )}
          </>
        )}
      </Bolum>

      <Bolum baslik="Son bir yıl" ek={<Micro>{`${yaricap.kisa} km`}</Micro>}>
        {sonYil.length === 0 ? (
          <p className="text-small text-ink-3">Son bir yılda bu alanda kayıtlı deprem yok.</p>
        ) : (
          <>
            <p className="text-small text-ink-2">
              {`${d?.kisaVadeYerelDeprem ?? sonYil.length} deprem; en büyüğü M ${buyukluk(sonYil[0].magnitude)}. Kısa vadeli tahminin girdisi.`}
            </p>
            <ul className="mt-1.5 border-t border-line">
              {sonYil.slice(0, 5).map((x) => (
                <DepremSatiri key={depremKimligi(x)} d={x} uzaklik />
              ))}
            </ul>
          </>
        )}
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

      <Bolum baslik="Haritayı okuma">
        <Okuma ilSecili />
      </Bolum>

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
