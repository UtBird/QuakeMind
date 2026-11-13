import { useQuery } from '@tanstack/react-query'
import { apiGet, apiPost } from './istemci'
import type { Kutu } from '@/durum/secimDurumu'

/* ---------------------------------------------------------------------------
   Uydu hasar analizi — modelin koştuğu iş.

   Akış (MIMARI §3-§4, CLAUDE.md kural 3):
     1. POST /api/road_damage/analyze  → HTTP 202 + iş kimliği (model burada
        koşmaz, iş kuyruğa girer)
     2. ilerleme canlı akıştan gelir: `is-durumu` mesajları
     3. "bitti" mesajı gelince sonuç TEK istekle indirilir — yoklama yok
--------------------------------------------------------------------------- */

export const BOLGELER = [
  { id: 'antakya', ad: 'Antakya (Hatay)', lat: 36.202, lon: 36.161 },
  { id: 'maras', ad: 'Kahramanmaraş', lat: 37.57, lon: 36.93 },
  { id: 'antep', ad: 'Gaziantep', lat: 37.06, lon: 37.38 },
  { id: 'malatya', ad: 'Malatya', lat: 38.35, lon: 38.3 },
  { id: 'adiyaman', ad: 'Adıyaman', lat: 37.76, lon: 38.27 },
] as const

export type BolgeId = (typeof BOLGELER)[number]['id']

/** Görüntü kaynağı — sonucun künyesine yazılır (kural 1). */
export const KAYNAKLAR = [
  { id: 'google', ad: 'Güncel uydu görüntüsü' },
  { id: 'esri', ad: 'Esri Wayback (tarihli arşiv)' },
  { id: 'oam', ad: 'OpenAerialMap' },
] as const

export type KaynakId = (typeof KAYNAKLAR)[number]['id']

/* ---- Esri Wayback: tarihli uydu görüntüsü arşivi ----------------------- */

export type WaybackSurumu = { id: string; date: string; label: string }

/** Sürüm listesi neredeyse durağandır; SSE'den de tazelenmez, bir kez çekilir. */
export function useWaybackSurumleri() {
  return useQuery({
    queryKey: ['wayback-surumleri'],
    queryFn: async () => {
      const y = await apiGet<{ versions: WaybackSurumu[] }>('/api/road_damage/wayback_versions')
      return y.versions
    },
  })
}

/** Çalışma alanımızın olayı: 6 Şubat 2023 depremleri. */
export const DEPREM_TARIHI = '2023-02-06'

/* Wayback'te sürüm tarihi görüntünün ÇEKİM tarihi değildir (J-35): sürüm bir
   karoyu güncellemediyse karo eski sürümden gelir, görüntü de sürümden aylar
   önce çekilmiş olabilir. Ölçüldü: Antakya merkezinde 23 Şubat 2023 sürümü
   27 Eylül 2021 çekimini gösteriyor; deprem sonrası ilk çekim ancak 8 Şubat
   2024 sürümünde geliyor. Sunucu, analizin kullanacağı yakınlaştırmada konumun
   görüntü geçmişini Esri'nin metadata katmanından çıkarır. */

export type WaybackGoruntu = {
  /** Bu görüntüyü getiren (karoyu güncelleyen) sürüm. */
  surumId: string
  surumTarihi: string
  cekimTarihi: string | null
  /** Uydu: WV02, WV03, LG02… */
  kaynak: string | null
  cozunurlukM: number | null
  olaySonrasi: boolean | null
}

export type WaybackGoruntuGecmisi = {
  zoom: number
  olayTarihi: string
  /** Yeniden eskiye. */
  surumler: WaybackGoruntu[]
  /** "taban": olaydan önce yayımlanmış ilk sürüme inildi; "karo-yok": daha
      eski sürümlerde bu yakınlaştırmada karo yok. */
  bitis: 'taban' | 'karo-yok' | 'sinir' | 'arsiv-basi' | 'bilinmeyen-surum'
}

/** Soğuk ilk istek Esri'ye birkaç çağrı yapar (1–6 sn); sonuç değişmez, önbellekte kalır. */
export function useWaybackGoruntuGecmisi(g: {
  lat: number
  lon: number
  radiusKm: number
  aktif: boolean
}) {
  return useQuery({
    queryKey: ['wayback-goruntuler', g.lat, g.lon, g.radiusKm],
    enabled: g.aktif,
    queryFn: () =>
      apiGet<WaybackGoruntuGecmisi>('/api/road_damage/wayback_goruntuler', {
        latitude: g.lat,
        longitude: g.lon,
        radiusKm: g.radiusKm,
      }),
  })
}

