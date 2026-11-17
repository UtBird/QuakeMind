import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { apiGet } from './istemci'

/** Zaman şeridinin olay yoğunluğu (J-167 F-4): saat başına SOS ve ihbar.
    Sayım sunucuda SQL'de. Yoklanmaz: anahtar `['ozet', …]` altında olduğu için
    yeni SOS ya da ihbar canlı akışta gelince tazelenir (kural 4); şerit
    başlangıcı saat başına yuvarlandığından anahtar saatte bir değişir. */

export const YOGUNLUK_DILIMI_SN = 3600

export type OlayYogunlugu = {
  baslangic: number
  bitis: number
  dilimSn: number
  sos: number[]
  ihbar: number[]
}

export function useOlayYogunlugu(seritBaslangicMs: number) {
  const baslangic = Math.floor(seritBaslangicMs / 1000 / YOGUNLUK_DILIMI_SN) * YOGUNLUK_DILIMI_SN
  return useQuery({
    queryKey: ['ozet', 'yogunluk', baslangic],
    queryFn: () =>
      apiGet<OlayYogunlugu>('/api/olay-yogunlugu', { baslangic, dilimSn: YOGUNLUK_DILIMI_SN }),
    placeholderData: keepPreviousData,
  })
}
