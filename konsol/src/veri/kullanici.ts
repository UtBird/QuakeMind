import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPatch, apiPost } from './istemci'
import type { Rol } from '@/kimlik/roller'

/* ---------------------------------------------------------------------------
   Hesap yönetimi (J-155, J-156, J-157). Kayıt ekranından açılan her hesap
   afetzede olur; ekip ve koordinasyon hesaplarını koordinasyon açar, düzenler,
   askıya alır. Kim neyi yapabilir SUNUCU söyler (`verebilecegiRoller`); ekran
   yalnız gösterir. Liste canlı akıştaki "hesap" mesajıyla tazelenir (kural 4).
--------------------------------------------------------------------------- */

export type KullaniciSatiri = {
  id: string
  eposta: string
  adSoyad: string
  rol: Rol
  ekipId: string | null
  /** epoch ms */
  olusturuldu: number | null
  sonGiris: number | null
  /** Askıdaki hesap giremez; açık oturumu da geçersizdir. */
  askida: boolean
  /** Geçici şifreyle açıldı / şifresi yenilendi; henüz kendi şifresini koymadı. */
  sifreDegismeli: boolean
}

export type KullaniciListesi = {
  kullanicilar: KullaniciSatiri[]
  /** Oturumdaki kişinin verebileceği roller (sunucunun kuralı). */
  verebilecegiRoller: Rol[]
  benimId: string
}

export type HesapAcmaIstegi = {
  eposta: string
  adSoyad: string
  rol: Exclude<Rol, 'afetzede'>
  ekipId?: string
}

/** Şifre sunucuda üretilir ve YALNIZ bu yanıtta bir kez gelir; saklanmaz. */
export type GeciciSifreli = { kullanici: KullaniciSatiri; geciciSifre: string }

/** Gönderilmeyen alan değişmez; `ekipId: null` kişiyi ekipten çıkarır. */
export type HesapGuncelleme = {
  adSoyad?: string
  rol?: Rol
  ekipId?: string | null
  askida?: boolean
}

export type HesapKaydi = {
  id: number
  /** epoch ms */
  zaman: number
  yapanId: string | null
  yapanAd: string | null
  hedefId: string
  hedefAd: string | null
  hedefEposta: string | null
  islem:
    | 'hesap-acildi'
    | 'rol-degisti'
    | 'ekip-degisti'
    | 'ad-degisti'
    | 'askiya-alindi'
    | 'etkinlestirildi'
    | 'sifre-yenilendi'
    | 'sifre-degistirildi'
  ayrinti: Record<string, unknown> | null
}

function tazele(qc: ReturnType<typeof useQueryClient>) {
  void qc.invalidateQueries({ queryKey: ['kullanicilar'] })
  void qc.invalidateQueries({ queryKey: ['hesap-kayitlari'] })
  void qc.invalidateQueries({ queryKey: ['uye-adaylari'] })
  void qc.invalidateQueries({ queryKey: ['ekipler'] })
}

export function useKullanicilar() {
  return useQuery({
    queryKey: ['kullanicilar'],
    queryFn: () => apiGet<KullaniciListesi>('/api/oturum/kullanicilar'),
  })
}

/** Kayıt defteri; `kullaniciId` verilirse yalnız o kişinin geçmişi. */
export function useHesapKayitlari(kullaniciId?: string | null, acik = true) {
  return useQuery({
    queryKey: ['hesap-kayitlari', kullaniciId ?? 'hepsi'],
    enabled: acik,
    queryFn: () =>
      apiGet<HesapKaydi[]>('/api/oturum/hesap-kayitlari', {
        kullaniciId: kullaniciId ?? undefined,
        sinir: kullaniciId ? 50 : 200,
      }),
  })
}

export function useHesapAc() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (g: HesapAcmaIstegi) => apiPost<GeciciSifreli>('/api/oturum/kullanicilar', g),
    onSettled: () => tazele(qc),
  })
}

export function useHesapGuncelle() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...g }: HesapGuncelleme & { id: string }) =>
      apiPatch<{ kullanici: KullaniciSatiri; degisen: string[] }>(`/api/oturum/kullanicilar/${id}`, g),
    onSettled: () => tazele(qc),
  })
}

export function useSifreSifirla() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (kullaniciId: string) =>
      apiPost<{ kullaniciId: string; geciciSifre: string }>(
        `/api/oturum/kullanicilar/${kullaniciId}/sifre`,
        {},
      ),
    onSettled: () => tazele(qc),
  })
}
