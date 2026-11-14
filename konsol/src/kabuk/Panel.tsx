import type { ReactNode } from 'react'
import { sn } from '@/lib/sinif'
import { Chip, Micro } from './parcalar'

/* ---------------------------------------------------------------------------
   PANEL KURALI (ARAYUZ_KARARLARI.md §9). Her panel şu sırayla kurulur:
     1. Tek cümlelik amaç        → <Amac>
     2. Hazır seçenekler (3-5)   → <HazirSecenekler>
     3. İnce ayar en altta       → <InceAyar>
     4. "Şu an ne görüyorum"     → <SuAn>
     5. Teknik not en altta      → <Teknik>
   Bu bileşenler sırayı kodda görünür kılar; panel yazan kişi sırayı bozarsa
   gözden kaçmaz.
--------------------------------------------------------------------------- */

export function Panel({
  baslik,
  ek,
  children,
  className,
}: {
  baslik: string
  ek?: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <section
      aria-label={baslik}
      className={sn(
        // w-full: panel, sabit genişlikli sütunun TAMAMINI kaplar. Eskiden içerik
        // kadar daralıyordu; hasar analizinde ilerleme çubuğu gelince sağ panel
        // bir anda genişliyordu (kullanıcı, 13 Kasım).
        'flex w-full min-h-0 flex-col overflow-hidden rounded-panel border border-line bg-panel',
        className,
      )}
    >
      <header className="flex shrink-0 items-center justify-between gap-2 border-b border-line px-3 pt-3 pb-2.5">
        <Micro>{baslik}</Micro>
        {ek}
      </header>
      <div className="min-h-0 flex-1 overflow-auto overscroll-contain">{children}</div>
    </section>
  )
}

export function Bolum({
  baslik,
  ek,
  children,
  dolgusuz,
}: {
  baslik?: string
  ek?: ReactNode
  children: ReactNode
  dolgusuz?: boolean
}) {
  return (
    <div className={sn('border-b border-line last:border-b-0', !dolgusuz && 'px-3 py-3')}>
      {baslik && (
        <div className={sn('mb-2 flex items-center justify-between gap-2', dolgusuz && 'px-3 pt-3')}>
          <Micro>{baslik}</Micro>
          {ek}
        </div>
      )}
      {children}
    </div>
  )
}

/** 1. Tek cümlelik amaç: panel hangi soruyu cevaplıyor? */
export function Amac({ children }: { children: ReactNode }) {
  return <p className="text-small leading-relaxed text-ink-2">{children}</p>
}

/** 2. Hazır seçenekler: gerçek iş sorularını temsil eden 3-5 düğme. */
export function HazirSecenekler<T extends string>({
  secenekler,
  secili,
  onSec,
  etiket,
}: {
  secenekler: ReadonlyArray<{ id: T; etiket: string }>
  secili: T | null
  onSec: (id: T) => void
  etiket: string
}) {
  return (
    <div role="group" aria-label={etiket} className="mt-2.5 flex flex-wrap gap-1.5">
      {secenekler.map((s) => (
        <Chip key={s.id} secili={secili === s.id} onClick={() => onSec(s.id)}>
          {s.etiket}
        </Chip>
      ))}
    </div>
  )
}

/** 3. İnce ayar: kaydırıcı ve anahtarlar hazır seçeneklerin ALTINDA durur. */
export function InceAyar({ baslik, children }: { baslik?: string; children: ReactNode }) {
  return (
    <div className="mt-3">
      {baslik && <Micro className="block">{baslik}</Micro>}
      <div className="mt-1.5">{children}</div>
    </div>
  )
}

/** 4. Şu an ne görüyorum: seçim değişince güncellenen tek satır. */
export function SuAn({ children }: { children: ReactNode }) {
  return (
    <p aria-live="polite" className="mt-3 text-small leading-relaxed text-ink-2">
      {children}
    </p>
  )
}

/** 5. Teknik not: işaretli ve en altta. */
export function Teknik({ children }: { children: ReactNode }) {
  return (
    <p className="mt-2 text-small leading-relaxed text-ink-3">
      <span className="text-ink-2">Teknik:</span> {children}
    </p>
  )
}

/** Veri yoksa uydurulmaz; eksik olduğu yazılır (CLAUDE.md kural 1). */
export function VeriYok({ ne, neden }: { ne: string; neden?: string }) {
  return (
    <p className="text-small leading-relaxed text-ink-3">
      {ne} için veri yok{neden ? ` — ${neden}` : ''}.
    </p>
  )
}
