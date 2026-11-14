import { create } from 'zustand'
import type { QueryClient } from '@tanstack/react-query'
import { AKIS_ANAHTARLARI, MESAJ_TIPLERI, tazelenecekler, type CanliMesaj } from './mesajlar'

/* ---------------------------------------------------------------------------
   TEK canlı akış istemcisi (MIMARI §6, CLAUDE.md kural 4).

   · Uygulamada tek bir EventSource açılır; başka hiçbir yerde açılmaz.
   · setInterval ile uç nokta yoklamak YASAKTIR. Sorgular yalnız mesaj gelince
     tazelenir.
   · Uç nokta henüz yoksa akış boş çalışır: bağlantı kurulamaz, durum
     "bağlı değil" olarak gösterilir, yeniden deneme üstel geri çekilmeyle
     seyrekleşir (yoklamaya dönüşmez).
--------------------------------------------------------------------------- */

export type BaglantiDurumu = 'kapali' | 'baglaniyor' | 'bagli' | 'kopuk'

type AkisDurumu = {
  durum: BaglantiDurumu
  sonMesaj: { tip: CanliMesaj['tip']; zaman: number } | null
  mesajSayisi: number
  denemeSayisi: number
  sonrakiDenemeMs: number | null
}

export const useCanliAkisDurumu = create<AkisDurumu>(() => ({
  durum: 'kapali',
  sonMesaj: null,
  mesajSayisi: 0,
  denemeSayisi: 0,
  sonrakiDenemeMs: null,
}))

const ILK_BEKLEME = 2_000
const EN_UZUN_BEKLEME = 60_000
/* Sunucu boşta kalınca 20 sn'de bir `nabiz` olayı gönderir. Bu sürede hiçbir
   sinyal gelmezse bağlantı sessizce ölmüş sayılır: vekil sunucu ya da mobil ağ
   bağlantıyı kapatmadan bırakınca EventSource bunu kendisi fark etmez ve
   ekran "canlı" derken hiçbir mesaj gelmez (J-45 sınamasında görüldü). */
const NABIZ_SINIRI = 45_000
const BEKCI_ARALIGI = 10_000
/* Tazeleme birleştirme (J-158). Afette saniyede onlarca SOS gelebilir; her
   mesaj her açık konsolda listenin TAMAMINI yeniden istetirse sunucu doyar
   (ölçüm: 5 konsol × 50 SOS/sn ≈ 250 tam liste/sn). Aynı sorgu anahtarı için
   ilk mesaj hemen tazeler; pencere içinde gelenler pencere sonunda TEK
   tazelemede birleşir. Sessiz anda gecikme yoktur; yoğunlukta en çok 1 sn. */
export const BIRLESTIRME_PENCERESI_MS = 1_000

/** Anahtar başına ilk-çağrı + son-çağrı birleştirici; saat yalnız mesaj gelince kurulur. */
export function birlestirici(calistir: (anahtar: string[]) => void, pencereMs = BIRLESTIRME_PENCERESI_MS) {
  const acik = new Map<string, { zamanlayici: number; bekleyen: boolean }>()
  const tetikle = (anahtar: string[]) => {
    const ad = JSON.stringify(anahtar)
    const durum = acik.get(ad)
    if (durum) {
      durum.bekleyen = true // pencere sonunda bir kez daha
      return
    }
    calistir(anahtar)
    const kapat = () => {
      const d = acik.get(ad)
      acik.delete(ad)
      if (d?.bekleyen) tetikle(anahtar) // son mesajı kaçırma; yeni pencere açar
    }
    acik.set(ad, { zamanlayici: window.setTimeout(kapat, pencereMs), bekleyen: false })
  }
  const temizle = () => {
    for (const d of acik.values()) window.clearTimeout(d.zamanlayici)
    acik.clear()
  }
  return { tetikle, temizle }
}

export type AkisSecenek = {
  url?: string
  /** Mesajları dinlemek isteyen yerler için (bildirim, harita nabzı). */
  dinleyici?: (m: CanliMesaj) => void
}

