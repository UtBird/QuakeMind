import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost, apiPut } from './istemci'
import { mesafe, sureMetni } from '@/lib/bicim'

/* ---------------------------------------------------------------------------
   Sevk görevi ve ekip (J-54).

   Kullanıcı: "hangi ihbar, neredeki ihbar, hangi ekip gidecek ya da gidiyor,
   kaç kişi gidiyor; bunlar hep belirsiz."

   Her sevk bir görevdir: olay (SOS ya da ihbar), ekip, giden kişi sayısı,
   atayan ve durum sırası. Durumu hem ekip kendi telefonundan hem koordinasyon
   (telsizle gelen bilgi) işaretler; her adım kimden geldiğiyle yazılır.
   Mesafeler sunucuda hesaplanır ve kuş uçuşudur; ekran bunu yazar.
--------------------------------------------------------------------------- */

export type GorevDurumu = 'atandi' | 'yolda' | 'olay-yerinde' | 'tamamlandi' | 'iptal'
export type HedefTur = 'sos' | 'ihbar'
export type EkipTuru = 'arama-kurtarma' | 'saglik' | 'itfaiye' | 'lojistik' | 'diger'

/** Bir nokta ve en yakın yer adı (altlığın OSM yer listesinden; 5 km içinde yoksa boş). */
export type Konum = {
  lon: number
  lat: number
  yerAdi?: string | null
  zaman?: number | null
}

export type GorevAdimi = {
  durum: GorevDurumu
  zaman: number
  kisiAd?: string | null
  /** "ekip": ekibin kendi telefonundan · "koordinasyon": konsoldan (telsizle gelen bilgi). */
  kaynak: 'ekip' | 'koordinasyon'
  not?: string | null
}

/** Görevin gittiği olayın özeti. */
export type HedefOzeti = {
  tur: 'sos' | 'fotograf' | 'metin' | 'ihtiyac'
  id: string
  lon: number
  lat: number
  mahalle?: string | null
  oncelik?: 'kritik' | 'yuksek' | 'orta' | null
  etiket?: string | null
  durum?: string | null
}

/** Ekipten olaya yoldan (J-55): araç ağında, tek yönlere uyarak, bilinen
    kapanmalardan kaçınarak. Süre yol türüne göre ortalama hız VARSAYIMIYLA
    tahmin; anlık trafik verisi yok. */
export type YolOzeti = {
  mesafeM: number
  sureDk: number
  /** Başka yol olmadığı için rotanın geçtiği bilinen kapanma sayısı. */
  kapanmadanGecer: number
  /** Rotanın hasar noktasına 400 m'den yakın kısmı. */
  riskliM: number
  /** Ekibin konumundan en yakın yola düz uzaklık. */
  baglantiM?: number
}

export type Gorev = {
  id: string
  hedefTur: HedefTur
  hedefId: string
  durum: GorevDurumu
  kisiSayisi: number
  /** Olaya zaten ekip giderken gönderildi. */
  ekDestek: boolean
  atandi: number
  yolaCikti: number | null
  vardi: number | null
  bitti: number | null
  ekip: {
    id: string
    ad: string
    kurum?: string | null
    tur?: EkipTuru | null
  }
  /** Ekibin atandığı andaki konumu: "nereden geliyor". */
  cikis: Konum | null
  /** Ekibin son bildirdiği konum; yalnız görev açıkken. */
  ekipKonumu: Konum | null
  /** Ekipten olaya kuş uçuşu (m); yalnız görev açıkken ve ekibin konumu varsa. */
  kalanM: number | null
  /** Yoldan uzaklık ve tahmini süre; araç ağı yoksa ya da ekip bölge dışındaysa boş. */
  yol?: YolOzeti | null
  /** Ekipten olaya rota çizgisi [lon, lat]. */
  rota?: [number, number][] | null
  /* Yalnız konsolda (afetzedeye gelmez): */
  not?: string | null
  sonuc?: string | null
  olaySuruyor?: boolean
  atayanAd?: string | null
  adimlar?: GorevAdimi[]
  hedef?: HedefOzeti | null
}

/** Ekibin şu anki görevi (ekip listesinde). */
export type EkipGorevi = {
  id: string
  durum: GorevDurumu
  kisiSayisi: number
  atandi: number
  yolaCikti: number | null
  vardi: number | null
  kalanM: number | null
  yol?: YolOzeti | null
  rota?: [number, number][] | null
  hedefTur: HedefTur
  hedefId: string
  hedef: HedefOzeti | null
}

