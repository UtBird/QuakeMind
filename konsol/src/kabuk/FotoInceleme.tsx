import { useEffect, useRef, useState, type ReactNode } from 'react'
import { ArrowsIn, MagnifyingGlassMinus, MagnifyingGlassPlus, X } from '@phosphor-icons/react'
import { sn } from '@/lib/sinif'
import type { Tespit } from '@/veri/ihbar'
import { IsaretliFoto, TespitListesi, hasarliSirali } from './IsaretliFoto'

/* Fotoğrafı tam ekranda inceleme (J-165).

   Sağ paneldeki fotoğraf 336 px'e sığıyordu: ince çatlak kutuları ve sunucunun
   resme bastığı etiketler okunmuyordu. Burada fotoğraf ekranı kaplar, kutular
   numaralı ve seçilebilir; listeden ya da kutudan seçilen tespit öne çıkar.

   Klavye: ← → tespitler arasında gezer, + − yakınlaştırır, 0 sığdırır, Esc kapatır.
   Ölçek 1'de fotoğraf alana sığar; büyüdükçe alan kaydırılır. */

const OLCEKLER = [1, 1.5, 2, 3, 4] as const

export function FotoInceleme({
  acik,
  kapat,
  baslik,
  veri,
  en,
  boy,
  tespitler,
  baslangic = null,
  ozet,
  kunye,
}: {
  acik: boolean
  kapat: () => void
  baslik: string
  veri: string
  en: number
  boy: number
  tespitler: Tespit[]
  /** Açılınca seçili gelecek tespit (listedeki sıra). */
  baslangic?: number | null
  /** Listenin üstünde: sonucun tek cümlesi. */
  ozet?: ReactNode
  /** Listenin altında: model, süre, kaynak. */
  kunye?: ReactNode
}) {
  const ref = useRef<HTMLDialogElement>(null)
  const [secili, setSecili] = useState<number | null>(baslangic)
  const [vurgu, setVurgu] = useState<number | null>(null)
  const [olcek, setOlcek] = useState(0)
  const [enAzGuven, setEnAzGuven] = useState(0)
  const [kutular, setKutular] = useState(true)
  const sirali = hasarliSirali(tespitler)
  const gorunen = vurgu ?? secili

  useEffect(() => {
    const d = ref.current
    if (!d) return
    if (acik && !d.open) {
      setSecili(baslangic)
      d.showModal()
    } else if (!acik && d.open) d.close()
  }, [acik, baslangic])

  function tus(e: React.KeyboardEvent) {
    if (e.key === 'Escape') {
      e.preventDefault()
      kapat()
    } else if (e.key === 'ArrowRight' && sirali.length) {
      setSecili((s) => (s == null ? 0 : (s + 1) % sirali.length))
    } else if (e.key === 'ArrowLeft' && sirali.length) {
      setSecili((s) => (s == null ? sirali.length - 1 : (s - 1 + sirali.length) % sirali.length))
    } else if (e.key === '+' || e.key === '=') {
      setOlcek((o) => Math.min(o + 1, OLCEKLER.length - 1))
    } else if (e.key === '-') {
      setOlcek((o) => Math.max(o - 1, 0))
    } else if (e.key === '0') {
      setOlcek(0)
    }
  }

  const dugme =
    'flex h-9 items-center gap-1.5 rounded-control border border-line-2 px-2.5 text-body text-ink-2 hover:bg-hover hover:text-ink disabled:opacity-40'

  return (
    <dialog
      ref={ref}
      onClose={kapat}
      onCancel={(e) => {
        e.preventDefault()
        kapat()
      }}
      onKeyDown={tus}
      aria-label={baslik}
      className="fixed inset-0 m-0 h-full max-h-none w-full max-w-none bg-ground p-0 text-ink backdrop:bg-ground"
    >
      {acik && (
        <div className="flex h-full flex-col">
          <header className="flex shrink-0 items-center gap-2 border-b border-line bg-panel px-3.5 py-2">
            <h2 className="min-w-0 flex-1 truncate text-subtitle text-ink">{baslik}</h2>
            <button
              type="button"
              onClick={() => setOlcek((o) => Math.max(o - 1, 0))}
              disabled={olcek === 0}
              aria-label="Uzaklaştır (−)"
              title="Uzaklaştır (−)"
              className={dugme}
            >
              <MagnifyingGlassMinus size={16} aria-hidden />
            </button>
            <span className="w-12 text-center font-mono text-small text-ink-2" aria-live="polite">
              {OLCEKLER[olcek]}×
            </span>
            <button
              type="button"
              onClick={() => setOlcek((o) => Math.min(o + 1, OLCEKLER.length - 1))}
              disabled={olcek === OLCEKLER.length - 1}
              aria-label="Yakınlaştır (+)"
              title="Yakınlaştır (+)"
              className={dugme}
            >
              <MagnifyingGlassPlus size={16} aria-hidden />
            </button>
            <button
              type="button"
              onClick={() => setOlcek(0)}
              disabled={olcek === 0}
              title="Ekrana sığdır (0)"
              className={dugme}
            >
              <ArrowsIn size={16} aria-hidden />
              <span className="hidden sm:inline">Sığdır</span>
            </button>
            <button type="button" onClick={kapat} className={dugme}>
              <X size={16} aria-hidden />
              Kapat
            </button>
          </header>

          <div className="flex min-h-0 flex-1 flex-col md:flex-row">
            <div className={sn('min-h-0 flex-1 bg-sunken p-3', olcek === 0 ? 'overflow-hidden' : 'overflow-auto')}>
              {olcek === 0 ? (
                <IsaretliFoto
                  veri={veri}
                  en={en}
                  boy={boy}
                  tespitler={tespitler}
                  className="h-full"
                  numarali
                  secili={gorunen}
                  enAzGuven={enAzGuven}
                  kutularGorunur={kutular}
                  onSec={setSecili}
                />
              ) : (
                <IsaretliFoto
                  veri={veri}
                  en={en}
                  boy={boy}
                  tespitler={tespitler}
                  className="mx-auto shrink-0"
                  stil={{ width: `${OLCEKLER[olcek] * 100}%`, aspectRatio: `${en} / ${boy}` }}
                  numarali
                  secili={gorunen}
                  enAzGuven={enAzGuven}
                  kutularGorunur={kutular}
                  onSec={setSecili}
                />
              )}
            </div>

            <aside className="flex max-h-full shrink-0 flex-col overflow-auto border-t border-line bg-panel p-3.5 md:w-panel-r md:border-t-0 md:border-l">
              {ozet}
              <p className="mt-2 text-micro ls-micro text-ink-3 uppercase">
                Tespitler · {sirali.length}
              </p>
              {sirali.length ? (
                <div className="mt-1">
                  <TespitListesi
                    tespitler={tespitler}
                    numarali
                    secili={secili}
                    enAzGuven={enAzGuven}
                    onSec={(i) => setSecili((s) => (s === i ? null : i))}
                    onVurgula={setVurgu}
                  />
                  <p className="mt-1.5 text-small text-ink-3">
                    Satıra ya da kutuya tıkla: o tespit öne çıkar. ← → ile sırayla gez.
                  </p>
                </div>
              ) : (
                <p className="mt-1 text-small text-ink-2">Model bu fotoğrafta hasar işaretlemedi.</p>
              )}

              {kunye && <div className="mt-3 border-t border-line pt-2.5">{kunye}</div>}

              {/* İnce ayar en altta (ARAYUZ §6). */}
              {sirali.length > 0 && (
                <div className="mt-3 border-t border-line pt-2.5">
                  <p className="text-micro ls-micro text-ink-3 uppercase">İnce ayar</p>
                  <label className="mt-2 block text-small text-ink-2">
                    Güveni %{Math.round(enAzGuven * 100)} altındaki kutuları gizle
                    <input
                      type="range"
                      min={0}
                      max={0.9}
                      step={0.05}
                      value={enAzGuven}
                      onChange={(e) => setEnAzGuven(Number(e.target.value))}
                      className="mt-1 w-full accent-accent"
                    />
                  </label>
                  <label className="mt-2 flex items-center gap-2 text-small text-ink-2">
                    <input
                      type="checkbox"
                      checked={kutular}
                      onChange={(e) => setKutular(e.target.checked)}
                      className="accent-accent"
                    />
                    Kutuları göster (fotoğrafın kendisine bakmak için kapat)
                  </label>
                  <p className="mt-1.5 text-small text-ink-3">
                    Bu ayarlar yalnız görünümü değiştirir; modelin sonucu ve işlem kaydı aynı kalır.
                  </p>
                </div>
              )}
            </aside>
          </div>
        </div>
      )}
    </dialog>
  )
}
