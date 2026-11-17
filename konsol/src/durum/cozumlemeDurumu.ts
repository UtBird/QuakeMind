import { create } from 'zustand'

/** Metin ve kamera çözümlemelerinin son sonucu: sol panel gönderir, sağ panel
    gösterir. Sorgu değil tek seferlik iş olduğu için ayrı bir depoda durur. */

export type MetinSonucu = {
  kategori: string
  konum: [number, number] | null
  konum_metin: string | null
  konum_adaylari: string[]
  aciliyet: number
  guven_skoru: number
  nlpLocationId?: string
}

type CozumlemeDurumu = {
  metin: { girdi: string; sonuc: MetinSonucu; zaman: number } | null
  metinYaz: (girdi: string, sonuc: MetinSonucu) => void
  /** Risk modunda seçili bölge: iki panel aynı seçimi paylaşır. */
  riskBolge: string | null
  riskBolgeSec: (id: string) => void
}

/** Kamera tespitleri — sunucu biçimi: güven yüzde (0-100).
    `siddet` bina modelinin sınıfından gelir; çatlak modelinin tek sınıfı
    derece taşımaz ("belirsiz", J-165). `severity` eski istemciler içindir. */
export type KameraTespiti = {
  label: string
  sinif: string
  confidence: number
  model: string
  box: number[]
  siddet: 'agir' | 'orta' | 'yok' | 'belirsiz'
  severity: 'CRITICAL' | 'SAFE' | 'UNRATED'
}

export type KameraSonucu = {
  status: 'CRITICAL_EVACUATE' | 'CRACK_FOUND' | 'SAFE_SURFACE' | 'NO_DETECTION' | string
  modelType: string
  activeModels: string[]
  detections: KameraTespiti[]
  /** Eski istemciler için sunucunun işaretlediği resim; konsol kutuları kendi çizer. */
  annotatedImage: string | null
  advice: string
  imageWidth: number | null
  imageHeight: number | null
  sureMs?: number
  timestamp: string
}

/** Son analiz: sonuç + gönderilen fotoğraf (kutular tarayıcıda bunun üstüne çizilir). */
type KameraDurumu = {
  sonuc: KameraSonucu | null
  gorsel: string | null
  dosyaAdi: string | null
  yaz: (s: KameraSonucu, gorsel: string, dosyaAdi: string) => void
}

export const useKameraCozumleme = create<KameraDurumu>((set) => ({
  sonuc: null,
  gorsel: null,
  dosyaAdi: null,
  yaz: (sonuc, gorsel, dosyaAdi) => set({ sonuc, gorsel, dosyaAdi }),
}))

export const useCozumleme = create<CozumlemeDurumu>((set) => ({
  metin: null,
  metinYaz: (girdi, sonuc) => set({ metin: { girdi, sonuc, zaman: Date.now() } }),
  riskBolge: null,
  riskBolgeSec: (id) => set({ riskBolge: id }),
}))
