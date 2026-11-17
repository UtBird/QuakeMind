import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiGet } from './istemci'
import type { Rol } from '@/kimlik/roller'

/* İşlem kaydı (J-165): kim, ne zaman, ne yaptı. Silinmez, değiştirilmez.
   Sunucu: GET /api/islem-kayitlari (yalnız koordinatör ve yönetici).
   Yeni kayıt gelince canlı akıştaki "islem-kaydi" mesajı listeyi tazeler. */

export type IslemTuru =
  | 'kamera_analizi'
  | 'metin_analizi'
  | 'hasar_analizi_basladi'
  | 'hasar_analizi_bitti'
  | 'hasar_analizi_hata'
  | 'tatbikat_basladi'
  | 'tatbikat_bitti'
  | 'tatbikat_hata'
  | 'tatbikat_kapatildi'
  | 'sevk'
  | 'gorev_durumu'
  | 'sos_kapatildi'
  | 'ihbar_durumu'
  | 'ekip_eklendi'
  | 'ekip_degisti'
  | 'ekip_uyeleri'
  | 'bildirim_yayinlandi'
  | 'bildirim_geri_cekildi'
  | 'giris_basarili'
  | 'giris_basarisiz'
  | 'cikis'
  | 'kayit_oldu'
  | 'konum_paylasimi_basladi'
  | 'goruntuleme'

export type IslemKaydi = {
  id: number
  zaman: number
  yapanId: string | null
  yapanAd: string | null
  yapanRol: Rol | null
  tur: IslemTuru
  hedefTur: string | null
  hedefId: string | null
  ozet: string
  ayrinti: Record<string, unknown> | null
  /** Hash zinciri (J-166): bu kaydın ve bir öncekinin SHA-256 özeti. */
  hash: string | null
  oncekiHash: string | null
}

type Sayfa = { kayitlar: IslemKaydi[]; devami: boolean }

/** Satırın kısa etiketi ve tonu. Ton yalnız hata ve geri çekme için uyarı rengi alır. */
export const ISLEM_TURU: Record<IslemTuru, { ad: string; hata?: true }> = {
  kamera_analizi: { ad: 'Kamera analizi' },
  metin_analizi: { ad: 'Metin analizi' },
  hasar_analizi_basladi: { ad: 'Hasar analizi başladı' },
  hasar_analizi_bitti: { ad: 'Hasar analizi bitti' },
  hasar_analizi_hata: { ad: 'Hasar analizi hatası', hata: true },
  tatbikat_basladi: { ad: 'Tatbikat başladı' },
  tatbikat_bitti: { ad: 'Tatbikat bitti' },
  tatbikat_hata: { ad: 'Tatbikat hatası', hata: true },
  tatbikat_kapatildi: { ad: 'Tatbikat kapatıldı' },
  sevk: { ad: 'Ekip gönderildi' },
  gorev_durumu: { ad: 'Görev adımı' },
  sos_kapatildi: { ad: 'SOS kapatıldı' },
  ihbar_durumu: { ad: 'İhbar durumu' },
  ekip_eklendi: { ad: 'Ekip eklendi' },
  ekip_degisti: { ad: 'Ekip değişti' },
  ekip_uyeleri: { ad: 'Ekip hesapları' },
  bildirim_yayinlandi: { ad: 'Bildirim yayınlandı' },
  bildirim_geri_cekildi: { ad: 'Bildirim geri çekildi', hata: true },
  giris_basarili: { ad: 'Giriş' },
  giris_basarisiz: { ad: 'Başarısız giriş', hata: true },
  cikis: { ad: 'Çıkış' },
  kayit_oldu: { ad: 'Hesap açtı' },
  konum_paylasimi_basladi: { ad: 'Konum paylaşımı' },
  goruntuleme: { ad: 'Görüntüleme' },
}

/** Hazır süzgeçler: kaydı açan kişinin gerçek soruları. */
export const ISLEM_GRUPLARI = [
  { id: 'hepsi', etiket: 'Tümü', turler: null },
  {
    id: 'analiz',
    etiket: 'Analizler',
    turler: [
      'kamera_analizi',
      'metin_analizi',
      'hasar_analizi_basladi',
      'hasar_analizi_bitti',
      'hasar_analizi_hata',
      'tatbikat_basladi',
      'tatbikat_bitti',
      'tatbikat_hata',
      'tatbikat_kapatildi',
    ],
  },
  { id: 'sevk', etiket: 'Sevk ve görev', turler: ['sevk', 'gorev_durumu'] },
  { id: 'olay', etiket: 'SOS ve ihbar', turler: ['sos_kapatildi', 'ihbar_durumu'] },
  {
    id: 'ekip',
    etiket: 'Ekip ve konum',
    turler: ['ekip_eklendi', 'ekip_degisti', 'ekip_uyeleri', 'konum_paylasimi_basladi'],
  },
  { id: 'bildirim', etiket: 'Bildirimler', turler: ['bildirim_yayinlandi', 'bildirim_geri_cekildi'] },
  { id: 'giris', etiket: 'Girişler', turler: ['giris_basarili', 'giris_basarisiz', 'cikis', 'kayit_oldu'] },
  { id: 'goruntuleme', etiket: 'Görüntülemeler', turler: ['goruntuleme'] },
] as const satisfies ReadonlyArray<{ id: string; etiket: string; turler: readonly IslemTuru[] | null }>

export type IslemGrubu = (typeof ISLEM_GRUPLARI)[number]['id']

const SAYFA = 100

export function useIslemKayitlari(grup: IslemGrubu) {
  const turler = ISLEM_GRUPLARI.find((g) => g.id === grup)?.turler ?? null
  return useInfiniteQuery({
    queryKey: ['islem-kayitlari', grup],
    initialPageParam: null as number | null,
    queryFn: ({ pageParam }) =>
      apiGet<Sayfa>('/api/islem-kayitlari', {
        tur: turler ? [...turler] : undefined,
        once: pageParam ?? undefined,
        sinir: SAYFA,
      }),
    getNextPageParam: (son) => (son.devami && son.kayitlar.length ? son.kayitlar[son.kayitlar.length - 1].id : null),
  })
}

/** Zincir doğrulamasının sonucu (J-166). */
export type ZincirDenetimi = {
  zaman?: number
  yapanAd?: string | null
  kapsam: 'tam' | 'artimli'
  saglam: boolean
  dogrulanan: number
  sonId: number | null
  sonHash: string | null
  bozukId: number | null
  neden: string | null
  sureMs: number | null
  zincirOncesi?: number
  baslangicId?: number | null
}

/** Son doğrulamanın sonucu; doğrulama yapmaz, ekran açılışında ucuzdur. */
export function useSonZincirDenetimi() {
  return useQuery({
    queryKey: ['islem-zinciri', 'son'],
    queryFn: () => apiGet<ZincirDenetimi | null>('/api/islem-kayitlari/son-denetim'),
  })
}

/** Zinciri doğrular. Varsayılan artımlı (son sağlam denetimden sonrası);
    `tam`: baştan sona, 100 bin kayıtta ~3 sn ölçüldü. */
export function useZinciriDogrula() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (tam: boolean) =>
      apiGet<ZincirDenetimi>('/api/islem-kayitlari/dogrula', { tam: tam ? 'true' : undefined }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['islem-zinciri'] }),
  })
}
