import type { ReactNode } from 'react'
import { Crosshair, WarningCircle } from '@phosphor-icons/react'
import { Micro, Rozet } from '@/kabuk/parcalar'
import { sn } from '@/lib/sinif'
import { useHarita } from '@/harita/HaritaKabugu'
import { IHTIYAC_ADI } from '@/veri/sorgular'
import { IHTIYAC_IKONU } from '@/veri/ihbarIkon'
import type { MetinAnalizi } from '@/veri/ihbar'
import type { MetinSonucu } from '@/durum/cozumlemeDurumu'
import {
  DUZEY_ADI,
  KATEGORI_KAYNAGI,
  belirsizlikMetni,
  duzeyAciklamasi,
  konumYeterli,
  type AdresEslesmesi,
  type IhtiyacBilgisi,
  type KategoriUyarisi,
  type KisiBilgisi,
  type KonumDuzeyi,
  type SinyalBilgisi,
} from '@/veri/metin'

/* ---------------------------------------------------------------------------
   Metin analizinin sonuç kartı (J-170). Afetzedenin yazılı ihbarı ve
   konsoldaki deneme analizi aynı kartla görünür.

   Sıra koordinatörün soru sırasıdır: ne oldu ve ne kadar acil → model nerede
   kararsız → metnin kendisi (bulunan her şey metnin içinde işaretli) → ekip
   nereye gidecek ve o yer ne kadar kesin → kaç kişi, ne lazım → künye.
--------------------------------------------------------------------------- */

export const ACILIYET_TONU = (n: number) => (n >= 5 ? 'crit' : n >= 4 ? 'high' : n >= 3 ? 'mid' : 'ok')

/** İki kaynağın ortak görünümü. */
export type MetinGorunumu = {
  ilgisiz: boolean
  kategori: string | null
  aciliyet: number | null
  guven: number | null
  kategoriKaynagi: string | null
  ikinciKategori: { kategori: string; puan: number } | null
  uyarilar: KategoriUyarisi[]
  /** [enlem, boylam] */
  konum: [number, number] | null
  konumMetin: string | null
  konumDuzeyi: KonumDuzeyi | null
  belirsizlikM: number | null
  adresNotlari: string[]
  adresEslesmeleri: AdresEslesmesi[]
  adaylar: string[]
  kisiler: KisiBilgisi[]
  ihtiyaclar: IhtiyacBilgisi[]
  sinyaller: SinyalBilgisi[]
  /** J-170 öncesi ihbar: düzey, vurgu ve çıkarım yok. */
  eski: boolean
  sureMs?: number
  modelAdi?: string
}

export function ihbarGorunumu(a: MetinAnalizi): MetinGorunumu {
  return {
    ilgisiz: a.ilgisiz,
    kategori: a.kategori,
    aciliyet: a.aciliyet,
    guven: a.guven,
    kategoriKaynagi: a.kategoriKaynagi ?? null,
    ikinciKategori: a.ikinciKategori ?? null,
    uyarilar: a.kategoriUyarilari ?? [],
    konum: a.konum ? [a.konum.lat, a.konum.lon] : null,
    konumMetin: a.konumMetin,
    konumDuzeyi: a.konumDuzeyi ?? null,
    belirsizlikM: a.belirsizlikM ?? null,
    adresNotlari: a.adresNotlari ?? [],
    adresEslesmeleri: a.adresEslesmeleri ?? [],
    adaylar: a.adaylar ?? [],
    kisiler: a.kisiler ?? [],
    ihtiyaclar: a.ihtiyaclar ?? [],
    sinyaller: a.sinyaller ?? [],
    eski: a.konumDuzeyi === undefined && a.sinyaller === undefined,
  }
}

export function denemeGorunumu(s: MetinSonucu): MetinGorunumu {
  return {
    ilgisiz: !s.ilgili,
    kategori: s.ilgili ? s.kategori : null,
    aciliyet: s.aciliyet,
    guven: s.guven,
    kategoriKaynagi: s.kategoriKaynagi,
    ikinciKategori: s.ikinciKategori,
    uyarilar: s.kategoriUyarilari,
    konum: s.konum,
    konumMetin: s.konumMetin,
    konumDuzeyi: s.konumDuzeyi,
    belirsizlikM: s.belirsizlikM,
    adresNotlari: s.adresNotlari,
    adresEslesmeleri: s.adresEslesmeleri,
    adaylar: s.adresAdaylari.map((a) => a.konumMetin),
    kisiler: s.kisiler,
    ihtiyaclar: s.ihtiyaclar,
    sinyaller: s.sinyaller,
    eski: false,
    sureMs: s.sureMs,
    modelAdi: s.model?.siniflandirici,
  }
}

