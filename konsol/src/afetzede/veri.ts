import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost } from '@/veri/istemci'
import type { Ihtiyac, SosCagrisi } from '@/veri/sorgular'
import type { AltlikKaynagi } from '@/veri/altlik'
import type { FotografModeli, Ihbar, IhbarTuru, MetinAnalizi, Tespit } from '@/veri/ihbar'
import type { EtkinKonum } from './konum'

/* ---------------------------------------------------------------------------
   Afetzede ekranının verisi (J-43). Konsolun sorgularından ayrı durur: bu yol
   harita motorunu ve analiz modüllerini indirmez (MIMARI §7).

   Tazeleme yalnız canlı akışla olur (kural 4): kendi çağrının durumu değişince
   "yeni-sos" mesajı gelir. Bildirimler ortak modülde (`veri/bildirim.ts`).
--------------------------------------------------------------------------- */

const GUN_MS = 86_400_000

/** Son 7 günün çağrıları. Afetzede yalnız kendininkini alır; bu sınır sunucuda. */
export function useCagrilarim() {
  return useQuery({
    queryKey: ['sos', 'kendi'],
    // Pencere istek anında hesaplanır: anahtar sabit kaldığı için "yeni-sos"
    // mesajı bu sorguyu da tazeler (önek ['sos']).
    queryFn: () => apiGet<SosCagrisi[]>('/api/sos', { baslangic: Date.now() - 7 * GUN_MS }),
  })
}

export type CagriIstegi = {
  lon: number
  lat: number
  oncelik: SosCagrisi['oncelik']
  kisiSayisi: number
  ihtiyaclar?: Ihtiyac[]
  metin?: string
  mahalle?: string
  konumKaynagi: 'gps' | 'mahalle'
  konumDogrulukM?: number
  /** false: afetzede durum seçmeden SOS'a bastı (J-50). */
  durumSecildi?: boolean
}

export function useCagriGonder() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (govde: CagriIstegi) => apiPost<SosCagrisi>('/api/sos', govde),
    // Hata olsa da liste tazelenir: yanıt yolda kaybolduysa çağrı sunucuda
    // açılmış olabilir, afetzede onu listede görür ve ikinci kez göndermez.
    onSettled: () => qc.invalidateQueries({ queryKey: ['sos'] }),
  })
}

/** Altlığı üretilmiş bölgelerin yer adları: konum alınamazsa mahalle seçtirilir. */
export type Yer = {
  ad: string
  tur: 'city' | 'town' | 'village' | 'suburb' | 'neighbourhood' | 'quarter'
  lon: number
  lat: number
  bolge: string
  bolgeAd: string
}

export function useYerler(acik: boolean) {
  return useQuery({
    queryKey: ['altlik-yerler'],
    enabled: acik,
    queryFn: () => apiGet<{ yerler: Yer[] }>('/api/altlik/yerler').then((y) => y.yerler),
  })
}

/* ---- yakındaki yerler (J-50) ---------------------------------------------
   Toplanma alanları AFAD listesinden, hastane / sağlık merkezi / eczane /
   itfaiye / polis yerel OSM kopyasından. Uzaklığı sunucu hesaplar. */

export type YerTuru = 'toplanma' | 'hastane' | 'saglik' | 'eczane' | 'itfaiye' | 'polis'

export type YakinYer = {
  id: string
  tur: YerTuru
  /** OSM'de adı olmayan yer için boş. */
  ad: string | null
  adres: string | null
  lat: number
  lon: number
  /** Kuş uçuşu uzaklık, metre. */
  mesafeM: number
  /** Yürüme mesafesi (J-44): kendi yol ağımızda, hasar cezalı en iyi rotanın
      uzunluğu. Bölgenin yol ağı yoksa ya da yere yol yoksa boş. */
  yuruyusM?: number | null
}

/** Rota ve mesafenin hesaba kattığı bilinen hasar verisi. */
export type RotaHasari = {
  kapanma: number
  hasarNoktasi: number
  /** En yeni kaydın zamanı (ms). */
  sonVeri: number | null
}

