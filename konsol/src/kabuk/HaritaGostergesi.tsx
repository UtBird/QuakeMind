import { useState } from 'react'
import { CaretDown } from '@phosphor-icons/react'
import { Micro } from './parcalar'
import { useSimulasyon } from '@/durum/simulasyonDurumu'
import { sn } from '@/lib/sinif'

/* ---------------------------------------------------------------------------
   Harita göstergesi (J-95).

   Tatbikat haritasında üç ayrı şey aynı kırmızıyı kullanıyor (hasar kütlesi,
   kapalı yol, afetzede) ve rota varyantları da renkle ayrılıyor. Haritada
   bunların ne olduğunu söyleyen HİÇBİR ŞEY yoktu; kullanıcı "kırmızı nokta ne,
   kırmızı çizgi ne, sarı yol ne belirsiz" dedi (27 Eylül). Gösterge yalnız
   tatbikat koşarken görünür — normal akışta yer kaplamasın.

   Renk kuralı (ARAYUZ §6): kırmızı, turuncu ve sarı yalnız hasar ve aciliyet
   içindir; burada üçü de o anlamda. Ayrım renkten başka BİÇİMLE de yapılır:
   alan / kalın çizgi / içi boş halka / dolu daire.
--------------------------------------------------------------------------- */

type Bicim =
  | 'alan'
  | 'cizgi'
  | 'cizgi-kalin'
  | 'cizgi-kesik'
  | 'cizgi-sonuk'
  | 'halka'
  | 'daire'
  | 'kare'

type Satir = { renk: string; bicim: Bicim; ad: string; not?: string }

const SATIRLAR: Satir[] = [
  { renk: 'var(--color-crit)', bicim: 'alan', ad: 'Hasarlı alan', not: 'modelin bulduğu' },
  { renk: 'var(--color-crit)', bicim: 'cizgi-kalin', ad: 'Kapalı yol', not: 'hasar yola taşıyor' },
  { renk: 'var(--color-high)', bicim: 'cizgi', ad: 'Cezalı yol', not: 'hasara yakın' },
  { renk: 'var(--color-crit)', bicim: 'cizgi-sonuk', ad: 'Bilmeyen ekibin sürdüğü yol', not: 'çıkmazlar dahil' },
  { renk: 'var(--color-accent)', bicim: 'cizgi-kalin', ad: 'QuakeMind güzergâhı', not: 'kapalılar çıkarılmış' },
  { renk: 'var(--color-mid)', bicim: 'cizgi', ad: 'Enkazdan uzak', not: 'hasara yakın kenar pahalı' },
  { renk: 'var(--color-ink-3)', bicim: 'cizgi-kesik', ad: 'Kapanma olmasaydı', not: 'kıyas çizgisi' },
  { renk: 'var(--color-accent)', bicim: 'daire', ad: 'Ekip', not: 'mahalle girişi' },
  { renk: 'var(--color-crit)', bicim: 'halka', ad: 'Afetzede', not: 'senaryo' },
  { renk: 'var(--color-ch-cam)', bicim: 'kare', ad: 'Kamera tespiti', not: 'gerçek foto · YOLO' },
  { renk: 'var(--color-ch-nlp)', bicim: 'daire', ad: 'Metin ihbarı', not: 'üretilmiş metin · BERTurk' },
]

function Isaret({ renk, bicim }: { renk: string; bicim: Bicim }) {
  const ortak = 'inline-block shrink-0'
  if (bicim === 'alan')
    return <span className={sn(ortak, 'h-3 w-5 rounded-xs')} style={{ background: renk, opacity: 0.72 }} />
  if (bicim === 'daire')
    return <span className={sn(ortak, 'h-2.5 w-2.5 rounded-full')} style={{ background: renk }} />
  if (bicim === 'kare')
    return <span className={sn(ortak, 'h-2.5 w-2.5 rounded-xs')} style={{ background: renk }} />
  if (bicim === 'halka')
    return (
      <span
        className={sn(ortak, 'h-2.5 w-2.5 rounded-full')}
        style={{ border: `2px solid ${renk}` }}
      />
    )
  if (bicim === 'cizgi-sonuk')
    return (
      <span
        className={sn(ortak, 'w-5')}
        style={{ borderTop: `5px solid ${renk}`, opacity: 0.45 }}
      />
    )
  const kalinlik = bicim === 'cizgi-kalin' ? 3 : 2
  return (
    <span
      className={sn(ortak, 'w-5')}
      style={
        bicim === 'cizgi-kesik'
          ? { borderTop: `${kalinlik}px dashed ${renk}`, opacity: 0.8 }
          : { borderTop: `${kalinlik}px solid ${renk}` }
      }
    />
  )
}

export function HaritaGostergesi() {
  const isId = useSimulasyon((d) => d.isId)
  // Varsayılan KAPALI (J-167 U-4): açıkken haritanın yaklaşık üçte birini
  // kapatıyordu. Başlık ("Haritada ne var") her zaman görünür, tek tıkla açılır.
  const [acik, setAcik] = useState(false)
  if (!isId) return null

  return (
    <div className="pointer-events-auto rounded-md border border-line bg-panel/95 shadow-panel">
      <button
        type="button"
        onClick={() => setAcik((a) => !a)}
        aria-expanded={acik}
        className="flex w-full items-center gap-2 px-3 py-2 text-small text-ink"
      >
        <span>Haritada ne var</span>
        <CaretDown
          size={14}
          className={sn('ml-auto transition-transform', acik && 'rotate-180')}
          aria-hidden
        />
      </button>
      {acik && (
        <ul className="flex flex-col gap-1.5 border-t border-line px-3 py-2">
          {SATIRLAR.map((s, i) => (
            <li key={`${s.ad}-${i}`} className="flex items-center gap-2">
              <Isaret renk={s.renk} bicim={s.bicim} />
              <span className="text-small text-ink">{s.ad}</span>
              {s.not && <Micro>{s.not}</Micro>}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