/** Seçili sürümün bu konumda gösterdiği görüntü: sürüm tarihinden önce ya da
    o gün gelen en yeni görüntü. Bilinen geçmişten eskiyse tanımsız. */
export function surumunGoruntusu(
  surumTarihi: string,
  gecmis: WaybackGoruntuGecmisi | undefined,
): WaybackGoruntu | undefined {
  return gecmis?.surumler.find((g) => g.surumTarihi <= surumTarihi)
}

/** Depremden sonra çekilmiş en erken görüntü — hasar aramaya en uygun olanı. */
export function ilkOlaySonrasi(gecmis: WaybackGoruntuGecmisi | undefined) {
  return [...(gecmis?.surumler ?? [])]
    .filter((g) => g.olaySonrasi && g.cekimTarihi)
    .sort(
      (a, b) =>
        a.cekimTarihi!.localeCompare(b.cekimTarihi!) || a.surumTarihi.localeCompare(b.surumTarihi),
    )[0]
}

/** Depremden önce çekilmiş en yeni görüntü. */
export function sonOlayOncesi(gecmis: WaybackGoruntuGecmisi | undefined) {
  return gecmis?.surumler.find((g) => g.olaySonrasi === false)
}

/** Çekimin depremden kaç gün sonra (eksi: önce) yapıldığı. */
export function olaydanGun(cekimTarihi: string): number {
  return Math.round((Date.parse(cekimTarihi) - Date.parse(DEPREM_TARIHI)) / 86_400_000)
}

/** Merkez + yarıçaptan analiz kutusu — sunucudaki bbox_from_center ile aynı formül. */
export function merkezKutusu(lon: number, lat: number, yaricapKm: number): Kutu {
  const r = Math.max(0.5, yaricapKm)
  const dLat = r / 111
  const dLon = r / (111 * Math.max(Math.cos((lat * Math.PI) / 180), 0.2))
  return [lon - dLon, lat - dLat, lon + dLon, lat + dLat]
}

/** Görüntünün sınır kutusu analiz alanının ne kadarını kapsıyor (0–1). Sınır
    kutusu görüntünün gerçek izinden büyük olabilir; bu bir üst sınırdır. */
export function kapsamaOrani(goruntu: Kutu, alan: Kutu): number {
  const g = Math.max(0, Math.min(goruntu[2], alan[2]) - Math.max(goruntu[0], alan[0]))
  const y = Math.max(0, Math.min(goruntu[3], alan[3]) - Math.max(goruntu[1], alan[1]))
  const alanBoyu = (alan[2] - alan[0]) * (alan[3] - alan[1])
  return alanBoyu > 0 ? (g * y) / alanBoyu : 0
}

/** Analiz alanını seçilen görüntünün üstüne taşır (J-160).

    Görüntü alandan küçükse (drone sahneleri ~0,5 km) alan görüntünün kendisi
    olur. Büyükse alanın boyu korunur, merkezi görüntünün içine kaydırılır ve
    görüntüyle kesiştirilir. Böylece model hiç görüntü olmayan yeri taramaz.
    Ölçüm: Defne/Elektrik, şehir merkezi + 2,5 km → z17, 0 kapalı yol; görüntü
    alanı → z18, 8 kapalı yol. */
export function goruntuyeTasinmisAlan(goruntu: Kutu, alan: Kutu): Kutu {
  const gAlan = (goruntu[2] - goruntu[0]) * (goruntu[3] - goruntu[1])
  const aAlan = (alan[2] - alan[0]) * (alan[3] - alan[1])
  if (gAlan <= aAlan) return goruntu
  const yG = (alan[2] - alan[0]) / 2
  const yB = (alan[3] - alan[1]) / 2
  const sinirla = (x: number, a: number, b: number) => (a > b ? (a + b) / 2 : Math.min(Math.max(x, a), b))
  const mx = sinirla((alan[0] + alan[2]) / 2, goruntu[0] + yG, goruntu[2] - yG)
  const my = sinirla((alan[1] + alan[3]) / 2, goruntu[1] + yB, goruntu[3] - yB)
  return [
    Math.max(goruntu[0], mx - yG),
    Math.max(goruntu[1], my - yB),
    Math.min(goruntu[2], mx + yG),
    Math.min(goruntu[3], my + yB),
  ]
}

/** Bu orandan az kapsayan görüntüyle analiz başlatılmaz (J-160): sonuç büyük
    ölçüde boş görüntüden çıkar ve "hasar yok" gibi okunur. */
export const EN_AZ_KAPSAMA = 0.5

/* ---- OpenAerialMap: tarih aralığıyla görüntü arama ---------------------- */

