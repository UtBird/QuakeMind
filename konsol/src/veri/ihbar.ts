import { useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost } from './istemci'
import { IHTIYAC_ADI, type Ihtiyac } from './sorgular'
import type { SorguAraligi } from '@/durum/zamanDurumu'
import type { Gorev } from './gorev'

/* ---------------------------------------------------------------------------
   Afetzede ihbarları (J-51): hasar fotoğrafı, yazılı ihbar, ihtiyaç talebi.
   SOS kendi ucunda kalır (/api/sos); burada yalnız görünen adı ve rengi var,
   çünkü afetzede ekranı ve konsol dört türü yan yana gösterir.

   Renk ve ad tek yerde: afetzedenin "Bildir" düğmesi, konsolun "Son ihbarlar"
   satırı ve harita noktası aynı türü aynı renkle gösterir. Simgeler ayrı
   dosyada (ihbarIkon.ts): canlı akış bu dosyayı ana parçaya çeker, simgeler
   ise yalnız onları çizen ekranla iner.
--------------------------------------------------------------------------- */

export type IhbarTuru = 'fotograf' | 'metin' | 'ihtiyac'
export type IhbarDurumu = 'yeni' | 'goruldu' | 'kapandi'
export type FotografModeli = 'catlak' | 'bina' | 'ikisi'

export type Tespit = {
  model: 'catlak' | 'bina'
  sinif: string | null
  /** Afetzedenin dilinde: "Çatlak", "Ağır yapı hasarı"… */
  ad: string
  /** false: bina modelinin "hasarsız" sınıfı (güvenli demek değildir). */
  hasar: boolean
  skor: number
  /** Modelin kendi olasılığı, 0–1. */
  guven: number
  /** [x1, y1, x2, y2], incelenen görüntünün pikselinde. */
  kutu: [number, number, number, number]
}

export type MetinAnalizi = {
  ilgisiz: boolean
  kategori: string | null
  aciliyet: number | null
  guven: number | null
  konum: { lat: number; lon: number } | null
  konumMetin: string | null
  adaylar: string[]
}

export type Ihbar = {
  id: string
  tur: IhbarTuru
  lon: number
  lat: number
  zaman: number
  durum: IhbarDurumu
  metin?: string | null
  mahalle?: string | null
  etiket?: string | null
  skor?: number | null
  guven?: number | null
  fotografVar: boolean
  konumKaynagi?: 'gps' | 'manuel' | 'mahalle' | 'metin' | null
  konumDogrulukM?: number | null
  bildirilenKategoriAdi?: string
  bildirilenAciliyet?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  mahsurSayisi?: number
  yaraliSayisi?: number
  guncellendi?: number | null
  /* fotoğraf */
  model?: FotografModeli
  tespitler?: Tespit[]
  en?: number
  boy?: number
  /* yazılı ihbar */
  analiz?: MetinAnalizi | null
  /* ihtiyaç */
  ihtiyaclar?: Ihtiyac[]
  kisiSayisi?: number | null
  /** Konsolda: işleyen görevli (afetzedeye gelmez). */
  isleyenAd?: string | null
  /** İhbara giden ekipler, yeniden eskiye (J-54). */
  gorevler?: Gorev[]
}

type TurBilgisi = {
  ad: string
  /** Liste ve düğmede kısa ad. */
  kisa: string
  renk: `--color-${string}`
  /* Tailwind sınıfları açık yazılır ki derleyici bulsun. */
  metin: string
  zemin: string
  soluk: string
  kenar: string
  solKenar: string
}

export const IHBAR_TURU: Record<IhbarTuru | 'sos', TurBilgisi> = {
  sos: {
    ad: 'SOS çağrısı',
    kisa: 'SOS',
    renk: '--color-ihbar-sos',
    metin: 'text-ihbar-sos',
    zemin: 'bg-ihbar-sos',
    soluk: 'bg-ihbar-sos/15',
    kenar: 'border-ihbar-sos',
    solKenar: 'border-l-ihbar-sos',
  },
  fotograf: {
    ad: 'Hasar fotoğrafı',
    kisa: 'Fotoğraf',
    renk: '--color-ihbar-fotograf',
    metin: 'text-ihbar-fotograf',
    zemin: 'bg-ihbar-fotograf',
    soluk: 'bg-ihbar-fotograf/15',
    kenar: 'border-ihbar-fotograf',
    solKenar: 'border-l-ihbar-fotograf',
  },
  metin: {
    ad: 'Yazılı ihbar',
    kisa: 'Metin',
    renk: '--color-ihbar-metin',
    metin: 'text-ihbar-metin',
    zemin: 'bg-ihbar-metin',
    soluk: 'bg-ihbar-metin/15',
    kenar: 'border-ihbar-metin',
    solKenar: 'border-l-ihbar-metin',
  },
  ihtiyac: {
    ad: 'İhtiyaç talebi',
    kisa: 'İhtiyaç',
    renk: '--color-ihbar-ihtiyac',
    metin: 'text-ihbar-ihtiyac',
    zemin: 'bg-ihbar-ihtiyac',
    soluk: 'bg-ihbar-ihtiyac/15',
    kenar: 'border-ihbar-ihtiyac',
    solKenar: 'border-l-ihbar-ihtiyac',
  },
}