/** Kuyrukta "kontrol et" işareti: koordinatörün gözüyle bakması gereken ihbar. */
export function kontrolNedeni(g: MetinGorunumu | null): string | null {
  if (!g) return 'model incelemedi'
  if (g.ilgisiz) return 'model afetle ilgisiz buldu'
  if (g.uyarilar.length) return 'kategori metinle çelişiyor'
  if (g.kategori === 'Belirsiz') return 'model kararsız'
  if (!g.eski && !konumYeterli(g.konumDuzeyi)) return g.konumDuzeyi ? 'adres yalnız bölge düzeyinde' : 'metinde adres yok'
  return null
}

const yuzde = (x: number) => `%${Math.round(x * 100)}`

/* ---- vurgulu metin ------------------------------------------------------- */

type VurguTuru = 'adres' | 'sinyal' | 'kisi' | 'ihtiyac'

const VURGU: Record<VurguTuru, { ad: string; sinif: string; isaret: string }> = {
  adres: { ad: 'Adres', sinif: 'bg-accent-soft border-accent', isaret: 'bg-accent' },
  sinyal: { ad: 'Aciliyet işareti', sinif: 'bg-high/15 border-high', isaret: 'bg-high' },
  kisi: { ad: 'Kişi', sinif: 'bg-ihbar-metin/15 border-ihbar-metin', isaret: 'bg-ihbar-metin' },
  ihtiyac: { ad: 'İhtiyaç', sinif: 'bg-ihbar-ihtiyac/15 border-ihbar-ihtiyac', isaret: 'bg-ihbar-ihtiyac' },
}

type Vurgu = { bas: number; son: number; tur: VurguTuru; baslik: string }

function vurgular(metin: string, g: MetinGorunumu): Vurgu[] {
  const ham: Vurgu[] = [
    ...g.adresEslesmeleri.map((e) => ({ ...e, tur: 'adres' as const, baslik: `Adres (${e.tur})` })),
    ...g.kisiler.map((k) => ({ ...k, tur: 'kisi' as const, baslik: `${k.sayi} ${k.ne}` })),
    ...g.sinyaller.map((s) => ({ ...s, tur: 'sinyal' as const, baslik: s.ad })),
    ...g.ihtiyaclar.map((i) => ({ ...i, tur: 'ihtiyac' as const, baslik: IHTIYAC_ADI[i.ihtiyac] ?? i.ihtiyac })),
  ]
    // Aralık metne denk düşmüyorsa (metin sonradan değiştiyse) işaretlenmez.
    .filter((v) => v.son > v.bas && metin.slice(v.bas, v.son) === (v as unknown as { metin: string }).metin)
    .map(({ bas, son, tur, baslik }) => ({ bas, son, tur, baslik }))
    .sort((a, b) => a.bas - b.bas || b.son - a.son)
  // Çakışanlardan önce başlayan (eşitse uzun olan) kalır.
  const out: Vurgu[] = []
  for (const v of ham) if (!out.length || v.bas >= out[out.length - 1].son) out.push(v)
  return out
}

export function VurguluMetin({ metin, g }: { metin: string; g: MetinGorunumu }) {
  const liste = vurgular(metin, g)
  const parcalar: ReactNode[] = []
  let i = 0
  for (const v of liste) {
    if (v.bas > i) parcalar.push(metin.slice(i, v.bas))
    parcalar.push(
      <mark key={v.bas} title={v.baslik} className={sn('border-b-2 px-0.5 text-ink', VURGU[v.tur].sinif)}>
        {metin.slice(v.bas, v.son)}
      </mark>,
    )
    i = v.son
  }
  if (i < metin.length) parcalar.push(metin.slice(i))
  const turler = [...new Set(liste.map((v) => v.tur))]
  return (
    <>
      <blockquote className="rounded-control border border-line-2 bg-sunken px-2.5 py-2 text-body leading-relaxed whitespace-pre-line text-ink">
        {parcalar}
      </blockquote>
      {turler.length > 0 && (
        <ul aria-label="İşaretlerin anlamı" className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-small text-ink-3">
          {turler.map((t) => (
            <li key={t} className="flex items-center gap-1.5">
              <span aria-hidden className={sn('h-2 w-2 rounded-full', VURGU[t].isaret)} />
              {VURGU[t].ad}
            </li>
          ))}
        </ul>
      )}
    </>
  )
}

