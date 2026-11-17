import { CaretRight } from '@phosphor-icons/react'
import { sn } from '@/lib/sinif'
import { IHBAR_TURU, type IhbarTuru } from '@/veri/ihbar'
import { IHBAR_IKONU } from '@/veri/ihbarIkon'

/* "Bildir" düğmeleri (J-51): hasar fotoğrafı, yazılı ihbar, ihtiyaç talebi.
   Her tür kendi rengi ve simgesiyle durur; konsolda aynı ihbar aynı renkle
   görünür. Renk tek başına ayırt edici değildir: ad ve açıklama da yazılır. */

const DUGMELER: ReadonlyArray<{ tur: IhbarTuru; baslik: string; alt: string }> = [
  { tur: 'fotograf', baslik: 'Hasar fotoğrafı', alt: 'Fotoğraf çek, modele incelet, ihbar et' },
  { tur: 'metin', baslik: 'Yazarak bildir', alt: 'Ne olduğunu yaz; model adresi çıkarır' },
  { tur: 'ihtiyac', baslik: 'İhtiyaç bildir', alt: 'Su, gıda, barınma, ısınma, ilaç' },
]

export function BildirDugmeleri({ ac }: { ac: (tur: IhbarTuru) => void }) {
  return (
    <nav aria-label="Bildir" className="grid shrink-0 grid-cols-1 gap-gutter sm:grid-cols-3">
      {DUGMELER.map((d) => {
        const t = IHBAR_TURU[d.tur]
        const Ikon = IHBAR_IKONU[d.tur]
        return (
          <button
            key={d.tur}
            type="button"
            // Ekran okuyucuya açık ad (J-167 U-6): kart içinde birkaç metin parçası var.
            aria-label={`${d.baslik}: ${d.alt}`}
            onClick={() => ac(d.tur)}
            className={sn(
              'group flex min-h-20 items-center gap-3 rounded-panel border border-line border-l-4 bg-panel px-3 py-2.5 text-left hover:bg-raised',
              t.solKenar,
            )}
          >
            <span aria-hidden className={sn('grid h-11 w-11 shrink-0 place-items-center rounded-control', t.soluk, t.metin)}>
              <Ikon size={24} weight="bold" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-subtitle text-ink">{d.baslik}</span>
              <span className="block text-small text-ink-3">{d.alt}</span>
            </span>
            <CaretRight size={16} className="shrink-0 text-ink-3 group-hover:text-ink" aria-hidden />
          </button>
        )
      })}
    </nav>
  )
}
