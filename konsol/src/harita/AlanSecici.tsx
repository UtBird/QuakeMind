import { useEffect } from 'react'
import type { MapMouseEvent } from 'maplibre-gl'
import { useHarita } from './HaritaKabugu'
import { cokgenKutusu, useSecim, type Nokta } from '@/durum/secimDurumu'

/* ---------------------------------------------------------------------------
   Haritada analiz alanı çizimi.

   · "Nokta seç": tek tıklama analiz merkezini taşır.
   · "Alan çiz": basılı tut ve sürükle → dikdörtgen.
   · "Çokgen çiz": her tıklama bir köşe; Bitir düğmesi, çift tıklama ya da
     Enter kapatır, Esc vazgeçer.

   Çizim durumu tamamen mağazada tutulur (köşeler dahil): panel ile harita
   aynı veriyi görür, efekt yeniden kurulsa da köşeler kaybolmaz.
--------------------------------------------------------------------------- */

export function AlanSecici() {
  const { hazir, haritaAl } = useHarita()
  const modu = useSecim((d) => d.modu)

  // Moddan çıkınca yarım kalan çizim iptal: köşeler başka moda taşınmasın.
  useEffect(() => () => useSecim.getState().cizimiIptal(), [])

  useEffect(() => {
    const harita = haritaAl()
    if (!hazir || !harita) return

    const durum = useSecim.getState

    if (modu === 'sehir') {
      harita.getCanvas().style.cursor = ''
      return
    }
    harita.getCanvas().style.cursor = 'crosshair'

    // --- nokta seç -------------------------------------------------------
    if (modu === 'nokta') {
      const tiklama = (e: MapMouseEvent) => durum().merkezSec([e.lngLat.lng, e.lngLat.lat])
      harita.on('click', tiklama)
      return () => {
        harita.off('click', tiklama)
        harita.getCanvas().style.cursor = ''
      }
    }

    // --- dikdörtgen ------------------------------------------------------
    if (modu === 'alan') {
      let baslangic: Nokta | null = null

      const bas = (e: MapMouseEvent) => {
        baslangic = [e.lngLat.lng, e.lngLat.lat]
        harita.dragPan.disable()
        durum().taslakKutu([baslangic[0], baslangic[1], baslangic[0], baslangic[1]])
      }
      const surukle = (e: MapMouseEvent) => {
        if (!baslangic) return
        durum().taslakKutu(cokgenKutusu([baslangic, [e.lngLat.lng, e.lngLat.lat]]))
      }
      const birak = (e: MapMouseEvent) => {
        if (!baslangic) return
        const kutu = cokgenKutusu([baslangic, [e.lngLat.lng, e.lngLat.lat]])
        baslangic = null
        harita.dragPan.enable()
        // Kazara tek tıklamada minik kutu oluşmasın.
        if (kutu[2] - kutu[0] < 1e-4 || kutu[3] - kutu[1] < 1e-4) {
          durum().taslakKutu(null)
          return
        }
        durum().kutuSec(kutu)
      }

      harita.on('mousedown', bas)
      harita.on('mousemove', surukle)
      harita.on('mouseup', birak)
      return () => {
        harita.off('mousedown', bas)
        harita.off('mousemove', surukle)
        harita.off('mouseup', birak)
        harita.dragPan.enable()
        harita.getCanvas().style.cursor = ''
      }
    }

    // --- çokgen ----------------------------------------------------------
    const tiklama = (e: MapMouseEvent) => durum().koseEkle([e.lngLat.lng, e.lngLat.lat])
    const bitir = () => durum().cizimiBitir()
    const tus = (e: KeyboardEvent) => {
      if (e.key === 'Enter') {
        e.preventDefault()
        durum().cizimiBitir()
      }
      if (e.key === 'Escape') durum().cizimiIptal()
      if (e.key === 'Backspace' && durum().ciziyor) {
        e.preventDefault()
        durum().sonKoseyiSil()
      }
    }

    harita.on('click', tiklama)
    harita.on('dblclick', bitir)
    harita.doubleClickZoom.disable()
    window.addEventListener('keydown', tus)
    return () => {
      harita.off('click', tiklama)
      harita.off('dblclick', bitir)
      harita.doubleClickZoom.enable()
      window.removeEventListener('keydown', tus)
      harita.getCanvas().style.cursor = ''
    }
  }, [hazir, modu, haritaAl])

  return null
}
