import { useCallback, useMemo } from 'react'
import { create } from 'zustand'
import { Amac, Bolum, HazirSecenekler, SuAn, Teknik, VeriYok } from '@/kabuk/Panel'
import { Micro } from '@/kabuk/parcalar'
import { useSorguAraligi } from '@/durum/zamanDurumu'
import { sayi } from '@/lib/bicim'
import { sn } from '@/lib/sinif'
import { IHTIYAC_ADI, type Ihtiyac } from '@/veri/sorgular'
import { IHTIYAC_SIRASI, ihtiyacTalebiMi, useIhbarlar, type Ihbar } from '@/veri/ihbar'
import { IHTIYAC_IKONU } from '@/veri/ihbarIkon'
import { GelenIhbarlar } from './ihbarParcalari'

/* ---------------------------------------------------------------------------
   İhtiyaç talepleri modu (J-51). Afetzede ekranındaki "İhtiyaç bildir"
   talepleri burada durur: su, gıda, barınma, ısınma, ilaç, hijyen. Hayati
   tehlike içeren çağrılar SOS kuyruğundadır; talepler hasar olmadığı için ısı
   haritasına yazılmaz.
--------------------------------------------------------------------------- */

const SUZGECLER = [
  { id: 'acik', etiket: 'Açık talepler' },
  { id: 'yeni', etiket: 'Yeni gelenler' },
  { id: 'tum', etiket: 'Tümü' },
] as const
type SuzgecId = (typeof SUZGECLER)[number]['id']

const useIhtiyacSuzgeci = create<{
  suzgec: SuzgecId
  ihtiyac: Ihtiyac | null
  suzgecSec: (s: SuzgecId) => void
  ihtiyacSec: (i: Ihtiyac | null) => void
}>((set) => ({
  suzgec: 'acik',
  ihtiyac: null,
  suzgecSec: (suzgec) => set({ suzgec }),
  ihtiyacSec: (ihtiyac) => set({ ihtiyac }),
}))

function durumaUyar(i: Ihbar, s: SuzgecId): boolean {
  if (s === 'acik') return i.durum !== 'kapandi'
  if (s === 'yeni') return i.durum === 'yeni'
  return true
}

export function IhtiyacSol() {
  const aralik = useSorguAraligi()
  const ihbar = useIhbarlar(aralik)
  const { suzgec, ihtiyac, suzgecSec, ihtiyacSec } = useIhtiyacSuzgeci()

  const talepler = useMemo(
    () => (ihbar.data ?? []).filter((i) => ihtiyacTalebiMi(i) && durumaUyar(i, suzgec)),
    [ihbar.data, suzgec],
  )
  // İhtiyaç başına talep ve kişi sayısı: listenin sayımı, sunucuda hesap yok.
  const dokum = useMemo(
    () =>
      IHTIYAC_SIRASI.map((t) => {
        const ilgili = talepler.filter((i) => i.ihtiyaclar?.includes(t))
        return { t, talep: ilgili.length, kisi: ilgili.reduce((n, i) => n + (i.kisiSayisi ?? 0), 0) }
      }),
    [talepler],
  )
  const enCok = [...dokum].sort((a, b) => b.talep - a.talep)[0]
  const toplamKisi = talepler.reduce((n, i) => n + (i.kisiSayisi ?? 0), 0)

  return (
    <Bolum baslik="İhtiyaç talepleri" ek={<Micro>afetzede ekranından</Micro>}>
      <Amac>
        Nerede ne eksik? Afetzedelerin su, gıda, barınma, ısınma, ilaç ve hijyen talepleri. Hayati
        tehlike içeren çağrılar SOS kuyruğundadır.
      </Amac>

      <HazirSecenekler etiket="Talep süzgeci" secenekler={SUZGECLER} secili={suzgec} onSec={suzgecSec} />

      <div className="mt-3">
        <Micro className="block">İhtiyaca göre · tıkla, listeyi daralt</Micro>
        <ul className="mt-1.5">
          {dokum.map(({ t, talep, kisi }) => {
            const Ikon = IHTIYAC_IKONU[t]
            const secili = ihtiyac === t
            return (
              <li key={t}>
                <button
                  type="button"
                  aria-pressed={secili}
                  onClick={() => ihtiyacSec(secili ? null : t)}
                  className={sn(
                    'flex w-full items-center gap-2.5 rounded-control px-2 py-1.5 text-left text-small',
                    secili ? 'bg-ihbar-ihtiyac/15 text-ink' : 'text-ink-2 hover:bg-hover hover:text-ink',
                  )}
                >
                  <Ikon size={16} className="shrink-0 text-ihbar-ihtiyac" aria-hidden />
                  <span className="flex-1">{IHTIYAC_ADI[t]}</span>
                  <span className="font-mono whitespace-nowrap">
                    {sayi(talep)} talep{kisi ? ` · ${sayi(kisi)} kişi` : ''}
                  </span>
                </button>
              </li>
            )
          })}
        </ul>
      </div>

      <SuAn>
        {ihbar.isError
          ? 'İhbar ucu yanıt vermiyor; talepler gösterilemiyor.'
          : !ihbar.data
            ? 'Talepler yükleniyor…'
            : talepler.length === 0
            ? `${SUZGECLER.find((s) => s.id === suzgec)?.etiket}: seçili aralıkta talep yok.`
            : `${SUZGECLER.find((s) => s.id === suzgec)?.etiket}: ${sayi(talepler.length)} talep${
                toplamKisi ? `, ${sayi(toplamKisi)} kişi` : ''
              }. En çok istenen: ${enCok && enCok.talep ? `${IHTIYAC_ADI[enCok.t]} (${sayi(enCok.talep)} talep)` : '—'}${
                ihtiyac ? `. Liste yalnız ${IHTIYAC_ADI[ihtiyac].toLocaleLowerCase('tr-TR')} isteyenleri gösteriyor.` : '.'
              }`}
      </SuAn>

      {ihbar.isError && (
        <div className="mt-2">
          <VeriYok ne="İhtiyaç talepleri" neden="ihbar ucu yanıt vermedi" />
        </div>
      )}

      <Teknik>
        Talepler canlı akışla gelir. Sayım listeden yapılır; kişi sayısı afetzedenin yazdığıdır,
        doğrulanmamıştır. Yazılı ihbarda ihtiyaç geçiyorsa o da buraya düşer; ihtiyacı ve kişi
        sayısını metinden model çıkarır (BERTurk ve kural tabanlı çıkarım). Konum afetzedenin cihazından ya da seçtiği mahallenin merkezinden gelir.
        Talepler hasar olmadığı için ısı haritasına yazılmaz.
      </Teknik>
    </Bolum>
  )
}

export function IhtiyacSag() {
  const { suzgec, ihtiyac } = useIhtiyacSuzgeci()
  const suz = useCallback(
    (i: Ihbar) => durumaUyar(i, suzgec) && (!ihtiyac || !!i.ihtiyaclar?.includes(ihtiyac)),
    [suzgec, ihtiyac],
  )
  return (
    <GelenIhbarlar
      tur="ihtiyac"
      kapsa={ihtiyacTalebiMi}
      baslik="Talepler"
      amac="Önce işlenmemiş talepler, sonra en yeni. Seçince ihtiyaçlar, kişi sayısı ve not açılır; karşılanan talebi kapatabilirsin."
      suz={suz}
      sinir={50}
    />
  )
}