export type YakinYerlerYaniti = {
  yerler: Record<YerTuru, YakinYer[]>
  yaricapKm: number
  kaynaklar: { toplanma: string; hizmet: AltlikKaynagi | null }
  /** Hastane vb. yalnız altlığı üretilmiş bölgelerde var; dışarıda "bilinmiyor". */
  hizmetKapsami: { uretildi: boolean; icinde: boolean; bolgeler: string[] }
  /** Yürüme mesafesi hesaplandıysa hangi ağla (J-44); yol ağı yoksa null. */
  yurume: { ag: string; osm: string; baglantiM: number; hasar: RotaHasari } | null
}

export const YAKIN_YARICAP_KM = 5

/** Anahtar ~100 m'ye yuvarlanır: konum biraz oynayınca istek tekrarlanmaz. */
export function useYakinYerler(konum: { lon: number; lat: number } | null) {
  const anahtar = konum ? [konum.lat.toFixed(3), konum.lon.toFixed(3)] : ['yok']
  return useQuery({
    queryKey: ['yakin-yerler', ...anahtar],
    enabled: !!konum,
    queryFn: () =>
      apiGet<YakinYerlerYaniti>('/api/yakin-yerler', {
        lat: konum!.lat,
        lon: konum!.lon,
        yaricapKm: YAKIN_YARICAP_KM,
      }),
  })
}

export type SokakRotasi = {
  /** [lon, lat] */
  koordinatlar: [number, number][]
  uzunlukM: number
  yuruyusDk: number
  kaynak: string
  /** Bilinen kapanmalara karşı denetim (J-181): servis kapanmayı bilmez,
      sunucu adayları denetleyip en az kapanmadan geçeni seçer. */
  kapanma: { cevrede: number; rotada: number; denenenRota: number; sapmaDenendi: boolean }
  uyari: string
}

/** Yürüme rotası (J-44): kendi yol ağımızda, Dijkstra ve hasar cezasıyla.
    Konum sunucudan dışarı çıkmaz; yer seçilince kendiliğinden istenir. */
export type YurumeRotasi = {
  /** [lon, lat] */
  koordinatlar: [number, number][]
  uzunlukM: number
  yuruyusDk: number
  /** Adım adım tarif: rotanın kendisinden hesaplanır (sokak adı OSM'den, dönüş
      yönü sokak geçişindeki açıdan). İlk adımda yürüme yönü de var. */
  adimlar: { ad: string; uzunlukM: number; manevra: Manevra; yon?: string }[]
  algoritma: string
  hasar: RotaHasari & { rotadaRiskliM: number; rotadaKapanma: number }
  baglanti: { baslangicM: number; hedefM: number }
  kaynak: { ag: string; osm: string; uretim: string }
  uyari: string
}

export type Manevra =
  | 'basla'
  | 'duz'
  | 'hafif-sag'
  | 'sag'
  | 'keskin-sag'
  | 'hafif-sol'
  | 'sol'
  | 'keskin-sol'

export function useYurumeRotasi(konum: { lon: number; lat: number } | null, hedef: YakinYer | null) {
  return useQuery({
    // Konum ~10 m'ye yuvarlanır: doğruluk güncellemesinde rota yeniden istenmez.
    queryKey: ['yurume-rota', konum?.lat.toFixed(4), konum?.lon.toFixed(4), hedef?.id],
    enabled: !!konum && !!hedef,
    staleTime: Infinity,
    // 404: bölgenin yol ağı yok; tekrar denemek sonucu değiştirmez.
    retry: false,
    queryFn: () =>
      apiPost<YurumeRotasi>('/api/afetzede/rota', {
        baslangicLat: konum!.lat,
        baslangicLon: konum!.lon,
        hedefLat: hedef!.lat,
        hedefLon: hedef!.lon,
      }),
  })
}

/** Yedek yol tarifi: dış servis (OSRM), yalnız afetzede isteyince ve yalnız
    kendi yol ağımızın olmadığı yerde. Servis kapanmaları bilmez; sunucu
    alternatifleri bilinen kapanmalara karşı denetler (J-181). */
export function useSokakRotasi() {
  return useMutation({
    mutationFn: (g: { baslangicLat: number; baslangicLon: number; hedefLat: number; hedefLon: number }) =>
      apiPost<SokakRotasi>('/api/afetzede/sokak-rotasi', g),
  })
}

/* ---- ihbarlar (J-51) -------------------------------------------------------
   Hasar fotoğrafı, yazılı ihbar ve ihtiyaç talebi. Fotoğraf ve metin önce
   modele incelettirilir (kayıt açmaz); afetzede sonucu görüp isterse ihbarı
   gönderir. Modelin çıktısını sunucu kendi belleğinden alır, istemci göndermez. */