export function canliAkisBaslat(qc: QueryClient, secenek: AkisSecenek = {}): () => void {
  const url = secenek.url ?? '/api/live'
  let kaynak: EventSource | null = null
  let zamanlayici: number | null = null
  let kapandi = false
  let deneme = 0
  let enAzBirKezBaglandi = false
  let sonSinyal = 0

  /* Sunucu kopukken yayınlanan mesajları biriktirmez; kopukluk sırasında
     gelen bildirim, geri çekme ya da ekip ataması kaybolur. Bu yüzden akış
     YENİDEN bağlandığında akışa bağlı sorgular bir kez tazelenir. Yoklama
     değildir: yalnız bağlantı geri geldiğinde, bir kez olur. */
  const hepsiniTazele = () => {
    for (const a of AKIS_ANAHTARLARI) void qc.invalidateQueries({ queryKey: a })
  }
  const tazeleyici = birlestirici((anahtar) => void qc.invalidateQueries({ queryKey: anahtar }))

  const isle = (ham: string) => {
    sonSinyal = Date.now()
    let mesaj: CanliMesaj
    try {
      mesaj = JSON.parse(ham) as CanliMesaj
    } catch {
      return // biçimsiz mesaj sessizce atılır, akış kapatılmaz
    }
    if (!mesaj || !MESAJ_TIPLERI.includes(mesaj.tip)) return
    for (const anahtar of tazelenecekler(mesaj)) tazeleyici.tetikle(anahtar)
    useCanliAkisDurumu.setState((d) => ({
      sonMesaj: { tip: mesaj.tip, zaman: Date.now() },
      mesajSayisi: d.mesajSayisi + 1,
    }))
    secenek.dinleyici?.(mesaj)
  }

  const bagla = () => {
    if (kapandi) return
    useCanliAkisDurumu.setState({ durum: 'baglaniyor', sonrakiDenemeMs: null })
    kaynak = new EventSource(url)

    kaynak.onopen = () => {
      sonSinyal = Date.now()
      deneme = 0
      useCanliAkisDurumu.setState({ durum: 'bagli', denemeSayisi: 0, sonrakiDenemeMs: null })
      if (enAzBirKezBaglandi) hepsiniTazele()
      enAzBirKezBaglandi = true
    }
    kaynak.onmessage = (e) => isle(e.data)
    // Sunucu adlandırılmış olay gönderirse (event: yeni-sos) o da aynı yoldan geçer.
    for (const tip of MESAJ_TIPLERI) {
      kaynak.addEventListener(tip, (e) => isle((e as MessageEvent<string>).data))
    }
    kaynak.addEventListener('nabiz', () => {
      sonSinyal = Date.now()
    })
    kaynak.onerror = koptu
  }

  const koptu = () => {
    kaynak?.close()
    kaynak = null
    if (kapandi) return
    deneme += 1
    const bekle = Math.min(EN_UZUN_BEKLEME, ILK_BEKLEME * 2 ** (deneme - 1))
    const sapma = Math.round(bekle * 0.2 * Math.random())
    useCanliAkisDurumu.setState({
      durum: 'kopuk',
      denemeSayisi: deneme,
      sonrakiDenemeMs: bekle + sapma,
    })
    zamanlayici = window.setTimeout(bagla, bekle + sapma)
  }

  // Bekçi yerel bir saattir, sunucuya istek atmaz: yalnız son sinyalin
  // yaşına bakar. Açık görünen ama sessiz akışı kapatıp yeniden bağlar.
  const bekci = window.setInterval(() => {
    if (kaynak?.readyState === EventSource.OPEN && Date.now() - sonSinyal > NABIZ_SINIRI) koptu()
  }, BEKCI_ARALIGI)

  bagla()

  return () => {
    kapandi = true
    tazeleyici.temizle()
    window.clearInterval(bekci)
    if (zamanlayici) window.clearTimeout(zamanlayici)
    kaynak?.close()
    useCanliAkisDurumu.setState({ durum: 'kapali', sonrakiDenemeMs: null })
  }
}