export type OamGoruntu = {
  id: string
  title: string
  provider: string
  /** ISO zaman damgası, ör. "2023-02-12T17:00:00.000Z" */
  date: string
  tms_url: string
  /** [batı, güney, doğu, kuzey] */
  bbox: [number, number, number, number]
}

/** Deprem bölgesinde varsayılan görüntü (J-35): Maxar uydu görüntüsü, analiz
    alanını en çok kapsayan; neredeyse tam kapsayanlar arasında en erken çekilen
    (enkaz kaldırılmadan önce). Drone ve hava fotoğrafları santimetre
    çözünürlükte; model 0,3–0,5 m uydu görüntüsüyle eğitildi (J-26), önerilmez. */
export function oamOnerisi(goruntuler: OamGoruntu[], alan: Kutu) {
  return goruntuler
    .filter((g) => g.provider.toLowerCase().includes('maxar'))
    .map((g) => ({ goruntu: g, oran: kapsamaOrani(g.bbox, alan) }))
    .filter((x) => x.oran > 0)
    .sort(
      (a, b) =>
        (b.oran >= 0.95 ? 1 : b.oran) - (a.oran >= 0.95 ? 1 : a.oran) ||
        a.goruntu.date.localeCompare(b.goruntu.date),
    )[0]
}

export type OamAramaGirdisi = {
  lat: number
  lon: number
  baslangic: string
  bitis: string
  kutu?: Kutu | null
  /** Arama yalnız düğmeye basılınca koşar. */
  aktif: boolean
}

export function useOamArama(g: OamAramaGirdisi) {
  return useQuery({
    queryKey: ['oam-arama', g.lat, g.lon, g.baslangic, g.bitis, g.kutu?.join(',') ?? ''],
    enabled: g.aktif,
    queryFn: async () => {
      const parametreler: Record<string, string | number> = {
        latitude: g.lat,
        longitude: g.lon,
        dateStart: g.baslangic,
        dateEnd: g.bitis,
      }
      if (g.kutu) {
        parametreler.bboxWest = g.kutu[0]
        parametreler.bboxSouth = g.kutu[1]
        parametreler.bboxEast = g.kutu[2]
        parametreler.bboxNorth = g.kutu[3]
      }
      const y = await apiGet<{ images: OamGoruntu[] }>(
        '/api/road_damage/oam_search',
        parametreler,
      )
      return y.images
    },
  })
}

/* ---- Etkin uydu modeli: künye (J-36) ------------------------------------ */

/** Sunucuda koşan modelin künye özeti. Karar ayarlarının varsayılanı buradan
    gelir: model hangi eşikle ölçüldüyse üründe de o eşikle koşar. */
export type UyduModeli = {
  ad: string
  etiket: string
  mimari: string
  kodlayici: string
  esik: number
  guclendirme: number
  sonIsleme: number
  kararKaynagi?: string | null
  /** Eğitim görüntülerinin çözünürlüğü, [en küçük, en büyük] m/piksel. */
  egitimGsdM: [number, number]
  sha256Kisa: string
  olcum: { sinamaIoU?: number | null; dogrulamaIoU?: number | null; not?: string }
}

/** Model yeniden başlatmadan değişmez; bir kez çekilir. */
export function useUyduModeli() {
  return useQuery({
    queryKey: ['uydu-modeli'],
    queryFn: () => apiGet<UyduModeli>('/api/road_damage/model'),
  })
}

/** Analizde seçilebilecek bütün modeller (modeller/uydu/*.json). */
export type AnalizModeli = {
  ad: string
  etiket: string
  mimari: string
  sinamaIoU: number | null
  esik: number
  guclendirme: number
  sonIsleme: number
  egitimGsdM: [number, number]
  ileriGecis512Sn: number | null
  agirlikSha256: string
  hazir: boolean
  etkin: boolean
}

export function useAnalizModelleri() {
  return useQuery({
    queryKey: ['analiz-modeller'],
    queryFn: () => apiGet<{ modeller: AnalizModeli[] }>('/api/road_damage/modeller'),
    select: (d) => d.modeller,
    staleTime: 5 * 60_000,
  })
}


