import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react'
import maplibregl, { type Map as MlMap } from 'maplibre-gl'
import { MapboxOverlay } from '@deck.gl/mapbox'
import type { Layer, PickingInfo } from '@deck.gl/core'
import 'maplibre-gl/dist/maplibre-gl.css'
import '@/stil/harita.css'
import { ANTAKYA, haritaStili } from './haritaStili'
import type { Kutu } from '@/durum/secimDurumu'
import { haritaIpucu } from './katmanlar'

/* ---------------------------------------------------------------------------
   TEK harita örneği (MIMARI §7, CLAUDE.md kural 6).
   Harita uygulama iskeletinde bir kez kurulur; mod değişince yeniden kurulmaz.
   Bileşenler katmanlarını `useHarita().katmanlariYaz()` ile verir.
--------------------------------------------------------------------------- */

type HaritaApi = {
  hazir: boolean
  /** Görünen alan ve yakınlaştırma; harita durunca (moveend) güncellenir, yoklama yok. */
  gorunum: { kutu: Kutu; zoom: number } | null
  katmanlariYaz: (katmanlar: Layer[]) => void
  /** Haritadaki bir nesneye tıklanınca çağrılır (seç ve yakınlaş). */
  tiklamaYaz: (fn: (bilgi: PickingInfo) => void) => void
  /** Kutuya sığdırarak uçar (tüm bölge görünümü). */
  kutuyaUc: (kutu: Kutu) => void
  ucus: (lon: number, lat: number, zoom?: number) => void
  haritaAl: () => MlMap | null
}

const Baglam = createContext<HaritaApi | null>(null)

export function useHarita(): HaritaApi {
  const api = useContext(Baglam)
  if (!api) throw new Error('useHarita, HaritaKabugu içinde çağrılmalı.')
  return api
}

type KabukSecenekleri = {
  children: React.ReactNode
  /** Haritanın dış kabının yerleşimi; verilmezse konsol yerleşimi. */
  className?: string
  /** Üstüne gelince bilgi; verilmezse konsolun ipucu (J-41). */
  ipucu?: (bilgi: PickingInfo) => ReturnType<typeof haritaIpucu>
  /** Açılış görünümü; verilmezse Antakya. */
  baslangic?: { lon: number; lat: number; zoom: number }
}

export function HaritaKabugu({ children, className, ipucu, baslangic }: KabukSecenekleri) {
  const kutu = useRef<HTMLDivElement>(null)
  const harita = useRef<MlMap | null>(null)
  const ortu = useRef<MapboxOverlay | null>(null)
  const [hazir, setHazir] = useState(false)
  const [gorunum, setGorunum] = useState<HaritaApi['gorunum']>(null)

  useEffect(() => {
    if (!kutu.current || harita.current) return

    const m = new maplibregl.Map({
      container: kutu.current,
      style: haritaStili(),
      center: [(baslangic ?? ANTAKYA).lon, (baslangic ?? ANTAKYA).lat],
      zoom: (baslangic ?? ANTAKYA).zoom,
      pitch: 0,
      bearing: 0,
      dragRotate: false,
      attributionControl: false,
      // Kaynak künyesi ve ölçek ekranda ayrıca duruyor (ARAYUZ §11).
    })
    m.touchZoomRotate.disableRotation()
    m.addControl(new maplibregl.ScaleControl({ unit: 'metric', maxWidth: 96 }), 'bottom-right')

    // Üstüne gelince bilgi (J-41): ne, ne zaman, ne kadar acil.
    const o = new MapboxOverlay({ interleaved: false, layers: [], getTooltip: ipucu ?? haritaIpucu })
    m.addControl(o)

    harita.current = m
    ortu.current = o
    const gorunumuYaz = () => {
      const b = m.getBounds()
      setGorunum({ kutu: [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()], zoom: m.getZoom() })
    }
    m.on('load', () => {
      setHazir(true)
      gorunumuYaz()
    })
    m.on('moveend', gorunumuYaz)

    return () => {
      setHazir(false)
      ortu.current = null
      harita.current = null
      m.remove()
    }
  }, [])

  // İşlevler yalnız ref okur; görünüm değişince yeniden kurulmazlar. Kurulsalardı
  // onlara bağlı her etki her kaydırmada yeniden koşar, haritayı geri uçururdu.
  const islevler = useMemo<Omit<HaritaApi, 'hazir' | 'gorunum'>>(
    () => ({
      katmanlariYaz: (katmanlar) => ortu.current?.setProps({ layers: katmanlar }),
      tiklamaYaz: (fn) => ortu.current?.setProps({ onClick: fn }),
      kutuyaUc: (k) => {
        const azalt = window.matchMedia('(prefers-reduced-motion: reduce)').matches
        // Geniş düzende paneller ve zaman şeridi haritanın üstünde durur; kutu
        // onların arasındaki açık alana sığdırılır (ölçüler token dosyasından).
        const kok = getComputedStyle(document.documentElement)
        const px = (ad: string) => parseFloat(kok.getPropertyValue(ad)) || 0
        const genis = window.matchMedia(`(min-width: ${px('--breakpoint-genis')}px)`).matches
        const pay = px('--spacing-gutter') * 3
        harita.current?.fitBounds(
          [
            [k[0], k[1]],
            [k[2], k[3]],
          ],
          {
            padding: genis
              ? {
                  top: pay * 2,
                  bottom: px('--spacing-timeline') + pay * 2,
                  left: px('--spacing-panel-l') + pay,
                  right: px('--spacing-panel-r') + pay,
                }
              : pay,
            duration: azalt ? 0 : 1000,
          },
        )
      },
      ucus: (lon, lat, zoom = 15) => {
        const azalt = window.matchMedia('(prefers-reduced-motion: reduce)').matches
        harita.current?.flyTo({
          center: [lon, lat],
          zoom,
          duration: azalt ? 0 : 900, // seçimde 700-1100 ms (ARAYUZ §7)
        })
      },
      haritaAl: () => harita.current,
    }),
    [],
  )
  const api = useMemo<HaritaApi>(() => ({ hazir, gorunum, ...islevler }), [hazir, gorunum, islevler])

  return (
    <Baglam.Provider value={api}>
      {/* Dar ekranda harita üstte durur; geniş ekranda paneller haritanın üstüne biner.
          Yerleşim sınıfları DIŞ kutuda: MapLibre kendi kabına `position: relative`
          yazıyor ve doğrudan verilen `absolute` sınıfını eziyor. */}
      <div className={className ?? 'h-72 w-full shrink-0 genis:absolute genis:inset-0 genis:h-auto'}>
        <div ref={kutu} className="h-full w-full" aria-label="Durum haritası" role="application" />
      </div>
      {children}
    </Baglam.Provider>
  )
}