/* ---- kart ---------------------------------------------------------------- */

/** Belirsizlik çemberi ekrana sığsın diye düzeye göre yakınlaşma. */
const UCUS_ZOOM: Record<KonumDuzeyi, number> = {
  sokak: 15.5,
  mahalle: 14,
  koy: 13.5,
  kasaba: 13,
  sehir: 12,
  ilce: 11,
  il: 8,
}

export function ucusZoom(d: KonumDuzeyi | null | undefined): number {
  return d ? UCUS_ZOOM[d] : 15
}

export function MetinSonucKarti({
  metin,
  g,
  konumNotu,
}: {
  metin: string
  g: MetinGorunumu | null
  /** Konum kartının altında: ihbarın konumu metinden mi, cihazdan mı geldi. */
  konumNotu?: ReactNode
}) {
  if (!g) {
    return (
      <>
        <blockquote className="rounded-control border border-line-2 bg-sunken px-2.5 py-2 text-body whitespace-pre-line text-ink">
          {metin}
        </blockquote>
        <p className="mt-2 text-small text-ink-2">
          Model incelemedi (afetzede incelemeden gönderdi). Kategori, aciliyet ve adres yok; metni okuyun.
        </p>
        {konumNotu}
      </>
    )
  }

  return (
    <div className="grid gap-3">
      <Karar g={g} />
      {g.uyarilar.map((u) => (
        <p
          key={u.onerilen}
          role="note"
          className="flex items-start gap-2 rounded-control border border-high px-2.5 py-2 text-small text-ink"
        >
          <WarningCircle size={16} weight="bold" className="mt-0.5 shrink-0 text-high" aria-hidden />
          <span>{u.metin}</span>
        </p>
      ))}
      <div>
        <VurguluMetin metin={metin} g={g} />
      </div>
      <KonumKarti g={g} not={konumNotu} />
      {!g.eski && <Cikarilanlar g={g} />}
      <Kunye g={g} />
    </div>
  )
}

function Karar({ g }: { g: MetinGorunumu }) {
  if (g.ilgisiz) {
    return (
      <div>
        <p className="text-subtitle text-ink">Model: afetle ilgisiz</p>
        <p className="mt-0.5 text-small text-ink-2">
          Model bu metni afet ihbarı saymadı{g.guven != null ? ` (güven ${yuzde(g.guven)})` : ''}. Yanılıyor olabilir;
          metni okuyun.
        </p>
      </div>
    )
  }
  return (
    <div>
      <div className="flex items-start justify-between gap-2">
        <p className="text-subtitle text-ink">{g.kategori ?? '—'}</p>
        {g.aciliyet != null ? (
          <Rozet ton={ACILIYET_TONU(g.aciliyet)}>{`aciliyet ${g.aciliyet}/5`}</Rozet>
        ) : (
          <Rozet ton="nötr">aciliyet yok</Rozet>
        )}
      </div>
      <p className="mt-0.5 text-small text-ink-2">
        {[
          g.guven != null ? `Model güveni ${yuzde(g.guven)}` : null,
          g.kategoriKaynagi && g.kategoriKaynagi !== 'model'
            ? `karar: ${KATEGORI_KAYNAGI[g.kategoriKaynagi] ?? g.kategoriKaynagi}`
            : null,
          g.ikinciKategori ? `ikinci olasılık ${g.ikinciKategori.kategori} (${yuzde(g.ikinciKategori.puan)})` : null,
        ]
          .filter(Boolean)
          .join(' · ')}
      </p>
      {g.aciliyet == null && (
        <p className="mt-0.5 text-small text-ink-3">Model kategoride kararsız kaldığı için aciliyet verilmedi.</p>
      )}
    </div>
  )
}