export type AnalizIstegi = {
  city: string
  latitude: number
  longitude: number
  source: KaynakId
  /** Gönderilmezse sunucu modelin künyesindeki değeri kullanır. */
  threshold?: number
  damageBooster?: number
  postProcessLevel?: number
  radiusKm: number
  /** source === 'esri' ise hangi tarihli Wayback sürümü kullanılacak. */
  waybackId?: string
  /** Hangi model koşsun (modeller/uydu/<ad>). Verilmezse sunucunun etkin modeli. */
  modelAdi?: string
  /** source === 'oam' ise seçilen görüntünün karo adresi. */
  oamTileUrl?: string
  /** J-161: eğitim ölçeğinden bir kademe yakın (deneysel, varsayılan kapalı). */
  yakinCekim?: boolean
  /** Haritada alan seçildiyse merkez+yarıçap yerine bu kutu analiz edilir. */
  bboxWest?: number
  bboxSouth?: number
  bboxEast?: number
  bboxNorth?: number
}

export type AnalizSonucu = {
  analysisId: string
  status: 'queued' | 'done' | 'error'
  city?: string
  /** Koşumun kendi künyesi: hangi kaynaktan, hangi arşiv sürümünden. */
  imagerySource?: string
  imageryLabel?: string
  waybackId?: string | null
  oamTitle?: string | null
  /** Fiilen kullanılan yakınlaştırma; istenende karo yoksa sunucu aşağı iner. */
  imageryZoom?: number
  imageryRequestedZoom?: number
  /** Bu koşu eğitim ölçeğinden bir kademe yakın mı yapıldı (J-161, deneysel). */
  yakinCekim?: boolean
  /** Wayback'te alanın çekimleri (sürümün metadata katmanından); öbür kaynaklarda boş. */
  imageryCaptures?: { cekimTarihi: string | null; kaynak: string | null; cozunurlukM: number | null }[]
  imageryEventTiming?: 'pre' | 'post' | 'mixed' | 'unknown'
  damageRate?: number
  /** Görüntünün BOŞ olmayan piksel oranı (0–1). Düşükse model çoğunlukla boşluk
      taramıştır; "0 kapalı yol" o zaman "hasar yok" demek değildir (J-160). */
  validPixelRatio?: number
  openRoads?: number
  blockedRoads?: number
  openRoadPct?: number
  blockedRoadPct?: number
  closureRule?: string
  blockageRadiusM?: number
  threshold?: number
  damageBooster?: number
  postProcessLevel?: number
  /** Sonucu üreten model ve bu analizin görüntü çözünürlüğü (J-36). */
  model?: UyduModeli & { kullanilanGsdM: number; gsdUyarisi: boolean }
  recommendedAction?: string
  bounds?: { west: number; south: number; east: number; north: number }
  error?: string
}

/** İstek yolunda model koşmaz: uç 202 döner, iş kuyrukta işlenir. */
export function analizBaslat(istek: AnalizIstegi) {
  return apiPost<{ analysisId: string; status: string }>('/api/road_damage/analyze', istek)
}

/** Canlı akış "bitti" dediğinde bir kez çağrılır.

    Tam sonuç ~17 MB'dir; bunun ~16 MB'i tanı görselleri, ~1,7 MB'i geometri.
    Panel yalnız sayıları ve künyeyi gösterdiği için ikisini de istemiyoruz:
    özet ~1 KB iner, geometri ayrı ve önbelleklenebilir uçtan gelir. */
export function analizSonucuAl(isId: string) {
  return apiGet<AnalizSonucu>(`/api/road_damage/status/${isId}`, {
    gorseller: 0,
    segmentler: 0,
  })
}

/* ---- Analiz geometrisi: haritaya binen yollar ------------------------- */

/** Sunucu [enlem, boylam] sırasıyla gönderir (Leaflet düzeni); deck.gl
    [boylam, enlem] ister. Çevirme tek yerde yapılır. */
export type Yol = [number, number][]

export type AnalizSegmentleri = {
  analysisId: string
  bounds?: { west: number; south: number; east: number; north: number }
  kapali: Yol[]
  acik: Yol[]
}

function cevir(segmentler: [number, number][][] | undefined): Yol[] {
  return (segmentler ?? []).map((yol) => yol.map(([enlem, boylam]) => [boylam, enlem] as [number, number]))
}

/** Analiz bitince değişmeyen veri: bir kez çekilir, önbellekte kalır. */
export function useAnalizSegmentleri(isId: string | null) {
  return useQuery({
    queryKey: ['analiz-segmentleri', isId],
    enabled: !!isId,
    queryFn: async () => {
      const y = await apiGet<{
        analysisId: string
        bounds?: AnalizSegmentleri['bounds']
        safeRoadSegments: [number, number][][]
        blockedRoadSegments: [number, number][][]
      }>(`/api/road_damage/segments/${isId}`)
      return {
        analysisId: y.analysisId,
        bounds: y.bounds,
        kapali: cevir(y.blockedRoadSegments),
        acik: cevir(y.safeRoadSegments),
      } satisfies AnalizSegmentleri
    },
  })
}
