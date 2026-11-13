import { useEffect, useId, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { CaretDown, Stack } from '@phosphor-icons/react'
import { Anahtar, Micro } from './parcalar'
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
import { DEPREM_EN_AZ, useDepremler, useFaylar, useKapanmalar, useToplanmaAlanlari } from '@/veri/katman'
import { useGorunenAltlik } from '@/harita/altlikGorunumu'
import { sayi } from '@/lib/bicim'
import { sn } from '@/lib/sinif'

/* ---------------------------------------------------------------------------
   Harita katmanları (J-56). Eskiden sol panelin altındaydı: her modda aynı iki
   bölüm (katmanlar, veri kaynakları) kaydırınca geliyordu ve panelin başlığı
   "Katmanlar" olduğu için mod değişince neyin değiştiği anlaşılmıyordu.
   Kullanıcı: "kullanışsız". Artık haritanın köşesinde bir düğme.

   Her katman kaynağını ve sayısını kendi satırında yazar (kural 1). Haritaya
   henüz bağlanmamış katmanın anahtarı yok, "bağlanmadı" yazar: eskiden
   anahtarı vardı ama hiçbir şey çizmiyordu.
--------------------------------------------------------------------------- */

export function KatmanDugmesi({ yukari = true }: { yukari?: boolean }) {
  const [acik, setAcik] = useState(false)
  const kutu = useRef<HTMLDivElement>(null)
  const kimlik = useId()
  const { mod } = useParams()
  const tanim = modBul(mod) ?? MODLAR[0]
  const katmanlar = useKonsol((d) => d.katmanlar)
  const katmanDegistir = useKonsol((d) => d.katmanDegistir)
  const aralik = useSorguAraligi()
  const ozet = useOzet(aralik)
  const sos = useSosCagrilari(aralik)
  const ihbar = useIhbarlar(aralik)
  const ekipler = useEkipler()
  // Aynı sorgu anahtarları kabuktakilerle paylaşılır: katman kapalıyken istek
  // atılmaz, açıkken sayı önbellekten gelir.
  const { gorunen: gorunenBolgeler } = useGorunenAltlik()
  const kapanmalar = useKapanmalar(katmanlar.hasarliYollar)
  const depremler = useDepremler(katmanlar.depremler)
  const faylar = useFaylar(katmanlar.faylar)
  const toplanma = useToplanmaAlanlari(katmanlar.toplanma, gorunenBolgeler)

  const acikSayisi = KATMANLAR.filter((k) => katmanlar[k] && KATMAN_BILGI[k].bagli).length

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
    depremler: depremler.data ? `${sayi(depremler.data.sayi)} deprem · M ≥ ${DEPREM_EN_AZ}` : null,
    faylar: faylar.data ? `${sayi(faylar.data.sayi)} hat` : null,
    toplanma: toplanma.data ? `${sayi(toplanma.data.sayi)} alan` : null,
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
            'absolute left-0 z-30 max-h-96 w-80 overflow-auto rounded-panel border border-line-2 bg-panel p-3 shadow-float',
            yukari ? 'bottom-full mb-1.5' : 'top-full mt-1.5',
          )}
        >
          <p className="text-small text-ink-2">
            <span className="text-ink">{tanim.ad}</span> modu için önerilen katmanlar açık. Mod değişince öneriler
            yeniden uygulanır; buradan ekleyip kaldırabilirsin.
          </p>

          <div className="mt-2.5 border-b border-line pb-2">
            <p className="flex items-baseline justify-between gap-2 text-body text-ink">
              SOS çağrıları
              <span className="text-small text-ink-3">
                her zaman açık{sos.data ? ` · ${sayi(sos.data.length)} çağrı` : ''}
              </span>
            </p>
            <p className="text-small text-ink-3">Afetzede ekranından gelen acil çağrılar</p>
          </div>

          {(Object.keys(KATMAN_GRUBU) as (keyof typeof KATMAN_GRUBU)[]).map((grup) => (
            <section key={grup} className="mt-2.5">
              <Micro>{KATMAN_GRUBU[grup]}</Micro>
              {KATMANLAR.filter((k) => KATMAN_BILGI[k].grup === grup).map((k) => {
                const b = KATMAN_BILGI[k]
                return b.bagli ? (
                  <div key={k}>
                    <Anahtar
                      acik={katmanlar[k]}
                      etiket={KATMAN_ADI[k]}
                      onDegis={() => katmanDegistir(k)}
                      ek={sayilar[k] ? <span className="text-small text-ink-3">{sayilar[k]}</span> : undefined}
                    />
                    <p className="-mt-1 pb-1 text-small text-ink-3">{b.kaynak}</p>
                  </div>
                ) : (
                  <div key={k} className="py-1.5">
                    <p className="flex items-baseline justify-between gap-2 text-body text-ink-3">
                      {KATMAN_ADI[k]}
                      <span className="text-small">bağlanmadı</span>
                    </p>
                    <p className="text-small text-ink-3">{b.kaynak}</p>
                  </div>
                )
              })}
            </section>
          ))}
        </div>
      )}
    </div>
  )
}
