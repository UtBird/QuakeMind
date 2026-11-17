import { create } from 'zustand'
import type { EnYakinYer, Guzergah } from '@/veri/guzergah'

/** "Yol ve rota" modunun durumu (J-171): sol panel soruyu ve noktaları seçer,
    sağ panel ve harita sonucu gösterir. Haritaya tıklayınca nokta seçilir
    (`secim` açıkken); KonsolKabugu tıklamayı buraya yönlendirir. */

export type RotaNoktasi = { lon: number; lat: number; ad: string }
export type RotaSorusu = 'nokta' | 'ekip' | 'hastane' | 'toplanma' | 'kapali'

type RotaDurumu = {
  soru: RotaSorusu
  bas: RotaNoktasi | null
  hedef: RotaNoktasi | null
  /** Haritaya tıklayınca hangi nokta seçilecek. */
  secim: 'bas' | 'hedef' | null
  kacin: boolean
  sonuc: Guzergah | null
  /** Kaçınmadan (hasar ve kapanma yok sayılarak) aynı rota: farkı göstermek için. */
  kiyas: Guzergah | null
  adaylar: EnYakinYer[] | null
  adayKaynagi: string | null
  seciliAday: number
  soruSec: (s: RotaSorusu) => void
  noktaYaz: (hangi: 'bas' | 'hedef', n: RotaNoktasi | null) => void
  secimAc: (hangi: 'bas' | 'hedef' | null) => void
  kacinYaz: (v: boolean) => void
  sonucYaz: (s: Guzergah | null, kiyas?: Guzergah | null) => void
  adaylarYaz: (a: EnYakinYer[] | null, kaynak?: string | null) => void
  adaySec: (i: number) => void
}

export const useRota = create<RotaDurumu>((set) => ({
  soru: 'nokta',
  bas: null,
  hedef: null,
  secim: null,
  kacin: true,
  sonuc: null,
  kiyas: null,
  adaylar: null,
  adayKaynagi: null,
  seciliAday: 0,
  soruSec: (soru) => set({ soru, sonuc: null, kiyas: null, adaylar: null, secim: null, hedef: null }),
  noktaYaz: (hangi, n) =>
    set((d) => ({ ...d, [hangi]: n, secim: null, sonuc: null, kiyas: null, adaylar: null })),
  secimAc: (secim) => set({ secim }),
  kacinYaz: (kacin) => set({ kacin, sonuc: null, kiyas: null, adaylar: null }),
  sonucYaz: (sonuc, kiyas = null) => set({ sonuc, kiyas }),
  adaylarYaz: (adaylar, adayKaynagi = null) =>
    set({ adaylar, adayKaynagi, seciliAday: 0, sonuc: adaylar?.[0] ?? null, kiyas: null }),
  adaySec: (i) => set((d) => ({ seciliAday: i, sonuc: d.adaylar?.[i] ?? null })),
}))

/** Haritaya tıklanan nokta (KonsolKabugu): seçim açıksa yazar ve true döner. */
export function haritadanNokta(lon: number, lat: number): boolean {
  const d = useRota.getState()
  if (!d.secim) return false
  d.noktaYaz(d.secim, { lon, lat, ad: `Seçilen nokta · ${lat.toFixed(5)}, ${lon.toFixed(5)}` })
  return true
}
