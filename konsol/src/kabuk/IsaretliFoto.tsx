import type { CSSProperties } from 'react'
import { sn } from '@/lib/sinif'
import { tespitRengi, type Tespit } from '@/veri/ihbar'

/* Fotoğraf ve modelin işaretlediği kutular (J-50, J-51). Kutular tarayıcıda
   çizilir: sunucunun işaretli görüntüsü "Bina Hasarsız / Güvenli" yazıyor ve
   Türkçe harfleri bozuyordu. Görüntü ile kutular aynı kutuya "contain" ile
   oturur, böylece hizalı kalır. Kutu rengi hasarın derecesidir (ağır kırmızı,
   orta turuncu, çatlak sarı), haritadaki hasar renkleriyle aynı. Hasarsız
   sınıfı çizilmez.

   J-165: kutular numaralı. Numara listedeki sırayla aynı (önce hasar derecesi,
   sonra güven); listede bir satıra gelince fotoğrafta o kutu öne çıkar. */

/** Çizilen ve listelenen tespitler, ortak sırayla. */
export function hasarliSirali(tespitler: Tespit[]): Tespit[] {
  return tespitler.filter((t) => t.hasar).sort((a, b) => b.skor - a.skor || b.guven - a.guven)
}

export function IsaretliFoto({
  veri,
  en,
  boy,
  tespitler,
  className,
  stil,
  numarali = false,
  secili = null,
  enAzGuven = 0,
  kutularGorunur = true,
  onSec,
}: {
  veri: string
  en: number
  boy: number
  tespitler: Tespit[]
  className?: string
  stil?: CSSProperties
  /** Kutuların köşesine liste numarası yazılır. */
  numarali?: boolean
  /** `hasarliSirali` içindeki sıra (0'dan). Seçili kutu öne çıkar, ötekiler soluklaşır. */
  secili?: number | null
  /** Bu güvenin (0–1) altındaki kutular çizilmez; numaralar değişmez. */
  enAzGuven?: number
  kutularGorunur?: boolean
  /** Verilirse kutular tıklanır. */
  onSec?: (sira: number) => void
}) {
  const kalinlik = Math.max(2, en / 320)
  const yazi = Math.max(14, Math.round(en / 42))
  const sirali = hasarliSirali(tespitler)
  return (
    <div className={sn('relative w-full overflow-hidden rounded-control bg-sunken', className ?? 'h-64')} style={stil}>
      <img src={veri} alt="Modelin işaretlediği fotoğraf" className="absolute inset-0 h-full w-full object-contain" />
      {kutularGorunur && (
        <svg
          viewBox={`0 0 ${en} ${boy}`}
          preserveAspectRatio="xMidYMid meet"
          className="pointer-events-none absolute inset-0 h-full w-full"
          aria-hidden="true"
        >
          {sirali.map((t, i) => {
            if (t.guven < enAzGuven) return null
            const renk = `var(${tespitRengi(t)})`
            const soluk = secili != null && secili !== i
            const [x1, y1, x2, y2] = t.kutu
            return (
              <g
                key={i}
                opacity={soluk ? 0.3 : 1}
                style={onSec ? { pointerEvents: 'all', cursor: 'pointer' } : undefined}
                onClick={onSec ? () => onSec(i) : undefined}
              >
                <rect
                  x={x1}
                  y={y1}
                  width={x2 - x1}
                  height={y2 - y1}
                  fill={secili === i ? renk : 'none'}
                  fillOpacity={secili === i ? 0.12 : 0}
                  stroke={renk}
                  strokeWidth={secili === i ? kalinlik * 2 : kalinlik}
                />
                {numarali && (
                  <>
                    <rect
                      x={x1}
                      y={Math.max(0, y1 - yazi * 1.3)}
                      width={yazi * (String(i + 1).length * 0.7 + 0.8)}
                      height={yazi * 1.3}
                      fill={renk}
                    />
                    <text
                      x={x1 + yazi * 0.4}
                      y={Math.max(0, y1 - yazi * 1.3) + yazi}
                      fontSize={yazi}
                      fontWeight={700}
                      fill="var(--color-ground)"
                    >
                      {i + 1}
                    </text>
                  </>
                )}
              </g>
            )
          })}
        </svg>
      )}
    </div>
  )
}

/** Tespitlerin özeti: model başına kaç işaret, en güvenlisi. */
export function TespitListesi({
  tespitler,
  numarali = false,
  secili = null,
  enAzGuven = 0,
  onSec,
  onVurgula,
}: {
  tespitler: Tespit[]
  numarali?: boolean
  secili?: number | null
  enAzGuven?: number
  /** Verilirse satırlar düğmedir. */
  onSec?: (sira: number) => void
  /** Fareyle ya da klavyeyle satıra gelince (çıkınca null). */
  onVurgula?: (sira: number | null) => void
}) {
  const hasarli = hasarliSirali(tespitler)
  if (hasarli.length === 0) return null
  return (
    <ul>
      {hasarli.map((t, i) => {
        const gizli = t.guven < enAzGuven
        const icerik = (
          <>
            <span className="flex min-w-0 items-center gap-2 text-ink">
              {numarali ? (
                <span
                  aria-hidden
                  className="grid h-5 min-w-5 shrink-0 place-items-center rounded-badge px-1 font-mono text-micro text-ground"
                  style={{ background: `var(${tespitRengi(t)})` }}
                >
                  {i + 1}
                </span>
              ) : (
                <span aria-hidden className="h-2.5 w-2.5 shrink-0 rounded-badge" style={{ background: `var(${tespitRengi(t)})` }} />
              )}
              <span className="truncate">{t.ad}</span>
              <span className="shrink-0 text-ink-3">{t.model === 'catlak' ? 'çatlak modeli' : 'bina modeli'}</span>
            </span>
            <span className="shrink-0 font-mono text-ink-2">güven %{Math.round(t.guven * 100)}</span>
          </>
        )
        const satir = sn(
          'flex w-full items-center justify-between gap-2 border-b border-line py-1.5 text-left text-small last:border-b-0',
          gizli && 'opacity-40',
        )
        return (
          <li key={i}>
            {onSec ? (
              <button
                type="button"
                aria-pressed={secili === i}
                aria-label={`${i + 1}. ${t.ad}, güven yüzde ${Math.round(t.guven * 100)}`}
                onClick={() => onSec(i)}
                onMouseEnter={() => onVurgula?.(i)}
                onMouseLeave={() => onVurgula?.(null)}
                onFocus={() => onVurgula?.(i)}
                onBlur={() => onVurgula?.(null)}
                className={sn(satir, 'rounded-control px-1 hover:bg-hover', secili === i && 'bg-raised')}
              >
                {icerik}
              </button>
            ) : (
              <div className={satir}>{icerik}</div>
            )}
          </li>
        )
      })}
    </ul>
  )
}