export type Ekip = {
  id: string
  ad: string
  kurum?: string | null
  tur?: EkipTuru | null
  kisiSayisi?: number | null
  lon: number | null
  lat: number | null
  /** Konumun en son ne zaman bildirildiği. */
  konumZamani?: number | null
  yerAdi?: string | null
  /** Elle verilen durum. Görevde olup olmadığı `gorev`den okunur. */
  durum: 'musait' | 'hizmet-disi' | string
  /** Hizmet dışı değil ve açık görevi yok. */
  musait: boolean
  gorev: EkipGorevi | null
  uyeler: { id: string; adSoyad: string }[]
  guncellendi?: number
}

export const EKIP_TURU: Record<EkipTuru, string> = {
  'arama-kurtarma': 'Arama-kurtarma',
  saglik: 'Sağlık',
  itfaiye: 'İtfaiye',
  lojistik: 'Lojistik',
  diger: 'Diğer',
}

/* Kırmızı, turuncu ve sarı yalnız hasar ve aciliyet içindir (ARAYUZ §2):
   görev durumu vurgu rengi, yeşil ve nötrle ayrılır. */
export const GOREV_DURUMU: Record<
  GorevDurumu,
  { ad: string; kisa: string; ton: 'accent' | 'ok' | 'nötr'; afetzede: string }
> = {
  atandi: {
    ad: 'Atandı, henüz yola çıkmadı',
    kisa: 'Atandı',
    ton: 'nötr',
    afetzede: 'Ekip görevlendirildi',
  },
  yolda: { ad: 'Yolda', kisa: 'Yolda', ton: 'accent', afetzede: 'Ekip yolda' },
  'olay-yerinde': {
    ad: 'Olay yerinde',
    kisa: 'Olay yerinde',
    ton: 'ok',
    afetzede: 'Ekip olay yerinde',
  },
  tamamlandi: {
    ad: 'Tamamlandı',
    kisa: 'Tamamlandı',
    ton: 'nötr',
    afetzede: 'Ekip işini bitirdi',
  },
  iptal: {
    ad: 'İptal edildi',
    kisa: 'İptal',
    ton: 'nötr',
    afetzede: 'Görev iptal edildi',
  },
}

/** Zaman çizelgesinin sırası. İptal ayrı gösterilir. */
export const GOREV_ADIMLARI: GorevDurumu[] = ['atandi', 'yolda', 'olay-yerinde', 'tamamlandi']

/** Sıradaki adım ve düğmedeki adı. */
export const SONRAKI_ADIM: Partial<
  Record<GorevDurumu, { durum: GorevDurumu; eylem: string; ekipEylemi: string }>
> = {
  atandi: { durum: 'yolda', eylem: 'Yola çıktı', ekipEylemi: 'Yola çıktık' },
  yolda: {
    durum: 'olay-yerinde',
    eylem: 'Olay yerine vardı',
    ekipEylemi: 'Vardık',
  },
  'olay-yerinde': {
    durum: 'tamamlandi',
    eylem: 'İş bitti',
    ekipEylemi: 'İşimiz bitti',
  },
}

export const acikGorev = (g: { durum: GorevDurumu }) =>
  g.durum === 'atandi' || g.durum === 'yolda' || g.durum === 'olay-yerinde'

/** Adımın zamanı: görevin kendi zaman alanlarından. */
export function adimZamani(
  g: Pick<Gorev, 'atandi' | 'yolaCikti' | 'vardi' | 'bitti' | 'durum'>,
  d: GorevDurumu,
) {
  if (d === 'atandi') return g.atandi
  if (d === 'yolda') return g.yolaCikti
  if (d === 'olay-yerinde') return g.vardi
  return g.durum === d ? g.bitti : null
}

/** "AKUT · Arama-kurtarma" (kurum ve tür; yazılmamışsa boş). */
export function kurumTur(e: { kurum?: string | null; tur?: EkipTuru | null }) {
  return [e.kurum, e.tur ? EKIP_TURU[e.tur] : null].filter(Boolean).join(' · ')
}

/** "~7 dk · yoldan 2,3 km"; araç ağında rota yoksa "kuş uçuşu 1,2 km". */
export function uzaklikMetni(yol: YolOzeti | null | undefined, kusUcusuM: number | null | undefined): string | null {
  if (yol) return `~${sureMetni(yol.sureDk)} · yoldan ${mesafe(yol.mesafeM)}`
  if (kusUcusuM != null) return `kuş uçuşu ${mesafe(kusUcusuM)}`
  return null
}

/** Olayın görev özeti, listede tek satır: "AKUT 1 yolda · 6 kişi" ya da
    "2 ekip · 10 kişi · 1'i olay yerinde". Açık görev yoksa null. */
export function gorevOzeti(gorevler: Gorev[] | undefined | null): string | null {
  const acik = (gorevler ?? []).filter(acikGorev)
  if (!acik.length) return null
  if (acik.length === 1) {
    const g = acik[0]
    return `${g.ekip.ad} ${GOREV_DURUMU[g.durum].kisa.toLocaleLowerCase('tr')} · ${g.kisiSayisi} kişi`
  }
  const kisi = acik.reduce((t, g) => t + g.kisiSayisi, 0)
  const varan = acik.filter((g) => g.durum === 'olay-yerinde').length
  return `${acik.length} ekip · ${kisi} kişi${varan ? ` · ${varan}'i olay yerinde` : ''}`
}

