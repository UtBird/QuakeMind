import { create } from 'zustand'
import type { EnYakinYer, Guzergah } from '@/veri/guzergah'
import type { KapanmaDurumu } from '@/veri/katman'

/** "Yol ve rota" modunun durumu (J-171): sol panel soruyu ve noktaları seçer,
    sağ panel ve harita sonucu gösterir. Haritaya tıklama KonsolKabugu'ndan
    `haritadanNokta`ya gelir.

    Tıklama sırası (J-190):
    · İki nokta arası: ilk tıklama başlangıç (A), ikincisi hedef (B). İkisi de
      seçiliyse tıklama yok sayılır; değiştirmek için noktanın düğmesine basılır.
      Eskiden hasar analizinin yarım çokgen çizimi bu modda da tıklamaları
      alıyordu: sınırsız nokta, sayfalar arası taşınan köşeler.
    · Çok duraklı: her tıklama sıradaki durak (en çok EN_COK_DURAK).
    · En yakın hastane / toplanma: tıklama başlangıç. */

export type RotaNoktasi = { lon: number; lat: number; ad: string }
export type RotaSorusu = 'nokta' | 'duraklar' | 'ekip' | 'hastane' | 'toplanma' | 'kapali'
export type KapanmaSuzgeci = KapanmaDurumu | 'hepsi'

export const EN_COK_DURAK = 10

type RotaDurumu = {
  soru: RotaSorusu
  bas: RotaNoktasi | null
  hedef: RotaNoktasi | null
  /** Çok duraklı rota: sırayla 1 → 2 → … */
  duraklar: RotaNoktasi[]
  /** Haritaya tıklayınca hangi nokta seçilecek (değiştir düğmesiyle açılır). */
  secim: 'bas' | 'hedef' | null
  kacin: boolean
  sonuc: Guzergah | null
  /** Kaçınmadan (hasar ve kapanma yok sayılarak) aynı rota: farkı göstermek için. */
  kiyas: Guzergah | null
  adaylar: EnYakinYer[] | null
  adayKaynagi: string | null
  seciliAday: number
  /** Kapanma yönetimi: seçili kapanma, durum süzgeci, açık analiz grubu. */
  seciliKapanma: string | null
  kapanmaSuzgeci: KapanmaSuzgeci
  acikAnaliz: string | null
  soruSec: (s: RotaSorusu) => void
  noktaYaz: (hangi: 'bas' | 'hedef', n: RotaNoktasi | null) => void
  secimAc: (hangi: 'bas' | 'hedef' | null) => void
  durakEkle: (n: RotaNoktasi) => void
  durakSil: (i: number) => void
  durakTasi: (i: number, yon: -1 | 1) => void
  duraklariTemizle: () => void
  noktalariTemizle: () => void
  kacinYaz: (v: boolean) => void
  sonucYaz: (s: Guzergah | null, kiyas?: Guzergah | null) => void
  adaylarYaz: (a: EnYakinYer[] | null, kaynak?: string | null) => void
  adaySec: (i: number) => void
  kapanmaSec: (id: string | null) => void
  kapanmaSuzgeciSec: (s: KapanmaSuzgeci) => void
  analizAc: (id: string | null) => void
}

const SONUCSUZ = { sonuc: null, kiyas: null, adaylar: null } as const

export const useRota = create<RotaDurumu>((set) => ({
  soru: 'nokta',
  bas: null,
  hedef: null,
  duraklar: [],
  secim: null,
  kacin: true,
  sonuc: null,
  kiyas: null,
  adaylar: null,
  adayKaynagi: null,
  seciliAday: 0,
  seciliKapanma: null,
  kapanmaSuzgeci: 'kapali',
  acikAnaliz: null,
  soruSec: (soru) => set({ soru, ...SONUCSUZ, secim: null, hedef: null }),
  noktaYaz: (hangi, n) => set((d) => ({ ...d, [hangi]: n, secim: null, ...SONUCSUZ })),
  secimAc: (secim) => set({ secim }),
  durakEkle: (n) =>
    set((d) => (d.duraklar.length >= EN_COK_DURAK ? d : { duraklar: [...d.duraklar, n], ...SONUCSUZ })),
  durakSil: (i) => set((d) => ({ duraklar: d.duraklar.filter((_, j) => j !== i), ...SONUCSUZ })),
  durakTasi: (i, yon) =>
    set((d) => {
      const j = i + yon
      if (j < 0 || j >= d.duraklar.length) return d
      const yeni = [...d.duraklar]
      ;[yeni[i], yeni[j]] = [yeni[j], yeni[i]]
      return { duraklar: yeni, ...SONUCSUZ }
    }),
  duraklariTemizle: () => set({ duraklar: [], ...SONUCSUZ }),
  noktalariTemizle: () => set({ bas: null, hedef: null, secim: null, ...SONUCSUZ }),
  kacinYaz: (kacin) => set({ kacin, ...SONUCSUZ }),
  sonucYaz: (sonuc, kiyas = null) => set({ sonuc, kiyas }),
  adaylarYaz: (adaylar, adayKaynagi = null) =>
    set({ adaylar, adayKaynagi, seciliAday: 0, sonuc: adaylar?.[0] ?? null, kiyas: null }),
  adaySec: (i) => set((d) => ({ seciliAday: i, sonuc: d.adaylar?.[i] ?? null })),
  kapanmaSec: (seciliKapanma) => set({ seciliKapanma }),
  kapanmaSuzgeciSec: (kapanmaSuzgeci) => set({ kapanmaSuzgeci }),
  analizAc: (acikAnaliz) => set({ acikAnaliz }),
}))

const noktaAdi = (lon: number, lat: number) => `${lat.toFixed(5)}, ${lon.toFixed(5)}`

/** Haritaya tıklanan nokta (KonsolKabugu). Kullanıldıysa true döner. */
export function haritadanNokta(lon: number, lat: number): boolean {
  const d = useRota.getState()
  const n = { lon, lat, ad: noktaAdi(lon, lat) }
  if (d.secim) {
    d.noktaYaz(d.secim, n)
    return true
  }
  if (d.soru === 'nokta') {
    if (!d.bas) d.noktaYaz('bas', n)
    else if (!d.hedef) d.noktaYaz('hedef', n)
    else return false
    return true
  }
  if (d.soru === 'duraklar') {
    if (d.duraklar.length >= EN_COK_DURAK) return false
    d.durakEkle(n)
    return true
  }
  if ((d.soru === 'hastane' || d.soru === 'toplanma') && !d.bas) {
    d.noktaYaz('bas', n)
    return true
  }
  return false
}