function KonumKarti({ g, not }: { g: MetinGorunumu; not?: ReactNode }) {
  const { ucus } = useHarita()
  const d = g.konumDuzeyi
  const yeterli = konumYeterli(d)
  return (
    <section aria-label="Metindeki adres" className="rounded-control border border-line-2 px-2.5 py-2">
      <div className="flex items-center justify-between gap-2">
        <Micro>Metindeki adres</Micro>
        {d && <Rozet ton={yeterli ? 'accent' : 'nötr'}>{`${DUZEY_ADI[d]} düzeyi`}</Rozet>}
      </div>
      {g.konum ? (
        <>
          <p className="mt-1.5 text-body text-ink">{g.konumMetin ?? 'adres bulundu'}</p>
          <p className="mt-0.5 text-small text-ink-2">
            {[
              belirsizlikMetni(g.belirsizlikM) && `${belirsizlikMetni(g.belirsizlikM)} sapabilir`,
              g.adresNotlari.length ? null : duzeyAciklamasi(d),
            ]
              .filter(Boolean)
              .join('. ')}
          </p>
          <button
            type="button"
            onClick={() => ucus(g.konum![1], g.konum![0], ucusZoom(d))}
            className="mt-2 flex items-center gap-1.5 rounded-control border border-line-2 px-2 py-1.5 text-small text-ink-2 hover:bg-hover hover:text-ink"
          >
            <Crosshair size={14} aria-hidden /> Haritada göster
          </button>
        </>
      ) : (
        <p className="mt-1.5 text-body text-ink-2">
          {g.eski ? (g.konumMetin ?? 'Metinde adres bulunamadı.') : 'Metinde adres dizininde bulunan bir yer yok.'}
        </p>
      )}
      {g.adresNotlari.length > 0 && (
        <ul className="mt-2 grid gap-1">
          {g.adresNotlari.map((n) => (
            <li key={n} className="text-small text-ink-3">
              {n}
            </li>
          ))}
        </ul>
      )}
      {g.adaylar.length > 0 && (
        <div className="mt-2">
          <Micro>Aynı adlı yerler</Micro>
          <ul className="mt-1">
            {g.adaylar.slice(0, 5).map((a) => (
              <li key={a} className="border-t border-line py-1 text-small text-ink-2">
                {a}
              </li>
            ))}
          </ul>
        </div>
      )}
      {not}
    </section>
  )
}

function Cikarilanlar({ g }: { g: MetinGorunumu }) {
  const ihtiyaclar = [...new Set(g.ihtiyaclar.map((i) => i.ihtiyac))]
  const sinyaller = [...new Map(g.sinyaller.map((s) => [s.sinyal, s.ad])).values()]
  if (!g.kisiler.length && !ihtiyaclar.length && !sinyaller.length) {
    return <p className="text-small text-ink-3">Metinde kişi sayısı, ihtiyaç ya da aciliyet işareti geçmiyor.</p>
  }
  return (
    <dl className="kilav-kv gap-x-2.5 gap-y-1.5 text-small">
      {g.kisiler.length > 0 && (
        <>
          <dt className="text-ink-3">Kişi</dt>
          <dd className="text-ink">{g.kisiler.map((k) => `${k.sayi} ${k.ne}`).join(', ')}</dd>
        </>
      )}
      {sinyaller.length > 0 && (
        <>
          <dt className="text-ink-3">İşaretler</dt>
          <dd className="text-ink">{sinyaller.join(', ')}</dd>
        </>
      )}
      {ihtiyaclar.length > 0 && (
        <>
          <dt className="text-ink-3">İhtiyaç</dt>
          <dd>
            <ul className="flex flex-wrap gap-1.5">
              {ihtiyaclar.map((i) => {
                const Ikon = IHTIYAC_IKONU[i]
                return (
                  <li
                    key={i}
                    className="flex items-center gap-1 rounded-control border border-ihbar-ihtiyac px-1.5 py-0.5 text-small text-ink"
                  >
                    {Ikon && <Ikon size={14} className="text-ihbar-ihtiyac" aria-hidden />}
                    {IHTIYAC_ADI[i] ?? i}
                  </li>
                )
              })}
            </ul>
          </dd>
        </>
      )}
    </dl>
  )
}

function Kunye({ g }: { g: MetinGorunumu }) {
  return (
    <p className="text-small leading-relaxed text-ink-3">
      {g.eski
        ? 'Bu ihbar eski çözümleyiciyle incelendi: adres düzeyi, işaretler ve kişi sayısı yok.'
        : [
            `Kategori: BERTurk sınıflandırıcı${g.modelAdi ? ` (${g.modelAdi})` : ''}, modelin tahmini.`,
            'Adres: yerel adres dizini (OpenStreetMap); metin dışarı gönderilmez.',
            'Kişi, ihtiyaç ve işaretler sözcük kurallarıyla bulunur.',
            g.sureMs != null ? `Süre ${g.sureMs} ms.` : null,
          ]
            .filter(Boolean)
            .join(' ')}
    </p>
  )
}