/* ---- sorgular ----------------------------------------------------------- */

const GOREV_ANAHTARLARI = [
  ['sos'],
  ['ihbar'],
  ['ekipler'],
  ['aday-ekipler'],
  ['gorevler'],
  ['ozet'],
  ['ekibim'],
]

function hepsiniTazele(qc: ReturnType<typeof useQueryClient>) {
  for (const queryKey of GOREV_ANAHTARLARI) void qc.invalidateQueries({ queryKey })
}

export function useEkipler() {
  return useQuery({
    queryKey: ['ekipler'],
    queryFn: () => apiGet<Ekip[]>('/api/ekipler'),
  })
}

export type AdayEkip = { ekip: Ekip; mesafeM: number | null; yol?: YolOzeti | null }

/** Olaya gönderilebilecek ekipler; önce müsaitler, olaya uzaklığa göre (sunucuda). */
export function useAdayEkipler(hedefTur: HedefTur, hedefId: string | null, acik: boolean) {
  return useQuery({
    queryKey: ['aday-ekipler', hedefTur, hedefId],
    enabled: acik && !!hedefId,
    queryFn: () => apiGet<AdayEkip[]>('/api/gorevler/aday-ekipler', { hedefTur, hedefId }),
  })
}

export type SevkIstegi = {
  hedefTur: HedefTur
  hedefId: string
  ekipId: string
  kisiSayisi?: number
  not?: string
  ekDestek?: boolean
}

export function useSevkEt() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (i: SevkIstegi) => apiPost<Gorev>('/api/gorevler', i),
    onSuccess: () => hepsiniTazele(qc),
  })
}

export type DurumIstegi = {
  gorevId: string
  durum: GorevDurumu
  not?: string
  olaySuruyor?: boolean
}

export function useGorevDurumu() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ gorevId, ...govde }: DurumIstegi) =>
      apiPost<Gorev>(`/api/gorevler/${gorevId}/durum`, govde),
    onSuccess: () => hepsiniTazele(qc),
  })
}

export type Ekibim = {
  ekip: Ekip | null
  gorev: (Gorev & { olay?: Record<string, unknown> | null }) | null
  gecmis: Gorev[]
}

export function useEkibim() {
  return useQuery({
    queryKey: ['ekibim'],
    queryFn: () => apiGet<Ekibim>('/api/ekibim'),
  })
}

export type EkipTanimi = {
  ad: string
  kurum?: string | null
  tur?: EkipTuru | null
  kisiSayisi?: number | null
  lon?: number | null
  lat?: number | null
  durum?: 'musait' | 'hizmet-disi'
}

/** Ekip ekler (kimlik yoksa) ya da günceller. */
export function useEkipKaydet() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...t }: EkipTanimi & { id?: string }) =>
      id ? apiPut<Ekip>(`/api/ekipler/${id}`, { durum: 'musait', ...t }) : apiPost<Ekip>('/api/ekipler', t),
    onSuccess: () => hepsiniTazele(qc),
  })
}

export type UyeAdayi = {
  id: string
  adSoyad: string
  eposta: string
  ekipId: string | null
}

export function useUyeAdaylari(acik: boolean) {
  return useQuery({
    queryKey: ['uye-adaylari'],
    enabled: acik,
    queryFn: () => apiGet<UyeAdayi[]>('/api/ekipler/uye-adaylari'),
  })
}

export function useUyeleriAyarla() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ ekipId, kullaniciIdleri }: { ekipId: string; kullaniciIdleri: string[] }) =>
      apiPut<Ekip>(`/api/ekipler/${ekipId}/uyeler`, { kullaniciIdleri }),
    onSuccess: () => {
      hepsiniTazele(qc)
      void qc.invalidateQueries({ queryKey: ['uye-adaylari'] })
    },
  })
}

export function useEkipKonumu() {
  return useMutation({
    // dogrulukM: telefonun bildirdiği doğruluk; konum geçmişinde saklanır (J-166).
    mutationFn: ({ ekipId, lon, lat, dogrulukM }: { ekipId: string; lon: number; lat: number; dogrulukM?: number }) =>
      apiPost<Ekip>(`/api/ekipler/${ekipId}/konum`, { lon, lat, dogrulukM }),
  })
}

/** SOS çağrısını kapatır; açık görevler de biter (sunucuda, J-54). */
export function useSosKapat() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (sosId: string) => apiPost<unknown>(`/api/sos/${sosId}/kapat`, {}),
    onSuccess: () => hepsiniTazele(qc),
  })
}
