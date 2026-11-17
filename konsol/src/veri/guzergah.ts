import { useQuery } from '@tanstack/react-query'
import { apiGet } from './istemci'

/* ---------------------------------------------------------------------------
   Araç rotası (J-171): QuakeMindBackend/uclar/guzergah.py, motor
   arac_rotasi.py. Sevk ve görev ekranları aynı motoru kullanır.
--------------------------------------------------------------------------- */

export type Manevra =
  | 'basla'
  | 'duz'
  | 'hafif-sag'
  | 'hafif-sol'
  | 'sag'
  | 'sol'
  | 'keskin-sag'
  | 'keskin-sol'

export type RotaAdimi = { ad: string; uzunlukM: number; manevra: Manevra; yon?: string }

export type Guzergah = {
  mesafeM: number
  sureDk: number
  /** Rotanın geçtiği bilinen kapanma sayısı (başka yol yoksa). */
  kapanmadanGecer: number
  /** Hasar noktasına yakın (cezalı) kısmın uzunluğu. */
  riskliM: number
  baglantiM: number
  /** [boylam, enlem] */
  rota: [number, number][]
  donus?: { sol: number; sag: number }
  adimlar?: RotaAdimi[]
  ag?: string
  hasar?: { kapanma: number; hasarNoktasi: number }
  aramaMs?: number
  kusUcusuM?: number
  kacin?: boolean
}

export type EnYakinYer = Guzergah & {
  ad: string
  adres?: string | null
  lon: number
  lat: number
  kusUcusuM: number
}

export type EnYakinYaniti = { yerler: EnYakinYer[]; kaynak: string; aday: number }

export type RotaKunyesi = {
  osm: string
  motor: string
  hizKmSa: Record<string, number>
  sehirDisiHizKmSa: Record<string, number>
  donusBedeliSn: Record<string, number>
  sehirler: { id: string; ad: string; kutu: [number, number, number, number] }[]
  genel: [number, number, number, number] | null
}

export function useRotaKunyesi() {
  return useQuery({
    queryKey: ['guzergah', 'kunye'],
    staleTime: Infinity,
    queryFn: () => apiGet<RotaKunyesi>('/api/guzergah/kunye'),
  })
}

export const MANEVRA_ADI: Record<Manevra, string> = {
  basla: 'Başla',
  duz: 'Düz devam et',
  'hafif-sag': 'Hafif sağa',
  'hafif-sol': 'Hafif sola',
  sag: 'Sağa dön',
  sol: 'Sola dön',
  'keskin-sag': 'Keskin sağa',
  'keskin-sol': 'Keskin sola',
}