/** Son 7 günün ihbarları; afetzede yalnız kendininkini alır (sunucu sınırı).
    Anahtar ['ihbar'] önekli: canlı akıştaki "ihbar" mesajı bunu da tazeler. */
export function useIhbarlarim() {
  return useQuery({
    queryKey: ['ihbar', 'kendi'],
    queryFn: () => apiGet<Ihbar[]>('/api/ihbarlar', { baslangic: Date.now() - 7 * GUN_MS }),
  })
}

export type FotografAnalizi = {
  analizId: string
  model: FotografModeli
  tespitler: Tespit[]
  hasarVar: boolean
  en: number
  boy: number
  sureMs: number
}

export function useFotografAnalizi() {
  return useMutation({
    mutationFn: (g: { imageBase64: string; model: FotografModeli }) =>
      apiPost<FotografAnalizi>('/api/afetzede/fotograf-analiz', g),
  })
}

export type MetinAnaliziYaniti = MetinAnalizi & { analizId: string; sureMs: number }

export function useMetinAnalizi() {
  return useMutation({
    mutationFn: (metin: string) => apiPost<MetinAnaliziYaniti>('/api/afetzede/metin-analiz', { metin }),
  })
}

export type IhbarIstegi = {
  tur: IhbarTuru
  analizId?: string
  metin?: string
  lon?: number
  lat?: number
  konumKaynagi: 'gps' | 'mahalle' | 'metin'
  konumDogrulukM?: number
  mahalle?: string
  ihtiyaclar?: Ihtiyac[]
  kisiSayisi?: number
}

export function useIhbarGonder() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (g: IhbarIstegi) => apiPost<Ihbar>('/api/ihbarlar', g),
    // SOS'taki gibi: yanıt yolda kaybolsa da liste tazelenir.
    onSettled: () => qc.invalidateQueries({ queryKey: ['ihbar'] }),
  })
}

/** İhbar isteğinin konum alanları: cihaz konumu ya da mahalle merkezi. */
export function konumAlanlari(k: EtkinKonum): Pick<
  IhbarIstegi,
  'lon' | 'lat' | 'konumKaynagi' | 'konumDogrulukM' | 'mahalle'
> {
  return k.kaynak === 'gps'
    ? { lon: k.lon, lat: k.lat, konumKaynagi: 'gps', konumDogrulukM: Math.round(k.dogrulukM) }
    : { lon: k.lon, lat: k.lat, konumKaynagi: 'mahalle', mahalle: k.yer.ad }
}

/* ---- Çevredeki tehlike (J-180) --------------------------------------------
   Kapalı yollar ve hasar bildirilen bölgeler. Koordinatörün ısı haritası
   afetzedeye açık değil (SOS konumları içerir, J-42); bu uç SOS'u saymaz ve
   yalnız en az 3 bildirimli ~250 m'lik kareleri döner. */

export type HasarBolgesi = {
  /** [güney, batı, kuzey, doğu] */
  kare: [number, number, number, number]
  sayi: number
  seviye: 1 | 2 | 3
  kaynaklar: { uydu: number; fotograf: number; metin: number }
  sonZaman: number
}

export type KapaliYol = { id: string; lon: number; lat: number; cizgi: [number, number][] | null }

export type CevreYaniti = {
  kapaliYollar: KapaliYol[]
  hasarBolgeleri: HasarBolgesi[]
  kaynak: { kapaliYollar: string; hasarBolgeleri: string; uyari: string }
  esik: { enAzBildirim: number; kareDerece: number; gun: number }
}

export const CEVRE_YARICAP_KM = 3

export function useCevre(konum: { lon: number; lat: number } | null) {
  // ~100 m'ye yuvarlanır: GPS'in her küçük oynamasında yeniden istenmesin.
  const k = konum ? { lat: Math.round(konum.lat * 1000) / 1000, lon: Math.round(konum.lon * 1000) / 1000 } : null
  return useQuery({
    queryKey: ['afetzede', 'cevre', k?.lat, k?.lon],
    enabled: !!k,
    staleTime: 5 * 60_000,
    placeholderData: (onceki) => onceki,
    queryFn: () => apiGet<CevreYaniti>('/api/afetzede/cevre', { lat: k!.lat, lon: k!.lon, yaricapKm: CEVRE_YARICAP_KM }),
  })
}