export const IHBAR_DURUMU: Record<IhbarDurumu, { ad: string; ton: 'ok' | 'nötr' | 'high'; aciklama: string }> = {
  yeni: { ad: 'Alındı', ton: 'high', aciklama: 'Koordinasyon ekibine ulaştı, henüz incelenmedi.' },
  goruldu: { ad: 'Görüldü', ton: 'ok', aciklama: 'Koordinasyon ekibi ihbarı gördü.' },
  kapandi: { ad: 'Kapandı', ton: 'nötr', aciklama: 'İhbar işlendi ve kapatıldı.' },
}

export const IHTIYAC_SIRASI = Object.keys(IHTIYAC_ADI) as Ihtiyac[]

export const FOTOGRAF_MODELI: Record<FotografModeli, { ad: string; aciklama: string }> = {
  catlak: { ad: 'Çatlak', aciklama: 'Duvar, kolon ya da kirişteki çatlakları arar.' },
  bina: { ad: 'Bina hasarı', aciklama: 'Binanın hasar derecesine bakar: orta ya da ağır hasar.' },
  ikisi: { ad: 'İkisi birden', aciklama: 'Önce çatlak, sonra bina modeli bakar.' },
}

/** Tespitin kutu rengi: haritadaki ve paneldeki hasar rengiyle aynı. */
export function tespitRengi(t: Tespit): `--color-${string}` {
  if (t.sinif === '2_VeryHeavyDamage') return '--color-crit'
  if (t.sinif === '1_ModerateDamage') return '--color-high'
  return '--color-mid'
}

/** Satır başlığı: "Hasar fotoğrafı · Ağır yapı hasarı". */
export function ihbarBasligi(i: Ihbar): string {
  return i.etiket ? `${IHBAR_TURU[i.tur].ad} · ${i.etiket}` : IHBAR_TURU[i.tur].ad
}

/** Konumun nereden geldiği, ekibin okuyacağı dille. */
export function ihbarKonumu(i: Ihbar): string {
  if (i.konumKaynagi === 'metin') {
    return `Metindeki adres: ${i.analiz?.konumMetin ?? 'model buldu'} (yaklaşık)`
  }
  if (i.konumKaynagi === 'mahalle') return `${i.mahalle ?? 'Mahalle'} merkezi (yaklaşık)`
  if (i.konumKaynagi === 'manuel') return 'Elle girilen koordinat'
  if (i.konumDogrulukM != null) return `Cihaz konumu, ±${Math.round(i.konumDogrulukM)} m`
  return 'Cihaz konumu'
}

/* ---- konsol ------------------------------------------------------------- */

/** Konsol: zaman penceresindeki bütün ihbarlar. Canlıda pencere bitişi açık
    (yeni ihbar saat ilerlemeyi beklemeden görünür); listeler tam pencereye
    istemcide süzülür (bkz. zamanDurumu). */
export function useIhbarlar(aralik: SorguAraligi) {
  const { baslangic, bitis, kesinBaslangic } = aralik
  const suz = useCallback(
    (l: Ihbar[]) => (kesinBaslangic == null ? l : l.filter((i) => i.zaman >= kesinBaslangic)),
    [kesinBaslangic],
  )
  return useQuery({
    queryKey: ['ihbar', 'liste', baslangic, bitis ?? 'canli'],
    queryFn: () => apiGet<Ihbar[]>('/api/ihbarlar', { baslangic, bitis: bitis ?? undefined }),
    select: suz,
  })
}

/** Fotoğraf yalnız seçilince iner; değişmez, bir kez alınır. */
export function useIhbarFotografi(id: string | null) {
  return useQuery({
    queryKey: ['ihbar-fotograf', id],
    enabled: !!id,
    staleTime: Infinity,
    gcTime: 5 * 60_000,
    queryFn: () => apiGet<{ veri: string; en: number; boy: number }>(`/api/ihbarlar/${id}/fotograf`),
  })
}

/** Görüldü / kapandı. Sunucu geri gidişi 409 ile reddeder. */
export function useIhbarDurum() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, durum }: { id: string; durum: Exclude<IhbarDurumu, 'yeni'> }) =>
      apiPost<Ihbar>(`/api/ihbarlar/${id}/durum`, { durum }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['ihbar'] }),
  })
}
