import { useMemo } from 'react'
import { useHarita } from './HaritaKabugu'
import type { EtiketSeviyesi } from './katmanlar'
import type { Kutu } from '@/durum/secimDurumu'
import { kutularKesisir, useAltlikKatalogu, useAltlikPaketleri, type Etiket } from '@/veri/altlik'

/* Altlığın görünen alana göre seçimi: konsol ve afetzede haritası aynı kuralı
   kullanır (J-40, J-41, J-50). Yalnız görünen bölgelerin paketleri iner. */

/** Altlık bölge ölçeğinde çizilir; bundan uzakta paket indirilmez. */
export const ALTLIK_EN_AZ_ZOOM = 9
/** Yapılar bu yakınlaştırmadan itibaren seçilir; altında katman kurulmaz. */
export const YAPI_EN_AZ_ZOOM = 13
/** Toplanma alanları (J-56): beş bölgede 3.682 kayıt var; bölge ölçeğinde
    hepsi çizilince harita nokta tarlasına dönüyordu. Şehir ölçeğinde çizilir. */
export const TOPLANMA_EN_AZ_ZOOM = 11

/** Yakınlaştırmaya göre yazılan adlar (J-41): uzakta bölge adı, sonra şehir ve
    ilçe, köy, mahalle, en yakında sokak. */
export function etiketSeviyesi(zoom: number | undefined): EtiketSeviyesi {
  if (zoom === undefined || zoom < ALTLIK_EN_AZ_ZOOM) return -1
  if (zoom < 12) return 0
  if (zoom < 13) return 1
  if (zoom < 15) return 2
  return 3
}

/** "Antakya (Hatay)" → "Antakya": düğme ve uzak ad kısa yazılır. */
export const kisaAd = (ad: string) => ad.replace(/\s*\(.*\)\s*$/, '')

export const kutuMerkezi = (k: Kutu): [number, number] => [(k[0] + k[2]) / 2, (k[1] + k[3]) / 2]

/** Görünen alanla kesişen altlık bölgeleri (katalogdan). `ulke` paketi
    (J-40 sınırı: il daireleri ve operasyon bölgeleri dışında zemin boştu)
    zoom ve kesişimden bağımsız her zaman eklenir; detaylı paketler onun
    üstüne çizilsin diye dizide ondan sonra gelir. */
export function useGorunenAltlik() {
  const { gorunum } = useHarita()
  const katalog = useAltlikKatalogu()
  const gorunen = useMemo(() => {
    if (!gorunum || !katalog.data) return []
    const ulke = katalog.data.filter((b) => b.tur === 'ulke')
    if (gorunum.zoom < ALTLIK_EN_AZ_ZOOM) return ulke
    const digerleri = katalog.data.filter(
      (b) => b.tur !== 'ulke' && kutularKesisir(b.kutu, gorunum.kutu),
    )
    return [...ulke, ...digerleri]
  }, [katalog.data, gorunum])
  return { katalog, gorunum, gorunen }
}

/** Altlık katmanlarının girdisi: paketler, yapı görünürlüğü, ad seviyesi. */
export function useAltlikGirdisi() {
  const { gorunen, gorunum, katalog } = useGorunenAltlik()
  const altlik = useAltlikPaketleri(gorunen)
  const bolgeAdlari = useMemo<Etiket[]>(
    () =>
      (katalog.data ?? [])
        .filter((b) => b.tur !== 'ulke')
        .map((b) => {
          const [lon, lat] = kutuMerkezi(b.kutu)
          return { ad: kisaAd(b.ad), lon, lat, aci: 0, oncelik: 100 }
        }),
    [katalog.data],
  )
  return {
    altlik,
    altlikYapiGorunur: (gorunum?.zoom ?? 0) >= YAPI_EN_AZ_ZOOM,
    bolgeAdlari,
    adSeviyesi: etiketSeviyesi(gorunum?.zoom),
    gorunen,
    katalog,
    gorunum,
  }
}
