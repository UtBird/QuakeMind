import { useQuery } from '@tanstack/react-query'
import { create } from 'zustand'
import { apiGet, apiPost } from './istemci'

/* Deprem riski verisi (J-173; yeniden düzen J-191). Panel ve harita aynı
   sorguları paylaşır (TanStack Query aynı anahtarı bir kez ister). */

/** Katalogdan bir deprem (sunucu `risk_hizmeti.olay`). Zaman UTC metni. */
export type RiskDeprem = {
  time: string
  place: string
  magnitude: number
  depth: number | null
  distanceKm?: number
  latitude: number
  longitude: number
}

export type RiskYaniti = {
  city: string
  coordinates: { lat: number; lon: number }
  riskScore: number
  riskLevel: string
  lastUpdate?: string
  metrics: {
    shortRisk: number
    longHazard: number
    faultScore: number
    faultDistanceKm: number
    nearbyQuakeCount?: number
    maxMagnitude?: number
  }
  dayanak?: {
    kisaVadeKaynagi: 'yerel' | 'ulke'
    kisaVadeYerelDeprem: number
    uzunVadeAnaSok: number
    katalogBasi: string
    katalogSonu: string
    agirlik: { kisa: number; uzun: number; fay: number }
    yaricapKm: { kisa: number; uzun: number; yakinDeprem: number }
  }
  yakinFaylar?: { tur: string; kimlik: string; km: number }[]
  sonDepremler?: RiskDeprem[]
  /** Uzun vadeli bileşenin saydığı M≥6 ana şoklar (200 km, artçısız). */
  anaSoklar?: RiskDeprem[]
  /** Kısa vadeli bileşenin baktığı son bir yıl (150 km), büyükten küçüğe en çok 60. */
  sonYilDepremler?: RiskDeprem[]
}

export type RiskSirasi = {
  il: string
  lat: number
  lon: number
  skor: number
  seviye: string
  kisa: number
  uzun: number
  fay: number
  fayKm: number
  kisaVadeKaynagi: 'yerel' | 'ulke'
}

export type UlkeAnaSoklari = {
  depremler: RiskDeprem[]
  esikM: number
  katalogBasi: string
  katalogSonu: string
}

export type RiskDuzeyi = 'crit' | 'high' | 'mid' | 'ok'

export const RISK_TONU = (skor: number): RiskDuzeyi =>
  skor >= 75 ? 'crit' : skor >= 50 ? 'high' : skor >= 25 ? 'mid' : 'ok'

export const DUZEY_ADI: Record<RiskDuzeyi, string> = {
  crit: 'Çok yüksek',
  high: 'Yüksek',
  mid: 'Orta',
  ok: 'Düşük',
}

/** Haritada ve listede aynı deprem: zaman + konum. */
export const depremKimligi = (d: RiskDeprem) => `${d.time}|${d.latitude}|${d.longitude}`
export const depremZamani = (d: RiskDeprem) => Date.parse(d.time.replace(' ', 'T'))
export const depremYili = (d: RiskDeprem) => d.time.slice(0, 4)
export const buyukluk = (m: number) => m.toFixed(1).replace('.', ',')

export function useRiskSiralamasi(acik = true) {
  return useQuery({
    queryKey: ['risk', 'siralama'],
    // Harita kabuğu her modda çağırır; yalnız risk modunda istenir (J-175).
    enabled: acik,
    staleTime: 10 * 60_000,
    queryFn: () => apiGet<{ iller: RiskSirasi[] }>('/api/risk/siralama'),
  })
}

export function useRisk(il: RiskSirasi | null) {
  return useQuery({
    queryKey: ['risk', 'il', il?.il],
    enabled: !!il,
    staleTime: 10 * 60_000,
    queryFn: () =>
      apiPost<RiskYaniti>('/api/risk/predict', { city: il!.il, manualLatitude: il!.lat, manualLongitude: il!.lon }),
  })
}

export function useUlkeAnaSoklari(acik: boolean) {
  return useQuery({
    queryKey: ['risk', 'ana-soklar'],
    enabled: acik,
    staleTime: 30 * 60_000,
    queryFn: () => apiGet<UlkeAnaSoklari>('/api/risk/ana-soklar'),
  })
}

/** Panelde ve haritada vurgulanan deprem; il listesinin düzey süzgeci. */
export const useRiskSecimi = create<{
  deprem: string | null
  duzey: RiskDuzeyi | null
  depremSec: (id: string | null) => void
  duzeySec: (d: RiskDuzeyi | null) => void
}>((set) => ({
  deprem: null,
  duzey: null,
  depremSec: (deprem) => set({ deprem }),
  duzeySec: (duzey) => set({ duzey }),
}))

/** İlin hesap alanını (yarıçap km) içine alan kutu: [batı, güney, doğu, kuzey]. */
export function alanKutusu(lon: number, lat: number, km: number): [number, number, number, number] {
  const dLat = km / 110.574
  const dLon = km / (111.32 * Math.cos((lat * Math.PI) / 180))
  return [lon - dLon, lat - dLat, lon + dLon, lat + dLat]
}
